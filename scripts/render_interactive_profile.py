#!/usr/bin/env python3
"""GitHub-safe animated SVG link cards and evidence-backed project portfolio.

Requires the strict lifetime audit and render_profile_dashboard.py to run first.
Rebuilds only the explicitly marked README sections plus generated SVG assets.
No JavaScript, no inline SVG in README, no external hosting or private repo names.

Motion is declarative CSS inside SVG images. GitHub/browser support varies;
the default/static SVG always displays final values. Clickable areas are HTML
<a> wrappers around images, and GitHub-native <details> are actual controls.
"""
from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

ROOT = Path(".")
ASSETS = ROOT / "assets"
README = ROOT / "README.md"
DATA = ROOT / "docs/github-audit/audit.json"
INK = "#0E1315"
PANEL = "#121A1B"
EDGE = "#405451"
WHITE = "#F4F7F3"
PALE = "#A9BDB5"
MINT = "#C2ECD1"
DIM = "#7F9690"
ACCENT = "#8AC4AE"

PROJECTS = [
    {
        "id": "photobooth", "repo": "christo-zero-john/virtual-background-photobooth",
        "title": "Virtual Background Photobooth", "kind": "INTERACTIVE MEDIA",
        "description": ("Real-time background replacement", "and remote camera control."),
        "tags": "WEBGL · MEDIAPIPE · SUPABASE",
    },
    {
        "id": "roco", "repo": "christo-zero-john/roco-the-agentic-car",
        "title": "ROCO / The Agentic Car", "kind": "ROBOTICS / EXPERIMENTAL",
        "description": ("A 4WD hardware experiment moving", "toward increasingly intelligent control."),
        "tags": "ROBOTICS · PROTOTYPING · AGENTS",
    },
    {
        "id": "movie", "repo": "christo-zero-john/movie-watch-history-tracker-webapp",
        "title": "Movie Watch History Tracker", "kind": "PRODUCT / FRONTEND",
        "description": ("Track viewing history and explore", "film recommendations through TMDB."),
        "tags": "REACT · TMDB · PRODUCT UI",
    },
    {
        "id": "complaints", "repo": "christo-zero-john/complaint-management-system",
        "title": "Complaint Management System", "kind": "FULL STACK / INSTITUTIONAL",
        "description": ("An institutional issue-tracking", "workflow built during undergraduate study."),
        "tags": "PHP · DATA WORKFLOWS · WEB",
    },
]

ACTIONS = [
    ("portfolio", "PORTFOLIO", "SELECTED PRODUCT WORK", "https://tesnic.vercel.app", "01 / VISIT"),
    ("linkedin", "LINKEDIN", "PROFESSIONAL NETWORK", "https://www.linkedin.com/in/christo-john-kalapurackal/", "02 / CONNECT"),
    ("work", "SELECTED WORK", "FEATURED REPOSITORIES", "#selected-work", "03 / EXPLORE"),
    ("email", "CONTACT", "LET'S BUILD SOMETHING", "mailto:10.christojohn@gmail.com", "04 / SAY HELLO"),
]
AUDIT_LINKS = [
    ("audit", "FULL GIT AUDIT", "Lifetime metrics & evidence", "./docs/github-audit/REPORT.md", "01 / RECORD"),
    ("repositories", "REPOSITORY INDEX", "Contributions by repository", "./docs/github-audit/repositories.md", "02 / WORK"),
    ("languages", "LANGUAGE HISTORY", "Code classification & trends", "./docs/github-audit/languages.md", "03 / DATA"),
    ("attribution", "ATTRIBUTION NOTES", "Forks, AI agents & methodology", "./docs/github-audit/APPENDIX.md", "04 / PROOF"),
]


def fmt(value: int | None) -> str:
    return f"{value:,}" if isinstance(value, int) else "—"


def tag(x: int, y: int, value: str, size: int = 16, color: str = WHITE,
        weight: int = 500, tracking: float = 0, anchor: str = "") -> str:
    attrs = (
        f'x="{x}" y="{y}" font-size="{size}" fill="{color}" '
        f'font-family="Inter, Segoe UI, Arial, sans-serif" font-weight="{weight}"'
    )
    if tracking:
        attrs += f' letter-spacing="{tracking}"'
    if anchor:
        attrs += f' text-anchor="{anchor}"'
    return f'<text {attrs}>{escape(str(value))}</text>'


def shell(width: int, height: int, title: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{escape(title)}">',
        f'<rect width="{width}" height="{height}" rx="18" fill="{INK}"/>',
        f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="17" '
        f'fill="none" stroke="{EDGE}" stroke-opacity=".85"/>',
    ]


def css_block() -> str:
    return """<style><![CDATA[
      @keyframes arise {0%{opacity:.02;transform:translateY(10px)} 100%{opacity:1;transform:translateY(0)}}
      @keyframes trace {0%{stroke-dashoffset:700;opacity:.2} 100%{stroke-dashoffset:0;opacity:1}}
      @keyframes glimmer {0%,100%{opacity:.32} 50%{opacity:.82}}
      @keyframes growline {0%{transform:scaleX(.08)}100%{transform:scaleX(1)}}
      @keyframes drift {0%{transform:translateX(-18px)}100%{transform:translateX(18px)}}
      .appear {animation:arise .82s ease-out both}
      .appear-late {animation:arise 1s .22s ease-out both}
      .trace {stroke-dasharray:700;animation:trace 1.6s .25s ease-out both}
      .glow {animation:glimmer 3.2s ease-in-out infinite}
      .grow {transform-origin:left center;transform-box:fill-box;animation:growline 1.4s .16s ease-out both}
      .float {animation:drift 8s ease-in-out infinite alternate}
      @media(prefers-reduced-motion:reduce){*{animation:none!important}}
    ]]></style>"""


def validate(svg: str) -> str:
    ET.fromstring(svg)
    return svg.rstrip() + "\n"


def make_action_svg(entry) -> str:
    key, title, caption, _, kicker = entry
    w, h = 305, 116
    p = shell(w, h, f"{title}: {caption}")
    p.append(css_block())
    p.extend([
        f'<path d="M1 83 H304" stroke="{EDGE}" opacity=".62"/>',
        f'<rect x="20" y="20" width="26" height="2" rx="1" fill="{MINT}" class="glow"/>',
        tag(58, 27, kicker, 10, DIM, 700, 1.0),
        tag(21, 65, title, 21 if len(title) <= 14 else 18, WHITE, 700, .35),
        tag(21, 102, caption, 11, PALE, 500, .45),
        f'<circle cx="279" cy="56" r="16" fill="{PANEL}" stroke="{EDGE}"/>',
        tag(279, 63, "↗" if key not in ("work",) else "↓", 22, MINT, 650, anchor="middle"),
        '<path d="M27 6 H120" fill="none" class="trace" stroke="#C2ECD1" stroke-opacity=".38"/>',
        '</svg>'
    ])
    return validate("\n".join(p))


def make_audit_svg(entry) -> str:
    key, title, desc, _, kicker = entry
    w, h = 610, 145
    p = shell(w, h, f"{title}. {desc}")
    p.append(css_block())
    p.extend([
        f'<rect x="0" y="0" width="6" height="{h}" rx="3" fill="{MINT}" opacity=".75"/>',
        f'<path d="M22 37 H585" stroke="{EDGE}" stroke-opacity=".45"/>',
        tag(26, 28, kicker, 12, MINT, 700, 1.35),
        tag(25, 83, title, 27, WHITE, 700, .35),
        tag(26, 119, desc, 15, PALE),
        f'<circle cx="558" cy="86" r="24" fill="{PANEL}" stroke="{EDGE}"/>',
        tag(558, 95, "↗", 27, MINT, 550, anchor="middle"),
        f'<path class="trace" d="M0 143 H600" fill="none" stroke="{MINT}" stroke-width="2" stroke-opacity=".6"/>',
        "</svg>",
    ])
    return validate("\n".join(p))


def project_duration(record: dict) -> tuple[str, str, str]:
    a, b = record.get("first_commit"), record.get("last_commit")
    if not a or not b:
        return "—", "UNAVAILABLE", "UNAVAILABLE"
    try:
        d0, d1 = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
    except ValueError:
        return "—", "UNAVAILABLE", "UNAVAILABLE"
    if d1 < d0:
        return "—", "INVALID DATES", "INVALID DATES"
    days = (d1 - d0).days
    return f"{days:,}D", d0.strftime("%d %b %Y").upper(), d1.strftime("%d %b %Y").upper()


def project_svg(spec: dict, record: dict | None, legacy_snapshot: bool = False) -> str:
    w, h = 660, 337
    m = (record or {}).get("metrics") or {}
    first = (record or {}).get("first_commit")
    last = (record or {}).get("last_commit")
    duration, begin, end = project_duration(record or {})
    commits = fmt(m.get("commits")) if record and record.get("status") == "ok" else "—"
    loc = fmt(m.get("code_lines_changed")) if record and record.get("status") == "ok" else "—"
    title = spec["title"]
    name_size = 30 if len(title) <= 26 else (27 if len(title) <= 31 else 25)
    p = shell(w, h, f"{title}: {commits} qualified commits, {loc} strict code-changed lines, {duration} between first and last qualifying commits")
    p.append(css_block())
    p.extend([
        f'<rect x="18" y="18" width="624" height="301" rx="12" fill="{PANEL}" fill-opacity=".5"/>',
        f'<path d="M24 166 H635" stroke="{EDGE}" stroke-opacity=".8"/>',
        f'<path d="M24 279 H635" stroke="{EDGE}" stroke-opacity=".8"/>',
        tag(28, 44, spec["kind"], 12, MINT, 700, 1.2),
        tag(629, 44, "RECHECK REQUIRED" if legacy_snapshot else "VIEW SOURCE  ↗", 11, PALE, 700, .8, "end"),
        tag(28, 85, title, name_size, WHITE, 700, -.2),
        tag(29, 119, spec["description"][0], 16, PALE),
        tag(29, 145, spec["description"][1], 16, PALE),
    ])
    values = [
        (29, "ATTRIBUTED COMMITS", commits, 40),
        (253, "STRICT CODE Δ", loc, 37),
        (491, "COMMIT SPAN", duration, 38),
    ]
    for x, label, number, size in values:
        p.extend([
            tag(x, 191, label, 11, DIM, 700, 1.1),
            f'<g class="appear-late">{tag(x, 244, number, size, WHITE if x != 253 else MINT, 700)}</g>',
        ])
    p.extend([
        tag(29, 306, f"{begin} → {end}", 12, PALE, 600, .2),
        tag(632, 306, spec["tags"], 11, DIM, 650, .25, "end"),
        f'<path d="M29 266 H634" stroke="{MINT}" stroke-opacity=".22" stroke-width="2" class="trace"/>',
        '</svg>'
    ])
    return validate("\n".join(p))


def clickable(src: str, href: str, alt: str) -> str:
    # All destinations are authored constants; no arbitrary URLs from metadata.
    return (
        f'<a href="{escape(href)}">'
        f'<img src="./assets/{escape(src)}" width="100%" alt="{escape(alt)}" />'
        f'</a>'
    )


def grid(items: list[str], cols: int = 2) -> str:
    rows = ["<table>"]
    for j in range(0, len(items), cols):
        rows.append("<tr>")
        for item in items[j:j+cols]:
            rows.append(f'<td width="{100//cols}%" valign="top" align="center">{item}</td>')
        rows.append("</tr>")
    rows.append("</table>")
    return "\n".join(rows)


def marked(text: str, name: str, replacement: str) -> str:
    first, last = f"<!-- {name}:START -->", f"<!-- {name}:END -->"
    if text.count(first) != 1 or text.count(last) != 1:
        raise ValueError(f"README must contain exactly one pair of {name} markers")
    a, b = text.index(first), text.index(last)
    if b <= a:
        raise ValueError(f"{name} end marker appears before start marker")
    return text[:a] + first + "\n\n" + replacement.strip() + "\n\n" + text[b:]


def project_markup(spec: dict, record: dict | None, legacy_snapshot: bool = False) -> str:
    metrics = (record or {}).get("metrics") or {}
    duration, begin, end = project_duration(record or {})
    since = "—" if begin == "UNAVAILABLE" else begin
    until = "—" if end == "UNAVAILABLE" else end
    accessible = bool(record and not record.get("private") and record.get("status") == "ok")
    title = escape(spec["title"])
    if not accessible:
        # Never fabricate a metric for a missing/unscanned repo.
        details = "Project metrics unavailable from the latest scan."
    else:
        details = (
            f'<strong>Attributed author/coauthor commits:</strong> {fmt(metrics.get("commits"))}. '
            f'<strong>Provisional Christo-pattern commits:</strong> {fmt(metrics.get("name_only_attributed", 0))}. '
            f'<strong>Code-classified text lines changed:</strong> {fmt(metrics.get("code_lines_changed"))}. '
            f'<strong>All changed text lines:</strong> {fmt(metrics.get("lines_changed"))}. '
            f'<strong>First / latest qualifying author dates:</strong> {since} / {until}. '
            f'<strong>Calendar span:</strong> {duration} (not total days worked). '
            'Metrics represent attributed Git history from available repository refs. '
            'Code LOC is additions + deletions, not unique authored source. '
            + ('IMPORTANT: these figures come from a previous attribution rule; '
               'rerun the workflow to recalculate using the Christo/fork policy.'
               if legacy_snapshot else
               'Email-verified matches and provisional Christo-name matches '
               'are distinguished in the lifetime report.')
        )
    card = clickable(f'feature-{spec["id"]}.svg',
                     'https://github.com/' + spec["repo"],
                     f'Open {title} repository and view attributed commit metrics')
    disclosure = (
        f'<details><summary>▸ Contribution evidence / {title}</summary>'
        f'<p>{details}</p>'
        '</details>'
    )
    return card + "\n" + disclosure


def add_animation(svg: str) -> str:
    if "premium-count-motion" in svg:
        return svg
    style = """<style><![CDATA[
      /* premium-count-motion: progressive enhancement with static numeric fallback */
      @keyframes cover {0%,7%,78%{opacity:1}100%{opacity:0}}
      @keyframes count0 {0%,23%{opacity:1}24%,100%{opacity:0}}
      @keyframes count1 {0%,23%{opacity:0}24%,48%{opacity:1}49%,100%{opacity:0}}
      @keyframes count2 {0%,48%{opacity:0}49%,73%{opacity:1}74%,100%{opacity:0}}
      @keyframes count3 {0%,73%{opacity:0}74%,95%{opacity:1}96%,100%{opacity:0}}
      @keyframes arrive {from{opacity:.2;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
      .counter-veil{opacity:0;animation:cover 1.6s .15s ease-out 1 both}
      .st0,.st1,.st2,.st3{opacity:0}
      .st0{animation:count0 1.6s .15s steps(1,end) 1}
      .st1{animation:count1 1.6s .15s steps(1,end) 1}
      .st2{animation:count2 1.6s .15s steps(1,end) 1}
      .st3{animation:count3 1.6s .15s steps(1,end) 1}
      @media(prefers-reduced-motion:reduce){*{animation:none!important}.counter-veil{opacity:0!important}}
    ]]></style>"""
    if "</svg>" not in svg:
        raise ValueError("Statistics SVG is not a valid SVG document")
    # The original stat SVG has 4 numeric-value <text> elements at y=185.
    value_tags = re.findall(
        r'<text x="(\d+)" y="185"[^>]*font-size="(\d+)"[^>]*>([\d,]+)</text>',
        svg
    )
    # Note that xtext() emits font-size after x/y and an ordered set of props.
    # No silent "animated" label when the source layout changes.
    if len(value_tags) != 4:
        raise ValueError("Expected exactly four numeric stats for counter animation")
    overlay = []
    for x_str, size_str, value_str in value_tags:
        x, size = int(x_str), int(size_str)
        value = int(value_str.replace(",", ""))
        seq = [round(value * factor) for factor in (.07, .28, .57, .81)]
        overlay.append(
            f'<g class="counter-veil">'
            f'<rect x="{x-3}" y="132" width="258" height="67" rx="4" fill="{INK}"/>'
            + "".join(f'<g class="st{i}">{tag(x,185,fmt(n),size,WHITE,700)}</g>' for i,n in enumerate(seq))
            + '</g>'
        )
    svg = svg.replace("</svg>", style + "\n" + "\n".join(overlay) + "\n</svg>", 1)
    return validate(svg)


def animated_language(svg: str) -> str:
    if "premium-language-motion" in svg:
        return svg
    svg = svg.replace(
        "</svg>",
        """<style><![CDATA[
         /* premium-language-motion: bars show final value when animations are unsupported */
         @keyframes unfold{from{transform:scaleX(.04)}to{transform:scaleX(1)}}
         @keyframes fadebar{from{opacity:.45}to{opacity:1}}
         .live-bar{transform-origin:left center;transform-box:fill-box;
                   animation:unfold 1.65s .25s ease-out both}
         .live-percent{animation:fadebar 1.65s .2s ease-out both}
         @media(prefers-reduced-motion:reduce){*{animation:none!important}}
        ]]></style></svg>""",
        1
    )
    svg, n = re.subn(r'(<rect x="270"[^>]+fill="#C2ECD1")',
                     r'\1 class="live-bar"', svg)
    if n < 3:
        raise ValueError("Language chart shape changed: no animated bars found")
    return validate(svg)


def main() -> None:
    if not DATA.is_file():
        raise ValueError("Strict audit JSON missing")
    data = json.loads(DATA.read_text(encoding="utf-8"))
    if data.get("schema_version") != 2 or data.get("coverage") not in (
        "partial", "complete_for_enumerated_repos"
    ):
        raise ValueError("Cannot publish from an unverified or invalidated audit")
    if data.get("repositories_scanned", 0) < 1:
        raise ValueError("No repositories were scanned")
    repos = {r["name"]: r for r in data.get("repositories", [])
             if isinstance(r, dict) and not r.get("private")}
    legacy_snapshot = data.get("identity_policy_version") != 3
    content = README.read_text(encoding="utf-8")
    # Validate all boundaries before modifying any files.
    for label in ("PREMIUM_ACTIONS", "PREMIUM_PROJECTS", "PREMIUM_FOOTER"):
        if content.count(f"<!-- {label}:START -->") != 1 or content.count(f"<!-- {label}:END -->") != 1:
            raise ValueError("Missing required static profile section: " + label)
    if content.count("<!-- PROFILE_STATS:START -->") != 1:
        raise ValueError("Run render_profile_dashboard.py before the interactive layer")
    if "Full methodology &amp; audit" not in content and "<!-- PREMIUM_AUDIT_NAV:START -->" not in content:
        raise ValueError("Missing expected audit link navigation placeholder")

    ASSETS.mkdir(parents=True, exist_ok=True)
    for entry in ACTIONS:
        (ASSETS / f"action-{entry[0]}.svg").write_text(make_action_svg(entry), encoding="utf-8")
    for entry in AUDIT_LINKS:
        (ASSETS / f"audit-{entry[0]}.svg").write_text(make_audit_svg(entry), encoding="utf-8")
    for spec in PROJECTS:
        (ASSETS / f'feature-{spec["id"]}.svg').write_text(
            project_svg(spec, repos.get(spec["repo"]), legacy_snapshot=legacy_snapshot), encoding="utf-8")

    chart = ASSETS / "lifetime-engineering.svg"
    lang = ASSETS / "language-landscape.svg"
    chart.write_text(add_animation(chart.read_text(encoding="utf-8")), encoding="utf-8")
    lang.write_text(animated_language(lang.read_text(encoding="utf-8")), encoding="utf-8")

    nav = grid([
        clickable(f"action-{item[0]}.svg", item[3], item[1] + " / " + item[2])
        for item in ACTIONS
    ], cols=4)
    content = marked(content, "PREMIUM_ACTIONS", nav)
    pairs = []
    for spec in PROJECTS:
        pairs.append(project_markup(spec, repos.get(spec["repo"]), legacy_snapshot=legacy_snapshot))
    content = marked(content, "PREMIUM_PROJECTS", grid(pairs, cols=2))
    content = marked(content, "PREMIUM_FOOTER", grid([
        clickable("action-portfolio.svg", ACTIONS[0][3], "Visit portfolio"),
        clickable("action-email.svg", ACTIONS[3][3], "Contact by email"),
        clickable("audit-audit.svg", AUDIT_LINKS[0][3], "Open lifetime Git audit")
    ], cols=3))

    audit_nav = grid([
        clickable(f"audit-{item[0]}.svg", item[3], item[1] + " / " + item[2])
        for item in AUDIT_LINKS
    ], cols=2)
    audit_markup = (
        "<!-- PREMIUM_AUDIT_NAV:START -->\n\n"
        + audit_nav +
        "\n\n<!-- PREMIUM_AUDIT_NAV:END -->"
    )
    if "<!-- PREMIUM_AUDIT_NAV:START -->" in content:
        content = marked(content, "PREMIUM_AUDIT_NAV", audit_nav)
    else:
        # Replace the renderer's generic blue Markdown links in stats.
        content, replacements = re.subn(
            r"(?m)^\[Full methodology &amp; audit\].*$",
            lambda _: audit_markup, content, count=1
        )
        if replacements != 1:
            raise ValueError("Could not replace generic audit Markdown links")
    if re.search(r"(?m)^\[[^]]+\]\([^)]+\)", content):
        raise ValueError("Detected an unexpected plain Markdown link in README")

    README.write_text(content, encoding="utf-8")
    print("Premium interactive README refreshed:", len(PROJECTS),
          "project cards, 4 action tiles, 4 audit tiles; motion is progressive SVG.", flush=True)


if __name__ == "__main__":
    main()
