# Installation — GitHub Lifetime Audit

Target profile repository: `christo-zero-john/christo-zero-john`.

## 1. Merge the pull request

This pull request adds the **two source files** in your existing profile repository, at these paths:

- `.github/workflows/github-lifetime-audit.yml`
- `scripts/github_lifetime_audit.py`

Do **not** replace your existing `README.md`, `assets/engineering-stats.svg`, or statistics workflow. The generator appends or replaces only a small delimited section in the README.

## 2. Create a read token for cross-repository scanning

Navigate to GitHub → Settings → Developer settings → Personal access tokens.

**Recommended for personal repos:** a fine-grained token with resource owner `christo-zero-john`, `All repositories`, and **Contents: Read-only** and Metadata read. To discover more historical aliases, enable **Email addresses: Read-only** (account permission), where available. Note that a fine-grained token tied to a single resource owner might not cover your private repositories in other organizations.

**If you need *every* private organization and collaborator repo available to your account:** a classic PAT with `repo` and, if required for org enumeration, `read:org`; `user:email` retrieves verified email aliases if permitted. **Classic `repo` is a broad scope**; use a short-lived token, keep it secret, and rotate it. Organization policies may disallow or require approval of any PAT. No token can reveal repos you cannot access.

Save the token as a profile repository **Actions secret** named exactly `GH_AUDIT_READ_TOKEN` at:

`https://github.com/christo-zero-john/christo-zero-john/settings/secrets/actions`

The workflow's built-in `GITHUB_TOKEN` is used **only for committing the report back to the profile repo**. It is not relied on to access your other private repositories.

## 3. Automatic identity discovery — no author emails required

**AUDIT_EMAILS is optional. You can leave it unset.**

Before scanning histories, the workflow finds historical author emails automatically:

1. Starts with your GitHub login, numeric account ID, and standard GitHub no-reply addresses.
2. Queries your verified account email addresses via the GitHub API when the access token allows it.
3. Searches GitHub's historical commits by the account-linked author login, and extracts the original author email for any commit GitHub links to your account. This detects different GitHub Desktop identities, including many identities from prior installations.
4. Matches all discovered email aliases when counting authored and co-authored commits across repositories.
5. For repositories you own, commits with an exact matching Git author name but an unverified email are counted as **provisional name-only matches**. The report explicitly marks coverage **PARTIAL** and reports the provisional count. Author names are not proof of identity.

Git author email aliases are used only in memory. The published Markdown and JSON show only alias counts, not actual email addresses.

**Optional Actions repository variables:**

- **AUDIT_EMAILS**: extra historical author emails if you later discover any missed identity; normally leave unset.
- **AUDIT_NAMES**: additional names if GitHub Desktop used a different author name; normally leave unset.
- **AUDIT_AGENT_IDENTIFIERS**: customize which bot and agent author/co-author identities count.

A historical email not linked to your GitHub account and written under an unrecognized name **cannot be reliably proven to be yours** solely from Git history. GitHub's indexed commit search may also omit deleted or inaccessible history. The report must not describe this as exact, total lifetime authorship.

## 4. Grant workflow permission to update your README

Profile repository → **Settings → Actions → General → Workflow permissions** → **Read and write permissions** (where your organization policy permits). The workflow explicitly requests `contents: write`.

## 5. Run

`https://github.com/christo-zero-john/christo-zero-john/actions/workflows/github-lifetime-audit.yml`

Click **Run workflow**. Once completed, your README will link to:

`https://github.com/christo-zero-john/christo-zero-john/blob/main/docs/github-audit/REPORT.md`

It also runs every Sunday. Delete the `schedule` block to make it manual-only.

## What the numbers mean

- Reports include **both repository/SHA occurrences and cross-repository unique SHA totals**. The latter deduplicates the same Git commit appearing in forks or mirrors. Annual/monthly/language tables use per-repository occurrences.
- `Attributed commits` includes **self authored + self co-authored + agent-only commits** attributed by detectable agent signatures in your repos. A SHA counts once per repo, not once per author/co-author. Commits with both you and an agent count as self-authored or self-coauthored, and separately as `agent-assisted` (not an extra commit).
- `Lines added` and `lines deleted` are summed from Git **numstat** on every attributed commit across full reachable repository history. `Lines changed = additions + deletions`. All text files are included: code, documentation, configuration, generated text, and lockfiles. `Code-classified` is shown separately.
- Merge diffs are compared to first parent; their changes can duplicate changes counted in the branch being merged. Renames are detected. Binary changes cannot be represented as line totals.
- This is **cumulative churn**, not the size of the current codebase, not unique LOC ever written, and not a human-versus-agent code-generation estimate.
- The report shows **PARTIAL** when scans fail, GitHub indexing searches are incomplete, or commits are attributed provisionally by author name. Fix these before publishing any counts as exhaustive.
- GitHub's API cannot reconstruct deleted repos, never-pushed commits, invisible organization repos, all expired user events, or AI-generated code with no Git attribution. Public repo contributions from other maintainers may be found by global authored-commit search, but **coauthored-only external repos cannot be discovered reliably**.
- The public report masks private repo names/URLs by default while including their aggregate counts. **Even aggregated private statistics may be sensitive**; review before sharing. Set `AUDIT_SHOW_PRIVATE_NAMES` to `true` **only if** disclosure is intentional.

## Tuning performance

Cloning each repository's complete history, including branches and tags, may be slow or consume many gigabytes of runner disk. GitHub-hosted runners have finite disk and action durations; jobs may fail on particularly large histories. The workflow uses 3 worker threads and a 360-minute job timeout, with a 15-minute clone and 20-minute Git-history budget per repository. A timed-out repository is marked as failed and the published report is marked PARTIAL. Adjust `AUDIT_WORKERS` between 1 and 12; reduce it for very large repositories. Adjust `AUDIT_CLONE_TIMEOUT_SECONDS`, `AUDIT_GIT_LOG_TIMEOUT_SECONDS`, and `AUDIT_DISCOVERY_MAX_QUERIES` if needed. `AUDIT_GLOBAL_DISCOVERY: 'true'` searches authored commits on GitHub to find public repositories outside your explicit repository list; change it to `false` to accelerate audits at the expense of coverage.

## Privacy

The script does not write auth tokens or author email aliases into Markdown or JSON. Private repository names are redacted by default. GitHub Actions logs can still reveal errors and some API paths; avoid publishing verbose logs or making this workflow callable by untrusted pull requests. The workflow is manual/scheduled, not PR-triggered.

## Validate locally (without a GitHub token)

Run `python -m unittest discover -s tests -v` from the extracted package folder. The included integration tests create temporary Git repositories and validate branch traversal, rename statistics, co-author and agent attribution, merge counting, and private-repo redaction.