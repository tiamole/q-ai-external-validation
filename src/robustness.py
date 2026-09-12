from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from scipy.optimize import linear_sum_assignment

if __package__:
    from .reproduce_source import forced_score_vector, read_qsort_matrix, varimax
else:
    from reproduce_source import forced_score_vector, read_qsort_matrix, varimax


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_frozen_robustness_config(package_root: Path) -> tuple[dict[str, Any], list[int]]:
    freeze_path = package_root / "protocol" / "robustness-freeze-record.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    for key in ("addendum", "bootstrap_seed_list"):
        record = freeze[key]
        path = package_root / record["path"]
        actual_hash = sha256(path)
        if actual_hash != record["sha256"]:
            raise ValueError(f"Frozen robustness artifact checksum mismatch: {record['path']}")

    addendum_path = package_root / freeze["addendum"]["path"]
    with addendum_path.open(encoding="utf-8") as source:
        config = yaml.safe_load(source)
    seed_path = package_root / freeze["bootstrap_seed_list"]["path"]
    seeds = [int(line) for line in seed_path.read_text(encoding="ascii").splitlines()]
    if len(seeds) != int(freeze["bootstrap_seed_list"]["count"]):
        raise ValueError("Bootstrap seed count differs from the frozen record")
    if len(seeds) != len(set(seeds)):
        raise ValueError("Bootstrap seed list contains duplicates")
    return config, seeds


def centroid_extract(
    correlation_matrix: np.ndarray,
    factor_count: int,
    convergence_threshold: float = 1e-5,
) -> np.ndarray:
    if correlation_matrix.ndim != 2 or correlation_matrix.shape[0] != correlation_matrix.shape[1]:
        raise ValueError("Centroid input must be a square correlation matrix")
    if not np.allclose(correlation_matrix, correlation_matrix.T):
        raise ValueError("Centroid input must be symmetric")

    residual = correlation_matrix.astype(float, copy=True)
    sort_count = residual.shape[0]
    factors = np.empty((sort_count, factor_count), dtype=float)
    for factor_index in range(factor_count):
        np.fill_diagonal(residual, 0.0)
        reflected: list[int] = []
        reflection_steps = 0
        column_sums = residual.sum(axis=0)
        while not np.all(column_sums > 0):
            reflect_index = int(np.argmin(column_sums))
            residual[reflect_index, :] *= -1
            residual[:, reflect_index] *= -1
            reflected.append(reflect_index)
            reflection_steps += 1
            if reflection_steps > sort_count * 20:
                raise RuntimeError("Centroid positive-manifold reflection did not converge")
            column_sums = residual.sum(axis=0)

        estimated_communality = column_sums / (sort_count - 1)
        numerator = estimated_communality + column_sums
        factor = numerator / np.sqrt(numerator.sum())
        extraction_steps = 0
        while not np.all(np.abs(estimated_communality - factor**2) < convergence_threshold):
            estimated_communality = factor**2
            numerator = column_sums + estimated_communality
            factor = numerator / np.sqrt(numerator.sum())
            extraction_steps += 1
            if extraction_steps > 10000:
                raise RuntimeError("Centroid factor extraction did not converge")

        reflected_factor = factor.copy()
        reflected_factor[reflected] *= -1
        factors[:, factor_index] = reflected_factor
        residual = residual - np.outer(factor, factor)
        for reflect_index in reversed(reflected):
            residual[reflect_index, :] *= -1
            residual[:, reflect_index] *= -1
    return factors


def rotate_with_kaiser(loadings: np.ndarray) -> tuple[np.ndarray, int]:
    communalities = np.sqrt(np.sum(loadings**2, axis=1))
    if np.any(communalities == 0):
        raise ValueError("Kaiser normalization is undefined for a zero-communality Q-sort")
    rotated_normalized, iterations = varimax(loadings / communalities[:, np.newaxis])
    return rotated_normalized * communalities[:, np.newaxis], iterations


def extract_rotated_solution(
    qsorts: np.ndarray,
    method: str,
    factor_count: int,
    centroid_threshold: float = 1e-5,
) -> dict[str, Any]:
    correlation_matrix = np.corrcoef(qsorts)
    eigenvalues, eigenvectors = np.linalg.eigh(correlation_matrix)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    if method == "pca":
        unrotated = eigenvectors[:, order[:factor_count]] * np.sqrt(eigenvalues[:factor_count])
    elif method == "centroid":
        unrotated = centroid_extract(correlation_matrix, factor_count, centroid_threshold)
    else:
        raise ValueError(f"Unsupported extraction method: {method}")
    rotated, iterations = rotate_with_kaiser(unrotated)
    return {
        "method": method,
        "eigenvalues": eigenvalues,
        "loadings": rotated,
        "variance_percent": np.sum(rotated**2, axis=0) / qsorts.shape[0] * 100,
        "varimax_iterations": iterations,
    }


def defining_flags(
    loadings: np.ndarray,
    loading_threshold: float,
    confounding_margin: float,
) -> np.ndarray:
    absolute = np.abs(loadings)
    order = np.argsort(absolute, axis=1)
    largest_indexes = order[:, -1]
    largest = np.take_along_axis(absolute, largest_indexes[:, np.newaxis], axis=1)[:, 0]
    second_largest = np.take_along_axis(absolute, order[:, -2:-1], axis=1)[:, 0]
    qualifies = (largest >= loading_threshold) & (
        largest - second_largest >= confounding_margin
    )
    flags = np.zeros_like(loadings, dtype=bool)
    flags[np.arange(loadings.shape[0])[qualifies], largest_indexes[qualifies]] = True
    return flags


def factor_arrays_from_flags(
    qsorts: np.ndarray,
    loadings: np.ndarray,
    flags: np.ndarray,
    minimum_defining_sorts: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    statement_count, factor_count = qsorts.shape[1], loadings.shape[1]
    z_scores = np.full((statement_count, factor_count), np.nan, dtype=float)
    arrays = np.full((statement_count, factor_count), np.nan, dtype=float)
    defining_counts = flags.sum(axis=0).astype(int)
    target_scores = forced_score_vector()
    for factor_index in range(factor_count):
        defining_indexes = np.flatnonzero(flags[:, factor_index])
        if len(defining_indexes) < minimum_defining_sorts:
            continue
        defining_loadings = loadings[defining_indexes, factor_index]
        weights = defining_loadings / (1 - defining_loadings**2)
        weighted_sums = np.sum(qsorts[defining_indexes] * weights[:, np.newaxis], axis=0)
        standard_deviation = np.std(weighted_sums, ddof=1)
        if standard_deviation == 0:
            continue
        factor_z_scores = (weighted_sums - np.mean(weighted_sums)) / standard_deviation
        order = np.argsort(factor_z_scores, kind="stable")
        factor_array = np.empty(statement_count, dtype=int)
        factor_array[order] = target_scores
        z_scores[:, factor_index] = factor_z_scores
        arrays[:, factor_index] = factor_array
    return defining_counts, z_scores, arrays


def align_factor_arrays(reference: np.ndarray, candidate: np.ndarray) -> dict[str, Any]:
    factor_count = reference.shape[1]
    correlations = np.zeros((factor_count, factor_count), dtype=float)
    for reference_index in range(factor_count):
        if not np.isfinite(reference[:, reference_index]).all():
            continue
        for candidate_index in range(factor_count):
            if np.isfinite(candidate[:, candidate_index]).all():
                correlation = np.corrcoef(
                    reference[:, reference_index], candidate[:, candidate_index]
                )[0, 1]
                correlations[reference_index, candidate_index] = abs(float(correlation))
    reference_indexes, candidate_indexes = linear_sum_assignment(-correlations)
    optimum = float(correlations[reference_indexes, candidate_indexes].sum())
    tied_assignments: list[tuple[int, ...]] = []
    for permutation in itertools.permutations(range(factor_count)):
        total = float(
            sum(correlations[index, permutation[index]] for index in range(factor_count))
        )
        if np.isclose(total, optimum, rtol=0.0, atol=1e-12):
            tied_assignments.append(permutation)
    selected_assignment = min(tied_assignments) if tied_assignments else tuple(candidate_indexes)
    matched = np.zeros(factor_count, dtype=float)
    assignment = np.array(selected_assignment, dtype=int)
    for reference_index, candidate_index in enumerate(selected_assignment):
        matched[reference_index] = correlations[reference_index, candidate_index]
    return {
        "matched_correlations": matched,
        "candidate_by_reference": assignment,
        "correlation_matrix": correlations,
    }


def reference_robustness_solution(
    qsorts: np.ndarray,
    method: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    solution = extract_rotated_solution(
        qsorts,
        method,
        int(config["leave_one_sort_out"]["factor_count"]),
        float(config["centroid"]["convergence_threshold"]),
    )
    threshold = 2.58 / np.sqrt(qsorts.shape[1])
    flags = defining_flags(
        solution["loadings"],
        threshold,
        float(config["defining_sorts"]["confounding_margin_absolute_loading"]),
    )
    defining_counts, z_scores, arrays = factor_arrays_from_flags(
        qsorts,
        solution["loadings"],
        flags,
        int(config["defining_sorts"]["minimum_per_factor"]),
    )
    return {
        **solution,
        "flags": flags,
        "defining_counts": defining_counts,
        "z_scores": z_scores,
        "factor_arrays": arrays,
    }


def compare_extraction_methods(
    qsorts: np.ndarray,
    config: dict[str, Any],
) -> dict[str, Any]:
    pca = reference_robustness_solution(qsorts, "pca", config)
    centroid = reference_robustness_solution(qsorts, "centroid", config)
    alignment = align_factor_arrays(pca["factor_arrays"], centroid["factor_arrays"])
    assignment = alignment["candidate_by_reference"]
    return {
        "reference_method": "pca",
        "candidate_method": "centroid",
        "pca_factor": list(range(1, len(assignment) + 1)),
        "matched_centroid_factor": [int(value) + 1 for value in assignment],
        "absolute_factor_array_correlation": [
            float(value) for value in alignment["matched_correlations"]
        ],
        "pca_defining_counts": [int(value) for value in pca["defining_counts"]],
        "matched_centroid_defining_counts": [
            int(value) for value in centroid["defining_counts"][assignment]
        ],
    }


def leave_one_sort_out(
    participant_ids: list[str],
    qsorts: np.ndarray,
    method: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    reference = reference_robustness_solution(qsorts, method, config)
    correlations = np.zeros((len(participant_ids), 5), dtype=float)
    defining_counts = np.zeros((len(participant_ids), 5), dtype=int)
    failures: list[dict[str, str]] = []
    for omitted_index in range(len(participant_ids)):
        reduced_qsorts = np.delete(qsorts, omitted_index, axis=0)
        try:
            candidate = reference_robustness_solution(reduced_qsorts, method, config)
            alignment = align_factor_arrays(reference["factor_arrays"], candidate["factor_arrays"])
            correlations[omitted_index] = alignment["matched_correlations"]
            defining_counts[omitted_index] = candidate["defining_counts"][
                alignment["candidate_by_reference"]
            ]
        except (ValueError, RuntimeError, np.linalg.LinAlgError) as error:
            failures.append(
                {"run_id": participant_ids[omitted_index], "reason": f"{type(error).__name__}: {error}"}
            )
    return {
        "method": method,
        "reference_defining_counts": reference["defining_counts"],
        "participant_ids": participant_ids,
        "correlations": correlations,
        "defining_counts": defining_counts,
        "failures": failures,
    }


def participant_bootstrap(
    qsorts: np.ndarray,
    method: str,
    config: dict[str, Any],
    seeds: list[int],
) -> dict[str, Any]:
    reference = reference_robustness_solution(qsorts, method, config)
    correlations = np.zeros((len(seeds), 5), dtype=float)
    defining_counts = np.zeros((len(seeds), 5), dtype=int)
    failures: list[dict[str, str | int]] = []
    for iteration, seed in enumerate(seeds):
        random = np.random.default_rng(seed)
        sample_indexes = random.integers(0, qsorts.shape[0], size=qsorts.shape[0])
        sampled_qsorts = qsorts[sample_indexes]
        try:
            candidate = reference_robustness_solution(sampled_qsorts, method, config)
            alignment = align_factor_arrays(reference["factor_arrays"], candidate["factor_arrays"])
            correlations[iteration] = alignment["matched_correlations"]
            defining_counts[iteration] = candidate["defining_counts"][
                alignment["candidate_by_reference"]
            ]
        except (ValueError, RuntimeError, np.linalg.LinAlgError) as error:
            failures.append(
                {"run_id": seed, "reason": f"{type(error).__name__}: {error}"}
            )
    return {
        "method": method,
        "reference_defining_counts": reference["defining_counts"],
        "correlations": correlations,
        "defining_counts": defining_counts,
        "failures": failures,
    }


def summarize_stability(
    correlations: np.ndarray,
    stable_thresholds: dict[str, Any],
    analysis: str,
) -> dict[str, Any]:
    median = np.median(correlations, axis=0)
    fifth_percentile = np.percentile(correlations, 5, axis=0, method="linear")
    minimum = np.min(correlations, axis=0)
    if analysis == "leave_one_out":
        stable = fifth_percentile >= float(
            stable_thresholds["leave_one_out_fifth_percentile_correlation_minimum"]
        )
    elif analysis == "bootstrap":
        stable = (
            median >= float(stable_thresholds["bootstrap_median_correlation_minimum"])
        ) & (
            fifth_percentile
            >= float(stable_thresholds["bootstrap_fifth_percentile_correlation_minimum"])
        )
    else:
        raise ValueError(f"Unsupported stability analysis: {analysis}")
    return {
        "median": median,
        "fifth_percentile": fifth_percentile,
        "minimum": minimum,
        "recovery_rate_percent": np.mean(correlations > 0, axis=0) * 100,
        "stable": stable,
    }


def classify_stability(
    leave_stable: np.ndarray,
    bootstrap_stable: np.ndarray,
    reference_defining_counts: np.ndarray,
    minimum_defining_sorts: int,
) -> dict[str, Any]:
    factor_has_minimum = reference_defining_counts >= minimum_defining_sorts
    eligible_leave_stable = leave_stable & factor_has_minimum
    eligible_bootstrap_stable = bootstrap_stable & factor_has_minimum
    factor_stable = eligible_leave_stable & eligible_bootstrap_stable
    stable_count = int(np.sum(factor_stable))
    if stable_count == len(factor_stable):
        solution_class = "stable_solution"
    elif stable_count >= 3:
        solution_class = "mixed_solution"
    else:
        solution_class = "fragile_solution"
    return {
        "reference_has_minimum": bool(np.all(factor_has_minimum)),
        "leave_stable": eligible_leave_stable,
        "bootstrap_stable": eligible_bootstrap_stable,
        "factor_stable": factor_stable,
        "stable_count": stable_count,
        "solution_class": solution_class,
    }


def parallel_analysis(
    qsorts: np.ndarray,
    iterations: int,
    seed: int,
    percentile: float,
    quantile_method: str,
) -> dict[str, Any]:
    observed = np.linalg.eigvalsh(np.corrcoef(qsorts))[::-1]
    null_eigenvalues = np.empty((iterations, len(observed)), dtype=float)
    random = np.random.default_rng(seed)
    for iteration in range(iterations):
        permuted = np.vstack([random.permutation(row) for row in qsorts])
        null_eigenvalues[iteration] = np.linalg.eigvalsh(np.corrcoef(permuted))[::-1]
    threshold = np.percentile(
        null_eigenvalues,
        percentile,
        axis=0,
        method=quantile_method,
    )
    retained = [index + 1 for index, (value, limit) in enumerate(zip(observed, threshold, strict=True)) if value > limit]
    return {
        "observed_eigenvalues": observed,
        "null_mean_eigenvalues": np.mean(null_eigenvalues, axis=0),
        "null_percentile_eigenvalues": threshold,
        "retained_components": retained,
    }


def maximum_acceleration_scree(eigenvalues: np.ndarray, components_considered: int) -> dict[str, Any]:
    considered = eigenvalues[:components_considered]
    acceleration = considered[:-2] - 2 * considered[1:-1] + considered[2:]
    factor_count = int(np.argmax(acceleration) + 2)
    return {
        "factor_count": factor_count,
        "acceleration": acceleration,
        "eigenvalues_considered": considered,
    }


def run_retention_diagnostics(
    package_root: Path = PACKAGE_ROOT,
    output_root: Path | None = None,
    parallel_iterations: int | None = None,
) -> dict[str, Any]:
    config, seeds = load_frozen_robustness_config(package_root)
    matrix_path = package_root / "data" / "normalized" / "pidgeon-2025" / "qsorts_repaired.csv"
    _, qsorts = read_qsort_matrix(matrix_path)
    parallel_config = config["parallel_analysis"]
    iterations = parallel_iterations or int(parallel_config["iterations"])
    parallel = parallel_analysis(
        qsorts,
        iterations,
        int(parallel_config["seed"]),
        float(parallel_config["percentile"]),
        parallel_config["quantile_method"],
    )
    scree = maximum_acceleration_scree(
        parallel["observed_eigenvalues"], int(config["scree"]["components_considered"])
    )

    statement_count = qsorts.shape[1]
    thresholds = {
        "p01": 2.58 / np.sqrt(statement_count),
        "source": float(config["defining_sorts"]["source_threshold"]),
    }
    margin = float(config["defining_sorts"]["confounding_margin_absolute_loading"])
    minimum = int(config["defining_sorts"]["minimum_per_factor"])
    factor_range = range(int(config["factor_counts"]["first"]), int(config["factor_counts"]["last"]) + 1)
    rows: list[dict[str, Any]] = []
    for method in ("pca", "centroid"):
        for factor_count in factor_range:
            solution = extract_rotated_solution(
                qsorts,
                method,
                factor_count,
                float(config["centroid"]["convergence_threshold"]),
            )
            for threshold_name, threshold in thresholds.items():
                flags = defining_flags(solution["loadings"], threshold, margin)
                counts = flags.sum(axis=0)
                rows.append(
                    {
                        "method": method,
                        "factor_count": factor_count,
                        "threshold": threshold_name,
                        "threshold_value": float(threshold),
                        "defining_counts": [int(value) for value in counts],
                        "all_factors_have_minimum": bool(np.all(counts >= minimum)),
                        "total_variance_percent": float(np.sum(solution["variance_percent"])),
                        "parallel_supported_count": len(parallel["retained_components"]),
                        "scree_supported_count": scree["factor_count"],
                        "interpretability": "pending_independent_assessment",
                    }
                )

    output_base = output_root or package_root
    output_directory = output_base / "outputs" / "robustness"
    output_directory.mkdir(parents=True, exist_ok=True)
    with (output_directory / "parallel-analysis.csv").open(
        "w", newline="", encoding="utf-8"
    ) as destination:
        writer = csv.writer(destination, lineterminator="\n")
        writer.writerow(["component", "observed", "null_mean", "null_percentile", "retained"])
        retained_set = set(parallel["retained_components"])
        for index, values in enumerate(
            zip(
                parallel["observed_eigenvalues"],
                parallel["null_mean_eigenvalues"],
                parallel["null_percentile_eigenvalues"],
                strict=True,
            ),
            start=1,
        ):
            writer.writerow([index, *[f"{value:.10f}" for value in values], str(index in retained_set).lower()])

    with (output_directory / "retention-diagnostics.csv").open(
        "w", newline="", encoding="utf-8"
    ) as destination:
        fieldnames = [
            "method",
            "factor_count",
            "threshold",
            "threshold_value",
            "defining_counts",
            "all_factors_have_minimum",
            "total_variance_percent",
            "parallel_supported_count",
            "scree_supported_count",
            "interpretability",
        ]
        writer = csv.DictWriter(destination, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            output_row = dict(row)
            output_row["defining_counts"] = ";".join(str(value) for value in row["defining_counts"])
            writer.writerow(output_row)

    report = {
        "schema_version": "1.0",
        "study_id": "pidgeon-2025",
        "parallel_analysis": {
            "iterations": iterations,
            "retained_components": parallel["retained_components"],
            "null_model": parallel_config["null_model"],
            "percentile": parallel_config["percentile"],
        },
        "scree": {
            "method": config["scree"]["method"],
            "factor_count": scree["factor_count"],
            "acceleration": [float(value) for value in scree["acceleration"]],
        },
        "thresholds": {name: float(value) for name, value in thresholds.items()},
        "confounding_margin": margin,
        "retention_diagnostics": rows,
        "bootstrap_seed_count": len(seeds),
    }
    with (output_directory / "retention-summary.json").open(
        "w", encoding="utf-8", newline="\n"
    ) as destination:
        json.dump(report, destination, indent=2, sort_keys=True)
        destination.write("\n")
    return report


def write_stability_rows(
    path: Path,
    row_ids: list[str],
    correlations: np.ndarray,
    defining_counts: np.ndarray,
) -> None:
    with path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.writer(destination, lineterminator="\n")
        header = ["run_id"]
        for factor in range(1, 6):
            header.extend([f"factor_{factor}_correlation", f"factor_{factor}_defining_sorts"])
        writer.writerow(header)
        for row_id, row_correlations, row_counts in zip(
            row_ids, correlations, defining_counts, strict=True
        ):
            row: list[str | int] = [row_id]
            for correlation, count in zip(row_correlations, row_counts, strict=True):
                row.extend([f"{correlation:.10f}", int(count)])
            writer.writerow(row)


def run_stability_analyses(
    package_root: Path = PACKAGE_ROOT,
    output_root: Path | None = None,
    bootstrap_iterations: int | None = None,
) -> dict[str, Any]:
    config, frozen_seeds = load_frozen_robustness_config(package_root)
    matrix_path = package_root / "data" / "normalized" / "pidgeon-2025" / "qsorts_repaired.csv"
    participant_ids, qsorts = read_qsort_matrix(matrix_path)
    requested_iterations = bootstrap_iterations or int(config["bootstrap"]["iterations_per_method"])
    seeds = frozen_seeds[:requested_iterations]
    if len(seeds) != requested_iterations:
        raise ValueError("Requested more bootstrap iterations than frozen seeds")

    output_base = output_root or package_root
    output_directory = output_base / "outputs" / "robustness"
    output_directory.mkdir(parents=True, exist_ok=True)
    classification = config["descriptive_robustness_classification"]["stable_factor"]
    methods: dict[str, Any] = {}
    for method in config["leave_one_sort_out"]["extraction_methods"]:
        leave_one_out = leave_one_sort_out(participant_ids, qsorts, method, config)
        bootstrap = participant_bootstrap(qsorts, method, config, seeds)
        leave_summary = summarize_stability(
            leave_one_out["correlations"], classification, "leave_one_out"
        )
        bootstrap_summary = summarize_stability(
            bootstrap["correlations"], classification, "bootstrap"
        )
        write_stability_rows(
            output_directory / f"{method}-leave-one-out.csv",
            leave_one_out["participant_ids"],
            leave_one_out["correlations"],
            leave_one_out["defining_counts"],
        )
        write_stability_rows(
            output_directory / f"{method}-bootstrap.csv",
            [str(seed) for seed in seeds],
            bootstrap["correlations"],
            bootstrap["defining_counts"],
        )
        stability_classification = classify_stability(
            leave_summary["stable"],
            bootstrap_summary["stable"],
            leave_one_out["reference_defining_counts"],
            int(config["defining_sorts"]["minimum_per_factor"]),
        )
        methods[method] = {
            "reference_defining_counts": [
                int(value) for value in leave_one_out["reference_defining_counts"]
            ],
            "reference_has_minimum_defining_sorts": stability_classification[
                "reference_has_minimum"
            ],
            "leave_one_out": {
                "runs": len(participant_ids),
                "failed_runs": len(leave_one_out["failures"]),
                "failures": leave_one_out["failures"],
                "factor_recovery_rate_percent": [
                    float(value) for value in leave_summary["recovery_rate_percent"]
                ],
                "median_factor_array_correlation": [
                    float(value) for value in leave_summary["median"]
                ],
                "fifth_percentile_factor_array_correlation": [
                    float(value) for value in leave_summary["fifth_percentile"]
                ],
                "minimum_factor_array_correlation": [
                    float(value) for value in leave_summary["minimum"]
                ],
                "stable_by_factor": [
                    bool(value) for value in stability_classification["leave_stable"]
                ],
            },
            "bootstrap": {
                "runs": len(seeds),
                "failed_runs": len(bootstrap["failures"]),
                "failures": bootstrap["failures"],
                "factor_recovery_rate_percent": [
                    float(value) for value in bootstrap_summary["recovery_rate_percent"]
                ],
                "median_factor_array_correlation": [
                    float(value) for value in bootstrap_summary["median"]
                ],
                "fifth_percentile_factor_array_correlation": [
                    float(value) for value in bootstrap_summary["fifth_percentile"]
                ],
                "minimum_factor_array_correlation": [
                    float(value) for value in bootstrap_summary["minimum"]
                ],
                "stable_by_factor": [
                    bool(value) for value in stability_classification["bootstrap_stable"]
                ],
            },
            "factor_stable_under_both": [
                bool(value) for value in stability_classification["factor_stable"]
            ],
            "stable_factor_count": stability_classification["stable_count"],
            "solution_classification": stability_classification["solution_class"],
        }

    extraction_comparison = compare_extraction_methods(qsorts, config)
    with (output_directory / "pca-centroid-factor-array-comparison.csv").open(
        "w", newline="", encoding="utf-8"
    ) as destination:
        writer = csv.writer(destination, lineterminator="\n")
        writer.writerow(
            [
                "pca_factor",
                "matched_centroid_factor",
                "absolute_factor_array_correlation",
                "pca_defining_sorts",
                "centroid_defining_sorts",
            ]
        )
        for values in zip(
            extraction_comparison["pca_factor"],
            extraction_comparison["matched_centroid_factor"],
            extraction_comparison["absolute_factor_array_correlation"],
            extraction_comparison["pca_defining_counts"],
            extraction_comparison["matched_centroid_defining_counts"],
            strict=True,
        ):
            writer.writerow([values[0], values[1], f"{values[2]:.10f}", values[3], values[4]])

    report = {
        "schema_version": "1.0",
        "study_id": "pidgeon-2025",
        "bootstrap_iterations_per_method": len(seeds),
        "methods": methods,
        "extraction_method_comparison": extraction_comparison,
        "interpretability": "pending_independent_assessment",
        "classification_note": (
            "Descriptive robustness classes follow the pre-analysis addendum and remain "
            "separate from the exact source-reproduction classification."
        ),
    }
    with (output_directory / "stability-summary.json").open(
        "w", encoding="utf-8", newline="\n"
    ) as destination:
        json.dump(report, destination, indent=2, sort_keys=True)
        destination.write("\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run prespecified Pidgeon robustness analyses.")
    parser.add_argument("--package-root", type=Path, default=PACKAGE_ROOT)
    args = parser.parse_args()
    package_root = args.package_root.resolve()
    report = run_retention_diagnostics(package_root)
    stability = run_stability_analyses(package_root)
    print(
        f"Retention diagnostics complete: parallel components "
        f"{report['parallel_analysis']['retained_components']}; "
        f"scree count {report['scree']['factor_count']}. "
        f"Stability classes: "
        f"{', '.join(f'{method}={result['solution_classification']}' for method, result in stability['methods'].items())}."
    )


if __name__ == "__main__":
    main()