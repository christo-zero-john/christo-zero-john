"""Verify accurate, safe and repeatable README dashboard generation."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "render_profile_dashboard.py"
spec = importlib.util.spec_from_file_location("render_profile_dashboard", SCRIPT)
dashboard = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dashboard
spec.loader.exec_module(dashboard)


def fixture():
    return {
        "schema_version": 2,
        "coverage": "partial",
        "run_at_utc": "2026-11-06T16:00:00+00:00",
        "repositories_scanned": 125,
        "repositories_enumerated": 126,
        "summary": {"commits": 16177, "code_lines_changed": 1056830,
                    "lines_changed": 9783956, "agent_assisted": 2791},
        "unique_attributed_sha_summary": {"commits": 15882, "code_lines_changed": 1030800,
                                          "lines_changed": 9698291},
        "current_language_bytes": {"Python": 22741497, "TypeScript": 18736848,
                                   "HTML": 9184890, "JavaScript": 5939307},
    }


class DashboardTests(unittest.TestCase):
    def test_reject_invalidated_legacy_and_zero_repositories(self):
        old = dashboard.DATA
        with tempfile.TemporaryDirectory() as d:
            try:
                dashboard.DATA = Path(d) / "audit.json"
                self.assertRaises(ValueError, dashboard.load_audit)
                for bad in (
                    {**fixture(), "schema_version": 1},
                    {**fixture(), "coverage": "invalidated"},
                    {**fixture(), "repositories_scanned": 0},
                    {**fixture(), "unique_attributed_sha_summary": {
                        "commits": 30000, "code_lines_changed": 1, "lines_changed": 1}},
                ):
                    if bad.get("schema_version") == 1:
                        bad["schema_version"] = 1
                    dashboard.DATA.write_text(json.dumps(bad), encoding="utf-8")
                    if bad.get("schema_version") == 2 and "coverage" not in bad:
                        bad["coverage"] = "invalidated"
                    with self.assertRaises(ValueError):
                        dashboard.load_audit()
                dashboard.DATA.write_text(json.dumps(fixture()), encoding="utf-8")
                self.assertEqual(dashboard.load_audit()["repositories_scanned"], 125)
            finally:
                dashboard.DATA = old

    def test_generated_svg_is_valid_and_uses_deduplicated_totals(self):
        sample = fixture()
        stats = dashboard.stat_svg(sample)
        languages = dashboard.language_svg(sample)
        ET.fromstring(stats)
        ET.fromstring(languages)
        self.assertIn("15,882", stats)
        self.assertIn("1,030,800", stats)
        self.assertNotIn("16,177", stats)
        self.assertIn("PARTIAL COVERAGE", stats)
        self.assertIn("TypeScript", languages)
        self.assertIn("ALL AUTHORS", languages)
        self.assertNotIn("github_pat_", stats + languages)
        self.assertNotIn("private/repository", stats + languages)

    def test_updates_only_marked_region_and_never_invents_missing_markers(self):
        old = dashboard.README
        with tempfile.TemporaryDirectory() as d:
            try:
                dashboard.README = Path(d) / "README.md"
                dashboard.README.write_text(
                    "# Editorial hero\n\n" + dashboard.OPEN + "\nold stats\n" +
                    dashboard.CLOSE + "\n\n## Work\n", encoding="utf-8")
                self.assertTrue(dashboard.update_readme(fixture()))
                content = dashboard.README.read_text(encoding="utf-8")
                self.assertIn("# Editorial hero", content)
                self.assertIn("## Work", content)
                self.assertIn("15,882 verified-identity Git SHAs", content)
                self.assertIn("Partial", content)
                self.assertEqual(content.count(dashboard.OPEN), 1)
                self.assertEqual(content.count(dashboard.CLOSE), 1)
                self.assertFalse(dashboard.update_readme(fixture()))
                dashboard.README.write_text("# No markers", encoding="utf-8")
                with self.assertRaises(ValueError):
                    dashboard.update_readme(fixture())
            finally:
                dashboard.README = old

    def test_timestamp_is_sourced_from_audit(self):
        sample = fixture()
        self.assertIn("06 NOV 2026", dashboard.date_label(sample))
        self.assertIn("06 NOV 2026", dashboard.stats_markdown(sample))


if __name__ == "__main__":
    unittest.main()
