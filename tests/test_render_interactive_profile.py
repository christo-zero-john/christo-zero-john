"""Premium profile link-card, authorship and SVG progressive enhancement tests."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def import_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ui = import_module("render_interactive_profile_test", SCRIPTS / "render_interactive_profile.py")
base = import_module("render_profile_dashboard_test", SCRIPTS / "render_profile_dashboard.py")


def fixture():
    entries = []
    for project in ui.PROJECTS:
        entries.append({
            "name": project["repo"], "private": False, "fork": False, "status": "ok",
            "first_commit": "2026-09-11", "last_commit": "2026-09-17",
            "metrics": {"commits": 218, "code_lines_changed": 2561,
                        "lines_changed": 72458, "agent_assisted": 215}
        })
    # Private identity must remain entirely absent from the public README/assets.
    entries.append({"name": "owner/SECRET_PRIVATE_PROJECT", "private": True,
                    "status": "ok", "first_commit": "2025-01-01", "last_commit": "2026-01-01",
                    "metrics": {"commits": 9999, "code_lines_changed": 888888}})
    return {
        "schema_version": 2,
        "coverage": "partial",
        "run_at_utc": "2026-11-06T16:40:00+00:00",
        "repositories_scanned": 5,
        "repositories_enumerated": 5,
        "summary": {"commits": 5000, "agent_assisted": 215,
                    "code_lines_changed": 200000, "lines_changed": 400000},
        "unique_attributed_sha_summary": {"commits": 4000,
                    "code_lines_changed": 100000, "lines_changed": 300000},
        "current_language_bytes": {
            "Python": 100000, "TypeScript": 75000, "JavaScript": 50000,
            "CSS": 20000, "HTML": 15000
        },
        "repositories": entries,
    }


class PremiumUiTests(unittest.TestCase):
    def test_project_window_is_calendar_span_not_days_worked(self):
        d, first, last = ui.project_duration({
            "first_commit": "2026-09-11", "last_commit": "2026-09-17"
        })
        self.assertEqual(d, "6D")
        self.assertIn("2026", first)
        self.assertIn("2026", last)

    def test_svg_links_and_projects_parse_without_unverified_data(self):
        for item in ui.ACTIONS:
            ET.fromstring(ui.make_action_svg(item))
        for item in ui.AUDIT_LINKS:
            ET.fromstring(ui.make_audit_svg(item))
        for p in ui.PROJECTS:
            svg = ui.project_svg(p, fixture()["repositories"][0])
            ET.fromstring(svg)
            self.assertIn("218", svg)
            self.assertIn("2,561", svg)
        missing = ui.project_svg(ui.PROJECTS[0], None)
        self.assertIn("—", missing)
        self.assertNotIn("9999", missing)

    def test_dashboard_motion_keeps_static_final_numbers(self):
        d = fixture()
        rendered = ui.add_animation(base.stat_svg(d))
        language = ui.animated_language(base.language_svg(d))
        ET.fromstring(rendered)
        ET.fromstring(language)
        self.assertIn("premium-count-motion", rendered)
        self.assertIn("4,000", rendered)
        self.assertIn("premium-language-motion", language)
        self.assertIn("live-bar", language)
        self.assertEqual(rendered, ui.add_animation(rendered))
        self.assertEqual(language, ui.animated_language(language))

    def test_github_safe_readme_and_idempotent_regeneration(self):
        original = (ui.ASSETS, ui.README, ui.DATA)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            try:
                ui.ASSETS = root / "assets"
                ui.README = root / "README.md"
                ui.DATA = root / "docs/github-audit/audit.json"
                ui.DATA.parent.mkdir(parents=True)
                data = fixture()
                ui.DATA.write_text(json.dumps(data), encoding="utf-8")
                ui.ASSETS.mkdir()
                (ui.ASSETS / "lifetime-engineering.svg").write_text(base.stat_svg(data))
                (ui.ASSETS / "language-landscape.svg").write_text(base.language_svg(data))
                ui.README.write_text(
                    "# Hero\n\n"
                    "<!-- PREMIUM_ACTIONS:START -->\nplaceholder\n<!-- PREMIUM_ACTIONS:END -->\n"
                    "<!-- PROFILE_STATS:START -->\n"
                    "[Full methodology &amp; audit](./docs/github-audit/REPORT.md) · "
                    "[Repository evidence](./docs/github-audit/repositories.md)\n"
                    "<!-- PROFILE_STATS:END -->\n"
                    "<!-- PREMIUM_PROJECTS:START -->\nplaceholder\n<!-- PREMIUM_PROJECTS:END -->\n"
                    "<!-- PREMIUM_FOOTER:START -->\nplaceholder\n<!-- PREMIUM_FOOTER:END -->\n",
                    encoding="utf-8")
                ui.main()
                readme = ui.README.read_text(encoding="utf-8")
                self.assertIn("feature-photobooth.svg", readme)
                self.assertIn("action-linkedin.svg", readme)
                self.assertIn("audit-repositories.svg", readme)
                self.assertIn("Contribution evidence", readme)
                self.assertIn("<details>", readme)
                self.assertNotIn("SECRET_PRIVATE_PROJECT", readme)
                self.assertNotIn("[Full methodology", readme)
                self.assertNotIn("](https://", readme)
                for path in ui.ASSETS.glob("*.svg"):
                    ET.parse(path)
                    self.assertNotIn("SECRET_PRIVATE_PROJECT", path.read_text())
                ui.main()
                self.assertEqual(readme, ui.README.read_text(encoding="utf-8"))
                self.assertEqual(len(list(ui.ASSETS.glob("*.svg"))), 14)
            finally:
                ui.ASSETS, ui.README, ui.DATA = original

    def test_rejects_old_untrusted_audits(self):
        with tempfile.TemporaryDirectory() as directory:
            old = (ui.ASSETS, ui.README, ui.DATA)
            try:
                ui.DATA = Path(directory) / "audit.json"
                ui.README = Path(directory) / "README.md"
                ui.ASSETS = Path(directory) / "assets"
                data = fixture()
                data["coverage"] = "invalidated"
                ui.DATA.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    ui.main()
            finally:
                ui.ASSETS, ui.README, ui.DATA = old


if __name__ == "__main__":
    unittest.main()
