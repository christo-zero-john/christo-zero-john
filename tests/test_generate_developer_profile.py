"""Tests for evidence-aware developer portfolio rendering."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "generate_developer_profile.py"
SPEC = importlib.util.spec_from_file_location("generate_developer_profile", MODULE_PATH)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class DeveloperBiodataTests(unittest.TestCase):
    def test_package_manifests(self):
        manifest = json.dumps({
            "dependencies": {"next": "15", "@supabase/supabase-js": "^2", "react": "^19"},
            "devDependencies": {"typescript": "^5", "@playwright/test": "*"}
        })
        tags = module.infer_from_manifest("web/package.json", manifest)
        self.assertTrue({"Next.js", "Supabase", "React", "TypeScript", "Playwright"}.issubset(tags))
        python_tags = module.infer_from_manifest("requirements.txt", "fastapi==0.1\npydantic>=2\n")
        self.assertEqual(python_tags, {"FastAPI", "Pydantic"})
        self.assertEqual(module.infer_from_manifest("package.json", "not valid json"), set())

    def test_render_produces_pages_without_private_repo_names(self):
        previous_base = module.BASE
        previous_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                module.BASE = Path(directory) / "docs" / "github-audit"
                private = {"name": "Private repository #001", "private": True,
                           "metrics": {"commits": 2, "code_lines_changed": 8, "lines_changed": 14}}
                public = {"name": "owner/public-project", "private": False,
                          "url": "https://github.com/owner/public-project",
                          "metrics": {"commits": 4, "code_lines_changed": 10, "lines_changed": 20}}
                data = {
                    "account": "owner", "coverage": "partial", "run_at_utc": "2026-11-06T13:49:00Z",
                    "repositories": [public, private], "repositories_enumerated": 2,
                    "repositories_scanned": 2, "warnings": 1,
                    "summary": {"commits": 6, "direct": 5, "coauthored": 1, "code_lines_changed": 18},
                    "unique_attributed_sha_summary": {"commits": 5, "code_lines_changed": 16, "lines_changed": 32},
                    "years": {"2026": {"commits": 6, "lines_changed": 34}},
                    "months": {"2026-11": {"commits": 6, "lines_changed": 34}},
                    "historical_languages": {"TypeScript": {
                        "code_lines_changed": 18, "code_additions": 14, "code_deletions": 4,
                        "lines_changed": 18, "additions": 14, "deletions": 4}},
                    "current_language_bytes": {"TypeScript": 10000},
                    "platform_activity": {"pull_requests_opened": 2}
                }
                bio = {"name": "Example Developer", "role": "AI Product Engineer",
                       "portfolio": "https://example.org", "linkedin": "https://example.org",
                       "primary_stack": ["Next.js"], "featured_public_repositories": ["owner/public-project"]}
                metadata = {"owner/public-project": {
                    "description": "A tested sample", "manifest_tags": ["Next.js"],
                    "evidence": {"Next.js": "package.json"}, "inspection": "inspected",
                    "stars": 2, "forks": 1, "created_at": "2026-01-01",
                    "pushed_at": "2026-11-06", "topics": ["web"]}}
                module.render(data, bio, metadata, [])
                for filename in ["PROFILE.md", "TECH_STACK.md", "PROJECTS.md", "INSIGHTS.md"]:
                    page = (module.BASE / filename).read_text(encoding="utf-8")
                    self.assertNotIn("secret-private-name", page)
                self.assertIn("Private repository #001", (module.BASE / "PROJECTS.md").read_text())
                self.assertIn("Next.js", (module.BASE / "TECH_STACK.md").read_text())
                self.assertIn("AI Product Engineer", (module.BASE / "PROFILE.md").read_text())
            finally:
                module.BASE = previous_base
                os.chdir(previous_cwd)


if __name__ == "__main__":
    unittest.main()
