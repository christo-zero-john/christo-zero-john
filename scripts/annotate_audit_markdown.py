#!/usr/bin/env python3
"""Add native GitHub Markdown disclosure controls to every audit table row.

Each row receives a <details> cell with a context-specific definition and
an appendix anchor. No client-side JavaScript, CSS, tooltips or external assets.
"""
from __future__ import annotations
from html import escape
from pathlib import Path
import re
import os

DIR = Path(os.getenv("AUDIT_OUTPUT_DIR", "docs/github-audit"))
START = "<!-- AUDIT_EXPLAINERS_START -->"
END = "<!-- AUDIT_EXPLAINERS_END -->"

SECTIONS = {
    "identity": (
        "Authorship and confirmed Git identities",
        "A directly authored commit is counted only when its Git author email matches a verified or GitHub-account-linked email. Names alone never prove authorship. Historical email aliases can come from the authenticated account email API and commits indexed under the exact GitHub user. An unfamiliar, unlinked historical email must be reviewed separately. Emails are never published in public Markdown or JSON."),
    "coauthors": (
        "Co-authored Git commits",
        "A commit authored by someone else qualifies as co-authored by the developer only when a Co-authored-by trailer contains an exact, known developer email. The same Git SHA counts once even when several qualifying trailers occur. An unrelated agent named in a co-author trailer does not make that commit yours."),
    "agents": (
        "AI-assisted versus agent-authored commits",
        "An agent-assisted commit is a human-authored or human-coauthored commit also featuring detectable agent metadata. This is a descriptive flag, not an extra commit. An agent-only commit qualifies solely if its exact repository@40-character-SHA is deliberately approved through AUDIT_APPROVED_AGENT_COMMITS; otherwise it is excluded. Claude/Codex contribution trailers in somebody else's upstream history are not proof of ownership. AI-written code without identifiable Git metadata cannot be measured exactly."),
    "forks": (
        "Forked repositories and upstream ancestry",
        "A fork includes inherited upstream history. Mere possession of a fork does not transfer author credit. Each commit must still pass exact identity matching or explicit agent-SHA approval. The audit separately checks a fork default branch against its parent using GitHub's compare API. Ahead 0 means no fork-only commits on that default branch versus the upstream comparison; other branches can diverge. Behind measures upstream commits absent from the fork. An unavailable ancestry check is disclosed and does not authorize inherited history."),
    "counts": (
        "Commit counting and deduplication",
        "One Git SHA counts once per repository across all reachable branches and tags. Repository/SHA occurrences may count the same original commit again in another fork or mirror. Account-wide unique Git SHA totals deduplicate that overlap. Git commits made by other authors remain in the reachable-history inventory but are never counted as this developer's attributed contributions."),
    "loc": (
        "Historical lines of code and cumulative changes",
        "Git --numstat reports added and deleted text lines within every included commit. Changed lines equals additions plus deletions. This is historical churn, not the current size of a project or a number of original lines authored by a human. Repeated edits, code moved between files, merges, imports and generated content can increase the total. Binary changes do not have numeric line counts. Merge diffs are compared to their first parent and may duplicate earlier changes."),
    "languages": (
        "GitHub Linguist and language classifications",
        "The current-language byte snapshot is returned by GitHub's /repos/{owner}/{repo}/languages endpoint, which uses GitHub Linguist for the current default branch. Historical changed-line classifications use the official GitHub Linguist filename/extension registry, not every historical blob's content-level parser. Ambiguous paths are explicitly unclassified rather than guessed. File extensions do not prove skill or human authorship; GitHub Linguist data can also include upstream authors."),
    "code": (
        "Strict code-classified lines versus all text",
        "All-text LOC includes prose, configuration, data files, generated code and lockfiles. Strict code-classified LOC uses Linguist programming/markup filename types and excludes recognizable vendored, generated and distribution paths. Ambiguous and unknown files are excluded from the strict code subset. This is conservative filename classification; complete historical parser-level classification and file-level authorship cannot be inferred from paths alone."),
    "timelines": (
        "Dates, monthly activity and yearly activity",
        "Historical Git activity is bucketed by commit author timestamp in UTC, not by push date. History can be imported, rewritten or dated differently from when work was performed. Monthly and yearly tables use repository/SHA occurrences, so duplicated fork history can appear in the per-period series; the all-account unique SHA total is separate."),
    "platform": (
        "GitHub social, PR and issue activity",
        "PR, issue, reviewer and commenter counts come from GitHub's indexed Search APIs. They are neither Git commits nor a complete historical event archive. Review counts typically refer to distinct PRs, not individual review comments. Followers, stars and forks are current snapshots and can change."),
    "coverage": (
        "Coverage, accuracy, and excluded evidence",
        "COMPLETE means no known errors for enumerated accessible repositories and search sources; it does not mean all deleted, local-only, unpushed or inaccessible work was reconstructed. PARTIAL indicates scan, API, GitHub index or ancestry gaps. Unverified name-only matches and unexplained agent-only commits are excluded, not included optimistically. Errors and exclusions are summarized so published totals are not misrepresented as unquestionable lifetime truth."),
    "portfolio": (
        "Repository ownership, visibility and project summaries",
        "Owned, forked, archived and collaborator repositories are different relationships. Repository ownership does not establish who wrote inherited Git history. Public project descriptions, topics and dependency manifests are a current snapshot and do not verify production deployments, business results, work hours or depth of proficiency. Private repo titles and URLs are masked by default."),
    "privacy": (
        "Private-data and account-identity protection",
        "Access tokens and author email addresses are never placed into the public reports. Private repositories contribute to aggregate statistics, but their names, links and descriptions are anonymized by default. GitHub Actions logs must be kept free from token contents. Aggregate private statistics may still reveal sensitive scale and should be reviewed before sharing."),
}


def classify(label, headers):
    x = (label + " " + " ".join(headers)).casefold()
    if any(y in x for y in ("fork", "ahead", "behind", "upstream")):
        return "forks"
    if any(y in x for y in ("co-author", "coauthored", "co authored")):
        return "coauthors"
    if any(y in x for y in ("agent", "claude", "codex", "ai-assisted")):
        return "agents"
    if any(y in x for y in ("authored", "email", "alias", "name-only", "name matches")):
        return "identity"
    if any(y in x for y in ("code-classified", "code loc", "code lines")):
        return "code"
    if any(y in x for y in ("language", "classification", "typescript", "python", "javascript", "sql", "byte")):
        return "languages"
    if any(y in x for y in ("added", "deleted", "changed", "line", "numstat")):
        return "loc"
    if any(y in x for y in ("year", "month", "date", "peak", "earliest", "latest")):
        return "timelines"
    if any(y in x for y in ("pull request", "issue", "comment", "review", "follower", "star", "merged pr")):
        return "platform"
    if any(y in x for y in ("partial", "scan", "failed", "coverage", "warning", "excluded", "enumerated")):
        return "coverage"
    if any(y in x for y in ("repository", "project", "public", "private", "visible", "type")):
        return "portfolio"
    return "counts"


def split_cells(line):
    return re.split(r"(?<!\\)\|", line.strip())


def annotate_table(lines):
    output = []
    inside = False
    headers = []
    already = False
    for line in lines:
        if not line.startswith("| ") or not line.rstrip().endswith("|"):
            output.append(line)
            inside = False
            continue
        cells = split_cells(line)
        if len(cells) < 4:
            output.append(line)
            inside = False
            continue
        values = [cell.strip() for cell in cells[1:-1]]
        if not inside:
            headers = values
            already = any("Details" in h for h in headers)
            output.append(line if already else line.rstrip()[:-1] + " ℹ Details |")
            inside = True
            continue
        if all(re.fullmatch(r":?-{3,}:?", v) for v in values):
            output.append(line if already else line.rstrip()[:-1] + " --- |")
            continue
        if already:
            output.append(line)
            continue
        key = classify(values[0], headers)
        heading, description = SECTIONS[key]
        help_text = escape(description[:260], quote=True)
        detail = ("<details><summary>ℹ Explain</summary>"
                  f"<p>{help_text} "
                  f'<a href="./APPENDIX.md#{key}">Full appendix: {escape(heading)}</a></p>'
                  "</details>")
        output.append(line.rstrip()[:-1] + " " + detail + " |")
    return output


def appendix():
    lines = ["# GitHub engineering audit — metric and methodology appendix", "",
             "This is the reference for every expandable Info cell in the generated audit tables. "
             "The definitions distinguish evidence-based contributions from work that was merely present in a fork.",
             ""]
    for key, (title, explanation) in SECTIONS.items():
        lines.extend([f'<a id="{key}"></a>', f"## {title}", "", explanation, ""])
    lines.extend(["## Data-source hierarchy", "",
                  "1. **Verified authored/co-authored work:** exact Git email identity plus attributed commit histories.",
                  "2. **Approved agent-only work:** individually authorized repository/SHA pairs; never an upstream coauthor alone.",
                  "3. **GitHub Linguist:** current language bytes and official filename metadata, not a claim of full historical per-blob parsing.",
                  "4. **Repository/PR metadata:** live snapshots and indexed search, not human skill verification.",
                  "5. **Self-reported biodata:** work history, education and preferred tools remain separate from audit metrics.",
                  ""])
    return "\n".join(lines)


def main():
    if not DIR.is_dir():
        raise SystemExit("Audit report directory missing.")
    (DIR / "APPENDIX.md").write_text(appendix(), encoding="utf-8")
    changed = 0
    for path in DIR.glob("*.md"):
        if path.name in ("APPENDIX.md", "INSTALL.md"):
            continue
        content = path.read_text(encoding="utf-8")
        if START in content:
            content = content.split(START, 1)[0].rstrip() + "\n"
        updated = "\n".join(annotate_table(content.splitlines()))
        updated += ("\n\n" + START + "\n\n## Appendix: what these numbers actually mean\n\n"
                    "Expand the **ℹ Explain** control on any row for its definition and a direct "
                    "[appendix section](./APPENDIX.md). The full methodology explains "
                    "verified identities, fork ancestry, agents, GitHub Linguist, "
                    "generated code, LOC, privacy and coverage.\n\n"
                    "[Read the complete methodology appendix](./APPENDIX.md)\n\n" +
                    END + "\n")
        path.write_text(updated, encoding="utf-8")
        changed += 1
    print("Annotated tables with expandable details and appendix:", changed, "Markdown reports.")


if __name__ == "__main__":
    main()
