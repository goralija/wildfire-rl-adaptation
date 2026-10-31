from __future__ import annotations

import unittest
import importlib.util

OPTIONAL_RESEARCH_PACKAGES = ("numpy", "pandas", "pyproj", "rasterio", "scipy")
MISSING_RESEARCH_PACKAGES = [
    package for package in OPTIONAL_RESEARCH_PACKAGES
    if importlib.util.find_spec(package) is None
]
if MISSING_RESEARCH_PACKAGES:
    raise unittest.SkipTest(
        f"optional research dependencies are unavailable: {MISSING_RESEARCH_PACKAGES}"
    )

from scripts.build_cfsds_case import (
    require_target_blind_candidate,
    require_target_blind_screen,
)


class CFSDSCaseScreenTests(unittest.TestCase):
    def test_rejects_legacy_screen_without_explicit_target_blind_flags(self) -> None:
        with self.assertRaisesRegex(ValueError, "target-blind crop selection"):
            require_target_blind_screen({"screening_candidates": []})

    def test_accepts_screen_with_explicit_false_target_use_flags(self) -> None:
        require_target_blind_screen({
            "target_geometry_used_for_crop_selection": False,
            "target_geometry_used_for_candidate_ranking": False,
        })

    def test_rejects_candidate_ranked_using_target_geometry(self) -> None:
        with self.assertRaisesRegex(ValueError, "ranking used target geometry"):
            require_target_blind_candidate({
                "target_geometry_used_for_window_selection": False,
                "target_geometry_used_for_candidate_ranking": True,
            })

    def test_rejects_non_object_screen(self) -> None:
        with self.assertRaisesRegex(ValueError, "JSON object"):
            require_target_blind_screen([])


if __name__ == "__main__":
    unittest.main()
