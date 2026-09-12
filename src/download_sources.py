from __future__ import annotations

import argparse
import csv
import hashlib
import urllib.request
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = Path("data-manifest/source-files.csv")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_source_records(package_root: Path) -> list[dict[str, Any]]:
    manifest_path = package_root / MANIFEST_PATH
    with manifest_path.open(newline="", encoding="utf-8") as source:
        records = list(csv.DictReader(source))
    required = {"record_id", "local_path", "bytes", "local_sha256", "download_url"}
    if not records or not required.issubset(records[0]):
        raise ValueError(f"Source manifest is empty or missing required fields: {manifest_path}")
    return records


def resolve_target(package_root: Path, relative_path: str) -> Path:
    root = package_root.resolve()
    target = (root / relative_path).resolve()
    if not target.is_relative_to(root):
        raise ValueError(f"Manifest path escapes package root: {relative_path}")
    return target


def download_source(
    package_root: Path,
    record: dict[str, Any],
    replace_invalid: bool = False,
) -> str:
    target = resolve_target(package_root, record["local_path"])
    expected_hash = record["local_sha256"].lower()
    expected_bytes = int(record["bytes"])
    if target.is_file():
        observed_hash = sha256(target)
        if observed_hash == expected_hash and target.stat().st_size == expected_bytes:
            return "verified"
        if not replace_invalid:
            raise ValueError(
                f"Existing source does not match its manifest: {record['local_path']}"
            )

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f"{target.name}.part")
    temporary.unlink(missing_ok=True)
    request = urllib.request.Request(
        record["download_url"],
        headers={"User-Agent": "q-ai-external-validation/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response, temporary.open(
            "wb"
        ) as destination:
            for block in iter(lambda: response.read(1024 * 1024), b""):
                destination.write(block)
        observed_hash = sha256(temporary)
        observed_bytes = temporary.stat().st_size
        if observed_hash != expected_hash or observed_bytes != expected_bytes:
            raise ValueError(
                f"Downloaded source failed verification: {record['local_path']} "
                f"(bytes {observed_bytes}/{expected_bytes}, "
                f"SHA-256 {observed_hash}/{expected_hash})"
            )
        temporary.replace(target)
        target.chmod(0o444)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return "downloaded"


def download_all_sources(
    package_root: Path = PACKAGE_ROOT,
    replace_invalid: bool = False,
) -> list[tuple[str, str]]:
    results = []
    for record in load_source_records(package_root):
        status = download_source(package_root, record, replace_invalid)
        results.append((record["record_id"], status))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download and SHA-256 verify the frozen upstream source artifacts."
    )
    parser.add_argument("--package-root", type=Path, default=PACKAGE_ROOT)
    parser.add_argument(
        "--replace-invalid",
        action="store_true",
        help="Replace an existing artifact that does not match the frozen manifest.",
    )
    args = parser.parse_args()
    results = download_all_sources(args.package_root.resolve(), args.replace_invalid)
    for record_id, status in results:
        print(f"{record_id}: {status}")


if __name__ == "__main__":
    main()
