# Engineering audit — methodology and metric appendix

This page explains how the strict lifetime audit attributes Git history. **Previous totals were withdrawn** because third-party agent coauthors in inherited forks were incorrectly treated as personal commits. The GitHub Actions workflow will regenerate this appendix with expandable table links after its first corrected run.

<a id="identity"></a>
## Authorship and confirmed Git identities

**Directly authored** means the Git author email exactly matches an authenticated, account-linked or explicitly user-supplied email. The developer's author name alone does **not** prove identity. Old GitHub Desktop installations and GitHub no-reply addresses can be discovered from verified account emails and GitHub-account-linked commits. Raw email addresses are not published in the public audit.

<a id="coauthors"></a>
## Co-authored commits

A commit authored by another person counts only if a `Co-authored-by` trailer contains a confirmed developer email. A single commit is counted once, regardless of the number of matched trailers.

<a id="agents"></a>
## Agent-assisted versus agent-only

**Agent-assisted** is a flag on a qualifying human-authored or co-authored commit that includes AI-agent attribution. It does not add another commit. **Agent-only commits** qualify only if their exact repository name and SHA have been explicitly approved with the `AUDIT_APPROVED_AGENT_COMMITS` secret. An agent coauthor on somebody else's upstream commit never establishes developer ownership.

<a id="forks"></a>
## Forks, upstream and ancestry

A fork inherits the full upstream repository history. None of that history automatically belongs to the person who forked it. The audit checks fork parent and compares default branches; `ahead 0` means no branch-only additions to the fork's default branch relative to upstream, while `behind` is the number of upstream commits missing from the fork. Other branches are also scanned, but every included Git SHA must still pass exact author/coauthor identity or deliberate agent approval.

<a id="counts"></a>
## Commit counts and unique SHAs

A Git SHA is counted once per repository even if it is reachable via multiple branches and tags. The same SHA in multiple forks can inflate repository-level totals; account-wide unique SHA totals deduplicate it. Repository histories include unrelated authors as context, not personal contributions.

<a id="loc"></a>
## Cumulative lines of code

`git --numstat` measures line additions and deletions in qualifying commits. `Changed LOC = additions + deletions`. It measures historical edit volume, **not unique human-written code**, surviving project size or hours worked. The all-text total includes code, documentation, configuration, lockfiles and generated data. Binary files have no numeric line counts. Merges compared with their first parent can overlap previously counted changes.

<a id="code"></a>
## Code-classified versus all-text LOC

Strict code classification includes recognized programming/markup source paths and excludes recognizable generated, vendored, distribution and lockfile paths. Historical ambiguous or unknown language paths are separated rather than forced into a programming language. Raw all-text change totals remain independently available.

<a id="languages"></a>
## Linguist and language detection

**Current language bytes:** GitHub's `/languages` endpoint uses GitHub Linguist on each repository's default-branch snapshot and can include other people's files. **Historical changed lines:** files are classified with GitHub Linguist's official filename and extension registry. This cannot reproduce content-level heuristics, shebangs or per-commit historical `.gitattributes` rules without inspecting each historical blob.

<a id="timelines"></a>
## Yearly and monthly activity

Author dates are grouped in UTC and may differ from GitHub push, merge and contribution graph dates. Period tables use repository/SHA occurrences, which can include duplicate Git SHAs in forks.

<a id="platform"></a>
## PRs, issues, code reviews and popularity

GitHub PR/issue count queries use GitHub's search indexes. They are separate from Git histories and may be incomplete. Stars, forks and followers represent current values, not lifetime event totals.

<a id="coverage"></a>
## Coverage, excluded evidence, and warnings

`COMPLETE` only means no known gaps among scanned accessible repositories and queried sources; deleted, unpushed, inaccessible and unidentified histories cannot be recovered. `PARTIAL` means one or more scan, search, identity or fork-ancestry checks are incomplete. Unverified name-only matches and unapproved agent-only commits are excluded, even if they appear in owned repositories.

<a id="portfolio"></a>
## Project identity

Owned repositories, forks, and organizational collaborations are distinct categories. Project titles, descriptions and dependency manifests do not prove who authored commits or whether a product was launched.

<a id="privacy"></a>
## Private and sensitive data

Private repositories contribute to aggregate statistics, but their identifiers are masked in public Markdown and JSON by default. GitHub tokens and private author-email lists never belong in public reports.

---

[Return to main audit](./REPORT.md)
