# Lifetime GitHub engineering audit

**Status: Not generated yet.** This placeholder intentionally contains no invented metrics.

Once the workflow runs successfully, this file is replaced with a comprehensive lifetime report covering:
- attributed Git commits (authored by you, co-authored by you, and detected agent contributions)
- historical text lines added and deleted, code-classified LOC, merge commits, and deduplicated Git SHAs
- all enumerated accessible repositories, including private repositories in aggregate
- annual and monthly timelines, historical filename-based languages, current GitHub Linguist bytes
- repository breakdown, pull requests, issues, and reviewer/comment activity
- explicit coverage warnings where history, attribution or access is incomplete

## First run

1. [Follow the setup instructions](./INSTALL.md), including the `GH_AUDIT_READ_TOKEN` secret and your `AUDIT_EMAILS` aliases.
2. Merge the pull request containing the workflow.
3. Run [GitHub lifetime engineering audit](../../actions/workflows/github-lifetime-audit.yml) from the **Actions** tab.
4. Reopen this page after the workflow commits generated files.

> Metrics are cumulative history across accessible repositories, **not** unique human-written code or current codebase size. Agent attribution uses Git metadata and is not guaranteed to detect every AI-assisted edit.
