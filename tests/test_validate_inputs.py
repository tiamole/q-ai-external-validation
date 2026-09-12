from __future__ import annotations

import csv
import hashlib
import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from src.validate_inputs import normalize_sort, validate_and_normalize  # noqa: E402


class ValidateInputsTest(unittest.TestCase):
    def test_real_workbook_is_repaired_without_modifying_source(self) -> None:
        source_path = PACKAGE_ROOT / "data" / "original" / "pidgeon-2025" / "Participants Q sorts.xlsx"
        hash_before = hashlib.sha256(source_path.read_bytes()).hexdigest()

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_root = Path(temporary_directory)
            report = validate_and_normalize(PACKAGE_ROOT, output_root)

            repaired_path = output_root / "data" / "normalized" / "pidgeon-2025" / "qsorts_repaired.csv"
            with repaired_path.open(newline="", encoding="utf-8") as source:
                repaired_rows = list(csv.DictReader(source))
            self.assertEqual(len(repaired_rows), 47)
            self.assertEqual(repaired_rows[-1]["participant"], "P47")
            self.assertEqual(repaired_rows[-1]["s2"], "1")

            expected_distribution = Counter(
                {"-4": 1, "-3": 3, "-2": 6, "-1": 8, "0": 9, "1": 8, "2": 6, "3": 3, "4": 1}
            )
            for row in repaired_rows:
                observed = Counter(row[f"s{number}"] for number in range(1, 46))
                self.assertEqual(observed, expected_distribution, row["participant"])

            exclusion_path = output_root / "data" / "normalized" / "pidgeon-2025" / "qsorts_without_P47.csv"
            with exclusion_path.open(newline="", encoding="utf-8") as source:
                exclusion_rows = list(csv.DictReader(source))
            self.assertEqual(len(exclusion_rows), 46)
            self.assertNotIn("P47", {row["participant"] for row in exclusion_rows})

            report_path = output_root / "outputs" / "integrity" / "pidgeon-input-validation.json"
            saved_report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_report, report)
            self.assertEqual(report["observed"]["repairs"][0]["source_cell"], "Q Sort !C48")

        hash_after = hashlib.sha256(source_path.read_bytes()).hexdigest()
        self.assertEqual(hash_after, hash_before)

    def test_unprespecified_anomaly_stops_processing(self) -> None:
        expected_distribution = Counter({-4: 1, -3: 3, -2: 6, -1: 8, 0: 9, 1: 8, 2: 6, 3: 3, 4: 1})
        values = tuple(score for score, count in expected_distribution.items() for _ in range(count))
        malformed_values = (-14, *values[1:])
        repair_config = {
            "source_cell": "Q Sort !C48",
            "participant_id": "P47",
            "statement_id": "s2",
            "raw_value": -14,
            "normalized_value": 1,
        }
        with self.assertRaisesRegex(ValueError, "Unprespecified out-of-range score"):
            normalize_sort(
                "P1",
                2,
                [f"s{number}" for number in range(1, 46)],
                malformed_values,
                expected_distribution,
                repair_config,
            )


if __name__ == "__main__":
    unittest.main()