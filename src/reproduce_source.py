from __future__ import annotations

import argparse
import csv
import itertools
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
from PyPDF2 import PdfReader
from scipy.optimize import linear_sum_assignment


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def read_qsort_matrix(path: Path) -> tuple[list[str], np.ndarray]:
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise ValueError(f"No Q-sorts found in {path}")
    statement_ids = [f"s{number}" for number in range(1, 46)]
    participant_ids = [row["participant"] for row in rows]
    matrix = np.array(
        [[float(row[statement_id]) for statement_id in statement_ids] for row in rows],
        dtype=float,
    )
    return participant_ids, matrix


def extract_source_loadings(pdf_path: Path) -> tuple[list[str], np.ndarray]:
    reader = PdfReader(pdf_path)
    table_pages: list[str] = []
    found_table = False
    for page in reader.pages:
        text = page.extract_text() or ""
        if "Table 6.2" in text and "Part. No." in text and "Q-sort Factor 1" in text:
            found_table = True
        if found_table:
            table_pages.append(text)
            if "% Explained Variance" in text:
                break
    if not table_pages or "% Explained Variance" not in table_pages[-1]:
        raise ValueError("Could not locate the complete thesis Table 6.2")

    block = "\n".join(table_pages)
    source_rows: list[tuple[str, list[float]]] = []
    for line in block.splitlines():
        match = re.match(
            r"^\s*(\d+)\s+P(\d+)\s+(.+?)\s*$",
            line.replace("Flagged", " "),
        )
        if not match or match.group(1) != match.group(2):
            continue
        values = re.findall(r"-?\d+(?:\.\d+)?", match.group(3))
        if len(values) == 5:
            source_rows.append((f"P{match.group(2)}", [float(value) for value in values]))

    participant_ids = [participant_id for participant_id, _ in source_rows]
    expected_ids = [f"P{number}" for number in range(1, 48)]
    if participant_ids != expected_ids:
        raise ValueError(f"Unexpected participant sequence in thesis Table 6.2: {participant_ids}")
    return participant_ids, np.array([values for _, values in source_rows], dtype=float)


def varimax(
    matrix: np.ndarray,
    gamma: float = 1.0,
    maximum_iterations: int = 1000,
    tolerance: float = 1e-12,
) -> tuple[np.ndarray, int]:
    row_count, factor_count = matrix.shape
    rotation = np.eye(factor_count)
    objective = 0.0
    for iteration in range(1, maximum_iterations + 1):
        previous_objective = objective
        rotated = matrix @ rotation
        target = rotated**3 - (gamma / row_count) * rotated @ np.diag(
            np.diag(rotated.T @ rotated)
        )
        left, singular_values, right = np.linalg.svd(matrix.T @ target)
        rotation = left @ right
        objective = float(singular_values.sum())
        if previous_objective and (
            objective - previous_objective < tolerance * previous_objective
        ):
            return matrix @ rotation, iteration
    raise RuntimeError(f"Varimax did not converge within {maximum_iterations} iterations")


def pca_varimax(qsorts: np.ndarray, factor_count: int = 5) -> dict[str, Any]:
    correlation_matrix = np.corrcoef(qsorts)
    eigenvalues, eigenvectors = np.linalg.eigh(correlation_matrix)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    unrotated = eigenvectors[:, :factor_count] * np.sqrt(eigenvalues[:factor_count])

    communalities = np.sqrt(np.sum(unrotated**2, axis=1))
    if np.any(communalities == 0):
        raise ValueError("Kaiser normalization is undefined for a zero-communality Q-sort")
    normalized = unrotated / communalities[:, np.newaxis]
    rotated_normalized, iterations = varimax(normalized)
    rotated = rotated_normalized * communalities[:, np.newaxis]
    variance_percent = np.sum(rotated**2, axis=0) / qsorts.shape[0] * 100
    return {
        "correlation_matrix": correlation_matrix,
        "eigenvalues": eigenvalues,
        "unrotated_loadings": unrotated,
        "rotated_loadings": rotated,
        "variance_percent": variance_percent,
        "varimax_iterations": iterations,
    }


def factor_correlations(reference: np.ndarray, candidate: np.ndarray) -> np.ndarray:
    reference_count = reference.shape[1]
    candidate_count = candidate.shape[1]
    correlations = np.empty((reference_count, candidate_count), dtype=float)
    for reference_index in range(reference_count):
        for candidate_index in range(candidate_count):
            correlations[reference_index, candidate_index] = np.corrcoef(
                reference[:, reference_index], candidate[:, candidate_index]
            )[0, 1]
    return correlations


def align_factors(reference: np.ndarray, candidate: np.ndarray) -> dict[str, Any]:
    correlations = factor_correlations(reference, candidate)
    reference_indexes, candidate_indexes = linear_sum_assignment(-np.abs(correlations))
    optimum = float(np.abs(correlations[reference_indexes, candidate_indexes]).sum())

    tied_assignments: list[tuple[int, ...]] = []
    for permutation in itertools.permutations(range(candidate.shape[1])):
        total = float(
            sum(abs(correlations[index, permutation[index]]) for index in range(reference.shape[1]))
        )
        if np.isclose(total, optimum, rtol=0.0, atol=1e-12):
            tied_assignments.append(permutation)
    assignment = min(tied_assignments) if tied_assignments else tuple(candidate_indexes)

    aligned = np.empty_like(reference)
    signs: list[int] = []
    matched_correlations: list[float] = []
    for reference_index, candidate_index in enumerate(assignment):
        correlation = correlations[reference_index, candidate_index]
        sign = 1 if correlation >= 0 else -1
        aligned[:, reference_index] = candidate[:, candidate_index] * sign
        signs.append(sign)
        matched_correlations.append(abs(float(correlation)))
    return {
        "aligned": aligned,
        "assignment": [index + 1 for index in assignment],
        "signs": signs,
        "matched_correlations": matched_correlations,
        "correlation_matrix": correlations,
    }


def write_loadings(path: Path, participant_ids: list[str], loadings: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.writer(destination, lineterminator="\n")
        writer.writerow(["participant", *[f"factor_{number}" for number in range(1, 6)]])
        for participant_id, values in zip(participant_ids, loadings, strict=True):
            writer.writerow([participant_id, *[f"{value:.10f}" for value in values]])


def forced_score_vector() -> np.ndarray:
    return np.array(
        [-4, *([-3] * 3), *([-2] * 6), *([-1] * 8), *([0] * 9), *([1] * 8), *([2] * 6), *([3] * 3), 4],
        dtype=int,
    )


def read_source_factor_arrays(path: Path) -> tuple[list[str], np.ndarray]:
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    statement_ids = [row["statement_id"] for row in rows]
    expected_ids = [f"s{number}" for number in range(1, 46)]
    if statement_ids != expected_ids:
        raise ValueError(f"Unexpected source factor-array statement sequence: {statement_ids}")
    arrays = np.array(
        [[int(row[f"factor_{factor}"]) for factor in range(1, 6)] for row in rows],
        dtype=int,
    )
    expected_scores = sorted(forced_score_vector().tolist())
    for factor_index in range(arrays.shape[1]):
        if sorted(arrays[:, factor_index].tolist()) != expected_scores:
            raise ValueError(f"Source factor {factor_index + 1} does not match the forced distribution")
    return statement_ids, arrays


def reconstruct_factor_arrays(
    qsorts: np.ndarray, loadings: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    assignments = np.argmax(np.abs(loadings), axis=1)
    z_scores = np.empty((qsorts.shape[1], loadings.shape[1]), dtype=float)
    arrays = np.empty_like(z_scores, dtype=int)
    target_scores = forced_score_vector()
    for factor_index in range(loadings.shape[1]):
        defining_indexes = np.flatnonzero(assignments == factor_index)
        if not len(defining_indexes):
            raise ValueError(f"Factor {factor_index + 1} has no primary-loading Q-sorts")
        defining_loadings = loadings[defining_indexes, factor_index]
        if np.any(np.abs(defining_loadings) >= 1):
            raise ValueError(f"Factor {factor_index + 1} contains an invalid unit loading")
        weights = defining_loadings / (1 - defining_loadings**2)
        factor_z_scores = (
            np.sum(qsorts[defining_indexes] * weights[:, np.newaxis], axis=0)
            / np.sum(np.abs(weights))
        )
        order = np.argsort(factor_z_scores, kind="stable")
        factor_array = np.empty(qsorts.shape[1], dtype=int)
        factor_array[order] = target_scores
        z_scores[:, factor_index] = factor_z_scores
        arrays[:, factor_index] = factor_array
    return assignments, z_scores, arrays


def distinguishing_direction_agreement(
    reference_path: Path, reproduced_z_scores: np.ndarray
) -> dict[str, Any]:
    with reference_path.open(newline="", encoding="utf-8") as source:
        references = list(csv.DictReader(source))
    comparisons: list[dict[str, Any]] = []
    for reference in references:
        factor_index = int(reference["factor"]) - 1
        statement_index = int(reference["statement_id"][1:]) - 1
        factor_score = float(reproduced_z_scores[statement_index, factor_index])
        other_scores = np.delete(reproduced_z_scores[statement_index, :], factor_index)
        observed_direction = "higher" if factor_score > float(np.max(other_scores)) else "lower" if factor_score < float(np.min(other_scores)) else "neither"
        matches = observed_direction == reference["direction"]
        comparisons.append(
            {
                "factor": factor_index + 1,
                "statement_id": reference["statement_id"],
                "source_marker": reference["source_marker"],
                "expected_direction": reference["direction"],
                "observed_direction": observed_direction,
                "matches": matches,
            }
        )
    matched = sum(comparison["matches"] for comparison in comparisons)
    return {
        "source_marked_pairs": len(comparisons),
        "matched_pairs": matched,
        "agreement_percent": matched / len(comparisons) * 100,
        "comparisons": comparisons,
    }


def write_factor_arrays(
    path: Path,
    statement_ids: list[str],
    source_arrays: np.ndarray,
    reproduced_arrays: np.ndarray,
    z_scores: np.ndarray,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.writer(destination, lineterminator="\n")
        header = ["statement_id"]
        for factor in range(1, 6):
            header.extend(
                [
                    f"source_factor_{factor}",
                    f"reproduced_factor_{factor}",
                    f"reproduced_z_factor_{factor}",
                ]
            )
        writer.writerow(header)
        for statement_index, statement_id in enumerate(statement_ids):
            row: list[str | int] = [statement_id]
            for factor_index in range(5):
                row.extend(
                    [
                        int(source_arrays[statement_index, factor_index]),
                        int(reproduced_arrays[statement_index, factor_index]),
                        f"{z_scores[statement_index, factor_index]:.10f}",
                    ]
                )
            writer.writerow(row)


def reproduce_source(
    package_root: Path = PACKAGE_ROOT,
    output_root: Path | None = None,
) -> dict[str, Any]:
    repaired_path = package_root / "data" / "normalized" / "pidgeon-2025" / "qsorts_repaired.csv"
    exclusion_path = package_root / "data" / "normalized" / "pidgeon-2025" / "qsorts_without_P47.csv"
    thesis_path = package_root / "data" / "original" / "pidgeon-2025" / "Pidgeon_2025_thesis.pdf"

    participant_ids, qsorts = read_qsort_matrix(repaired_path)
    source_ids, source_loadings = extract_source_loadings(thesis_path)
    if participant_ids != source_ids:
        raise ValueError("Participant order differs between normalized data and source loading table")

    reproduced = pca_varimax(qsorts)
    alignment = align_factors(source_loadings, reproduced["rotated_loadings"])
    aligned_loadings = alignment["aligned"]
    absolute_differences = np.abs(source_loadings - aligned_loadings)
    factor_maximum_differences = np.max(absolute_differences, axis=0)
    factor_mean_differences = np.mean(absolute_differences, axis=0)
    loading_tolerance = 0.01
    loading_status = (
        "exact_numerical_reproduction"
        if bool(np.all(factor_maximum_differences <= loading_tolerance))
        else "not_exact"
    )

    source_array_path = package_root / "data-manifest" / "pidgeon-source-factor-arrays.csv"
    statement_ids, source_arrays = read_source_factor_arrays(source_array_path)
    source_assignments, _, source_reconstructed_arrays = reconstruct_factor_arrays(
        qsorts, source_loadings
    )
    if not np.array_equal(source_reconstructed_arrays, source_arrays):
        raise ValueError("Source factor-array transcription failed its loading-based cross-check")
    reproduced_assignments, reproduced_z_scores, reproduced_arrays = reconstruct_factor_arrays(
        qsorts, aligned_loadings
    )
    assignment_agreement = float(np.mean(source_assignments == reproduced_assignments) * 100)
    factor_array_matches = np.sum(source_arrays == reproduced_arrays, axis=0)
    arrays_identical = bool(np.array_equal(source_arrays, reproduced_arrays))
    distinguishing = distinguishing_direction_agreement(
        package_root / "data-manifest" / "pidgeon-source-distinguishing-statements.csv",
        reproduced_z_scores,
    )

    exclusion_ids, exclusion_qsorts = read_qsort_matrix(exclusion_path)
    exclusion = pca_varimax(exclusion_qsorts)
    full_without_p47 = aligned_loadings[[participant_id != "P47" for participant_id in participant_ids], :]
    sensitivity_alignment = align_factors(full_without_p47, exclusion["rotated_loadings"])

    output_base = output_root or package_root
    output_directory = output_base / "outputs" / "reproduction"
    output_directory.mkdir(parents=True, exist_ok=True)
    write_loadings(output_directory / "source-loadings.csv", source_ids, source_loadings)
    write_loadings(output_directory / "reproduced-loadings.csv", participant_ids, aligned_loadings)
    write_loadings(
        output_directory / "sensitivity-without-P47-loadings.csv",
        exclusion_ids,
        sensitivity_alignment["aligned"],
    )
    write_factor_arrays(
        output_directory / "factor-array-comparison.csv",
        statement_ids,
        source_arrays,
        reproduced_arrays,
        reproduced_z_scores,
    )

    with (output_directory / "primary-factor-assignments.csv").open(
        "w", newline="", encoding="utf-8"
    ) as destination:
        writer = csv.writer(destination, lineterminator="\n")
        writer.writerow(["participant", "source_primary_factor", "reproduced_primary_factor", "matches"])
        for participant_id, source_factor, reproduced_factor in zip(
            participant_ids, source_assignments, reproduced_assignments, strict=True
        ):
            writer.writerow(
                [
                    participant_id,
                    int(source_factor) + 1,
                    int(reproduced_factor) + 1,
                    str(source_factor == reproduced_factor).lower(),
                ]
            )

    eigenvalues = reproduced["eigenvalues"]
    with (output_directory / "eigenvalues.csv").open(
        "w", newline="", encoding="utf-8"
    ) as destination:
        writer = csv.writer(destination, lineterminator="\n")
        writer.writerow(["component", "eigenvalue"])
        for component, eigenvalue in enumerate(eigenvalues, start=1):
            writer.writerow([component, f"{eigenvalue:.10f}"])

    report = {
        "schema_version": "1.0",
        "study_id": "pidgeon-2025",
        "method": {
            "matrix": "by-person Pearson correlation",
            "extraction": "principal components",
            "retained_factors": 5,
            "rotation": "varimax with Kaiser row normalization",
            "factor_alignment": "Hungarian assignment on absolute factor correlations with sign reversal",
            "varimax_iterations": reproduced["varimax_iterations"],
        },
        "source_loading_table": {
            "source": "Pidgeon thesis Table 6.2",
            "participants": len(source_ids),
            "factors": int(source_loadings.shape[1]),
        },
        "eigenvalues": [float(value) for value in eigenvalues[:8]],
        "variance_percent": [float(value) for value in reproduced["variance_percent"]],
        "variance_percent_rounded": [int(round(value)) for value in reproduced["variance_percent"]],
        "source_reported_variance_percent": [21, 9, 12, 9, 5],
        "alignment": {
            "reproduced_factor_by_source_factor": alignment["assignment"],
            "signs": alignment["signs"],
            "factor_loading_correlations": alignment["matched_correlations"],
        },
        "loading_comparison": {
            "absolute_tolerance": loading_tolerance,
            "maximum_absolute_difference_by_factor": [
                float(value) for value in factor_maximum_differences
            ],
            "mean_absolute_difference_by_factor": [float(value) for value in factor_mean_differences],
            "status": loading_status,
        },
        "primary_factor_assignment": {
            "agreement_percent": assignment_agreement,
            "source_counts": [
                int(np.sum(source_assignments == factor_index)) for factor_index in range(5)
            ],
            "reproduced_counts": [
                int(np.sum(reproduced_assignments == factor_index)) for factor_index in range(5)
            ],
            "note": "Primary-factor memberships reconstruct the published composite arrays; they are not treated as the unrecoverable color-coded significant-sort identities.",
        },
        "factor_array_comparison": {
            "integer_scores_identical": arrays_identical,
            "matching_scores_by_factor": [int(value) for value in factor_array_matches],
            "scores_per_factor": int(source_arrays.shape[0]),
            "factor_array_correlations": [
                float(np.corrcoef(source_arrays[:, factor], reproduced_arrays[:, factor])[0, 1])
                for factor in range(5)
            ],
        },
        "distinguishing_statement_direction": distinguishing,
        "consensus_statements": {
            "source_reported_count": 0,
            "source": "Pidgeon thesis Table 6.1",
        },
        "p47_exclusion_sensitivity": {
            "participants": len(exclusion_ids),
            "factor_correlations_with_full_solution": sensitivity_alignment[
                "matched_correlations"
            ],
            "variance_percent": [float(value) for value in exclusion["variance_percent"]],
        },
        "overall_reproduction_classification": (
            "exact_numerical_reproduction"
            if loading_status == "exact_numerical_reproduction"
            and arrays_identical
            and assignment_agreement == 100.0
            and distinguishing["agreement_percent"] == 100.0
            else "not_exact"
        ),
        "source_reporting_limitation": (
            "The thesis reports 32 significant Q-sorts, but participant identities are encoded partly "
            "by color in Table 6.2 and are not recoverable reliably from PDF text extraction."
        ),
    }
    with (output_directory / "pidgeon-reproduction-summary.json").open(
        "w", encoding="utf-8", newline="\n"
    ) as destination:
        json.dump(report, destination, indent=2, sort_keys=True)
        destination.write("\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Reproduce the Pidgeon five-factor PCA/varimax solution.")
    parser.add_argument("--package-root", type=Path, default=PACKAGE_ROOT)
    args = parser.parse_args()
    report = reproduce_source(args.package_root.resolve())
    correlations = report["alignment"]["factor_loading_correlations"]
    print(
        f"Loading reproduction: {report['loading_comparison']['status']}; "
        f"minimum matched correlation {min(correlations):.6f}; "
        f"overall classification {report['overall_reproduction_classification']}."
    )


if __name__ == "__main__":
    main()