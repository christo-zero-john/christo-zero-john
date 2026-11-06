# GitHub engineering audit — metric and methodology appendix

This is the reference for every expandable Info cell in the generated audit tables. The definitions distinguish evidence-based contributions from work that was merely present in a fork.

<a id="identity"></a>
## Authorship and confirmed Git identities

A directly authored commit is counted only when its Git author email matches a verified or GitHub-account-linked email. Names alone never prove authorship. Historical email aliases can come from the authenticated account email API and commits indexed under the exact GitHub user. An unfamiliar, unlinked historical email must be reviewed separately. Emails are never published in public Markdown or JSON.

<a id="coauthors"></a>
## Co-authored Git commits

A commit authored by someone else qualifies as co-authored by the developer only when a Co-authored-by trailer contains an exact, known developer email. The same Git SHA counts once even when several qualifying trailers occur. An unrelated agent named in a co-author trailer does not make that commit yours.

<a id="agents"></a>
## AI-assisted versus agent-authored commits

An agent-assisted commit is a human-authored or human-coauthored commit also featuring detectable agent metadata. This is a descriptive flag, not an extra commit. An agent-only commit qualifies solely if its exact repository@40-character-SHA is deliberately approved through AUDIT_APPROVED_AGENT_COMMITS; otherwise it is excluded. Claude/Codex contribution trailers in somebody else's upstream history are not proof of ownership. AI-written code without identifiable Git metadata cannot be measured exactly.

<a id="forks"></a>
## Forked repositories and upstream ancestry

A fork includes inherited upstream history. Mere possession of a fork does not transfer author credit. Each commit must still pass exact identity matching or explicit agent-SHA approval. The audit separately checks a fork default branch against its parent using GitHub's compare API. Ahead 0 means no fork-only commits on that default branch versus the upstream comparison; other branches can diverge. Behind measures upstream commits absent from the fork. An unavailable ancestry check is disclosed and does not authorize inherited history.

<a id="counts"></a>
## Commit counting and deduplication

One Git SHA counts once per repository across all reachable branches and tags. Repository/SHA occurrences may count the same original commit again in another fork or mirror. Account-wide unique Git SHA totals deduplicate that overlap. Git commits made by other authors remain in the reachable-history inventory but are never counted as this developer's attributed contributions.

<a id="loc"></a>
## Historical lines of code and cumulative changes

Git --numstat reports added and deleted text lines within every included commit. Changed lines equals additions plus deletions. This is historical churn, not the current size of a project or a number of original lines authored by a human. Repeated edits, code moved between files, merges, imports and generated content can increase the total. Binary changes do not have numeric line counts. Merge diffs are compared to their first parent and may duplicate earlier changes.

<a id="languages"></a>
## GitHub Linguist and language classifications

The current-language byte snapshot is returned by GitHub's /repos/{owner}/{repo}/languages endpoint, which uses GitHub Linguist for the current default branch. Historical changed-line classifications use the official GitHub Linguist filename/extension registry, not every historical blob's content-level parser. Ambiguous paths are explicitly unclassified rather than guessed. File extensions do not prove skill or human authorship; GitHub Linguist data can also include upstream authors.

<a id="code"></a>
## Strict code-classified lines versus all text

All-text LOC includes prose, configuration, data files, generated code and lockfiles. Strict code-classified LOC uses Linguist programming/markup filename types and excludes recognizable vendored, generated and distribution paths. Ambiguous and unknown files are excluded from the strict code subset. This is conservative filename classification; complete historical parser-level classification and file-level authorship cannot be inferred from paths alone.

<a id="timelines"></a>
## Dates, monthly activity and yearly activity

Historical Git activity is bucketed by commit author timestamp in UTC, not by push date. History can be imported, rewritten or dated differently from when work was performed. Monthly and yearly tables use repository/SHA occurrences, so duplicated fork history can appear in the per-period series; the all-account unique SHA total is separate.

<a id="platform"></a>
## GitHub social, PR and issue activity

PR, issue, reviewer and commenter counts come from GitHub's indexed Search APIs. They are neither Git commits nor a complete historical event archive. Review counts typically refer to distinct PRs, not individual review comments. Followers, stars and forks are current snapshots and can change.

<a id="coverage"></a>
## Coverage, accuracy, and excluded evidence

COMPLETE means no known errors for enumerated accessible repositories and search sources; it does not mean all deleted, local-only, unpushed or inaccessible work was reconstructed. PARTIAL indicates scan, API, GitHub index or ancestry gaps. Unverified name-only matches and unexplained agent-only commits are excluded, not included optimistically. Errors and exclusions are summarized so published totals are not misrepresented as unquestionable lifetime truth.

<a id="portfolio"></a>
## Repository ownership, visibility and project summaries

Owned, forked, archived and collaborator repositories are different relationships. Repository ownership does not establish who wrote inherited Git history. Public project descriptions, topics and dependency manifests are a current snapshot and do not verify production deployments, business results, work hours or depth of proficiency. Private repo titles and URLs are masked by default.

<a id="privacy"></a>
## Private-data and account-identity protection

Access tokens and author email addresses are never placed into the public reports. Private repositories contribute to aggregate statistics, but their names, links and descriptions are anonymized by default. GitHub Actions logs must be kept free from token contents. Aggregate private statistics may still reveal sensitive scale and should be reviewed before sharing.

## Data-source hierarchy

1. **Verified authored/co-authored work:** exact Git email identity plus attributed commit histories.
2. **Approved agent-only work:** individually authorized repository/SHA pairs; never an upstream coauthor alone.
3. **GitHub Linguist:** current language bytes and official filename metadata, not a claim of full historical per-blob parsing.
4. **Repository/PR metadata:** live snapshots and indexed search, not human skill verification.
5. **Self-reported biodata:** work history, education and preferred tools remain separate from audit metrics.
