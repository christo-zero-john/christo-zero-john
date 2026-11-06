# Programming languages — prior contribution totals withdrawn

The previous **historical language LOC figures are INVALIDATED**, because they were derived from a commit set contaminated by inherited fork history.

## Methods in the replacement audit

**Current languages:** GitHub's official Linguist API reports byte totals for repository default-branch snapshots. It is not a per-author LOC calculation.

**Historical languages:** Changed paths are classified from the official GitHub Linguist language registry; ambiguous filenames are separated instead of guessed. This is more comprehensive than the previous handwritten extension list but does not run Linguist's complete content parser on every historical blob.

**Generated, vendor and lockfile content:** Included in all-text churn when changed by a verified commit; recognizable generated/vendor paths are excluded from strict code-classified totals.

[Main report](./REPORT.md) · [Methodology appendix](./APPENDIX.md)
