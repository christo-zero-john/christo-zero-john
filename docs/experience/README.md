# Interactive engineering experience

This is an optional **real web application** for Christo John's engineering profile. GitHub READMEs do not execute JavaScript, so hover states, filters and count-up animation cannot work reliably inside the profile itself.

The README is deliberately still, responsive and legible. This companion site is where actual interaction belongs.

## What is implemented

- Responsive editorial design with restrained transitions.
- Short, once-only count-up metrics driven by the **strict policy-v3 audit**.
- Working category filters for featured public projects.
- Full-card hover and keyboard focus states.
- A native, accessible methodology dialog.
- Reduced-motion support.
- No third-party UI libraries, trackers, CDN fonts, client API keys or runtime GitHub access.

Files:

- `index.html` — self-contained HTML, CSS and JavaScript.
- `data.json` — generated after each lifetime audit by `scripts/render_refined_profile.py`. Contains **only** aggregate metrics and the four featured **public** project records. No private project names or credentials.

## Enable hosting (requires repository settings access)

The repository did not have GitHub Pages enabled when this was added. To deploy:

1. Merge the profile redesign PR into `main`.
2. Open GitHub repository **Settings → Pages**.
3. Under **Build and deployment**, select **Deploy from a branch**.
4. Select `main` and `/docs` as the publish folder.
5. Save and let GitHub Pages publish.

Expected hosted location after setup:

`https://christo-zero-john.github.io/christo-zero-john/experience/`

This is an expected URL **only after GitHub Pages is successfully enabled and published**; do not add it to the public profile as an active link before confirming it works.

Alternatively, deploy the entire `docs/experience/` directory to your existing hosting platform. Keep `index.html` and `data.json` together.

## Data refresh

The lifetime audit runs on the 1st of each month, can be triggered manually, and refreshes both the README and this site's `data.json`. GitHub Pages publishes the updated data file automatically when the default branch changes.

## Accuracy

- Commit identities come from the strict Christo-specific account policy.
- Forked upstream history is excluded unless independently attributable.
- AI agents are coauthors on qualifying user commits, not extra counted commits.
- Code LOC is cumulative additions and deletions, not uniquely written source lines.
- All available advertised Git refs are scanned.
- GitHub Linguist's current language bytes include other contributors.
- Private project names are excluded from the interactive site's JSON even if the separate public audit setting allows them in audit reports.
