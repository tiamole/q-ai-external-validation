from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from src.reproduce_source import read_qsort_matrix  # noqa: E402
from src.robustness import (  # noqa: E402
    align_factor_arrays,
    centroid_extract,
    classify_stability,
    defining_flags,
    extract_rotated_solution,
    factor_arrays_from_flags,
    load_frozen_robustness_config,
    run_retention_diagnostics,
    run_stability_analyses,
)


class RobustnessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        matrix_path = PACKAGE_ROOT / "data" / "normalized" / "pidgeon-2025" / "qsorts_repaired.csv"
        _, cls.qsorts = read_qsort_matrix(matrix_path)

    def test_frozen_seed_list_and_centroid_are_deterministic(self) -> None:
        _, seeds = load_frozen_robustness_config(PACKAGE_ROOT)
        self.assertEqual(len(seeds), 1000)
        self.assertEqual(len(set(seeds)), 1000)

        correlation = np.corrcoef(self.qsorts)
        first = centroid_extract(correlation, factor_count=5)
        second = centroid_extract(correlation, factor_count=5)
        np.testing.assert_array_equal(first, second)
        self.assertEqual(first.shape, (47, 5))
        self.assertTrue(np.isfinite(first).all())

    def test_defining_rule_requires_threshold_and_margin(self) -> None:
        loadings = np.array([[0.60, 0.40], [0.50, 0.45], [0.30, 0.10]])
        flags = defining_flags(loadings, loading_threshold=0.384, confounding_margin=0.10)
        np.testing.assert_array_equal(flags, [[True, False], [False, False], [False, False]])

    def test_underdefined_factor_does_not_erase_other_stable_factors(self) -> None:
        classification = classify_stability(
            np.ones(5, dtype=bool),
            np.ones(5, dtype=bool),
            np.array([4, 4, 4, 4, 1]),
            minimum_defining_sorts=2,
        )

        self.assertEqual(classification["stable_count"], 4)
        self.assertEqual(classification["solution_class"], "mixed_solution")
        np.testing.assert_array_equal(
            classification["factor_stable"],
            [True, True, True, True, False],
        )

    def test_retention_diagnostics_run_for_both_methods(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            report = run_retention_diagnostics(
                PACKAGE_ROOT,
                Path(temporary_directory),
                parallel_iterations=10,
            )
        self.assertEqual(report["parallel_analysis"]["iterations"], 10)
        self.assertEqual(len(report["retention_diagnostics"]), 28)
        self.assertEqual(
            {row["method"] for row in report["retention_diagnostics"]},
            {"pca", "centroid"},
        )
        centroid = extract_rotated_solution(self.qsorts, "centroid", 5)
        self.assertEqual(centroid["loadings"].shape, (47, 5))

    def test_factor_array_alignment_and_small_stability_run(self) -> None:
        reference = np.column_stack(
            (
                np.arange(10, dtype=float) ** 2,
                np.array([3, 1, 4, 1, 5, 9, 2, 6, 5, 3], dtype=float),
            )
        )
        candidate = np.column_stack((reference[:, 1], -reference[:, 0]))
        alignment = align_factor_arrays(reference, candidate)
        np.testing.assert_allclose(alignment["matched_correlations"], [1.0, 1.0])
        np.testing.assert_array_equal(alignment["candidate_by_reference"], [1, 0])

        flags = np.zeros((4, 2), dtype=bool)
        flags[:2, 0] = True
        flags[2:, 1] = True
        loadings = np.array([[0.6, 0.1], [0.7, 0.2], [0.1, 0.6], [0.2, 0.7]])
        _, _, arrays = factor_arrays_from_flags(self.qsorts[:4], loadings, flags, 2)
        self.assertEqual(arrays.shape, (45, 2))
        self.assertTrue(np.isfinite(arrays).all())

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_root = Path(temporary_directory)
            report = run_stability_analyses(
                PACKAGE_ROOT,
                output_root,
                bootstrap_iterations=3,
            )
            self.assertTrue(
                (
                    output_root
                    / "outputs"
                    / "robustness"
                    / "pca-centroid-factor-array-comparison.csv"
                ).is_file()
            )
        self.assertEqual(report["bootstrap_iterations_per_method"], 3)
        self.assertEqual(set(report["methods"]), {"pca", "centroid"})
        self.assertEqual(
            len(report["extraction_method_comparison"]["pca_factor"]),
            5,
        )
        for result in report["methods"].values():
            self.assertEqual(result["leave_one_out"]["runs"], 47)
            self.assertEqual(result["bootstrap"]["runs"], 3)

    def test_align_factor_arrays_breaks_ties_lexicographically(self) -> None:
        reference = np.array(
            [
                [-1.0, -1.0],
                [0.0, 0.0],
                [1.0, 1.0],
            ]
        )
        candidate = reference.copy()

        aligned = align_factor_arrays(reference, candidate)

        self.assertEqual(aligned["candidate_by_reference"].tolist(), [0, 1])
        self.assertTrue(np.allclose(aligned["matched_correlations"], 1.0))

if __name__ == "__main__":
    unittest.main()