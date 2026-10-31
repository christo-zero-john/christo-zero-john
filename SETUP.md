# GitHub profile kit — setup and privacy

**Account:** `christo-zero-john`  
**Contents:** `README.md`, `assets/` (custom SVG art and cards), `scripts/update-stats.mjs`, and `.github/workflows/refresh-profile-stats.yml`.

## Publish the profile

1. Open the **public** repository [christo-zero-john/christo-zero-john](https://github.com/christo-zero-john/christo-zero-john). This special repo already exists and has an older `Readme.md`. The pull request removes that older filename and installs the new `README.md`, avoiding case-conflicting files.
2. Copy the exact files/folders from this kit into the repository **root**, preserving their paths. `README.md` must live at the root for GitHub to show it on your profile.
3. Commit. The introductory header, content, and **verified snapshot of owned repository counts** work immediately. The contribution chart will show a setup prompt until authenticated sync succeeds.

## Include private repositories in AUTOMATIC stats

**Important:** The built-in `GITHUB_TOKEN` of your *public profile repository* cannot access private client repositories just because you can. A separate credential that has read access to those repositories is required.

1. Create a GitHub **personal access token** owned by `christo-zero-john`. Prefer a **fine-grained token** restricted to *read-only metadata* across relevant repositories if it works for your account; private collaborator/organization contributions may require additional access/approval. Some private contribution statistics may require a classic token with `repo` and `read:user`, which has **broad repository access**—do not create or store one if its risk is unacceptable. Use the least-privileged permission set that returns complete aggregate results. Prefer a limited-expiration token and rotate it.
2. In the **public profile repository** go to **Settings → Secrets and variables → Actions → New repository secret**. Name the secret **`GH_STATS_TOKEN`** and put the token there. **Never paste it into `README.md`, SVGs, a commit, or an issue.**
3. Go to **Actions → Refresh private-safe GitHub profile metrics → Run workflow**. After a successful run, the two image assets are updated; the job runs automatically every day thereafter.
4. On your GitHub profile, above the contributions calendar, choose **Contribution settings → Private contributions** if you want GitHub's own contribution calendar to show anonymized private activity. GitHub may exclude activity not meeting its contribution-eligibility rules, and inaccessible contributions cannot be reconstructed by this kit.

The script includes a `MIN_EXPECTED_PRIVATE_REPOS` guard initialized to **32** (the count verified on 28 October 2026). If the token cannot see at least that many owned private repos, it *refuses to overwrite* the last known stats card. If you intentionally delete or make repositories public, adjust that number in the workflow.

### What becomes public, exactly?

| Data | Visible in published cards? |
|:--|:--|
| Your total **owned** repository count | **Yes** |
| Owned public/private repository counts | **Yes** |
| Number of accessible collaborator repositories | **Yes** |
| Last 12 months' eligible GitHub contribution totals and heatmap | **Yes, after sync** |
| Private repository names, URLs and descriptions | **Never** |
| Client identifiers, source, file trees, issues or commit messages | **Never** |
| Token value | **Never** |

The update script uses GitHub GraphQL **metadata and aggregated activity only**. It does not fetch private source code, commits, issues, or PR contents. It prints only the aggregate repository count. GitHub Actions runs from a trusted scheduled/manual trigger; avoid adding untrusted pull-request triggers to this workflow. Public GitHub Actions logs still exist; audit your logs after enabling the workflow.

### Repository vs contribution counts

- `121 owned / 89 public / 32 private` was verified by reviewing connected GitHub repo metadata on 28 October 2026.
- `4 collaborations` includes one accessible private repository, **not** part of the 32 owned private count.
- A **repository** is not a contribution. The contribution graph comes from GitHub's contribution rules, not a sum of all commits across all branches.
- GitHub may not show private or organization work if you lack access or GitHub's eligibility/visibility settings exclude it.

## Adjust appearance

- `assets/hero.svg`: main hero artwork, custom gradient, technical grid, motion.
- `assets/footer.svg`: closing accent stripe.
- `scripts/update-stats.mjs`: renderer for the custom dark-teal stats and contribution cards.
- `README.md`: text, selected public repository links, and skill badges.

## Validate locally

```bash
node --check scripts/update-stats.mjs
node scripts/update-stats.mjs --snapshot
```

Snapshot mode intentionally **regenerates the October 2026 baseline**, not live data. Do not run it after automatic stats are working unless you specifically want to restore the baseline.

## Third-party media

The README uses Shields.io skill badges and the [readme-typing-svg](https://github.com/DenverCoder1/readme-typing-svg) externally hosted animation. The profile's header, footer, and stats cards are local assets. If an external image host goes down, only the corresponding typing/badge visual is affected. No authenticated GitHub token is sent to the typing or badge services.

## Source notes

- GitHub docs: https://docs.github.com/en/account-and-profile/how-tos/contribution-settings/manage-visibility-settings-for-private-contributions-and-achievements
- GitHub GraphQL: https://docs.github.com/en/graphql/reference/users
- GitHub GraphQL repo access: https://docs.github.com/en/graphql/reference/repos

**Confidentiality reminder:** Repository counts can reveal your overall work volume. Before publishing those numbers, make sure public disclosure of these aggregate totals is allowed by your client agreements.
