from __future__ import annotations

import sys
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from src.verify_results import verify_results  # noqa: E402


class ResultContractTest(unittest.TestCase):
    def test_prespecified_scientific_results(self) -> None:
        self.assertEqual(verify_results(PACKAGE_ROOT), [])


if __name__ == "__main__":
    unittest.main()
