from __future__ import annotations

import importlib.util
import unittest

OPTIONAL_RESEARCH_PACKAGES = ("numpy", "pandas", "pyproj", "rasterio", "scipy")
MISSING_RESEARCH_PACKAGES = [
    package for package in OPTIONAL_RESEARCH_PACKAGES
    if importlib.util.find_spec(package) is None
]
if MISSING_RESEARCH_PACKAGES:
    raise unittest.SkipTest(
        f"optional research dependencies are unavailable: {MISSING_RESEARCH_PACKAGES}"
    )

from scripts.profile_cfsds_cohort import validate_train_years


class CFSDSWindowScreenScopeTests(unittest.TestCase):
    def test_accepts_only_train_years(self) -> None:
        validate_train_years([2014, 2016, 2018])

    def test_rejects_validation_and_test_years_before_opening_data(self) -> None:
        with self.assertRaisesRegex(ValueError, "TRAIN-only"):
            validate_train_years([2018, 2019, 2022])

    def test_rejects_empty_year_selection(self) -> None:
        with self.assertRaisesRegex(ValueError, "At least one TRAIN year"):
            validate_train_years([])


if __name__ == "__main__":
    unittest.main()
