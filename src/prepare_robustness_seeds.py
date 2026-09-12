from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import yaml


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def prepare_seeds(package_root: Path = PACKAGE_ROOT) -> list[int]:
    config_path = package_root / "protocol" / "ROBUSTNESS_ADDENDUM_v1.0.yml"
    with config_path.open(encoding="utf-8") as source:
        config = yaml.safe_load(source)
    bootstrap = config["bootstrap"]
    seed_config = bootstrap["seed_generation"]
    sequence = np.random.SeedSequence(int(seed_config["master_seed"]))
    children = sequence.spawn(int(bootstrap["iterations_per_method"]))
    seeds = [int(child.generate_state(int(seed_config["generated_state_words"]))[0]) for child in children]
    if len(seeds) != len(set(seeds)):
        raise ValueError("Generated bootstrap seed list contains duplicates")

    output_path = package_root / seed_config["output_file"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(str(seed) for seed in seeds) + "\n", encoding="ascii")
    return seeds


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the frozen robustness bootstrap seed list.")
    parser.add_argument("--package-root", type=Path, default=PACKAGE_ROOT)
    args = parser.parse_args()
    seeds = prepare_seeds(args.package_root.resolve())
    print(f"Wrote {len(seeds)} unique bootstrap seeds.")


if __name__ == "__main__":
    main()