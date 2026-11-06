#!/usr/bin/env python3
"""Lifetime GitHub audit for a profile README; Python 3.11+, standard library only.

Metric contract:
- qualifying commit: GitHub-linked email plus Christo marker, or provisional
  Christo-name match in owned nonfork repositories, or approved exact agent SHA
- a fork's upstream contributors and unrelated AI coauthors are never owner work
- count at most once per repository + SHA; enumerate all accessible Git refs
- LOC: Git numstat additions + deletions, including text/config/documentation; binary
  diffs have no line totals; merges compared with first parent
- current language bytes come from GitHub Linguist; historical language churn is
  inferred from changed filenames (not GitHub Linguist)
- private repository names/URLs are not written to the public outputs by default
"""
from __future__ import annotations

import collections
import dataclasses
import datetime as dt
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

UTC = dt.timezone.utc
REPORT_DIR = Path(os.getenv("AUDIT_OUTPUT_DIR", "docs/github-audit"))
README = Path(os.getenv("AUDIT_README", "README.md"))
API_ROOT = os.getenv("GITHUB_API_URL", "https://api.github.com").rstrip("/")
TOKEN = os.getenv("AUDIT_TOKEN", "")
USER_EXPECTED = os.getenv("AUDIT_USER", "christo-zero-john")
MAX_WORKERS = int(os.getenv("AUDIT_WORKERS", "3"))
CLONE_TIMEOUT = int(os.getenv("AUDIT_CLONE_TIMEOUT_SECONDS", "900"))
LOG_TIMEOUT = int(os.getenv("AUDIT_GIT_LOG_TIMEOUT_SECONDS", "1200"))
DISCOVERY_MAX_QUERIES = int(os.getenv("AUDIT_DISCOVERY_MAX_QUERIES", "120"))
SHOW_PRIVATE_NAMES = os.getenv("AUDIT_SHOW_PRIVATE_NAMES", "false").lower() == "true"
GLOBAL_DISCOVERY = os.getenv("AUDIT_GLOBAL_DISCOVERY", "true").lower() == "true"
# Agent metadata alone never establishes personal authorship.
# All Claude/Codex assisted work counts through the owner's author/coauthor.
INCLUDE_FORKS = os.getenv("AUDIT_INCLUDE_FORKS", "true").lower() == "true"
FETCH_LANGUAGES = os.getenv("AUDIT_CURRENT_LANGUAGES", "true").lower() == "true"
AGENT_IDENTIFIERS = [s.strip().casefold() for s in re.split(r"[,;]", (os.getenv(
    "AUDIT_AGENT_IDENTIFIERS", "") or "claude,anthropic,codex,copilot,cursor,aider,devin,gemini")) if s.strip()]

CODE_EXTS = {
    ".ts": "TypeScript", ".tsx": "TypeScript", ".mts": "TypeScript", ".cts": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".py": "Python", ".pyi": "Python", ".sql": "SQL", ".rs": "Rust",
    ".go": "Go", ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin",
    ".swift": "Swift", ".dart": "Dart", ".php": "PHP", ".rb": "Ruby",
    ".c": "C", ".h": "C/C++", ".cc": "C++", ".cpp": "C++", ".hpp": "C++",
    ".cs": "C#", ".fs": "F#", ".fsx": "F#", ".scala": "Scala",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell", ".ps1": "PowerShell",
    ".vue": "Vue", ".svelte": "Svelte", ".astro": "Astro", ".html": "HTML",
    ".css": "CSS", ".scss": "SCSS", ".sass": "Sass", ".less": "Less",
    ".graphql": "GraphQL", ".gql": "GraphQL", ".r": "R", ".lua": "Lua",
    ".ex": "Elixir", ".exs": "Elixir", ".erl": "Erlang", ".elm": "Elm",
    ".zig": "Zig", ".pl": "Perl", ".sol": "Solidity", ".prisma": "Prisma",
    ".tf": "Terraform", ".tfvars": "Terraform", ".nix": "Nix",
    ".ipynb": "Notebook (JSON)", ".wasm": "WebAssembly",
}
DOC_EXTS = {".md", ".mdx", ".txt", ".rst", ".adoc", ".pdf", ".docx"}
CONFIG_EXTS = {".json", ".jsonc", ".yaml", ".yml", ".toml", ".xml", ".ini", ".cfg", ".lock", ".env", ".csv", ".tsv"}
SPECIAL_CODE = {"Dockerfile": "Dockerfile", "Makefile": "Makefile", "Jenkinsfile": "Groovy", "Gemfile": "Ruby", "Rakefile": "Ruby"}
COAUTHOR = re.compile(r"(?im)^\s*co-authored-by:\s*(.*?)\s*<([^>]+)>\s*$")
NUMSTAT = re.compile(rb"^(\d+|-)\t(\d+|-)\t(.*)$", re.DOTALL)


def log(message: str) -> None:
    print(message, flush=True)


def as_bool(v: str) -> bool:
    return str(v).casefold() in ("true", "1", "yes", "on")


def split_aliases(value: str) -> set[str]:
    return {v.strip().casefold() for v in re.split(r"[,;]", value) if v.strip()}


def clean_md(s: object) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ").replace("\r", " ").replace("<", "&lt;").replace(">", "&gt;")


def fmt(n: int) -> str:
    return f"{n:,}"


def now_utc() -> dt.datetime:
    return dt.datetime.now(UTC)


class APIError(RuntimeError):
    pass


class GitHubAPI:
    def __init__(self, token: str):
        if not token:
            raise APIError("AUDIT_TOKEN is required; set GH_AUDIT_READ_TOKEN in GitHub repository secrets")
        self.token = token

    def request(self, endpoint: str, params: dict | None = None, *, optional: bool = False):
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        query = urllib.parse.urlencode(params or {})
        url = API_ROOT + endpoint + ("?" + query if query else "")
        for attempt in range(7):
            req = urllib.request.Request(url, headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "christo-lifetime-github-audit/1.0",
            })
            try:
                with urllib.request.urlopen(req, timeout=45) as res:
                    return json.load(res)
            except urllib.error.HTTPError as exc:
                if optional and exc.code in (403, 404, 422):
                    return None
                rem = exc.headers.get("X-RateLimit-Remaining")
                retry_after = exc.headers.get("Retry-After")
                if attempt < 6 and (exc.code in (429, 500, 502, 503, 504) or
                                    (exc.code == 403 and (rem == "0" or retry_after))):
                    delay = min(180, (int(retry_after) if retry_after and retry_after.isdigit()
                                      else max(4, min(90, 3 * 2 ** attempt))))
                    if rem == "0" and exc.headers.get("X-RateLimit-Reset", "").isdigit():
                        delay = min(180, max(delay, int(exc.headers["X-RateLimit-Reset"]) - int(time.time()) + 2))
                    log(f"GitHub API throttled ({exc.code}); retrying in {delay}s")
                    time.sleep(delay)
                    continue
                try:
                    detail = exc.read(300).decode("utf-8", "replace")
                except Exception:
                    detail = ""
                raise APIError(f"GitHub API HTTP {exc.code} on {endpoint}: {detail}") from None
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt == 6:
                    raise APIError(f"GitHub API connection failed on {endpoint}: {exc}") from exc
                time.sleep(min(45, 2 ** attempt + 1))
        raise APIError(f"GitHub API request exhausted retries: {endpoint}")

    def pages(self, endpoint: str, params: dict | None = None):
        page = 1
        while True:
            args = dict(params or {})
            args.update(per_page=100, page=page)
            batch = self.request(endpoint, args)
            if not isinstance(batch, list):
                raise APIError(f"Expected list from {endpoint}")
            yield from batch
            if len(batch) < 100:
                return
            page += 1


LINGUIST_INDEX_PATH = Path(os.getenv("AUDIT_LINGUIST_INDEX", "/tmp/github-linguist-languages.json"))
if LINGUIST_INDEX_PATH.is_file():
    LINGUIST_INDEX = json.loads(LINGUIST_INDEX_PATH.read_text(encoding="utf-8"))
else:
    LINGUIST_INDEX = None


def excluded_source_path(path: str) -> bool:
    parts = path.casefold().replace("\\\\", "/").split("/")
    return (
        any(x in parts for x in ("node_modules", ".next", "dist", "build", "vendor",
                                  "vendors", "third_party", "third-party",
                                  "generated", "coverage", ".venv", "venv", "target",
                                  "__pycache__", ".turbo", "out"))
        or parts[-1].endswith((".min.js", ".min.css", ".map", ".lock"))
        or parts[-1] in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock")
    )


def linguist_path_language(path: str) -> tuple[str, bool] | None:
    # Official Linguist registry, with *uncertain* ambiguous filenames explicitly
    # excluded from strict code-LOC totals. Content-level detection would require
    # analyzing the blob at each historical commit.
    if not LINGUIST_INDEX:
        return None
    filename = path.replace("\\\\", "/").rsplit("/", 1)[-1]
    options = LINGUIST_INDEX.get("filenames", {}).get(filename)
    if not options:
        ext_map = LINGUIST_INDEX.get("extensions", {})
        lower = filename.casefold()
        # Try actual suffixes from longest to shortest instead of checking every
        # Linguist extension for every Git-history file (large repositories).
        options = []
        for index, char in enumerate(lower):
            if char == "." and lower[index:] in ext_map:
                options = ext_map[lower[index:]]
                break
    dedup = {(x.get("name"), x.get("type")) for x in options}
    if len(dedup) == 1:
        name, kind = next(iter(dedup))
        if excluded_source_path(path):
            return "Generated / vendored source", False
        return name, kind in ("programming", "markup")
    if len(dedup) > 1:
        return "Ambiguous Linguist filename", False
    return "Unclassified by Linguist filename metadata", False


def language_of(path: str) -> tuple[str, bool]:
    authoritative = linguist_path_language(path)
    if authoritative is not None:
        return authoritative
    name = path.replace("\\", "/").rsplit("/", 1)[-1]
    if excluded_source_path(path):
        return "Generated / vendored source", False
    if name in SPECIAL_CODE:
        return SPECIAL_CODE[name], True
    ext = Path(name).suffix.casefold()
    if ext in CODE_EXTS:
        return CODE_EXTS[ext], ext != ".ipynb"
    if ext in DOC_EXTS:
        return "Documentation", False
    if ext in CONFIG_EXTS or name.startswith(".env"):
        return "Configuration / data", False
    return "Other text / unknown", False


@dataclasses.dataclass
class Metrics:
    commits: int = 0
    direct: int = 0
    coauthored: int = 0
    agent_only: int = 0
    agent_assisted: int = 0
    name_only_attributed: int = 0  # provisional attribution in owned repositories
    merges: int = 0
    additions: int = 0
    deletions: int = 0
    code_additions: int = 0
    code_deletions: int = 0
    binary_changes: int = 0
    files_changed: int = 0

    def add(self, other: "Metrics") -> None:
        for field in dataclasses.fields(self):
            k = field.name
            setattr(self, k, getattr(self, k) + getattr(other, k))

    def as_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["lines_changed"] = self.additions + self.deletions
        d["code_lines_changed"] = self.code_additions + self.code_deletions
        d["net_lines"] = self.additions - self.deletions
        return d


class Identity:
    """Conservative account identity: Christo signal + email evidence, or owned-nonfork name inference.

    Name-only work is intentionally reported as provisional. A fork's inherited
    history never qualifies solely from an author name.
    """
    def __init__(self, username: str, user: dict, emails: list[str]):
        self.username = username
        self.account_id = str(user.get("id") or "")
        self.names = split_aliases(os.getenv("AUDIT_NAMES", "")) | {username.casefold()}
        if user.get("name"):
            self.names.add(user["name"].strip().casefold())
        self.emails = split_aliases(os.getenv("AUDIT_EMAILS", ""))
        self.emails.update(e.strip().casefold() for e in emails if e)
        if user.get("email"):
            self.emails.add(user["email"].strip().casefold())
        self.emails.add(username.casefold() + "@users.noreply.github.com")
        if user.get("id"):
            self.emails.add(f"{user['id']}+{username}@users.noreply.github.com".casefold())
        self.linked_commit_emails = 0

    def add_account_linked_commit_emails(self, emails: set[str]) -> int:
        """Trust only author emails of commits GitHub resolves to this account."""
        normalized = {e.strip().casefold() for e in emails if e and "@" in e}
        additions = normalized - self.emails
        self.emails.update(normalized)
        self.linked_commit_emails += len(additions)
        return len(additions)

    @staticmethod
    def has_christo(value: str) -> bool:
        # Case-insensitive explicit identity fragment required by the owner.
        # A matching name alone is NEVER called verified.
        return "christo" in str(value).casefold()

    def is_email_me(self, email: str) -> bool:
        email = email.strip().casefold()
        if not email:
            return False
        if email in self.emails:
            return True
        # GitHub's account ID is stable even if the GitHub login later changes.
        if self.account_id and re.fullmatch(
                re.escape(self.account_id) + r"\+[^@]+@users\.noreply\.github\.com",
                email):
            return True
        return False

    def attribution(self, name: str, email: str, repo_owner: str,
                    is_fork: bool = False) -> str | None:
        named = self.has_christo(name) or self.has_christo(email)
        # Exact known email and account ID are the strong GitHub identity links,
        # but require the Christo marker to prevent crediting unrelated developers
        # if a historic address was reused or misattributed.
        if self.is_email_me(email) and (named or (
                self.account_id and email.strip().casefold().startswith(
                    self.account_id + "+"))):
            return "verified"
        if named and repo_owner.casefold() == self.username.casefold() and not is_fork:
            # This can cover Github Desktop's unlinked/custom author email.
            # It is NOT proven identity; expose it as provisional in the report.
            return "inferred"
        return None

    def is_name_only(self, name: str, email: str, repo_owner: str,
                     is_fork: bool = False) -> bool:
        return (self.has_christo(name) or self.has_christo(email)) and (
            self.attribution(name, email, repo_owner, is_fork) != "verified"
        )

    def is_me(self, name: str, email: str, repo_owner: str = "",
              is_fork: bool = False) -> bool:
        return self.attribution(name, email, repo_owner, is_fork) is not None

    def is_agent(self, name: str, email: str) -> bool:
        whole = (name + " " + email).casefold()
        return any(pattern.strip() in whole for pattern in AGENT_IDENTIFIERS)

    def category(self, author_name: str, author_email: str,
                 message: str, repo_owner: str, commit_sha: str = "",
                 repo_full_name: str = "", is_fork: bool = False
                 ) -> tuple[str | None, bool]:
        # An agent co-author is only a FLAG on a qualifying human commit.
        # Never credit another author's work merely because Claude/Codex appears.
        agent_author = self.is_agent(author_name, author_email)
        partners = COAUTHOR.findall(message)
        agent_partner = any(self.is_agent(name, email) for name, email in partners)
        if self.attribution(author_name, author_email, repo_owner, is_fork):
            return "direct", agent_partner
        if any(self.attribution(name, email, repo_owner, is_fork)
               for name, email in partners):
            return "coauthored", (agent_author or agent_partner)
        # Owner's agents add Co-authored-by trailers to commits authored by the
        # owner. Standalone agent accounts are NEVER counted without the owner
        # author/coauthor identity, including in forks. This is intentionally
        # stricter than legacy manual agent-only approvals.
        return None, False


def nul_tokens(stream):
    """Yield NUL-delimited git --numstat -z records without loading output into RAM."""
    buf = b""
    while True:
        data = stream.read(65536)
        if not data:
            if buf:
                yield buf
            return
        parts = (buf + data).split(b"\0")
        yield from parts[:-1]
        buf = parts[-1]


def read_git_history(mirror: Path, identity: Identity, repo_owner: str,
                     repo_full_name: str = "", is_fork: bool = False) -> dict:
    """Read every reachable unique commit from a mirror; no first-parent *traversal*."""
    git_format = "%x1e%H%x1f%an%x1f%ae%x1f%aI%x1f%cn%x1f%ce%x1f%P%x1f%B%x1f"
    cmd = ["git", "--git-dir=" + str(mirror), "log", "--all", "--root",
           "--no-ext-diff", "--no-textconv", "--find-renames", "--diff-merges=first-parent",
           "--numstat", "-z", "--format=" + git_format]
    if shutil.which("timeout"):
        cmd = ["timeout", str(LOG_TIMEOUT) + "s", *cmd]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"})
    overall = Metrics()
    yearly: dict[str, Metrics] = collections.defaultdict(Metrics)
    monthly: dict[str, Metrics] = collections.defaultdict(Metrics)
    languages: dict[str, Metrics] = collections.defaultdict(Metrics)
    authors: collections.Counter = collections.Counter()
    first_date, last_date = None, None
    reachable = 0
    excluded_names = 0
    excluded_agents = 0
    current = None
    current_stats = None
    expecting_rename = 0
    pending_rename = None
    unique_shas = set()
    qualifying_commits = {}  # internal only; withheld from public per-repo JSON

    def apply_change(add: int | None, delete: int | None, file_path: str):
        if current is None or current["kind"] is None:
            return
        if add is None or delete is None:
            current_stats.binary_changes += 1
            return
        current_stats.files_changed += 1
        current_stats.additions += add
        current_stats.deletions += delete
        lang, code = language_of(file_path)
        languages[lang].additions += add
        languages[lang].deletions += delete
        languages[lang].files_changed += 1
        if code:
            current_stats.code_additions += add
            current_stats.code_deletions += delete
            languages[lang].code_additions += add
            languages[lang].code_deletions += delete

    def finish():
        nonlocal current, current_stats, first_date, last_date, reachable, excluded_names, excluded_agents
        if current is None:
            return
        reachable += 1
        excluded_names += int(current.get("excluded_name", False))
        excluded_agents += int(current.get("excluded_agent", False))
        if current["kind"]:
            stat = current_stats
            stat.commits = 1
            setattr(stat, current["kind"], 1)
            stat.agent_assisted = int(current["agent_assisted"] and current["kind"] != "agent_only")
            stat.name_only_attributed = int(current["name_only"])
            stat.merges = int(current["merge"])
            overall.add(stat)
            day = current["date"]
            yearly[day[:4]].add(stat)
            monthly[day[:7]].add(stat)
            first_date = min(first_date, day) if first_date else day
            last_date = max(last_date, day) if last_date else day
            authors[current["kind"]] += 1
            qualifying_commits[current["sha"]] = stat.as_dict()
        current, current_stats = None, None

    try:
        assert proc.stdout is not None
        for raw in nul_tokens(proc.stdout):
            part = raw.lstrip(b"\n\r")
            if not part:
                continue
            if part.startswith(b"\x1e"):
                finish()
                fields = part[1:].decode("utf-8", "replace").split("\x1f", 8)
                if len(fields) < 9:
                    raise RuntimeError("Malformed git log metadata record")
                sha, name, email, date, committer, committer_email, parents, message, _ = fields
                if sha in unique_shas:
                    # Git log --all normally deduplicates per SHA, even across tags/branches.
                    current = {"sha": sha, "kind": None, "date": date[:10], "merge": False, "agent_assisted": False, "name_only": False, "excluded_name": False, "excluded_agent": False}
                else:
                    unique_shas.add(sha)
                    kind, assisted = identity.category(
                        name, email, message, repo_owner, sha, repo_full_name, is_fork)
                    partners = COAUTHOR.findall(message)
                    author_provenance = identity.attribution(name, email, repo_owner, is_fork)
                    partners_provenance = [
                        identity.attribution(n, e, repo_owner, is_fork) for n, e in partners]
                    inferred = (kind == "direct" and author_provenance == "inferred"
                                or kind == "coauthored" and "verified" not in partners_provenance
                                and "inferred" in partners_provenance)
                    possible_name = identity.is_name_only(name, email, repo_owner, is_fork) or any(
                        identity.is_name_only(n, e, repo_owner, is_fork) for n, e in partners)
                    possible_agent = identity.is_agent(name, email) or any(
                        identity.is_agent(n, e) for n, e in partners)
                    current = {"sha": sha, "kind": kind, "date": date[:10],
                               "merge": len(parents.split()) > 1, "agent_assisted": assisted,
                               "name_only": inferred,
                               "excluded_name": kind is None and possible_name,
                               "excluded_agent": kind is None and possible_agent}
                current_stats = Metrics()
                expecting_rename = 0
                pending_rename = None
                continue
            if current is None:
                continue
            if expecting_rename:
                if expecting_rename == 2:
                    expecting_rename = 1
                else:
                    path = part.decode("utf-8", "replace")
                    apply_change(pending_rename[0], pending_rename[1], path)
                    pending_rename = None
                    expecting_rename = 0
                continue
            match = NUMSTAT.match(part)
            if not match:
                continue
            a, d, name = match.groups()
            add = None if a == b"-" else int(a)
            delete = None if d == b"-" else int(d)
            if not name:
                pending_rename = (add, delete)
                expecting_rename = 2
            else:
                apply_change(add, delete, name.decode("utf-8", "replace"))
        finish()
    finally:
        if proc.stdout:
            proc.stdout.close()
    stderr = proc.stderr.read().decode("utf-8", "replace") if proc.stderr else ""
    code = proc.wait()
    if proc.stderr:
        proc.stderr.close()
    if code:
        raise RuntimeError(f"git log failed (exit {code}): {stderr[-300:]}")
    return {"metrics": overall.as_dict(), "qualifying_commits": qualifying_commits, "reachable_commits": reachable,
            "excluded_name_only": excluded_names, "excluded_unverified_agent": excluded_agents,
            "first_commit": first_date, "last_commit": last_date,
            "years": {k: v.as_dict() for k, v in yearly.items()},
            "months": {k: v.as_dict() for k, v in monthly.items()},
            "languages": {k: v.as_dict() for k, v in languages.items()}}


def create_askpass(path: Path) -> Path:
    script = path / "git-askpass.sh"
    script.write_text("#!/bin/sh\ncase \"$1\" in\n*Username*) printf 'x-access-token' ;;\n*Password*) printf '%s' \"$AUDIT_TOKEN\" ;;\n*) printf '' ;;\nesac\n")
    script.chmod(0o700)
    return script


def inspect_repo(repo: dict, identity: Identity, api: GitHubAPI) -> dict:
    full = repo["full_name"]
    result = {"name": full, "private": repo.get("private", False),
              "fork": repo.get("fork", False), "archived": repo.get("archived", False),
              "owner": repo.get("owner", {}).get("login", full.split("/")[0]),
              "html_url": repo.get("html_url", f"https://github.com/{full}"),
              "created_at": repo.get("created_at"),
              "default_language": repo.get("language"),
              "stars": repo.get("stargazers_count", 0),
              "forks": repo.get("forks_count", 0), "size_kb": repo.get("size", 0),
              "status": "ok"}
    try:
        with tempfile.TemporaryDirectory(prefix="github-audit-") as tmp:
            directory = Path(tmp)
            askpass = create_askpass(directory)
            mirror = directory / "mirror.git"
            environment = {**os.environ, "GIT_ASKPASS": str(askpass),
                           "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1"}
            # The access token is never embedded into the URL, git config, or command line.
            url = f"https://github.com/{urllib.parse.quote(full, safe='/')}.git"
            command = ["git", "-c", "credential.helper=", "clone", "--mirror", "--quiet", url, str(mirror)]
            clone = subprocess.run(command, env=environment, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.PIPE, timeout=CLONE_TIMEOUT, check=False)
            if clone.returncode:
                err = clone.stderr.decode("utf-8", "replace")[-400:]
                # Avoid echoing tokens or any credential-like information in the error.
                err = err.replace(TOKEN, "[REDACTED]") if TOKEN else err
                raise RuntimeError(f"clone error {clone.returncode}: {err}")
            result.update(read_git_history(mirror, identity, result["owner"], full,
                                           is_fork=bool(result["fork"])))
    except (OSError, subprocess.TimeoutExpired, RuntimeError) as exc:
        result["status"] = "failed"
        result["error"] = str(exc).replace(TOKEN, "[REDACTED]") if TOKEN else str(exc)
    # Verify fork/default-branch ancestry independently from Git authorship.
    # 'ahead_by=0' confirms there are no fork-only commits on the DEFAULT
    # branch relative to the current parent; other refs can still diverge.
    if result["fork"]:
        evidence = {"status": "unknown", "parent": None, "ahead_default": None,
                    "behind_default": None}
        try:
            detailed = api.request("/repos/" + urllib.parse.quote(full, safe="/"))
            parent = (detailed or {}).get("parent") or {}
            parent_name = parent.get("full_name")
            if parent_name:
                evidence["parent"] = parent_name
                parent_branch = parent.get("default_branch") or "main"
                fork_branch = detailed.get("default_branch") or repo.get("default_branch") or "main"
                comparison_endpoint = ("/repos/" + urllib.parse.quote(parent_name, safe="/") +
                    "/compare/" + urllib.parse.quote(parent_branch, safe="") +
                    "..." + urllib.parse.quote(result["owner"] + ":" + fork_branch, safe=":"))
                comparison = api.request(comparison_endpoint, optional=True)
                if comparison and isinstance(comparison.get("ahead_by"), int):
                    evidence.update(status="checked", ahead_default=comparison["ahead_by"],
                                    behind_default=comparison.get("behind_by"))
                else:
                    evidence["status"] = "comparison_unavailable"
            else:
                evidence["status"] = "parent_not_visible"
        except APIError:
            evidence["status"] = "error"
        result["fork_evidence"] = evidence
    if FETCH_LANGUAGES:
        try:
            result["current_languages_bytes"] = api.request(
                "/repos/" + urllib.parse.quote(full, safe="/") + "/languages")
        except APIError as exc:
            result["current_languages_bytes"] = {}
            result["language_error"] = str(exc)
    return result


def discover_global_authored_repos(api: GitHubAPI, login: str, until: dt.date) -> tuple[dict[str, dict], list[str], set[str]]:
    """Find public repos missing from /user/repos via indexed account-linked author commits.

    GitHub commit search returns at most 1000 results per query; bisect dates to
    avoid using a truncated sample. Coauthored-only commits are NOT discoverable.
    """
    found: dict[str, dict] = {}
    warnings: list[str] = []
    linked_author_emails: set[str] = set()
    calls = 0

    def search(start: dt.date, end: dt.date):
        nonlocal calls
        if calls >= DISCOVERY_MAX_QUERIES:
            raise APIError("Global commit discovery exceeded AUDIT_DISCOVERY_MAX_QUERIES; increase limit to expand coverage")
        query = f"author:{login} author-date:{start.isoformat()}..{end.isoformat()}"
        data = api.request("/search/commits", {"q": query, "per_page": 100, "page": 1})
        calls += 1
        n = int(data.get("total_count", 0))
        if (n > 1000 or data.get("incomplete_results")) and start < end:
            middle = start + dt.timedelta(days=(end - start).days // 2)
            search(start, middle)
            search(middle + dt.timedelta(days=1), end)
            return
        if n > 1000 or data.get("incomplete_results"):
            warnings.append(f"GitHub commit-search could not exhaust {start} (indexed results over limit)")
        for page in range(1, min(10, math.ceil(min(n, 1000) / 100)) + 1):
            if page == 1:
                batch = data
            else:
                batch = api.request("/search/commits", {"q": query, "per_page": 100, "page": page})
                calls += 1
            for item in batch.get("items", []):
                linked_user = item.get("author") or {}
                author = (item.get("commit") or {}).get("author") or {}
                if linked_user.get("login", "").casefold() == login.casefold():
                    email = author.get("email", "").strip()
                    if email and "@" in email:
                        linked_author_emails.add(email)
                item_repo = item.get("repository") or {}
                full = item_repo.get("full_name")
                if full:
                    found[full.casefold()] = item_repo
    try:
        search(dt.date(1970, 1, 1), until)
    except APIError as exc:
        warnings.append("Global public commit discovery incomplete: " + str(exc))
    log(f"Global author search: {len(found)} repositories found using {calls} API requests")
    return found, warnings, linked_author_emails


def count_search(api: GitHubAPI, query: str) -> int:
    data = api.request("/search/issues", {"q": query, "per_page": 1})
    if data.get("incomplete_results"):
        raise APIError("Indexed search incomplete for: " + query)
    return int(data.get("total_count", 0))


def account_activity(api: GitHubAPI, user: dict, until: dt.date) -> tuple[dict, list[str]]:
    login = user["login"]
    created = (user.get("created_at") or "1970-01-01")[:10]
    year0 = max(1970, int(created[:4]))
    queries = {
        "pull_requests_opened": f"is:pr author:{login}",
        "pull_requests_merged": f"is:pr is:merged author:{login}",
        "issues_opened": f"is:issue author:{login}",
        "issues_closed": f"is:issue is:closed author:{login}",
        "distinct_prs_reviewed": f"is:pr reviewed-by:{login}",
        "distinct_threads_participated": f"commenter:{login}",
    }
    output: dict = {"years": {}, "followers_current": user.get("followers", 0),
                    "following_current": user.get("following", 0),
                    "public_repos_current": user.get("public_repos", 0),
                    "account_created_at": user.get("created_at")}
    problems = []
    for key, query in queries.items():
        try:
            output[key] = count_search(api, query)
        except APIError as exc:
            output[key] = None
            problems.append(f"{key}: {exc}")
    for y in range(year0, until.year + 1):
        end = f"{y}-12-31" if y < until.year else until.isoformat()
        window = f"created:{y}-01-01..{end}"
        record = {}
        for category, q in (("pull_requests_opened", queries["pull_requests_opened"]),
                            ("issues_opened", queries["issues_opened"])):
            try:
                record[category] = count_search(api, q + " " + window)
            except APIError as exc:
                record[category] = None
                problems.append(f"{y} {category}: {exc}")
        output["years"][str(y)] = record
    return output, problems


def merge_metrics(destination: Metrics, source: dict) -> None:
    destination.add(Metrics(**{k: source.get(k, 0) for k in Metrics.__dataclass_fields__}))


def totals_by_key(repos: list[dict], key: str) -> dict[str, dict]:
    records: dict[str, Metrics] = collections.defaultdict(Metrics)
    for repo in repos:
        if repo["status"] != "ok":
            continue
        for title, metrics in repo[key].items():
            merge_metrics(records[title], metrics)
    return {name: stat.as_dict() for name, stat in sorted(records.items())}


def md_table(headers: list[str], rows: list[list[object]]) -> str:
    if not rows:
        return "_No records._\n"
    head = "| " + " | ".join(headers) + " |"
    rule = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(clean_md(x) for x in row) + " |" for row in rows]
    return "\n".join([head, rule, *body]) + "\n"


def repo_label(repo: dict, private_indices: dict[str, int]) -> str:
    if repo.get("private") and not SHOW_PRIVATE_NAMES:
        return f"Private repository #{private_indices[repo['name']]:03d}"
    return repo["name"]


def link_repo(repo: dict, private_indices: dict[str, int]) -> str:
    label = repo_label(repo, private_indices)
    if repo.get("private") and not SHOW_PRIVATE_NAMES:
        return label
    return f"[{clean_md(label)}]({repo['html_url']})"


def render_reports(user: dict, repositories: list[dict], activity: dict,
                   warnings: list[str], as_of: dt.datetime, identity: Identity):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ok_repos = [r for r in repositories if r["status"] == "ok"]
    failures = [r for r in repositories if r["status"] != "ok"]
    priv_indices = {r["name"]: n for n, r in enumerate(sorted(
        (x for x in repositories if x["private"]), key=lambda x: x["name"]), 1)}
    total = Metrics()
    reachable_commits = 0
    first = None
    last = None
    private_total = Metrics()
    unique_commits = {}
    for repo in ok_repos:
        merge_metrics(total, repo["metrics"])
        if repo["private"]:
            merge_metrics(private_total, repo["metrics"])
        reachable_commits += repo["reachable_commits"]
        for sha, metric in repo.get("qualifying_commits", {}).items():
            unique_commits.setdefault(sha, metric)
        date = repo["first_commit"]
        if date:
            first = min(first, date) if first else date
        date = repo["last_commit"]
        if date:
            last = max(last, date) if last else date
    global_unique_total = Metrics()
    for metric in unique_commits.values():
        merge_metrics(global_unique_total, metric)
    global_unique_data = global_unique_total.as_dict()
    yearly = totals_by_key(ok_repos, "years")
    monthly = totals_by_key(ok_repos, "months")
    languages = totals_by_key(ok_repos, "languages")
    current_lang: collections.Counter = collections.Counter()
    for r in ok_repos:
        if r.get("current_languages_bytes"):
            current_lang.update(r["current_languages_bytes"])
    owned = [r for r in repositories if r["owner"].casefold() == user["login"].casefold()]
    created_years = collections.Counter(r["created_at"][:4] for r in owned if r.get("created_at"))
    failures_label = ", ".join(repo_label(x, priv_indices) for x in failures[:12])
    provisional_names = total.name_only_attributed
    excluded_names = sum(r.get("excluded_name_only", 0) for r in ok_repos)
    excluded_agents = sum(r.get("excluded_unverified_agent", 0) for r in ok_repos)
    fork_unknown = sum(bool(r.get("fork")) and
                       r.get("fork_evidence", {}).get("status") != "checked"
                       for r in repositories)
    incomplete = (len(failures) > 0 or len(warnings) > 0 or
                  excluded_names > 0 or provisional_names > 0 or fork_unknown > 0)
    status = "PARTIAL — incomplete sources or provisional identity matches" if incomplete else "COMPLETE for enumerated accessible repositories"
    generated = as_of.strftime("%Y-%m-%d %H:%M UTC")
    docs = "[Overview](./REPORT.md) · [Repositories](./repositories.md) · [Timeline](./timeline.md) · [Languages](./languages.md) · [Activity](./activity.md)"
    scope = ("All available refs in each cloned repository (branches, tags, and refs advertised by GitHub); "
             "each SHA once per repository. Verified Christo identity markers qualify; owned nonfork "
             "name/email-only matches are provisional. Inherited fork contributions without verified "
             "identity are excluded. Agent-only SHA approvals must be explicit.")
    warning_block = ("\n**Audit gaps:** " + str(len(failures)) + " repository clone/scan failures; " +
                     str(len(warnings)) + " discovery/API warnings; " +
                     fmt(provisional_names) + " name-only *included* commits; " + fmt(excluded_names) +
                     " name-only matches excluded; " + fmt(fork_unknown) + " fork comparisons unavailable. " +
                     "Check the [repository report](./repositories.md) and workflow logs. " +
                     "Name-only matches are not verified authorship.\n") if incomplete else ""
    totals = total.as_dict()
    lines = [
        "# Lifetime GitHub engineering audit", "", docs, "",
        f"**Account:** [{user['login']}](https://github.com/{user['login']})  ",
        f"**As of:** {generated}  ", f"**Coverage:** {status}", "",
        "## Lifetime engineering totals", "",
        md_table(["Metric", "Value"], [
            ["Repositories enumerated", fmt(len(repositories))],
            ["Repositories successfully scanned", fmt(len(ok_repos))],
            ["Owned repositories enumerated", fmt(len(owned))],
            ["Private repositories enumerated", fmt(sum(r["private"] for r in repositories))],
            ["Total reachable Git commits in scanned repositories (all authors)", fmt(reachable_commits)],
            ["Attributed commits — repository/SHA occurrences", fmt(totals["commits"])],
            ["Unique attributed Git SHAs — deduplicated across repositories", fmt(global_unique_data["commits"])],
            ["Unique attributed LOC changed — deduplicated across repositories", fmt(global_unique_data["lines_changed"])],
            ["Unique attributed lines added — cross-repo deduplicated", fmt(global_unique_data["additions"])],
            ["Unique attributed lines deleted — cross-repo deduplicated", fmt(global_unique_data["deletions"])],
            ["Unique code-classified LOC changed", fmt(global_unique_data["code_lines_changed"])],
            ["Directly authored", fmt(totals["direct"])],
            ["Co-authored by you (not direct author)", fmt(totals["coauthored"])],
            ["Standalone agent-only commits (not counted)", fmt(totals["agent_only"])],
            ["Agent-linked commits excluded (not proven yours)", fmt(excluded_agents)],
            ["Unverified name-only matches excluded", fmt(excluded_names)],
            ["Fork default-branch ancestry checks unavailable", fmt(fork_unknown)],
            ["Christo-name/email pattern matches (provisional, owned nonfork)", fmt(totals["name_only_attributed"])],
            ["Known author email aliases (count only; not published)", fmt(len(identity.emails))],
            ["New account-linked email aliases discovered", fmt(identity.linked_commit_emails)],
            ["Direct/co-authored commits also tagged with an agent", fmt(totals["agent_assisted"])],
            ["Merge commits included", fmt(totals["merges"])],
            ["Lines added across attributed commits", fmt(totals["additions"])],
            ["Lines deleted across attributed commits", fmt(totals["deletions"])],
            ["Total changed lines (added + deleted)", fmt(totals["lines_changed"])],
            ["Net line change (added − deleted)", f"{totals['net_lines']:,}"],
            ["Code-classified lines added", fmt(totals["code_additions"])],
            ["Code-classified lines deleted", fmt(totals["code_deletions"])],
            ["Text-file change entries", fmt(totals["files_changed"])],
            ["Binary-file change entries without line counts", fmt(totals["binary_changes"])],
            ["Earliest attributed commit author date (UTC)", first or "Not found"],
            ["Latest attributed commit author date (UTC)", last or "Not found"],
        ]), warning_block,
        "## Most active repositories", "",
        md_table(["Repository", "Attributed commits", "Lines changed"], [
            [link_repo(r, priv_indices), fmt(r["metrics"]["commits"]), fmt(r["metrics"]["lines_changed"])]
            for r in sorted(ok_repos, key=lambda r: r["metrics"]["commits"], reverse=True)[:12]]),
        "", "## Full-year context", "",
        "The annual table below includes every year present in the attributed Git history; "
        "it is **not limited to your GitHub contributions calendar**.", "",
        md_table(["Year", "Commits", "Added", "Deleted", "Changed"], [
            [y, fmt(d["commits"]), fmt(d["additions"]), fmt(d["deletions"]), fmt(d["lines_changed"])]
            for y, d in sorted(yearly.items(), reverse=True)]),
        "## How to interpret the totals", "",
        "1. **Attributed commits** = exact known GitHub email + Christo signal, "
        "or clearly flagged provisional Christo-name/email pattern match in repositories owned by "
        "the account that are NOT forks. "
        "Co-author trailers use the same rules. Unrelated agent metadata is excluded.",
        "2. **Total LOC changed** = sum of Git `--numstat` added + deleted text lines across every attributed commit. "
        "This includes docs, configs, lockfiles, generated text and repeated edits; it is not current codebase size or unique lines written.",
        "3. **Code-classified LOC** uses filename extensions. It is an approximation and excludes many unrecognized formats.",
        "4. **Renames** use Git rename detection; binary changes have no meaningful line count.",
        "5. **Merge diffs** are compared with their first parent. Their changes can overlap with commits on the merged branch, "
        "so cumulative changed-line counts are not unique surviving lines.",
        "6. **Forks** are included when available. Repo-level totals count the same SHA in two different repositories twice; "
        "the **unique attributed Git SHAs** and **unique LOC changed** fields deduplicate matching SHAs across repositories.",
        f"7. **Coverage scope:** {scope}",
        "8. Email aliases are discovered from GitHub-account-linked indexed commits and verified-email "
        "APIs. Case-insensitive Christo author names or emails with unknown addresses count as "
        "PROVISIONAL only in owned nonfork repositories; they cannot make an upstream fork commit yours.",
        "9. Commits on local branches never pushed to GitHub, deleted repositories, inaccessible private repositories, "
        "and contributions with no identifiable Git identity cannot be recovered as exact lifetime data.",
        "10. **Private-repository names and links** are masked in public Markdown/JSON by default. "
        "The combined totals still include scanned private repositories.",
        "11. GitHub's PR/issue/search indices and current follower/star counts are separate from Git commit history.",
        "", "**Note:** The per-year, per-month, and per-language history tables use repository/SHA occurrences; "
        "they may include duplicate Git SHAs when a repository is forked or mirrored.", "",
        "## Explore", "", docs, "",
        "Generated automatically by [GitHub Actions](../../.github/workflows/github-lifetime-audit.yml).", ""
    ]
    (REPORT_DIR / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    repo_rows = []
    for r in sorted(repositories, key=lambda x: (x["status"] != "ok", -(x.get("metrics", {}).get("commits", 0)), x["name"])):
        m = r.get("metrics", {})
        fork_ev = r.get("fork_evidence") or {}
        fork_review = ("not a fork" if not r.get("fork") else
                       (("ahead " + str(fork_ev.get("ahead_default")) +
                         ", behind " + str(fork_ev.get("behind_default"))) if
                        fork_ev.get("status") == "checked" else "unverified"))
        repo_rows.append([link_repo(r, priv_indices), "private" if r["private"] else "public",
                          "fork" if r["fork"] else ("owned" if r["owner"].casefold() == user["login"].casefold() else "collab/org"),
                          r["status"].upper(), fmt(r.get("reachable_commits", 0)) if m else "—",
                          fmt(m.get("commits", 0)) if m else "—", fmt(m.get("additions", 0)) if m else "—",
                          fmt(m.get("deletions", 0)) if m else "—",
                          fork_review,
                          fmt(r.get("excluded_name_only", 0)),
                          fmt(r.get("excluded_unverified_agent", 0))])
    (REPORT_DIR / "repositories.md").write_text("\n".join([
        "# Repositories — lifetime audit", "", docs, "", f"Updated {generated}.", "",
        "Every available repository was scanned, including forks unless configured otherwise. "
        "`Reachable` includes all authors; `Attributed` includes only your qualifying commits.", "",
        md_table(["Repository", "Visibility", "Type", "Scan", "Reachable", "Attributed", "+ lines", "− lines", "Fork default ancestry", "Name matches excluded", "AI-associated exclusions"], repo_rows),
        "", "## Failures", "",
        (f"{len(failures)} failed scans: {clean_md(failures_label)}." if failures else "No repository scan failures."),
        "", "Private names are masked unless explicitly enabled. Check workflow logs for diagnostic details.", ""
    ]), encoding="utf-8")

    (REPORT_DIR / "timeline.md").write_text("\n".join([
        "# Historical activity timeline", "", docs, "", "## Year-by-year Git history", "",
        md_table(["Year", "Commits", "Direct", "Co-authored", "Agent-only", "Agent-assisted", "Added", "Deleted", "Changed"], [
            [y, fmt(m["commits"]), fmt(m["direct"]), fmt(m["coauthored"]), fmt(m["agent_only"]),
             fmt(m["agent_assisted"]), fmt(m["additions"]), fmt(m["deletions"]), fmt(m["lines_changed"])]
            for y, m in sorted(yearly.items(), reverse=True)]), "",
        "## Repository creation history (owned repositories)", "",
        md_table(["Year", "Repos created, still accessible"], [
            [year, fmt(amount)] for year, amount in sorted(created_years.items(), reverse=True)]), "",
        "## Month-by-month Git history", "",
        md_table(["Month (UTC author date)", "Commits", "Added", "Deleted", "Changed"], [
            [y, fmt(m["commits"]), fmt(m["additions"]), fmt(m["deletions"]), fmt(m["lines_changed"])]
            for y, m in sorted(monthly.items(), reverse=True)]), "",
        "*Git commit dates are author dates; a commit's author timestamp may differ from when it was pushed or merged.*", ""
    ]), encoding="utf-8")

    (REPORT_DIR / "languages.md").write_text("\n".join([
        "# Languages and file-history classifications", "", docs, "",
        "## Historical changed lines by filename", "",
        "This classifies changed filenames using the official GitHub Linguist language "
        "definitions for filename and extension. Ambiguous classifications are kept separate. "
        "Historical blobs are not fed through Linguist's full content parser. "
        "Documentation/configuration rows are part of the overall LOC total but not the code-only subset.", "",
        md_table(["Classification", "Added", "Deleted", "Changed"], [
            [lang, fmt(m["additions"]), fmt(m["deletions"]), fmt(m["lines_changed"])]
            for lang, m in sorted(languages.items(), key=lambda x: -x[1]["lines_changed"])]),
        "", "## Current language bytes in repository default branches", "",
        "GitHub Linguist provides the current language-byte snapshot. It is **not** historic LOC and may count "
        "contributors other than you. Repositories are summed without deduplicating forks.", "",
        md_table(["GitHub language", "Current bytes"], [
            [k, fmt(v)] for k, v in current_lang.most_common()]),
        "", "Some languages and special filenames cannot be classified precisely without GitHub Linguist's full parser.", ""
    ]), encoding="utf-8")

    activity_rows = [
        ("Authored pull requests (GitHub search)", activity.get("pull_requests_opened")),
        ("Merged authored pull requests", activity.get("pull_requests_merged")),
        ("Authored issues", activity.get("issues_opened")),
        ("Closed authored issues", activity.get("issues_closed")),
        ("Distinct PRs reviewed (not number of reviews)", activity.get("distinct_prs_reviewed")),
        ("Distinct issue/PR threads commented on", activity.get("distinct_threads_participated")),
        ("Current followers", activity.get("followers_current")),
        ("Current following", activity.get("following_current")),
        ("Stars currently received by owned repos in inventory", sum(r.get("stars", 0) for r in owned)),
        ("Forks currently received by owned repos in inventory", sum(r.get("forks", 0) for r in owned)),
    ]
    (REPORT_DIR / "activity.md").write_text("\n".join([
        "# GitHub platform activity", "", docs, "",
        "These metrics come from GitHub's searchable issue/PR index and current repository/user metadata, "
        "not `git log`. Searches may have indexing gaps; they are not a complete historical event log.", "",
        md_table(["Metric", "Count"], [[k, fmt(v) if isinstance(v, int) else "Unavailable"] for k, v in activity_rows]),
        "", "## Issues and PRs opened by year", "",
        md_table(["Year created", "Opened PRs", "Opened issues"], [
            [year, fmt(x["pull_requests_opened"]) if x["pull_requests_opened"] is not None else "Unavailable",
             fmt(x["issues_opened"]) if x["issues_opened"] is not None else "Unavailable"]
            for year, x in sorted(activity["years"].items(), reverse=True)]),
        "", "*Historical star/follow/unfollow events, deleted discussions, and activity in inaccessible repositories "
        "cannot be reconstructed exactly from GitHub's current APIs.*", ""
    ]), encoding="utf-8")

    # Redact all private repo metadata from tracked JSON by default.
    safe_repos = []
    for r in repositories:
        allowed = not r["private"] or SHOW_PRIVATE_NAMES
        result = {"name": repo_label(r, priv_indices), "private": bool(r["private"]),
                  "fork": bool(r["fork"]), "status": r["status"],
                  "metrics": r.get("metrics"), "reachable_commits": r.get("reachable_commits"),
                  "excluded_name_only": r.get("excluded_name_only", 0),
                  "excluded_unverified_agent": r.get("excluded_unverified_agent", 0),
                  "fork_evidence": ({k: v for k, v in r.get("fork_evidence", {}).items()
                                      if k != "parent"} if r.get("private") and not SHOW_PRIVATE_NAMES
                                    else r.get("fork_evidence")),
                  "first_commit": r.get("first_commit"), "last_commit": r.get("last_commit"),
                  "years": r.get("years", {}), "months": r.get("months", {}),
                  "languages": r.get("languages", {})}
        if allowed:
            result["url"] = r["html_url"]
        safe_repos.append(result)
    data = {"schema_version": 2, "run_at_utc": as_of.isoformat(),
            "account": user["login"], "coverage": "partial" if incomplete else "complete_for_enumerated_repos",
            "repositories_enumerated": len(repositories), "repositories_scanned": len(ok_repos),
            "repositories_failed": len(failures), "warnings": len(warnings),
            "name_only_attributed_commits": provisional_names,
            "unverified_name_matches_excluded": excluded_names,
            "unattributed_agent_linked_excluded": excluded_agents,
            "unavailable_fork_ancestry_checks": fork_unknown,
            "known_email_alias_count": len(identity.emails),
            "account_linked_commit_email_aliases_added": identity.linked_commit_emails,
            "summary": totals, "unique_attributed_sha_summary": global_unique_data,
            "owned_repositories_created_by_year": dict(created_years),
            "private_summary": private_total.as_dict(),
            "reachable_commits_in_repository_histories": reachable_commits,
            "years": yearly, "months": monthly, "historical_languages": languages,
            "current_language_bytes": dict(current_lang), "platform_activity": activity,
            "repositories": safe_repos}
    (REPORT_DIR / "audit.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (REPORT_DIR / "STATUS.txt").write_text(("PARTIAL" if incomplete else "COMPLETE") + "\n", encoding="utf-8")
    update_readme(generated, incomplete)
    log(f"Generated audit: {fmt(total.commits)} attributed commits, {fmt(total.additions)} added, "
        f"{fmt(total.deletions)} deleted, {len(ok_repos)}/{len(repositories)} repositories scanned. "
        f"Status: {'PARTIAL' if incomplete else 'COMPLETE'}")
    if failures:
        log("Failed repository scans: " + ", ".join(repo_label(r, priv_indices) for r in failures[:12]))
    for item in warnings[:12]:
        log("WARNING: " + item)


def update_readme(generated: str, incomplete: bool):
    # The premium README is managed by render_profile_dashboard.py, which runs
    # after all audit reports. Preserve the editorial layout and do not append
    # the old audit block. Legacy profile repositories retain old behavior.
    if README.exists() and "<!-- PREMIUM_PROFILE_DASHBOARD -->" in README.read_text(encoding="utf-8"):
        return
    opening = "<!-- LIFETIME_GITHUB_AUDIT_START -->"
    closing = "<!-- LIFETIME_GITHUB_AUDIT_END -->"
    block = (f"{opening}\n\n### Lifetime GitHub audit\n\n"
             f"[**View complete engineering activity →**](./docs/github-audit/REPORT.md)  \n"
             f"Commits · AI-agent contributions · cumulative LOC · languages · repositories · historical timeline.  \n"
             f"<sub>Updated {generated} · {'Partial coverage — see audit notes' if incomplete else 'Verified accessible-repository scan'}</sub>\n\n"
             f"{closing}")
    if not README.exists():
        raise RuntimeError(f"README does not exist: {README}")
    original = README.read_text(encoding="utf-8")
    if opening in original and closing in original:
        start = original.index(opening)
        end = original.index(closing, start) + len(closing)
        updated = original[:start] + block + original[end:]
    else:
        anchor = "\n<br/>\n\n### Beyond the code"
        if anchor in original:
            updated = original.replace(anchor, "\n\n" + block + "\n" + anchor, 1)
        else:
            updated = original.rstrip() + "\n\n" + block + "\n"
    if updated != original:
        README.write_text(updated, encoding="utf-8")


def main() -> int:
    if shutil.which("git") is None:
        raise RuntimeError("Git executable not installed")
    if not 1 <= MAX_WORKERS <= 12:
        raise RuntimeError("AUDIT_WORKERS must be between 1 and 12")
    if CLONE_TIMEOUT < 30 or LOG_TIMEOUT < 30 or DISCOVERY_MAX_QUERIES < 5:
        raise RuntimeError("Audit timeout/query-limit settings must be positive and realistic")
    from concurrent.futures import ThreadPoolExecutor, as_completed
    as_of = now_utc()
    if LINGUIST_INDEX is None:
        raise RuntimeError("Official GitHub Linguist language registry missing. Run build_linguist_index.py first.")
    api = GitHubAPI(TOKEN)
    me = api.request("/user")
    username = me.get("login", "")
    if username.casefold() != USER_EXPECTED.casefold():
        raise RuntimeError(f"Token belongs to @{username}, expected @{USER_EXPECTED}. Refusing to mix accounts.")
    emails_response = api.request("/user/emails", optional=True)
    emails = [x["email"] for x in (emails_response or []) if x.get("verified") and x.get("email")]
    identity = Identity(username, me, emails)
    log(f"Auditing @{username}. Identity aliases: {len(identity.emails)} emails, "
        f"{len(identity.names)} names (values intentionally hidden).")
    all_repos: dict[str, dict] = {}
    for repo in api.pages("/user/repos", {"visibility": "all", "affiliation": "owner,collaborator,organization_member"}):
        if repo.get("full_name") and (INCLUDE_FORKS or not repo.get("fork")):
            all_repos[repo["full_name"].casefold()] = repo
    log(f"Account-authorized repositories: {len(all_repos)}")
    warnings: list[str] = []
    if GLOBAL_DISCOVERY:
        external, issues, discovered_emails = discover_global_authored_repos(api, username, as_of.date())
        warnings.extend(issues)
        added = identity.add_account_linked_commit_emails(discovered_emails)
        log(f"Account-linked author email aliases discovered: {added} new; "
            f"{len(identity.emails)} known total (values kept private).")
        extras = sorted(set(external) - set(all_repos))
        for full_lower in extras:
            candidate = external[full_lower]
            if not INCLUDE_FORKS and candidate.get("fork"):
                continue
            # Search payload normally contains full repo metadata; refresh to guard absent fields.
            try:
                full = candidate["full_name"]
                all_repos[full_lower] = api.request("/repos/" + urllib.parse.quote(full, safe="/"))
            except APIError as exc:
                warnings.append("Unable to fetch a discovered external repository: " + str(exc))
        log(f"After global authored-commit discovery: {len(all_repos)} repositories")
    if (not emails_response and not me.get("email") and not identity.linked_commit_emails
            and not split_aliases(os.getenv("AUDIT_EMAILS", ""))):
        warnings.append("Verified account emails and indexed account-linked emails were unavailable. "
                        "Name-only matches on owned repositories are provisional; some history may be missed.")
    repos = sorted(all_repos.values(), key=lambda r: r["full_name"].casefold())
    results = []
    log(f"Starting full Git mirror scans ({MAX_WORKERS} parallel workers)")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        tasks = {executor.submit(inspect_repo, repo, identity, api): repo for repo in repos}
        for i, task in enumerate(as_completed(tasks), 1):
            result = task.result()
            results.append(result)
            label = "[private repository]" if result["private"] else result["name"]
            count = result.get("metrics", {}).get("commits", 0)
            log(f"[{i}/{len(repos)}] {label}: {result['status']}, {count} attributed commits")
    try:
        activity, activity_warnings = account_activity(api, me, as_of.date())
    except APIError as exc:
        activity = {"years": {}, "account_created_at": me.get("created_at")}
        activity_warnings = [f"GitHub activity API unavailable: {exc}"]
    warnings.extend(activity_warnings)
    bad_languages = sum(1 for r in results if r.get("language_error"))
    if bad_languages:
        warnings.append(f"Current language-byte API failed for {bad_languages} repositories")
    # Never silently report all fork histories as personally authored.
    # Fork ancestry is advisory evidence; exact author/coauthor email remains
    # the gate for every attributed commit.
    render_reports(me, results, activity, warnings, as_of, identity)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (APIError, RuntimeError) as exc:
        print("AUDIT FATAL ERROR: " + str(exc).replace(TOKEN, "[REDACTED]"), file=sys.stderr)
        sys.exit(1)