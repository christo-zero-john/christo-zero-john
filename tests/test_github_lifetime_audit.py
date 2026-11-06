"""Integration checks for author attribution and full Git-ref history."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "github_lifetime_audit.py"
spec = importlib.util.spec_from_file_location("github_lifetime_audit", SCRIPT)
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit
spec.loader.exec_module(audit)


def git(folder: Path, *args: str) -> str:
    run = subprocess.run(["git", *args], cwd=folder, capture_output=True, text=True, check=True)
    return run.stdout.strip()


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.name", "Christo John")
        git(self.repo, "config", "user.email", "me@example.com")

    def tearDown(self):
        self.temp.cleanup()

    def commit(self, file: str, content: str, msg: str, author=None):
        path = self.repo / file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        git(self.repo, "add", file)
        cmd = ["commit", "-q", "-m", msg]
        if author:
            cmd += ["--author", author]
        git(self.repo, *cmd)

    def test_all_branches_and_coauthor_and_agents(self):
        self.commit("app.py", "print(1)\nprint(2)\n", "initial")
        git(self.repo, "switch", "-q", "-c", "feature")
        self.commit("agent.py", "a = 1\nb = 2\n", "agent", "Claude Code <claude@bots.test>")
        git(self.repo, "switch", "-q", "main")
        self.commit("readme.md", "hello\n", "other plus coauthor\n\nCo-authored-by: Christo John <me@example.com>", "Contributor <other@test.invalid>")
        git(self.repo, "merge", "-q", "--no-ff", "feature", "-m", "merge feature")
        git(self.repo, "mv", "app.py", "renamed.py")
        git(self.repo, "commit", "-q", "-m", "rename")
        ident = audit.Identity("christo-zero-john", {"id": 129399273, "name": "Christo John"}, ["me@example.com"])
        summary = audit.read_git_history(self.repo / ".git", ident, "christo-zero-john")
        metrics = summary["metrics"]
        self.assertEqual(metrics["commits"], 5)
        self.assertEqual(metrics["direct"], 3)
        self.assertEqual(metrics["coauthored"], 1)
        self.assertEqual(metrics["agent_only"], 1)
        self.assertEqual(metrics["agent_assisted"], 0)
        self.assertEqual(metrics["merges"], 1)
        self.assertEqual(metrics["lines_changed"], 7)
        self.assertEqual(summary["reachable_commits"], 5)
        self.assertEqual(metrics["code_additions"], 6)

    def test_agent_only_not_claimed_in_other_peoples_repos(self):
        ident = audit.Identity("christo-zero-john", {"id": 129399273, "name": "Christo John"}, ["me@example.com"])
        self.assertEqual(ident.category("Claude Code", "claude@agents.local", "", "other-owner"), (None, False))
        self.assertEqual(ident.category("Claude Code", "claude@agents.local", "", "christo-zero-john"), ("agent_only", True))
        self.assertEqual(ident.category("Someone", "other@test.invalid", "Co-authored-by: Christo John <me@example.com>", "other-owner"), ("coauthored", False))

    def test_private_repo_names_are_masked(self):
        original = audit.SHOW_PRIVATE_NAMES
        audit.SHOW_PRIVATE_NAMES = False
        try:
            self.assertNotIn("hidden-name", audit.repo_label({"name": "person/hidden-name", "private": True}, {"person/hidden-name": 1}))
        finally:
            audit.SHOW_PRIVATE_NAMES = original


if __name__ == "__main__":
    unittest.main()
