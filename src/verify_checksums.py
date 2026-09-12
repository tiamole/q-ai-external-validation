from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CHECKSUM_PATTERN = re.compile(r"^([0-9a-f]{64})  (.+)$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_checksums(package_root: Path = PACKAGE_ROOT) -> list[str]:
    root = package_root.resolve()
    manifest = root / "data-manifest" / "sha256sums.txt"
    failures: list[str] = []
    with manifest.open(encoding="utf-8") as source:
        entries = [line.rstrip("\n") for line in source if line.strip()]
    for line_number, entry in enumerate(entries, start=1):
        match = CHECKSUM_PATTERN.fullmatch(entry)
        if match is None:
            failures.append(f"line {line_number}: malformed checksum entry")
            continue
        expected_hash, relative_path = match.groups()
        target = (root / relative_path).resolve()
        if not target.is_relative_to(root):
            failures.append(f"line {line_number}: path escapes package root")
        elif not target.is_file():
            failures.append(f"missing: {relative_path}")
        else:
            observed_hash = sha256(target)
            if observed_hash != expected_hash:
                failures.append(
                    f"hash mismatch: {relative_path} "
                    f"(expected {expected_hash}, observed {observed_hash})"
                )
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify all frozen source and output SHA-256 checksums."
    )
    parser.add_argument("--package-root", type=Path, default=PACKAGE_ROOT)
    args = parser.parse_args()
    failures = verify_checksums(args.package_root.resolve())
    if failures:
        raise SystemExit("Checksum verification failed:\n" + "\n".join(failures))
    print("All frozen checksums verified.")


if __name__ == "__main__":
    main()
