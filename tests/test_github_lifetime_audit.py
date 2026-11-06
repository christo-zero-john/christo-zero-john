"""Integration checks for author attribution and full Git-ref history."""
from __future__ import annotations

import importlib.util
import datetime as dt
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
        self.assertEqual(metrics["commits"], 4)
        self.assertEqual(metrics["direct"], 3)
        self.assertEqual(metrics["coauthored"], 1)
        self.assertEqual(metrics["agent_only"], 0)
        self.assertEqual(metrics["agent_assisted"], 0)
        self.assertEqual(metrics["merges"], 1)
        self.assertEqual(metrics["lines_changed"], 5)
        self.assertEqual(summary["reachable_commits"], 5)
        self.assertEqual(metrics["code_additions"], 4)

    def test_agent_only_not_claimed_in_other_peoples_repos(self):
        ident = audit.Identity("christo-zero-john", {"id": 129399273, "name": "Christo John"}, ["me@example.com"])
        self.assertEqual(ident.category("Claude Code", "claude@agents.local", "", "other-owner"), (None, False))
        self.assertEqual(ident.category("Claude Code", "claude@agents.local", "", "christo-zero-john"), (None, False))
        self.assertEqual(ident.category("Someone", "other@test.invalid", "Co-authored-by: Christo John <me@example.com>", "other-owner"), ("coauthored", False))


    def test_historical_email_alias_discovery_is_account_verified(self):
        class FakeAPI:
            def request(self, endpoint, params):
                self.endpoint = endpoint
                return {
                    "total_count": 2,
                    "items": [
                        {"author": {"login": "christo-zero-john"},
                         "commit": {"author": {"email": "old-desktop@example.test"}},
                         "repository": {"full_name": "christo-zero-john/app"}},
                        {"author": {"login": "someone-else"},
                         "commit": {"author": {"email": "not-mine@example.test"}},
                         "repository": {"full_name": "someone-else/app"}}
                    ]
                }

        _, warnings, emails = audit.discover_global_authored_repos(
            FakeAPI(), "christo-zero-john", dt.date(2026, 11, 6))
        self.assertFalse(warnings)
        self.assertEqual(emails, {"old-desktop@example.test"})
        ident = audit.Identity("christo-zero-john", {"id": 129399273, "name": "Christo John"}, [])
        self.assertEqual(ident.add_account_linked_commit_emails(emails), 1)
        self.assertTrue(ident.is_email_me("old-desktop@example.test"))
        self.assertFalse(ident.is_email_me("not-mine@example.test"))
        # Deliberately suppress linked-but-unrelated author names unless the
        # author name or email also carries the owner's "christo" marker.
        self.assertEqual(ident.category("Other Name", "old-desktop@example.test", "", "other-org"),
                         (None, False))
        self.assertEqual(ident.category("Christo Old Desktop", "old-desktop@example.test", "", "other-org"),
                         ("direct", False))

    def test_unverified_name_only_is_provisional_in_owned_repos(self):
        ident = audit.Identity("christo-zero-john", {"id": 129399273, "name": "Christo John"}, [])
        self.assertEqual(ident.category("Christo John", "unlinked@example.test", "", "other-org"),
                         (None, False))
        self.assertEqual(ident.category("Christo John", "unlinked@example.test", "", "christo-zero-john"),
                         ("direct", False))
        self.commit("unknown.py", "print(1)\n", "unknown email identity",
                    "Christo John <unlinked@example.test>")
        result = audit.read_git_history(self.repo / ".git", ident, "christo-zero-john")
        self.assertEqual(result["metrics"]["commits"], 1)
        self.assertEqual(result["metrics"]["name_only_attributed"], 1)
        self.assertEqual(result["excluded_name_only"], 0)


    def test_claude_coauthor_on_upstream_fork_is_not_mine(self):
        self.commit("upstream.py", "print('upstream')\n", "upstream change\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
                    "marketcalls <rajandran@marketcalls.in>")
        ident = audit.Identity("christo-zero-john",
                               {"id": 129399273, "name": "Christo John"}, ["me@example.com"])
        result = audit.read_git_history(self.repo / ".git", ident, "christo-zero-john",
                                        "christo-zero-john/openalgo-for-stocketREX")
        self.assertEqual(result["reachable_commits"], 1)
        self.assertEqual(result["metrics"]["commits"], 0)
        self.assertEqual(result["metrics"]["lines_changed"], 0)
        self.assertEqual(result["excluded_unverified_agent"], 1)
        self.commit("my-change.py", "mine = True\n", "My own actual change")
        result = audit.read_git_history(self.repo / ".git", ident, "christo-zero-john",
                                        "christo-zero-john/openalgo-for-stocketREX")
        self.assertEqual(result["metrics"]["commits"], 1)
        self.assertEqual(result["metrics"]["additions"], 1)

    def test_explicit_agent_sha_approval_only(self):
        ident = audit.Identity("christo-zero-john",
                               {"id": 129399273, "name": "Christo John"}, [])
        self.commit("agent.py", "agent_value = 1\n", "agent's standalone commit",
                    "Claude Code <noreply@anthropic.com>")
        sha = git(self.repo, "rev-parse", "HEAD")
        key = "christo-zero-john/my-repo@" + sha
        self.assertEqual(ident.category("Claude Code", "noreply@anthropic.com", "",
                          "christo-zero-john", sha, "christo-zero-john/my-repo"),
                          (None, False))
        audit.APPROVED_AGENT_COMMITS.add(key)
        try:
            self.assertEqual(ident.category("Claude Code", "noreply@anthropic.com", "",
                              "christo-zero-john", sha, "christo-zero-john/my-repo"),
                              ("agent_only", True))
        finally:
            audit.APPROVED_AGENT_COMMITS.discard(key)


    def test_fork_never_claims_christo_name_with_unlinked_email(self):
        ident = audit.Identity("christo-zero-john",
                               {"id": 129399273, "name": "Christo John"}, ["10.christojohn@gmail.com"])
        self.commit("fork.py", "other = 1\n", "upstream with similar name",
                    "Christopher Other <random@thirdparty.test>")
        result = audit.read_git_history(self.repo / ".git", ident,
                                        "christo-zero-john",
                                        "christo-zero-john/other-fork", is_fork=True)
        self.assertEqual(result["metrics"]["commits"], 0)
        self.assertEqual(result["excluded_name_only"], 1)
        self.assertEqual(result["metrics"]["code_lines_changed"], 0)

    def test_matching_named_author_with_custom_desktop_email_in_own_nonfork(self):
        self.commit("app.py", "a = 1\n", "commit under GitHub Desktop alias",
                    "Christo Kalapurackal <desktop-generated-443@users.noreply.github.com>")
        ident = audit.Identity("christo-zero-john",
                               {"id": 129399273, "name": "Christo John"}, [])
        result = audit.read_git_history(self.repo / ".git", ident,
                                        "christo-zero-john",
                                        "christo-zero-john/my-app", is_fork=False)
        self.assertEqual(result["metrics"]["commits"], 1)
        self.assertEqual(result["metrics"]["name_only_attributed"], 1)
        self.assertEqual(result["metrics"]["code_additions"], 1)

    def test_numeric_github_id_survives_username_changes(self):
        ident = audit.Identity("christo-zero-john",
                               {"id": 129399273, "name": "Christo John"}, [])
        self.assertTrue(ident.is_email_me("129399273+christo-old-handle@users.noreply.github.com"))
        self.assertFalse(ident.is_email_me("999999999+christo-old-handle@users.noreply.github.com"))
        self.assertEqual(ident.category("Christo Previous", 
                         "129399273+christo-old-handle@users.noreply.github.com",
                         "", "other-organization"), ("direct", False))

    def test_unmerged_feature_branch_and_unrelated_author_excluded(self):
        self.commit("main.py", "mine = True\n", "main human")
        git(self.repo, "switch", "-q", "-c", "experimental")
        self.commit("experimental.py", "feature = True\n",
                    "feature authored by Christo", "Christo Builder <random-desktop@other.test>")
        self.commit("upstream.py", "notmine = True\n",
                    "foreign developer", "Another Developer <foreign@example.test>")
        git(self.repo, "switch", "-q", "main")
        ident = audit.Identity("christo-zero-john",
                               {"id": 129399273, "name": "Christo John"}, ["me@example.com"])
        result = audit.read_git_history(self.repo / ".git", ident,
                                        "christo-zero-john",
                                        "christo-zero-john/my-app", is_fork=False)
        self.assertEqual(result["reachable_commits"], 3)
        self.assertEqual(result["metrics"]["commits"], 2)
        self.assertEqual(result["metrics"]["name_only_attributed"], 1)
        self.assertEqual(result["metrics"]["code_additions"], 2)

    def test_human_christo_with_claude_coauthor_is_one_commit(self):
        ident = audit.Identity("christo-zero-john",
                               {"id": 129399273, "name": "Christo John"},
                               ["10.christojohn@gmail.com"])
        self.commit("feature.py", "x = True\n",
                    "implemented with agent\n\nCo-authored-by: Claude Code <noreply@anthropic.com>",
                    "Christo John <10.christojohn@gmail.com>")
        result = audit.read_git_history(self.repo / ".git", ident,
                                        "christo-zero-john", "christo-zero-john/app")
        self.assertEqual(result["metrics"]["commits"], 1)
        self.assertEqual(result["metrics"]["direct"], 1)
        self.assertEqual(result["metrics"]["agent_assisted"], 1)
        self.assertEqual(result["metrics"]["agent_only"], 0)

    def test_private_repo_names_are_masked(self):
        original = audit.SHOW_PRIVATE_NAMES
        audit.SHOW_PRIVATE_NAMES = False
        try:
            self.assertNotIn("hidden-name", audit.repo_label({"name": "person/hidden-name", "private": True}, {"person/hidden-name": 1}))
        finally:
            audit.SHOW_PRIVATE_NAMES = original


if __name__ == "__main__":
    unittest.main()
