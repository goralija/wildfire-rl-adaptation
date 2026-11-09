#!/usr/bin/env python3
"""Run the unit tests and require the skipped tests to match an exact allowlist.

Used by the CI `numeric` job. Skips are read from unittest's own result object, not
from log text, so warnings printed during a test cannot hide a skip. Output is
buffered per test (like `unittest -b`) and shown only for failures.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read_expected(path: Path) -> set[str]:
    entries = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            entries.add(line)
    return entries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=Path, default=ROOT / "tests")
    parser.add_argument("--expected-skips", type=Path, default=ROOT / "tests/ci_expected_skips.txt")
    args = parser.parse_args(argv)

    # Match `python -m unittest discover -s tests` run from the repository root, where the
    # root (and so the `scripts` package) is importable.
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    suite = unittest.defaultTestLoader.discover(str(args.start), top_level_dir=str(args.start))
    result = unittest.TextTestRunner(verbosity=2, buffer=True).run(suite)

    skipped = {test.id(): reason for test, reason in result.skipped}
    expected = read_expected(args.expected_skips)
    unexpected = sorted(set(skipped) - expected)
    not_skipped = sorted(expected - set(skipped))

    print("\nSkipped %d test(s):" % len(skipped))
    for test_id in sorted(skipped):
        print("  %s: %s" % (test_id, skipped[test_id]))
    ok = result.wasSuccessful()
    if unexpected:
        ok = False
        print("\nERROR: skipped but not in %s:" % args.expected_skips.name)
        for test_id in unexpected:
            print("  %s: %s" % (test_id, skipped[test_id]))
    if not_skipped:
        ok = False
        print("\nERROR: listed in %s but not skipped (remove or fix):" % args.expected_skips.name)
        for test_id in not_skipped:
            print("  %s" % test_id)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
