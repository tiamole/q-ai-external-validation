from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def verify_results(package_root: Path = PACKAGE_ROOT) -> list[str]:
    output_root = package_root.resolve() / "outputs"
    reproduction = load_json(
        output_root / "reproduction" / "pidgeon-reproduction-summary.json"
    )
    retention = load_json(output_root / "robustness" / "retention-summary.json")
    stability = load_json(output_root / "robustness" / "stability-summary.json")
    failures: list[str] = []

    if reproduction["overall_reproduction_classification"] != "exact_numerical_reproduction":
        failures.append("source analysis is not classified as exact numerical reproduction")
    loading = reproduction["loading_comparison"]
    if loading["status"] != "exact_numerical_reproduction":
        failures.append("loading comparison does not meet exact-reproduction criteria")
    if max(loading["maximum_absolute_difference_by_factor"]) >= loading["absolute_tolerance"]:
        failures.append("at least one reproduced loading exceeds the frozen tolerance")
    if not reproduction["factor_array_comparison"]["integer_scores_identical"]:
        failures.append("reproduced factor-array integer scores are not identical")
    if reproduction["primary_factor_assignment"]["agreement_percent"] != 100.0:
        failures.append("primary-factor assignments do not agree completely")
    if reproduction["distinguishing_statement_direction"]["agreement_percent"] != 100.0:
        failures.append("distinguishing-statement directions do not agree completely")

    parallel = retention["parallel_analysis"]
    if parallel["iterations"] != 1000 or parallel["retained_components"] != [1, 2]:
        failures.append("parallel analysis does not retain the prespecified two components")
    if retention["scree"]["factor_count"] != 2:
        failures.append("maximum-acceleration scree analysis does not select two components")

    expected_counts = {
        "pca": ([16, 6, 6, 4, 1], False),
        "centroid": ([17, 8, 6, 5, 2], True),
    }
    five_factor_rows = {
        row["method"]: row
        for row in retention["retention_diagnostics"]
        if row["factor_count"] == 5 and row["threshold"] == "p01"
    }
    for method, (counts, all_have_minimum) in expected_counts.items():
        row = five_factor_rows.get(method)
        if row is None:
            failures.append(f"missing five-factor {method} retention result")
        elif (
            row["defining_counts"] != counts
            or row["all_factors_have_minimum"] is not all_have_minimum
        ):
            failures.append(f"unexpected five-factor {method} defining-sort result")

    if stability["bootstrap_iterations_per_method"] != 1000:
        failures.append("stability analysis did not use all 1,000 frozen bootstrap seeds")
    if stability["interpretability"] != "pending_independent_assessment":
        failures.append("interpretability status changed from pending independent assessment")
    for method, counts in (("pca", [16, 6, 6, 4, 1]), ("centroid", [17, 8, 6, 5, 2])):
        result = stability["methods"][method]
        if result["reference_defining_counts"] != counts:
            failures.append(f"unexpected {method} stability reference counts")
        if result["stable_factor_count"] != 0:
            failures.append(f"unexpected stable-factor count for {method}")
        if result["solution_classification"] != "fragile_solution":
            failures.append(f"five-factor {method} solution is not classified as fragile")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify platform-independent reproduction and robustness criteria."
    )
    parser.add_argument("--package-root", type=Path, default=PACKAGE_ROOT)
    args = parser.parse_args()
    failures = verify_results(args.package_root.resolve())
    if failures:
        raise SystemExit("Scientific result verification failed:\n" + "\n".join(failures))
    print("All prespecified scientific result criteria verified.")


if __name__ == "__main__":
    main()
