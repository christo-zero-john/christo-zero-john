# Lifetime GitHub audit — previous statistics withdrawn

**Status: INVALIDATED.** The previous lifetime totals are not trustworthy. They mistakenly attributed third-party AI-assisted upstream commits found in forked repositories to this account.

## Confirmed false-positive example

- Repository: [christo-zero-john/openalgo-for-stocketREX](https://github.com/christo-zero-john/openalgo-for-stocketREX), a fork of [marketcalls/openalgo](https://github.com/marketcalls/openalgo)
- GitHub comparison of default branches: **0 commits ahead**, **376 commits behind** upstream (verified November 6, 2026).
- An [upstream commit](https://github.com/christo-zero-john/openalgo-for-stocketREX/commit/e78f2edee924141b8ff57a37da26132f5447fd5b) is authored by **marketcalls** and co-authored by an Anthropic agent, **not by Christo John**.
- **Verified authorship exception:** [Commit `4dc48eb...`](https://github.com/marketcalls/openalgo/commit/4dc48eb00db9813769d2d9a839dcd828bad16674) is genuinely authored by the connected GitHub account (June 8, 2026): **69 added, 25 deleted, 94 changed lines**. It exists in the original upstream, so it is one contribution, not a new change made after forking.
- The old metrics for this fork contain **1 directly authored commit and 1,619 incorrectly claimed agent-only commits**. All 1,619 appear in the legacy fork report because it treated other developers' Anthropic co-authors as the fork owner's agents.
- The former account-wide commit/LOC statistics are **withdrawn** and must be recomputed, not simply corrected by subtraction.

## Strict replacement counting policy

1. Direct authorship: exact Git author email associated with the connected GitHub account.
2. Co-authorship: exact developer email in a valid `Co-authored-by` trailer.
3. Agent-only commits: excluded unless an exact `owner/repository@commitSHA` is explicitly approved through the secret `AUDIT_APPROVED_AGENT_COMMITS`.
4. Forks: imported upstream commits require the same authorship evidence as every other repository. Ownership of a fork alone is **not** evidence.
5. LOC: historical additions and deletions in only qualifying commits, with all-text churn and stricter code-classified churn separately reported.
6. Historical languages: official GitHub Linguist filename/extension definitions; current language bytes from GitHub's Linguist API. Ambiguous historical files are not falsely assigned to a language.

**The replacement figures will be generated only after the fixed workflow runs successfully.** No previous numbers should be reused for public claims.

[Detailed methodology](./APPENDIX.md) · [Fork audit](./repositories.md) · [Languages](./languages.md)
