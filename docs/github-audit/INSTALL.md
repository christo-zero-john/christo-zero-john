# Installation — GitHub Lifetime Audit

Target profile repository: `christo-zero-john/christo-zero-john`.

## 1. Merge the pull request

This pull request adds the **two source files** in your existing profile repository, at these paths:

- `.github/workflows/github-lifetime-audit.yml`
- `scripts/github_lifetime_audit.py`

Do **not** replace your existing `README.md`, `assets/engineering-stats.svg`, or statistics workflow. The generator appends or replaces only a small delimited section in the README.

## 2. Create a read token for cross-repository scanning

Navigate to GitHub → Settings → Developer settings → Personal access tokens.

**Recommended for personal repos:** a fine-grained token with resource owner `christo-zero-john`, `All repositories`, and **Contents: Read-only** and Metadata read. To fetch GitHub emails automatically, optionally allow **Email addresses: Read-only** (account permission). Note that a fine-grained token tied to a single resource owner might not cover your private repositories in other organizations.

**If you need *every* private organization and collaborator repo available to your account:** a classic PAT with `repo` and, if required for org enumeration, `read:org`; `user:email` optionally retrieves all verified emails. **Classic `repo` is a broad scope**; use a short-lived token, keep it secret, and rotate it. Organization policies may disallow or require approval of any PAT. No token can reveal repos you cannot access.

Save the token as a profile repository **Actions secret** named exactly `GH_AUDIT_READ_TOKEN` at:

`https://github.com/christo-zero-john/christo-zero-john/settings/secrets/actions`

The workflow's built-in `GITHUB_TOKEN` is used **only for committing the report back to the profile repo**. It is not relied on to access your other private repositories.

## 3. Set identity aliases (important for exact attribution)

Repo → Settings → Secrets and variables → Actions → **Variables**:

- `AUDIT_EMAILS`: comma-separated list of **every email you have used as a Git commit author**, e.g. `email1@example.com,email2@example.com`; don't use secrets for this unless you'd prefer to keep private aliases out of the Actions variable settings. They are never printed to the report. These supplement verified email addresses returned by `/user/emails` if permitted.
- `AUDIT_NAMES`: other names you've committed under (optional). Default identity set already includes your GitHub login and current GitHub display name. Names can collide; emails are more reliable.
- `AUDIT_AGENT_IDENTIFIERS`: optional comma-separated substrings for identifying agent author/co-author names and emails. Default: `claude,anthropic,codex,copilot,cursor,aider,devin,gemini`.

Review the defaults in the workflow before running. Agent-only attribution is deliberately restricted to repositories **owned by you**, to avoid claiming unrelated commits made by agents in other people's projects. Set `AUDIT_AGENT_COLLAB_REPOS: 'true'` in the workflow only if that is justified.

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
- The report may show **PARTIAL** coverage when clones fail, verified emails cannot be queried, or GitHub indexing searches are incomplete. Fix these before publishing any counts as exhaustive.
- GitHub's API cannot reconstruct deleted repos, never-pushed commits, invisible organization repos, all expired user events, or AI-generated code with no Git attribution. Public repo contributions from other maintainers may be found by global authored-commit search, but **coauthored-only external repos cannot be discovered reliably**.
- The public report masks private repo names/URLs by default while including their aggregate counts. **Even aggregated private statistics may be sensitive**; review before sharing. Set `AUDIT_SHOW_PRIVATE_NAMES` to `true` **only if** disclosure is intentional.

## Tuning performance

Cloning each repository's complete history, including branches and tags, may be slow or consume many gigabytes of runner disk. GitHub-hosted runners have finite disk and action durations; jobs may fail on particularly large histories. The workflow uses 3 worker threads and a 360-minute job timeout, with a 15-minute clone and 20-minute Git-history budget per repository. A timed-out repository is marked as failed and the published report is marked PARTIAL. Adjust `AUDIT_WORKERS` between 1 and 12; reduce it for very large repositories. Adjust `AUDIT_CLONE_TIMEOUT_SECONDS`, `AUDIT_GIT_LOG_TIMEOUT_SECONDS`, and `AUDIT_DISCOVERY_MAX_QUERIES` if needed. `AUDIT_GLOBAL_DISCOVERY: 'true'` searches authored commits on GitHub to find public repositories outside your explicit repository list; change it to `false` to accelerate audits at the expense of coverage.

## Privacy

The script does not write auth tokens or author email aliases into Markdown or JSON. Private repository names are redacted by default. GitHub Actions logs can still reveal errors and some API paths; avoid publishing verbose logs or making this workflow callable by untrusted pull requests. The workflow is manual/scheduled, not PR-triggered.

## Validate locally (without a GitHub token)

Run `python -m unittest discover -s tests -v` from the extracted package folder. The included integration tests create temporary Git repositories and validate branch traversal, rename statistics, co-author and agent attribution, merge counting, and private-repo redaction.