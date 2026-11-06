"""Regression tests for the motion-free GitHub profile.

The renderer uses only the current strict audit, static SVG, valid links, and
one compact disclosure. Public README never leaks private repository names.
"""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET

SCRIPT=Path(__file__).resolve().parents[1]/"scripts"/"render_refined_profile.py"
spec=importlib.util.spec_from_file_location("refined_profile",SCRIPT)
profile=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=profile
spec.loader.exec_module(profile)


def fixture():
    repos=[]
    for idx,spec in enumerate(profile.FEATURED):
        repos.append({
            "name":spec[1], "status":"ok", "private":False,
            "first_commit":"2025-02-01", "last_commit":"2025-05-07",
            "metrics":{"commits":240+idx, "code_lines_changed":10800+idx,
                       "lines_changed":30000+idx, "name_only_attributed":0}
        })
    repos.append({"name":"christo-zero-john/PRIVATE_SECRET_INTERNAL_PLATFORM",
                  "private":True,"status":"ok",
                  "first_commit":"2025-01-01", "last_commit":"2026-01-01",
                  "metrics":{"commits":999999, "code_lines_changed":999999}})
    return {"schema_version":2,"identity_policy_version":3,"coverage":"partial",
            "run_at_utc":"2026-11-06T18:02:23+00:00",
            "repositories_scanned":5,
            "summary":{"commits":2000,"agent_assisted":300},
            "unique_attributed_sha_summary":{"commits":1800,"code_lines_changed":123456,
                "name_only_attributed":0},
            "current_language_bytes":{"TypeScript":1000,"Python":650,"JavaScript":400,
                                      "CSS":250,"HTML":150,"Shell":50},
            "repositories":repos}


class RefinedProfileTests(unittest.TestCase):
    def test_svg_markup_is_valid_and_motion_free(self):
        data=fixture()
        for svg in [
            profile.hero(),profile.record_card(data),profile.language_band(data),
            profile.nav_svg("PORTFOLIO",1),profile.audit_svg("AUDIT",1),
            profile.project_svg(profile.FEATURED[0],data["repositories"][0],1)
        ]:
            ET.fromstring(svg)
            self.assertNotIn("<script",svg)
            self.assertNotIn("<animate",svg)
            self.assertNotIn("<style",svg)
            self.assertNotIn("onmouseover=",svg)

    def test_reject_outdated_audits(self):
        for bad in [
            {**fixture(),"schema_version":1},
            {**fixture(),"identity_policy_version":2},
            {**fixture(),"coverage":"invalidated"},
            {**fixture(),"repositories_scanned":0},
        ]:
            with self.assertRaises(ValueError):
                with tempfile.TemporaryDirectory() as directory:
                    old=(profile.ASSETS,profile.README)
                    try:
                        profile.ASSETS=Path(directory)/"assets"
                        profile.README=Path(directory)/"README.md"
                        profile.produce(bad)
                    finally:
                        profile.ASSETS,profile.README=old

    def test_only_public_project_names_and_metrics(self):
        data=fixture()
        old=(profile.ASSETS,profile.README)
        with tempfile.TemporaryDirectory() as directory:
            try:
                profile.ASSETS=Path(directory)/"assets"
                profile.README=Path(directory)/"README.md"
                profile.produce(data)
                md=profile.README.read_text(encoding="utf-8")
                self.assertNotIn("PRIVATE_SECRET_INTERNAL_PLATFORM",md)
                self.assertIn("1800",md.replace(",",""))
                self.assertIn("profile-editorial.svg",md)
                self.assertIn("profile-engineering.svg",md)
                self.assertIn("profile-languages.svg",md)
                self.assertNotIn(".gif",md)
                self.assertNotIn("<table>",md)
                self.assertEqual(md.count("<details>"),1)
                self.assertEqual(md.count("<summary>"),1)
                for spec in profile.FEATURED:
                    self.assertIn("https://github.com/"+spec[1],md)
                self.assertIn('href="./docs/github-audit/REPORT.md"',md)
                site_data=json.loads((Path(directory)/"docs/experience/data.json").read_text())
                self.assertEqual(site_data["commits"],1800)
                self.assertEqual(site_data["codeLinesChanged"],123456)
                self.assertNotIn("PRIVATE_SECRET_INTERNAL_PLATFORM",
                                 json.dumps(site_data))
                self.assertEqual(len(site_data["projects"]),4)
                assets=list(profile.ASSETS.glob("*.svg"))
                self.assertEqual(len(assets),15)
                for path in assets:
                    ET.parse(path)
                    content=path.read_text()
                    self.assertNotIn("PRIVATE_SECRET_INTERNAL_PLATFORM",content)
                    self.assertNotIn("999,999",content)
                previous={p.name:p.read_bytes() for p in assets}
                profile.produce(data)
                self.assertEqual(previous,{p.name:p.read_bytes() for p in assets})
            finally:
                profile.ASSETS,profile.README=old

    def test_data_refresh_changes_values_without_changing_layout(self):
        old=(profile.ASSETS,profile.README)
        with tempfile.TemporaryDirectory() as directory:
            try:
                profile.ASSETS=Path(directory)/"assets"
                profile.README=Path(directory)/"README.md"
                payload=fixture()
                profile.produce(payload)
                before=(profile.ASSETS/"profile-engineering.svg").read_text()
                payload["unique_attributed_sha_summary"]["commits"]=2222
                profile.produce(payload)
                after=(profile.ASSETS/"profile-engineering.svg").read_text()
                self.assertIn("2,222",after)
                self.assertNotEqual(before,after)
                self.assertEqual(profile.README.read_text().count("### Selected work"),1)
            finally:
                profile.ASSETS,profile.README=old

    def test_duration_is_elapsed_span_not_time_worked(self):
        dates,days=profile.date_range({"first_commit":"2024-10-10",
                                       "last_commit":"2025-03-07"})
        self.assertEqual(days,"148 days")
        self.assertIn("2024",dates)
        self.assertEqual(profile.date_range({})[1],"—")


if __name__=="__main__":
    unittest.main()
