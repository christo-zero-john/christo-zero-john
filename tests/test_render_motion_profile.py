"""Tests for reliable animated GitHub profile GIFs and editorial navigation."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from xml.etree import ElementTree
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location("render_motion_profile",ROOT/"scripts"/"render_motion_profile.py")
motion=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=motion
spec.loader.exec_module(motion)


def fixture():
    return {
        "schema_version":2,"identity_policy_version":3,
        "coverage":"partial","run_at_utc":"2026-11-06T16:00:00+00:00",
        "repositories_scanned":2,
        "unique_attributed_sha_summary":{"commits":1452,"code_lines_changed":54323},
        "summary":{"agent_assisted":127},
        "name_only_attributed_commits":0,
        "current_language_bytes":{"TypeScript":1000,"Python":400,"CSS":100},
        "repositories":[],
    }


class MotionTests(unittest.TestCase):
    def test_countup_reaches_precisely_the_verified_total(self):
        self.assertEqual(motion.count(1452,0), "0")
        self.assertEqual(motion.count(1452,1), "1,452")
        self.assertEqual(motion.count(54323,1), "54,323")
        self.assertGreater(int(motion.count(1452,.7).replace(",","")),0)

    def test_link_tiles_are_valid_pure_svg(self):
        for width in (True,False):
            svg=motion.navigation_svg(2,"REPOSITORIES","All qualified work","INDEX",width)
            root=ElementTree.fromstring(svg)
            self.assertTrue(root.tag.endswith("svg"))
            self.assertIn("REPOSITORIES",svg)
            self.assertNotIn("<script",svg)
            self.assertNotIn("onmouseover=",svg)

    def test_real_gif_has_multiple_encoded_frames(self):
        old=(motion.ASSETS,motion.FRAMES,motion.PAUSE_MS)
        with tempfile.TemporaryDirectory() as folder:
            try:
                motion.ASSETS=Path(folder)
                motion.FRAMES=7
                motion.PAUSE_MS=300
                motion.save_motion("test.gif",motion.engineering(fixture()))
                with Image.open(Path(folder)/"test.gif") as gif:
                    self.assertEqual(gif.format,"GIF")
                    self.assertGreater(gif.n_frames,1)
                    gif.seek(gif.n_frames-1)
                    self.assertEqual(gif.size,(1200,304))
            finally:
                motion.ASSETS,motion.FRAMES,motion.PAUSE_MS=old

    def test_project_span_is_not_hours_worked(self):
        self.assertEqual(motion.span_days({
            "first_commit":"2024-10-10","last_commit":"2025-03-07"})[0],"148D")
        self.assertEqual(motion.span_days({})[0],"—")

    def test_readme_marker_and_link_integrity(self):
        s="intro\n<!-- PREMIUM_AUDIT_NAV:START -->OLD<!-- PREMIUM_AUDIT_NAV:END -->\noutro"
        updated=motion.replace_section(s,"PREMIUM_AUDIT_NAV","<details>hello</details>")
        self.assertIn("<details>",updated)
        self.assertIn("intro",updated)
        self.assertIn("outro",updated)
        with self.assertRaises(ValueError):
            motion.replace_section("not found","PREMIUM_AUDIT_NAV","oops")

    def test_pre_identity_policy_audit_refused(self):
        old=(motion.DATA,motion.README)
        with tempfile.TemporaryDirectory() as folder:
            try:
                motion.DATA=Path(folder)/"audit.json"
                motion.README=Path(folder)/"README.md"
                payload=fixture()
                payload["identity_policy_version"]=2
                motion.DATA.write_text(json.dumps(payload))
                with self.assertRaises(ValueError):
                    motion.run()
            finally:
                motion.DATA,motion.README=old


if __name__=="__main__":
    unittest.main()
