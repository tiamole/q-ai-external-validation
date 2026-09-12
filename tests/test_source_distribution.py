from __future__ import annotations

import sys
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from src.download_sources import download_all_sources, load_source_records  # noqa: E402
from src.verify_checksums import verify_checksums  # noqa: E402


class SourceDistributionTest(unittest.TestCase):
    def test_frozen_source_manifest_is_complete_and_verified(self) -> None:
        records = load_source_records(PACKAGE_ROOT)

        self.assertEqual(len(records), 3)
        self.assertEqual(
            {record["record_id"] for record in records},
            {"PIG-DATA-01", "PIG-DATA-02", "PIG-THESIS-01"},
        )
        self.assertEqual(
            download_all_sources(PACKAGE_ROOT),
            [
                ("PIG-DATA-01", "verified"),
                ("PIG-DATA-02", "verified"),
                ("PIG-THESIS-01", "verified"),
            ],
        )

    def test_immutable_checksum_ledger(self) -> None:
        self.assertEqual(
            verify_checksums(PACKAGE_ROOT, excluded_prefixes=("outputs/",)),
            [],
        )


if __name__ == "__main__":
    unittest.main()
