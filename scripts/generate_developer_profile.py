#!/usr/bin/env python3
"""Enrich the historical Git audit with an evidence-aware developer biodata.

Reads the privacy-safe audit.json and editable developer-bio.json, then inspects
public repositories' current GitHub metadata/manifests. No personal emails,
private repository identities or authentication credentials are published.
"""
from __future__ import annotations

import base64
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime as dt
import html
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = Path(os.environ.get("AUDIT_OUTPUT_DIR", "docs/github-audit"))
TOKEN = os.getenv("AUDIT_TOKEN", "")
API = os.getenv("GITHUB_API_URL", "https://api.github.com").rstrip("/")
NAV = "[Audit](./REPORT.md) · [Biodata](./PROFILE.md) · [Stack](./TECH_STACK.md) · [Projects](./PROJECTS.md) · [Insights](./INSIGHTS.md) · [History](./timeline.md) · [Activity](./activity.md)"

PACKAGE_NAMES = {
    "next": "Next.js", "react": "React", "react-dom": "React",
    "@supabase/supabase-js": "Supabase", "@supabase/ssr": "Supabase",
    "tailwindcss": "Tailwind CSS", "@tailwindcss/vite": "Tailwind CSS",
    "prisma": "Prisma", "@prisma/client": "Prisma",
    "drizzle-orm": "Drizzle ORM", "drizzle-kit": "Drizzle ORM",
    "vite": "Vite", "@vitejs/plugin-react": "Vite",
    "remotion": "Remotion", "@remotion/cli": "Remotion",
    "@playwright/test": "Playwright", "playwright": "Playwright",
    "express": "Express", "fastify": "Fastify", "hono": "Hono",
    "vue": "Vue", "nuxt": "Nuxt", "svelte": "Svelte", "@sveltejs/kit": "SvelteKit",
    "astro": "Astro", "gatsby": "Gatsby",
    "firebase": "Firebase", "firebase-admin": "Firebase",
    "openai": "OpenAI SDK", "@anthropic-ai/sdk": "Anthropic SDK",
    "langchain": "LangChain", "@langchain/core": "LangChain",
    "three": "Three.js", "@react-three/fiber": "React Three Fiber",
    "vitest": "Vitest", "jest": "Jest", "typescript": "TypeScript",
    "turbo": "Turborepo", "electron": "Electron",
    "stripe": "Stripe", "zod": "Zod", "lucide-react": "Lucide",
}
PYTHON_PACKAGES = {
    "django": "Django", "djangorestframework": "Django REST Framework",
    "fastapi": "FastAPI", "flask": "Flask", "starlette": "Starlette",
    "streamlit": "Streamlit", "sqlalchemy": "SQLAlchemy",
    "supabase": "Supabase", "openai": "OpenAI SDK",
    "anthropic": "Anthropic SDK", "langchain": "LangChain",
    "langgraph": "LangGraph", "playwright": "Playwright",
    "celery": "Celery", "pandas": "Pandas", "numpy": "NumPy",
    "pydantic": "Pydantic", "pytest": "Pytest", "torch": "PyTorch",
    "tensorflow": "TensorFlow", "scikit-learn": "scikit-learn",
}
MANIFESTS = {"package.json", "pyproject.toml", "requirements.txt", "Pipfile", "go.mod", "Cargo.toml"}
MAX_MANIFESTS = 14


def safe(value, limit=240):
    value = re.sub(r"[\r\n\t]+", " ", str(value or "")).strip()
    value = value[:limit]
    value = value.replace("|", "&#124;").replace("<", "&lt;").replace(">", "&gt;")
    return value or "—"


def code(value):
    return chr(96) + safe(value, 120).replace(chr(96), "'") + chr(96)


def num(value):
    return f"{int(value or 0):,}"


def md_table(headers, rows):
    if not rows:
        return "_No records available._"
    return "\n".join(["| " + " | ".join(headers) + " |",
                      "| " + " | ".join("---" for _ in headers) + " |"] +
                     ["| " + " | ".join(safe(v, 700) for v in row) + " |" for row in rows])


def api_get(url, optional=True):
    if not TOKEN:
        return None
    req = urllib.request.Request(API + url, headers={
        "Authorization": "Bearer " + TOKEN,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "lifetime-developer-biodata/1.0",
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=35) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 422):
                return None
            if exc.code in (403, 429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(min(20, 2 ** (attempt + 1)))
                continue
            if optional:
                return None
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 3:
                return None
            time.sleep(2 ** attempt)
    return None


def get_repo_file(full, path, branch):
    endpoint = "/repos/{}/contents/{}?ref={}".format(
        urllib.parse.quote(full, safe="/"),
        urllib.parse.quote(path, safe="/"),
        urllib.parse.quote(branch, safe=""))
    obj = api_get(endpoint)
    if not isinstance(obj, dict) or obj.get("encoding") != "base64":
        return None
    try:
        return base64.b64decode(obj.get("content", "")).decode("utf-8", "replace")
    except (ValueError, TypeError):
        return None


def infer_from_manifest(path, content):
    tags = set()
    name = path.rsplit("/", 1)[-1]
    if name == "package.json":
        try:
            p = json.loads(content)
            deps = dict(p.get("dependencies") or {})
            deps.update(p.get("devDependencies") or {})
            for dep in deps:
                if dep.casefold() in PACKAGE_NAMES:
                    tags.add(PACKAGE_NAMES[dep.casefold()])
        except (ValueError, TypeError, AttributeError):
            return tags
    if name in ("requirements.txt", "pyproject.toml", "Pipfile"):
        low = content.casefold()
        for package, tag in PYTHON_PACKAGES.items():
            # Matches requirements and TOML/Pipfile identifiers; not proof of active usage.
            if re.search(r"(?<![a-z0-9_-])" + re.escape(package) +
                         r"(?![a-z0-9_-])", low):
                tags.add(tag)
    if name == "Cargo.toml":
        tags.add("Rust / Cargo")
    if name == "go.mod":
        tags.add("Go modules")
    return tags


def inspect_public_repo(repo):
    full = repo["name"]
    obj = api_get("/repos/" + urllib.parse.quote(full, safe="/")) or {}
    record = {
        "name": full, "private": False, "description": obj.get("description") or "",
        "homepage": obj.get("homepage") or "",
        "topics": obj.get("topics") or [],
        "stars": obj.get("stargazers_count", 0),
        "forks": obj.get("forks_count", 0), "archived": obj.get("archived", False),
        "created_at": obj.get("created_at") or "",
        "pushed_at": obj.get("pushed_at") or "",
        "default_branch": obj.get("default_branch") or "main",
        "manifest_tags": [], "evidence": {}, "inspection": "not_inspected",
    }
    if not obj:
        return record
    ref = urllib.parse.quote(record["default_branch"], safe="")
    tree = api_get("/repos/{}/git/trees/{}?recursive=1".format(
        urllib.parse.quote(full, safe="/"), ref))
    if not isinstance(tree, dict) or "tree" not in tree:
        record["inspection"] = "metadata_only"
        return record
    record["inspection"] = "tree_truncated" if tree.get("truncated") else "inspected"
    paths = [entry.get("path", "") for entry in tree["tree"]
             if entry.get("type") == "blob" and entry.get("path")]
    paths = [p for p in paths if not any(part in (
        "node_modules", ".next", "dist", "vendor", "build", ".git") for part in p.split("/"))]
    tags = defaultdict(set)
    for path in paths:
        parts = path.split("/")
        name = parts[-1].casefold()
        if name == "dockerfile" or name.startswith("docker-compose") or name == "compose.yml":
            tags["Docker"].add(path)
        if len(parts) >= 2 and parts[0] == ".github" and parts[1] == "workflows":
            tags["GitHub Actions"].add(path)
        if path == "supabase/config.toml" or path.startswith("supabase/migrations/"):
            tags["Supabase"].add(path)
        if name == "claude.md":
            tags["Claude Code instructions"].add(path)
        if name == "agents.md":
            tags["Agent instructions"].add(path)
        if name == "vercel.json":
            tags["Vercel configuration"].add(path)
        if name == "firebase.json":
            tags["Firebase"].add(path)
    manifest_paths = [p for p in paths if p.split("/")[-1] in MANIFESTS and len(p.split("/")) <= 5]
    manifest_paths.sort(key=lambda p: (p.count("/"), p))
    for path in manifest_paths[:MAX_MANIFESTS]:
        content = get_repo_file(full, path, record["default_branch"])
        if not content or len(content) > 200000:
            continue
        for tag in infer_from_manifest(path, content):
            tags[tag].add(path)
    record["manifest_tags"] = sorted(tags)
    record["evidence"] = {tag: sorted(paths)[0] for tag, paths in tags.items()}
    return record


def render(data, bio, public_meta, errors):
    BASE.mkdir(parents=True, exist_ok=True)
    account = safe(bio.get("name") or data.get("account"))
    role = safe(bio.get("role") or "Software developer")
    account_id = safe(data.get("account"))
    summary = data.get("summary") or {}
    unique = data.get("unique_attributed_sha_summary") or {}
    repos = data.get("repositories") or []
    years = data.get("years") or {}
    months = data.get("months") or {}
    languages = data.get("historical_languages") or {}
    current = data.get("current_language_bytes") or {}
    activity = data.get("platform_activity") or {}
    generated = safe(data.get("run_at_utc"))
    coverage = safe(data.get("coverage"))
    known_public = [r for r in repos if not r.get("private")]
    known_private = [r for r in repos if r.get("private")]
    current_largest = sorted(current.items(), key=lambda x: -x[1])
    historical_largest = sorted(languages.items(), key=lambda x: -(x[1].get("code_lines_changed", 0)))
    public_repos = [r for r in known_public if r.get("url")]
    repo_by_name = {r["name"]: r for r in repos}
    counters = Counter()
    evidence = defaultdict(list)
    for name, meta in public_meta.items():
        for tag in meta["manifest_tags"]:
            counters[tag] += 1
            evidence[tag].append((name, meta["evidence"].get(tag, "")))

    def link_repo(repo):
        name = repo.get("name", "")
        url = repo.get("url", "")
        if not repo.get("private") and url.startswith("https://github.com/"):
            return "[{}]({})".format(safe(name, 110), url)
        return safe(name, 110)

    def write(name, blocks):
        (BASE / name).write_text("\n\n".join(str(b) for b in blocks if b is not None) + "\n", encoding="utf-8")

    primary = bio.get("primary_stack") or []
    extras = bio.get("other_stack") or []
    profile = [
        "# {} — Developer biodata".format(account), NAV,
        "**{}** · [GitHub](https://github.com/{}) · [Portfolio]({}) · [LinkedIn]({})".format(
            role, account_id, bio.get("portfolio", ""), bio.get("linkedin", "")),
        "> " + safe(bio.get("headline"), 400),
        "## Professional summary",
        safe(bio.get("about"), 650),
        "**Source of biography:** Editable, self-reported public professional profile; not verified by the GitHub commit scanner.",
        "## Engineering footprint (audited)",
        md_table(["Measurement", "Result"], [
            ["Repositories successfully scanned", num(data.get("repositories_scanned"))],
            ["Public / private repositories in scan", "{} / {}".format(len(known_public), len(known_private))],
            ["Unique attributed Git commits (cross-repository SHA deduplicated)", num(unique.get("commits"))],
            ["Attributed commits per repository/SHA", num(summary.get("commits"))],
            ["Directly authored commits", num(summary.get("direct"))],
            ["Co-authored commits", num(summary.get("coauthored"))],
            ["Agent-only attributed commits", num(summary.get("agent_only"))],
            ["Direct/co-authored commits tagged with an agent", num(summary.get("agent_assisted"))],
            ["Total changed text lines (unique attributed commits)", num(unique.get("lines_changed"))],
            ["Code-classified changed lines (unique attributed commits)", num(unique.get("code_lines_changed"))],
            ["Public/private scan coverage", coverage]
        ]),
        "The LOC figures are cumulative additions plus deletions across attributed Git history, not the current codebase size, not unique original code and not confirmed human-written lines.",
        "## Primary engineering stack (self-reported)",
        ", ".join(code(s) for s in primary) or "Not supplied.",
        "## Additional technologies (self-reported)",
        ", ".join(code(s) for s in extras) or "Not supplied.",
        "## Specializations",
        "\n".join("- " + safe(x) for x in bio.get("specializations", [])),
        "## Education (self-reported)",
        md_table(["Qualification", "Dates", "Status"], [
            [s.get("qualification"), s.get("period"), s.get("status")] for s in bio.get("education", [])]),
        "## Professional experience (self-reported)",
        md_table(["Area / role", "Organization", "When"], [
            [x.get("role"), x.get("organization"), x.get("status")] for x in bio.get("experience", [])]),
        "## GitHub trajectory",
        md_table(["Year", "Attributed commits", "Agent-only", "Code lines changed", "All text lines changed"], [
            [year, num(m.get("commits")), num(m.get("agent_only")), num(m.get("code_lines_changed")), num(m.get("lines_changed"))]
            for year, m in sorted(years.items(), reverse=True)]),
        "## Core languages measured in historical work",
        md_table(["Language", "Code lines changed", "Added", "Deleted"], [
            [label, num(m.get("code_lines_changed")), num(m.get("code_additions")), num(m.get("code_deletions"))]
            for label, m in historical_largest if m.get("code_lines_changed", 0) > 0][:15]),
        "## Selected open-source / public portfolio",
        md_table(["Repository", "Attributed commits", "Code lines changed", "About"], [
            [link_repo(repo_by_name[p]), num(repo_by_name[p].get("metrics", {}).get("commits")),
             num(repo_by_name[p].get("metrics", {}).get("code_lines_changed")),
             safe(public_meta.get(p, {}).get("description"), 150)]
            for p in bio.get("featured_public_repositories", []) if p in repo_by_name]),
        "## Further documentation",
        "- [Every accessible project, with public project summaries](./PROJECTS.md)\n"
        "- [Technology stack with verified manifest evidence](./TECH_STACK.md)\n"
        "- [Engineering timeline and quantitative insights](./INSIGHTS.md)\n"
        "- [Complete repository audit](./repositories.md)\n"
        "- [GitHub PR, issue and review activity](./activity.md)",
        "## Data provenance",
        "Generated from the current audit JSON, public repository GitHub metadata and manifest files, and editable professional information in developer-bio.json. "
        "Private repositories are only shown by anonymous identifiers; the file does not publish their source, metadata, or titles. "
        "This GitHub audit cannot verify offline work, employment, education or unidentified agent-written code.",
        "**Last generated:** {} · **Audit coverage:** {}".format(generated, coverage)
    ]
    write("PROFILE.md", profile)

    tag_rows = []
    for tag, count in counters.most_common():
        name, source = sorted(evidence[tag])[0]
        tag_rows.append([tag, num(count), safe(name, 90), code(source)])
    technology = [
        "# Technical stack and technology evidence", NAV,
        "## Personally stated primary stack",
        ", ".join(code(s) for s in primary),
        "**Evidence category:** Professional self-description. Figma, Codex and Claude Code cannot be reliably quantified simply from Git language statistics.",
        "## Frameworks, services and tools detected in public repositories",
        "Counts reflect evidence in current default-branch manifests and configuration files of **public repositories only**. "
        "A detected dependency is not proof of proficiency or past production usage. Monorepos or other branches may have additional technologies.",
        md_table(["Technology", "Public repos detected", "Example repository", "Evidence path"], tag_rows),
        "## Historical language activity from commits",
        "Historical statistics classify changed files by filename, including repeat edits and deletions.",
        md_table(["Classification", "Added lines", "Deleted lines", "Changed lines", "Code classified"], [
            [k, num(v.get("additions")), num(v.get("deletions")),
             num(v.get("lines_changed")), num(v.get("code_lines_changed"))]
            for k, v in sorted(languages.items(), key=lambda x: -x[1].get("lines_changed", 0))]),
        "## Current GitHub Linguist language bytes",
        "These are GitHub's current default-branch language byte counts, **not code you individually wrote**.",
        md_table(["Language", "Bytes", "Approximate MB"], [
            [k, num(v), "{:.2f}".format(v / 1_000_000)] for k, v in current_largest]),
        "## Interpretation",
        "- Private repository dependency manifests are not included in the public framework inventory, although their Git-history totals are included in the lifetime audit.\n"
        "- Build artifacts, generated code, lockfiles, vendored code, notebooks and data files may greatly increase raw line-change counts.\n"
        "- Tool detection does not imply authorship or agent execution; instruction files are listed explicitly as configuration evidence.\n"
        "- Historical language counts are inferred by extension; GitHub Linguist counts are current bytes, not historical code changes.",
        "## Scan limits",
        "{} of {} public repositories returned inspectable manifest trees; {} metadata/tree inspections unavailable or truncated.".format(
            sum(v.get("inspection") == "inspected" for v in public_meta.values()),
            len(public_repos), len(errors)),
        "**Last generated:** {}".format(generated)
    ]
    write("TECH_STACK.md", technology)

    project_rows = []
    for r in sorted(repos, key=lambda x: -int((x.get("metrics") or {}).get("commits") or 0)):
        m = r.get("metrics") or {}
        meta = public_meta.get(r["name"], {})
        privacy = "Private (anonymized)" if r.get("private") else "Public"
        desc = safe(meta.get("description"), 165) if not r.get("private") else "Description withheld"
        tags = ", ".join(meta.get("manifest_tags", [])[:6]) if not r.get("private") else "Not disclosed"
        project_rows.append([link_repo(r), privacy, desc,
            num(m.get("commits")), num(m.get("code_lines_changed")),
            num(m.get("lines_changed")), tags or "Not detected"])
    projects = [
        "# Complete accessible repository portfolio", NAV,
        "**{} repositories** from the latest accessible inventory, including **{} private** (names masked). "
        "These are repositories, not necessarily independently launched commercial products.".format(len(repos),len(known_private)),
        "## Project inventory, contributions and detected technologies",
        "Ordered by attributed commit count; LOC represents Git changes, not current source size. "
        "Descriptions and framework tags are fetched **only for public repos** from current GitHub metadata/manifest files.",
        md_table(["Repository", "Visibility", "Public description", "Attributed commits", "Code LOC changed", "Text LOC changed", "Detected tags"], project_rows),
        "## Public project metadata",
        md_table(["Public repository", "Stars", "Forks", "Created", "Last pushed", "Topics"], [
            [link_repo(r), num(public_meta.get(r["name"], {}).get("stars")),
             num(public_meta.get(r["name"], {}).get("forks")),
             (public_meta.get(r["name"], {}).get("created_at") or "—")[:10],
             (public_meta.get(r["name"], {}).get("pushed_at") or "—")[:10],
             ", ".join(public_meta.get(r["name"], {}).get("topics", [])[:8]) or "—"]
            for r in public_repos]),
        "## Notes",
        "Public metadata is a current snapshot; private names and project descriptions are not disclosed. "
        "Forked projects can contain history predating your fork; only qualifying attributed commits are counted. "
        "No claim of product launch, revenue, team size or users is inferred from a repository name.",
        "**Last generated:** {}".format(generated)
    ]
    write("PROJECTS.md", projects)

    monthly = sorted(months.items())
    peak_month = max(monthly, key=lambda x: x[1].get("commits", 0)) if monthly else None
    peak_churn = max(monthly, key=lambda x: x[1].get("lines_changed", 0)) if monthly else None
    owned_count = data.get("repositories_enumerated", 0)
    monthly_rows = [[month, num(m.get("commits")), num(m.get("direct")), num(m.get("coauthored")),
                     num(m.get("agent_only")), num(m.get("agent_assisted")),
                     num(m.get("lines_changed"))] for month, m in reversed(monthly)]
    insights = [
        "# Developer activity and engineering insights", NAV,
        "## Account and collaboration",
        md_table(["Metric", "Value"], [
            ["Repositories enumerated", num(owned_count)],
            ["Scanned successfully", num(data.get("repositories_scanned"))],
            ["Private repositories scanned", num(len(known_private))],
            ["Unique attributed commits", num(unique.get("commits"))],
            ["Total attributed repo/SHA occurrences", num(summary.get("commits"))],
            ["Directly authored", num(summary.get("direct"))],
            ["Co-authored by you", num(summary.get("coauthored"))],
            ["Agent-only attributed", num(summary.get("agent_only"))],
            ["Direct/co-authored with identifiable agent", num(summary.get("agent_assisted"))],
            ["Provisional name-only attribution", num(summary.get("name_only_attributed"))],
            ["Merged authored PRs (GitHub search)", num(activity.get("pull_requests_merged")) if activity.get("pull_requests_merged") is not None else "Unavailable"],
            ["Authored PRs", num(activity.get("pull_requests_opened")) if activity.get("pull_requests_opened") is not None else "Unavailable"],
            ["Authored issues", num(activity.get("issues_opened")) if activity.get("issues_opened") is not None else "Unavailable"],
            ["Reviewed distinct PRs", num(activity.get("distinct_prs_reviewed")) if activity.get("distinct_prs_reviewed") is not None else "Unavailable"]
        ]),
        "## Quantitative historical highlights",
        md_table(["Observation", "Result"], [
            ["Months with attributed commits", num(len(monthly))],
            ["Mean commits per active month (repo/SHA occurrences)", "{:.1f}".format(summary.get("commits", 0) / len(monthly)) if monthly else "—"],
            ["Peak month by attributed commits", "{} — {} commits".format(peak_month[0], num(peak_month[1].get("commits"))) if peak_month else "—"],
            ["Peak month by cumulative changed lines", "{} — {} lines".format(peak_churn[0], num(peak_churn[1].get("lines_changed"))) if peak_churn else "—"],
            ["Current GitHub indexed coverage", coverage],
            ["API/discovery warnings from original audit", num(data.get("warnings"))]
        ]),
        "## Year-by-year development activity",
        md_table(["Year", "Commits", "Direct", "Co-authored", "Agent only", "Agent assisted", "Changed lines"], [
            [y, num(m.get("commits")), num(m.get("direct")), num(m.get("coauthored")),
             num(m.get("agent_only")), num(m.get("agent_assisted")), num(m.get("lines_changed"))]
            for y, m in sorted(years.items(), reverse=True)]),
        "## Monthly development activity",
        md_table(["Month", "Commits", "Direct", "Co-authored", "Agent only", "Agent assisted", "Changed lines"], monthly_rows),
        "## Activity interpretation",
        "These series use commit author dates and repository/SHA occurrences (fork duplicates may exist). "
        "Activity cannot be translated into hours worked, productivity, code quality, proficiency, deployment frequency or number of users. "
        "Agent attribution requires detectable Git author/co-author metadata; human-authored commits might still contain AI-generated code. "
        "Outlier months may reflect generated files, bulk imports or reformatting.",
        "**Last generated:** {}".format(generated)
    ]
    write("INSIGHTS.md", insights)

    # The historical analyzer rewrites REPORT.md on every run. Reinsert navigation
    # *after* it executes, without changing any of its numeric calculations.
    report = BASE / "REPORT.md"
    if report.exists():
        content = report.read_text(encoding="utf-8")
        opening, closing = "<!-- DEVELOPER_BIODATA_LINKS_START -->", "<!-- DEVELOPER_BIODATA_LINKS_END -->"
        insertion = "\n".join([opening, "", "## Developer biodata and portfolio",
            "For a professional overview, start with the **[developer biodata](./PROFILE.md)**. "
            "Explore the **[technology evidence](./TECH_STACK.md)**, **[complete projects](./PROJECTS.md)** "
            "and **[engineering insights](./INSIGHTS.md)**.", "",
            closing])
        if opening in content and closing in content:
            begin, end = content.index(opening), content.index(closing) + len(closing)
            content = content[:begin] + insertion + content[end:]
        else:
            heading = "## Lifetime engineering totals"
            if heading in content:
                content = content.replace(heading, insertion + "\n\n" + heading, 1)
            else:
                content = content.rstrip() + "\n\n" + insertion + "\n"
        report.write_text(content, encoding="utf-8")

    readme = Path("README.md")
    if readme.exists():
        content = readme.read_text(encoding="utf-8")
        start = "<!-- LIFETIME_GITHUB_AUDIT_START -->"
        stop = "<!-- LIFETIME_GITHUB_AUDIT_END -->"
        if start in content and stop in content:
            a, b = content.index(start), content.index(stop)
            block = content[a:b]
            extra = "[**Developer biodata & portfolio**](./docs/github-audit/PROFILE.md) · [**Tech stack evidence**](./docs/github-audit/TECH_STACK.md) · [**All projects**](./docs/github-audit/PROJECTS.md)\n\n"
            if "Developer biodata & portfolio" not in block:
                block = block.rstrip() + "\n\n" + extra
                content = content[:a] + block + content[b:]
                readme.write_text(content, encoding="utf-8")

    print("Generated developer biodata, technical evidence, complete portfolio, and engineering insights; public repo metadata reviewed:",len(public_meta), "inspection warnings:",len(errors), flush=True)


def main():
    bio_path = BASE / "developer-bio.json"
    data_path = BASE / "audit.json"
    if not bio_path.is_file() or not data_path.is_file():
        raise SystemExit("Missing developer-bio.json or audit.json; run lifetime audit first.")
    bio = json.loads(bio_path.read_text(encoding="utf-8"))
    data = json.loads(data_path.read_text(encoding="utf-8"))
    public = [r for r in data.get("repositories", []) if not r.get("private") and r.get("url")]
    meta = {}
    errors = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        jobs = {executor.submit(inspect_public_repo, r): r["name"] for r in public}
        for task in as_completed(jobs):
            try:
                record = task.result()
                meta[record["name"]] = record
                if record["inspection"] != "inspected":
                    errors.append(record["name"] + ": " + record["inspection"])
            except Exception as exc:
                errors.append(jobs[task] + ": " + type(exc).__name__)
    render(data, bio, meta, errors)


if __name__ == "__main__":
    main()
