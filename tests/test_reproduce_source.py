from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from src.reproduce_source import extract_source_loadings, reproduce_source  # noqa: E402


class ReproduceSourceTest(unittest.TestCase):
    def test_thesis_loading_table_is_complete(self) -> None:
        thesis_path = PACKAGE_ROOT / "data" / "original" / "pidgeon-2025" / "Pidgeon_2025_thesis.pdf"
        participant_ids, loadings = extract_source_loadings(thesis_path)
        self.assertEqual(participant_ids, [f"P{number}" for number in range(1, 48)])
        self.assertEqual(loadings.shape, (47, 5))
        np.testing.assert_allclose(loadings[0], [0.7846, -0.0448, 0.2348, 0.2078, -0.0185])
        np.testing.assert_allclose(loadings[-1], [0.0592, -0.021, 0.4684, 0.5456, 0.2239])

    def test_pca_kaiser_varimax_reproduces_reported_loadings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            report = reproduce_source(PACKAGE_ROOT, Path(temporary_directory))

        self.assertEqual(report["loading_comparison"]["status"], "exact_numerical_reproduction")
        self.assertGreater(min(report["alignment"]["factor_loading_correlations"]), 0.99999)
        self.assertLess(max(report["loading_comparison"]["maximum_absolute_difference_by_factor"]), 0.002)
        np.testing.assert_allclose(
            report["eigenvalues"][:4],
            [15.11, 3.96, 3.02, 2.58],
            atol=0.005,
        )
        self.assertEqual(report["variance_percent_rounded"], [21, 9, 12, 9, 5])
        self.assertEqual(report["primary_factor_assignment"]["agreement_percent"], 100.0)
        self.assertEqual(report["primary_factor_assignment"]["source_counts"], [20, 7, 10, 7, 3])
        self.assertTrue(report["factor_array_comparison"]["integer_scores_identical"])
        self.assertEqual(report["factor_array_comparison"]["matching_scores_by_factor"], [45] * 5)
        self.assertEqual(report["distinguishing_statement_direction"]["agreement_percent"], 100.0)
        self.assertEqual(report["p47_exclusion_sensitivity"]["participants"], 46)
        self.assertEqual(
            report["overall_reproduction_classification"],
            "exact_numerical_reproduction",
        )


if __name__ == "__main__":
    unittest.main()