# Christo John — The Build Log

## Purpose and source contract

A 42-second, 1080 × 1920, 30 fps Instagram portrait film about Christo John's engineering work. The subject is the person and the sustained practice of building software. The film is text-led and sound-led, with no synthetic narration.

### Instagram frame contract

Master aspect ratio is exactly 9:16. Keep all essential type inside x=96–984 and y=280–1580, leaving generous room for the Reel header, controls, and caption overlay. The composition must also read as a centered 4:5 feed preview (y=285–1635). Supply a separate 1080 × 1350 cover crop with the name and film title centered; do not let the feed preview depend on a tiny full-height frame. Verify dimensions and displayed text bounds from rendered files, not only from composition settings.

All factual on-screen metrics, dates, and repository names come from `docs/github-audit/` as generated on 2026-11-06 14:59 UTC. The user's own role and workflow description, with `general_purpose_resume.pdf` as supporting context, supplies the personal and skill language. No repository source code, product screenshots, external biographies, or private repository identifiers enter the film.

### Approved facts for the film

| Film wording | Audit source |
| --- | --- |
| 05 APR 2023 — 06 NOV 2026 | `REPORT.md`, earliest and latest attributed commit author dates |
| 15,882 unique attributed commits | `REPORT.md`, deduplicated attributed Git SHAs |
| 125 repositories scanned | `REPORT.md`, successfully scanned repositories |
| `complaint-management-system` · 5,139 | `repositories.md`, attributed commits |
| `movie-watch-history-tracker-webapp` · 1,148 | `repositories.md`, attributed commits |
| `pbl-academy` · 907 | `repositories.md`, attributed commits |
| `mu-companion-webapp` · 622 | `repositories.md`, attributed commits |
| `virtual-background-photobooth` · 218 | `repositories.md`, attributed commits |

The five project names above are public and owned by the account in the audit. Their figures are repository/SHA occurrences, presented only beside those names. The film does not present them as independent project counts or aggregate them into the unique total.

## Creative direction

**Editorial evidence, with a pulse.** The visual is a large-format typographic publication set in motion. A vertical date rule becomes the timeline spine; repository rows become rhythmic printed evidence; one field of type expands to reveal the lifetime number. The camera stays steady. At most one scene uses a perspective move. All transitions have a physical cause: a printed line continues, a ledger scrolls, or a crop becomes the next frame.

The design uses near-black graphite `#11171A`, warm paper `#F3F1EA`, muted steel `#7C8A89`, and one restrained citron `#D3EE8D`. Titles use a contemporary grotesk with tight spacing; numbers and labels use a clear monospaced face. Contrast is high, ornament sparse, texture very fine. The accent appears only on a date marker, one active repository, and the final numerical reveal.

**Motion voice:** measured, weighted, accelerating once. Main actions take 20–45 frames, then hold. No camera shake, particle field, repeated light streaks, fake interface, or logo wall. At 480 px playback width, every intended reading line remains legible.

## Narrative and timeline

The film is 1,260 frames. Each segment has one primary movement and a genuine still point.

| # | Frames / time | Image and principal action | On-screen copy | Sound purpose |
| --- | --- | --- | --- | --- |
| 1 | 0–135 / 0–4.5s | Fine date rule draws; `CHRISTO JOHN` settles in a letterpress-like motion, then holds. | CHRISTO JOHN / THE BUILD LOG | Quiet room, one tactile impression, music enters under the hold. |
| 2 | 135–315 / 4.5–10.5s | Vertical timeline travels through 2023, 2024, 2025, 2026; motion accelerates, then brakes on the present. | 05 APR 2023 → 06 NOV 2026 | Four understated ticks with a short low-frequency lift into the brake. |
| 3 | 315–555 / 10.5–18.5s | Public repository names enter as a typeset index. Three rows take focus in turn; remaining rows give breadth, not clutter. | SELECTED WORK / five audit-sourced repository names and their per-repo attributed commits | Dry paper/machined texture, a single transition swell. |
| 4 | 555–735 / 18.5–24.5s | The index resolves into three stacked disciplines. Each line arrives on a measured beat. | DESIGN THINKING / FULL STACK DEVELOPMENT / PLANNING → DEPLOYMENT | Percussive pulse gains weight; leave the third line exposed. |
| 5 | 735–870 / 24.5–29s | One compact tool line traces a workflow from design to engineering. | FIGMA · NEXT.JS · SUPABASE · VS CODE · CLAUDE · CODEX | Softer rhythmic detail; no six identical sound hits. |
| 6 | 870–1080 / 29–36s | Ledger rows compress into a fine line; it opens into `15,882`, with the caption locked below. The number rests for more than one second. | 15,882 / UNIQUE ATTRIBUTED COMMITS / 125 REPOSITORIES SCANNED | Main musical arrival, one physical impact, long harmonic tail. |
| 7 | 1080–1260 / 36–42s | Camera backs away from the number to reveal a final, calm typographic portrait. Hold the name through the last 1.5s. | CHRISTO JOHN / ASPIRING AI PRODUCT ENGINEER | Percussion drops; warm chord and controlled decay. |

No spoken voice is required. The words are the script. The number and name are the two deliberate memory points. Source time and account link can live in the post caption, keeping the frame clean.

## Shotcraft mapping

- `brand-ink-open`: adapt the single subject, printed name, and full hold to portrait framing.
- `timeline-travel`: adapt the accelerate/brake grammar to a vertical year spine; dates are the audit's dates.
- `document-typewriter-reveal`: use only the disciplined reveal grammar for the real audit-derived repository index, without imitating a product UI.
- `paper-title-card`: adapt the word-by-word compression to the three disciplines, with portrait type scale.
- `ui-to-brand-morph`: adapt only the causal compression/reveal grammar for the number-to-name closing sequence; no invented company logo.

Each selected card must be checked against its Gallery record and accurate demo source before implementation. Portrait adaptation and render inspection govern the final timing.

## Audio direction and acceptance

The music has a close, intimate first bar, a restrained percussive build, one full arrival on `15,882`, and a warm unresolved-to-resolved final chord. Preferred palette: rounded sub-bass, brushed or muted percussion, one analog harmonic texture, and sparse high-frequency detail. The track must feel like a film about a person, rather than a generic software advertisement.

Audition at least three properly licensed candidates against a rough cut. Reject any candidate that makes the middle feel frantic or masks the two reading holds. Source a small number of CC0 physical SFX for print, timeline tick, ledger movement, and the numerical impact; record license and file hashes. Lock visuals before exact sound placement. Mix by ear in the rendered film, measure peaks and loudness, and inspect the waveform around scene joins. Listen on both headphones and a phone-sized speaker. Render a final music mix and an alternate without the music bed, retaining SFX.

## Delivery and verification

The working project lives in `film/`; final MP4s in `film/out/`. Render the first, middle, and final still of every shot, inspect the whole encoded video, verify every on-screen number against the audit, and run a separate final review with frame-number findings. Confirm both audio variants have the intended tracks and that their duration, frame size, text legibility, transitions, and audio peaks meet the spec. Stop any task-started server or helper after verification.
