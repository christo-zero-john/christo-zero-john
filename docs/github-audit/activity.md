# GitHub platform activity

[Overview](./REPORT.md) · [Repositories](./repositories.md) · [Timeline](./timeline.md) · [Languages](./languages.md) · [Activity](./activity.md)

These metrics come from GitHub's searchable issue/PR index and current repository/user metadata, not `git log`. Searches may have indexing gaps; they are not a complete historical event log.

| Metric | Count  | ℹ Details |
| --- | ---  | --- |
| Authored pull requests (GitHub search) | 49  | <details><summary>ℹ Explain</summary><p>A directly authored commit is counted only when its Git author email matches a verified or GitHub-account-linked email. Names alone never prove authorship. Historical email aliases can come from the authenticated account email API and commits indexed under the <a href="./APPENDIX.md#identity">Full appendix: Authorship and confirmed Git identities</a></p></details> |
| Merged authored pull requests | 38  | <details><summary>ℹ Explain</summary><p>A directly authored commit is counted only when its Git author email matches a verified or GitHub-account-linked email. Names alone never prove authorship. Historical email aliases can come from the authenticated account email API and commits indexed under the <a href="./APPENDIX.md#identity">Full appendix: Authorship and confirmed Git identities</a></p></details> |
| Authored issues | 77  | <details><summary>ℹ Explain</summary><p>A directly authored commit is counted only when its Git author email matches a verified or GitHub-account-linked email. Names alone never prove authorship. Historical email aliases can come from the authenticated account email API and commits indexed under the <a href="./APPENDIX.md#identity">Full appendix: Authorship and confirmed Git identities</a></p></details> |
| Closed authored issues | 40  | <details><summary>ℹ Explain</summary><p>A directly authored commit is counted only when its Git author email matches a verified or GitHub-account-linked email. Names alone never prove authorship. Historical email aliases can come from the authenticated account email API and commits indexed under the <a href="./APPENDIX.md#identity">Full appendix: Authorship and confirmed Git identities</a></p></details> |
| Distinct PRs reviewed (not number of reviews) | 5  | <details><summary>ℹ Explain</summary><p>PR, issue, reviewer and commenter counts come from GitHub&#x27;s indexed Search APIs. They are neither Git commits nor a complete historical event archive. Review counts typically refer to distinct PRs, not individual review comments. Followers, stars and forks are <a href="./APPENDIX.md#platform">Full appendix: GitHub social, PR and issue activity</a></p></details> |
| Distinct issue/PR threads commented on | Unavailable  | <details><summary>ℹ Explain</summary><p>PR, issue, reviewer and commenter counts come from GitHub&#x27;s indexed Search APIs. They are neither Git commits nor a complete historical event archive. Review counts typically refer to distinct PRs, not individual review comments. Followers, stars and forks are <a href="./APPENDIX.md#platform">Full appendix: GitHub social, PR and issue activity</a></p></details> |
| Current followers | 20  | <details><summary>ℹ Explain</summary><p>PR, issue, reviewer and commenter counts come from GitHub&#x27;s indexed Search APIs. They are neither Git commits nor a complete historical event archive. Review counts typically refer to distinct PRs, not individual review comments. Followers, stars and forks are <a href="./APPENDIX.md#platform">Full appendix: GitHub social, PR and issue activity</a></p></details> |
| Current following | 40  | <details><summary>ℹ Explain</summary><p>One Git SHA counts once per repository across all reachable branches and tags. Repository/SHA occurrences may count the same original commit again in another fork or mirror. Account-wide unique Git SHA totals deduplicate that overlap. Git commits made by other <a href="./APPENDIX.md#counts">Full appendix: Commit counting and deduplication</a></p></details> |
| Stars currently received by owned repos in inventory | 10  | <details><summary>ℹ Explain</summary><p>PR, issue, reviewer and commenter counts come from GitHub&#x27;s indexed Search APIs. They are neither Git commits nor a complete historical event archive. Review counts typically refer to distinct PRs, not individual review comments. Followers, stars and forks are <a href="./APPENDIX.md#platform">Full appendix: GitHub social, PR and issue activity</a></p></details> |
| Forks currently received by owned repos in inventory | 10  | <details><summary>ℹ Explain</summary><p>A fork includes inherited upstream history. Mere possession of a fork does not transfer author credit. Each commit must still pass exact identity matching or explicit agent-SHA approval. The audit separately checks a fork default branch against its parent usin <a href="./APPENDIX.md#forks">Full appendix: Forked repositories and upstream ancestry</a></p></details> |


## Issues and PRs opened by year

| Year created | Opened PRs | Opened issues  | ℹ Details |
| --- | --- | ---  | --- |
| 2026 | 11 | 1  | <details><summary>ℹ Explain</summary><p>Historical Git activity is bucketed by commit author timestamp in UTC, not by push date. History can be imported, rewritten or dated differently from when work was performed. Monthly and yearly tables use repository/SHA occurrences, so duplicated fork history  <a href="./APPENDIX.md#timelines">Full appendix: Dates, monthly activity and yearly activity</a></p></details> |
| 2025 | 9 | 6  | <details><summary>ℹ Explain</summary><p>Historical Git activity is bucketed by commit author timestamp in UTC, not by push date. History can be imported, rewritten or dated differently from when work was performed. Monthly and yearly tables use repository/SHA occurrences, so duplicated fork history  <a href="./APPENDIX.md#timelines">Full appendix: Dates, monthly activity and yearly activity</a></p></details> |
| 2024 | 20 | 68  | <details><summary>ℹ Explain</summary><p>Historical Git activity is bucketed by commit author timestamp in UTC, not by push date. History can be imported, rewritten or dated differently from when work was performed. Monthly and yearly tables use repository/SHA occurrences, so duplicated fork history  <a href="./APPENDIX.md#timelines">Full appendix: Dates, monthly activity and yearly activity</a></p></details> |
| 2023 | 9 | 2  | <details><summary>ℹ Explain</summary><p>Historical Git activity is bucketed by commit author timestamp in UTC, not by push date. History can be imported, rewritten or dated differently from when work was performed. Monthly and yearly tables use repository/SHA occurrences, so duplicated fork history  <a href="./APPENDIX.md#timelines">Full appendix: Dates, monthly activity and yearly activity</a></p></details> |


*Historical star/follow/unfollow events, deleted discussions, and activity in inaccessible repositories cannot be reconstructed exactly from GitHub's current APIs.*

<!-- AUDIT_EXPLAINERS_START -->

## Appendix: what these numbers actually mean

Expand the **ℹ Explain** control on any row for its definition and a direct [appendix section](./APPENDIX.md). The full methodology explains verified identities, fork ancestry, agents, GitHub Linguist, generated code, LOC, privacy and coverage.

[Read the complete methodology appendix](./APPENDIX.md)

<!-- AUDIT_EXPLAINERS_END -->
