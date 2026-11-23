# Lifetime GitHub Audit — installation, identity rules and reliability

This workflow publishes **Christo John's** GitHub engineering activity to the public profile repository `christo-zero-john/christo-zero-john`. The published metrics reflect a carefully specified attribution policy, **not** blanket ownership of all code in owned or forked repositories.

## Getting started

1. Merge the PR with the current code, and ensure the profile repository contains `.github/workflows/github-lifetime-audit.yml`, `scripts/github_lifetime_audit.py`, `scripts/render_profile_dashboard.py`, and `scripts/render_interactive_profile.py`.
2. In repository **Settings → Secrets and variables → Actions**, create the secret `GH_AUDIT_READ_TOKEN`. Use a fine-grained PAT with **Contents: Read-only**, **Metadata: Read-only**, **Email addresses: Read-only** and access to all personal repositories you wish to scan.
3. If you need to analyze private organization/collaborator repositories, expand token access as permitted by the organization. A classic PAT with `repo` may cover more repositories, but **is not read-only** and is more powerful; use a short expiration and revoke it when unnecessary.
4. In repository **Settings → Actions → General**, allow the workflow to write contents to your profile repository so it can publish README/Markdown/SVG updates.
5. Run [GitHub lifetime engineering audit](https://github.com/christo-zero-john/christo-zero-john/actions/workflows/github-lifetime-audit.yml) against `main`. It also runs weekly and after changes to audit/profile-renderer source on `main`.

No `AUDIT_EMAILS` or `AUDIT_NAMES` variable is required for normal setup.

## Current attribution policy (identity_policy_version 3)

**Two kinds of evidence, clearly separated:**

| Class | When a commit qualifies | Trust level |
| --- | --- | --- |
| Verified direct author | Git author email is an exact known GitHub-linked alias **and** author name/email local-part contains `christo` (case-insensitive), or numeric GitHub no-reply ID matches the account | Strong |
| Verified coauthor | Same rule applied to a valid `Co-authored-by` trailer | Strong |
| Old GitHub Desktop identity | Git author/coauthor name or email local-part contains `christo`, but the author email is unknown; repository is **owned by the account and NOT a fork** | **Provisional** |
| Unknown email in a fork or collaboration | Name contains `christo`, but no known account-linked email or numeric ID | **Excluded** |
| Other contributors | Neither known linked owner identity nor eligible provisional name marker | **Excluded** |
| Claude/Codex coauthor | Already qualifying owner-authored or owner-coauthored commit also credits an identifiable agent | Count **once**, with an AI-assisted flag |
| Standalone Claude/Codex commit | Owner does not appear as a qualifying author/coauthor | **Excluded** |
| Owner-authored merge | Identity qualifies, but the merge introduces lines from merged commits | Count merge **commit**, assign **0 merge LOC** |

**Why provisional?** Anybody can write `Christo` as a Git author name. It is not identity proof. Provisional counts appear separately and force `PARTIAL` coverage. The algorithm never calls those counts `verified`.

**Finding earlier emails:** The workflow reads verified email aliases available to the token, discovers the full standard/current GitHub no-reply addresses, recognizes the immutable numeric GitHub account ID even across renamed handles, and gathers author emails from commits that GitHub's search index resolves to this exact account. GitHub Desktop reinstallations and custom identities are supported through the provisional fallback **only in owned nonfork repositories**. An old custom email absent from these sources in a fork cannot be safely assigned without additional direct evidence.

## Forks and branches

- A fork **inherits upstream history**. It does not confer ownership. Upstream commits by other developers do not qualify simply because the fork is yours, or because Claude helped upstream authors.
- GitHub's fork-parent comparison records `ahead_by`/`behind_by` evidence for the default branch; it is *not* the authorship test.
- The workflow clones accessible repositories with `git clone --mirror` and traverses **all advertised refs**, with `git log --all`. This includes reachable commits on unmerged remote branches and tags—not only `main`.
- A commit on multiple branches in a repository is counted once per repository/SHA. **Unique Git SHA** totals deduplicate the same SHA across forks and mirrors.
- Deleted, inaccessible, or never-pushed branches cannot be reconstructed.

## What code-line statistics mean

For **non-merge qualifying commits**, Git's `--numstat` records text additions and deletions. Changed LOC = additions + deletions. The audit separately reports all-text changes, stricter code-classified changes, and binary-file events. A merge authored by you adds **zero extra LOC** to avoid attributing third-party merged code to you. The original qualifying commits on merged or independent branches are measured individually.

This is cumulative edit volume, **not** proof that every line was invented by you: a personally authored commit may contain pasted, generated, imported or vendored code. The strict code-only measure uses GitHub Linguist's official filename/extension definitions, conservatively excludes ambiguous/generated/vendor paths, and is not the full content-based Linguist parser. Current language-byte proportions include all authors in currently accessible default branches and are clearly labeled as such.

## Reports and publishing

The workflow regenerates `docs/github-audit/REPORT.md`, the repository/timeline/language/activity Markdown files, `APPENDIX.md`, and `audit.json`. It then updates the **marked statistics and project-card blocks** in `README.md` and all generated SVGs in `assets/`.

Before making public claims, inspect `audit.json` for `schema_version: 2` and **`identity_policy_version: 3`**, the summary of verified/provisional matches, and the `coverage` value. Existing files without the policy version are older snapshots and must be re-audited.

## Privacy (important)

The current workflow has **`AUDIT_SHOW_PRIVATE_NAMES: 'true'`** because this was explicitly selected for the profile. This means private repository names may be printed in **public Markdown and JSON**. Change to `'false'` if you do not want public disclosure. Private repo code and credentials are not published. Never paste token values into README, Markdown, script or workflow logs.

The GitHub profile itself cannot execute JavaScript. Premium links are clickable SVG image cards plus GitHub-supported `<details>` disclosures. SVG/CSS animations are progressive enhancements, may not run in all GitHub clients, and have accessible final-value static fallbacks.

## If a metric is wrong

Check the matching repository row, name-only provisional count, known-email coverage, fork status, and `excluded_unverified_agent` count. If you can identify a missing address, add it privately as `AUDIT_EMAILS` and rerun; manually supplied addresses are still subject to the Christo/numeric ID guard. Do not credit upstream/agent changes purely by repo ownership.

The workflow may show `PARTIAL` for incomplete GitHub indexing, inaccessible fork comparisons, clone failures or provisional matches. A complete scan of visible Git refs can never prove that all lifetime work across deleted/unpushed repositories was captured.

## GitHub API throttling (HTTP 403 or 429)

If the **Generate full lifetime report** step prints `GitHub API throttled (403)`,
GitHub is restricting API request frequency. This normally occurs during global
author-linked commit discovery (`/search/commits`), **after the repository list
has already loaded**, or during later fork comparisons. This does **not** mean
the token is invalid, and it does not mean all 125 repos are being counted
incorrectly.

The audit deliberately preserves **all accessible branches and repositories**:
`git clone --mirror` and `git log --all` are unchanged. The throttling fix
serializes GitHub REST API requests across workers, waits at least five seconds
between search calls, and obeys GitHub `Retry-After` and `X-RateLimit-Reset`.
On a secondary limit without a usable header, it waits at least 60 seconds
and backs off exponentially. A generic permission-related 403 is reported as
an access error, rather than retried as though it were a rate limit.

The rate-control environment variables are:

| Variable | Default | Purpose |
| --- | ---: | --- |
| `AUDIT_SEARCH_REQUEST_GAP_SECONDS` | `5.0` | Minimum seconds between GitHub Search API requests |
| `AUDIT_API_REQUEST_GAP_SECONDS` | `0.4` | Minimum seconds between **all** API requests |
| `AUDIT_DISCOVERY_MAX_QUERIES` | `120` | Upper bound on global public author-discovery searches |
| `AUDIT_WORKERS` | `3` | Parallel Git mirror workers; API traffic is serialized independently |

**While a run is active:** Leave it alone if the log says `retrying` or
`respecting cooldown`; repeated manual reruns can aggravate GitHub throttling.
If the job fails, inspect the **last** error line rather than the first 403.
After merging this fix, trigger a fresh manual workflow run. If API limits
remain severe, increase the search gap to `7.0` or `10.0` rather than
disabling global discovery or suppressing fork checks.

If the log instead shows `Resource not accessible by personal access token`
or a plain HTTP 403 **without rate-limit evidence**, review the fine-grained PAT
repository and email permissions. Never paste the token or its value into
logs, reports, or messages.

