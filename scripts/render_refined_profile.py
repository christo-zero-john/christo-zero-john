#!/usr/bin/env python3
"""Editorial GitHub profile: precise, motion-free, readable in every GitHub client.

SVG assets are static and resolution-independent. All numbers come from the
latest strictly attributed GitHub audit, not guesses or inherited fork history.
GitHub's profile README cannot execute JS, stylesheets, or web-app interactions.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

ROOT = Path(os.getenv("PROFILE_REPO_ROOT", "."))
ASSETS = ROOT / "assets"
README = ROOT / "README.md"
DATA = ROOT / "docs/github-audit/audit.json"

BG = "#0D1415"
EDGE = "#31403D"
PAPER = "#F3F2EB"
SECONDARY = "#B5C1B9"
MUTED = "#87988F"
ACCENT = "#BEDBC8"
ACCENT_DARK = "#7DADA0"
FONT = "Arial, Helvetica, sans-serif"

FEATURED = [
    ("photobooth", "christo-zero-john/virtual-background-photobooth",
     "Virtual Background Photobooth", "INTERACTIVE MEDIA",
     "Real-time background replacement · Remote shutter · Browser experience"),
    ("movie", "christo-zero-john/movie-watch-history-tracker-webapp",
     "Movie Watch History Tracker", "PRODUCT / FRONTEND",
     "A personal movie journal and discovery experience powered by TMDB"),
    ("complaints", "christo-zero-john/complaint-management-system",
     "Complaint Management System", "FULL-STACK / SYSTEMS",
     "Institutional issue reporting and management, built during undergraduate study"),
    ("roco", "christo-zero-john/roco-the-agentic-car",
     "ROCO / The Agentic Car", "HARDWARE / PROTOTYPING",
     "A hands-on 4WD robotics and agentic systems experiment"),
]

LINKS = [
    ("portfolio", "PORTFOLIO", "https://tesnic.vercel.app"),
    ("linkedin", "LINKEDIN", "https://www.linkedin.com/in/christo-john-kalapurackal/"),
    ("projects", "PROJECTS", "#selected-work"),
    ("contact", "CONTACT", "mailto:10.christojohn@gmail.com"),
]

AUDIT = [
    ("report", "AUDIT REPORT", "./docs/github-audit/REPORT.md"),
    ("repositories", "ALL REPOSITORIES", "./docs/github-audit/repositories.md"),
    ("languages", "LANGUAGE HISTORY", "./docs/github-audit/languages.md"),
    ("methodology", "METHODOLOGY", "./docs/github-audit/APPENDIX.md"),
]


def svg_text(x, y, string, size=18, color=PAPER, weight=400, spacing=0, anchor=None):
    extra = f' letter-spacing="{spacing}"' if spacing else ""
    if anchor:
        extra += f' text-anchor="{anchor}"'
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
            f'font-family="{FONT}" font-weight="{weight}"{extra}>'
            f'{escape(str(string))}</text>')


def svg_document(label, width, height, inner):
    # All values here are escaped; static SVG contains no script, animation, or remote image.
    result = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
              f'role="img" aria-label="{escape(label)}">\n'
              + f'<rect width="{width}" height="{height}" rx="9" fill="{BG}"/>\n'
              + "\n".join(inner) + "\n</svg>\n")
    ET.fromstring(result)
    return result


def hero():
    return svg_document("Christo John — AI Product Engineer", 1200, 280, [
        f'<rect x="1" y="1" width="1198" height="278" rx="8" fill="none" stroke="{EDGE}"/>',
        f'<rect x="44" y="38" width="27" height="3" rx="1" fill="{ACCENT}"/>',
        svg_text(86, 45, "AI PRODUCT ENGINEER", 15, SECONDARY, 700, 2),
        svg_text(1155, 45, "DESIGN  /  ENGINEER  /  SHIP", 12, MUTED, 600, 1, "end"),
        svg_text(44, 154, "Christo John", 83, PAPER, 700, -2.3),
        svg_text(48, 208, "I turn product ideas into engineered, production-ready experiences.", 22, SECONDARY),
        f'<line x1="48" y1="237" x2="1152" y2="237" stroke="{EDGE}"/>',
        svg_text(48, 260, "PRODUCT DESIGN", 11, ACCENT, 700, 1.3),
        svg_text(264, 260, "FULL-STACK ENGINEERING", 11, ACCENT, 700, 1.3),
        svg_text(587, 260, "APPLIED AI", 11, ACCENT, 700, 1.3),
        svg_text(1152, 260, "INDEPENDENT BUILDER", 11, MUTED, 600, 1.2, "end"),
    ])


def nav_svg(name, idx, footer=False):
    # Deliberately *not* an image button: a typographic navigation tab,
    # with no borders, colored box, gradient, icon circle, or faux UI styling.
    w, h = (246, 50) if not footer else (246, 43)
    return svg_document(name, w, h, [
        svg_text(8, 28 if not footer else 26, f"{idx:02d}", 11, MUTED, 700),
        svg_text(42, 29 if not footer else 27, name, 17, PAPER, 700, .3),
        svg_text(229, 29 if not footer else 27, "↗", 21, ACCENT, 700, anchor="end"),
        f'<line x1="8" y1="{h-4}" x2="238" y2="{h-4}" stroke="{EDGE}"/>',
    ])


def audit_svg(name, idx):
    return svg_document(name, 246, 50, [
        svg_text(8, 29, f"{idx:02d}", 11, ACCENT, 700),
        svg_text(42, 29, name, 15, PAPER, 700, .2),
        svg_text(231, 29, "↗", 20, ACCENT, 500, anchor="end"),
        f'<line x1="8" y1="46" x2="238" y2="46" stroke="{EDGE}"/>',
    ])


def number(n):
    return f"{int(n):,}"


def record_card(data):
    unique, summary = data["unique_attributed_sha_summary"], data["summary"]
    items = [
        ("REPOSITORIES", number(data["repositories_scanned"]), "accessible histories"),
        ("ATTRIBUTED COMMITS", number(unique["commits"]), "deduplicated Git SHAs"),
        ("CODE LINES CHANGED", number(unique["code_lines_changed"]), "historical additions + deletions"),
        ("AI-ASSISTED", number(summary["agent_assisted"]), "owner commits with agent metadata"),
    ]
    svg = [
        f'<rect x="1" y="1" width="1198" height="225" rx="8" fill="none" stroke="{EDGE}"/>',
        svg_text(43, 38, "THE ENGINEERING RECORD", 15, PAPER, 700, 1.8),
        svg_text(1155, 38, "ALL-TIME  /  VERIFIED IDENTITY POLICY", 11, MUTED, 600, 1, "end"),
        f'<line x1="44" y1="58" x2="1156" y2="58" stroke="{EDGE}"/>',
    ]
    for i, (name, value, note) in enumerate(items):
        x = 44 + i*287
        if i:
            svg.append(f'<line x1="{x-19}" y1="80" x2="{x-19}" y2="171" stroke="{EDGE}"/>')
        font_size = 47 if len(value) < 8 else 39
        svg.extend([
            svg_text(x, 99, name, 12, MUTED, 700, .5),
            svg_text(x, 150, value, font_size, ACCENT if i == 1 else PAPER, 700, -1),
            svg_text(x, 176, note, 12, SECONDARY),
        ])
    stamp = dt.datetime.fromisoformat(data["run_at_utc"].replace("Z", "+00:00"))
    status = "PARTIAL COVERAGE" if data["coverage"] == "partial" else "ENUMERATED REPOSITORIES COMPLETE"
    svg.extend([
        f'<line x1="43" y1="192" x2="1157" y2="192" stroke="{EDGE}"/>',
        svg_text(44, 213, stamp.strftime("UPDATED %d %b %Y  /  %H:%M UTC").upper(), 11, MUTED, 500, .3),
        svg_text(1153, 213, status, 11, ACCENT, 700, 1, "end"),
    ])
    return svg_document("Audited engineering record: repositories, commits, changed code lines, AI-assisted commits", 1200, 226, svg)


def language_band(data):
    raw = data.get("current_language_bytes") or {}
    ordered = sorted(((k,v) for k,v in raw.items() if type(v) is int and v > 0),
                     key=lambda p:-p[1])
    if not ordered:
        return svg_document("Language measurements unavailable", 1200, 120, [
            svg_text(43, 65, "Current language snapshot unavailable", 20)
        ])
    top = ordered[:5]
    total = sum(v for _,v in ordered)
    shares = [(k, v/total*100) for k,v in top]
    colors = ["#BAD9C4", "#91B9A8", "#6C9989", "#4F7B70", "#3B6059"]
    svg = [
        f'<rect x="1" y="1" width="1198" height="151" rx="8" fill="none" stroke="{EDGE}"/>',
        svg_text(43, 34, "LANGUAGE FOOTPRINT", 14, PAPER, 700, 1.3),
        svg_text(1154, 34, "CURRENT DEFAULT-BRANCH BYTES · ALL AUTHORS", 11, MUTED, 600, 1, "end"),
    ]
    x = 43
    for i, (_, pct) in enumerate(shares):
        width = round(1113*pct/100)
        svg.append(f'<rect x="{x}" y="54" width="{width}" height="12" fill="{colors[i]}"/>')
        x += width
    if x < 1155:
        svg.append(f'<rect x="{x}" y="54" width="{1155-x}" height="12" fill="{EDGE}"/>')
    for i, (name,pct) in enumerate(shares):
        x = 44 + 222*i
        svg.extend([
            f'<circle cx="{x+5}" cy="99" r="5" fill="{colors[i]}"/>',
            svg_text(x+19, 103, name, 16, PAPER, 600),
            svg_text(x+19, 124, f"{pct:.1f}%", 13, MUTED),
        ])
    return svg_document("Current language share across repositories, all authors not personal contributions",1200,152,svg)


def date_range(record):
    start,end=record.get("first_commit"),record.get("last_commit")
    if not start or not end:
        return "DATE UNAVAILABLE", "—"
    try:
        a,b=dt.date.fromisoformat(start),dt.date.fromisoformat(end)
    except ValueError:
        return "DATE UNAVAILABLE", "—"
    if b<a:
        return "DATE UNAVAILABLE","—"
    return f"{a.strftime('%b %Y').upper()}  —  {b.strftime('%b %Y').upper()}", f"{(b-a).days} days"


def project_svg(spec, record, idx):
    _,_,title,category,description=spec
    available=bool(record and record.get("status")=="ok" and not record.get("private"))
    m=record.get("metrics") or {} if record else {}
    dates,duration=date_range(record or {})
    commits=number(m["commits"]) if available else "—"
    code=number(m["code_lines_changed"]) if available else "—"
    if len(title) > 30:
        font_size=32
    else:
        font_size=39
    p=[
        f'<rect x="1" y="1" width="1198" height="194" rx="8" fill="none" stroke="{EDGE}"/>',
        svg_text(41, 37, f"0{idx}  /  {category}", 12, ACCENT, 700, 1.1),
        svg_text(1153, 36, "VIEW REPOSITORY  ↗", 12, ACCENT, 700, 1, "end"),
        svg_text(42, 94, title, font_size, PAPER, 700, -.6),
        svg_text(44, 126, description, 16, SECONDARY),
        svg_text(44, 169, dates, 12, MUTED, 600, .7),
        f'<line x1="620" y1="58" x2="620" y2="167" stroke="{EDGE}"/>',
    ]
    for j,(label,value) in enumerate([
        ("YOUR COMMITS", commits),
        ("CODE LINES CHANGED", code),
        ("COMMIT SPAN", duration),
    ]):
        x=645+j*174
        vsize=28 if len(value)<8 else 24
        p.append(svg_text(x, 81, label, 11, MUTED, 700, .3))
        p.append(svg_text(x, 123, value, vsize, PAPER if j!=1 else ACCENT, 700, -.4))
    return svg_document(f"{title} — {commits} attributed commits, {code} changed code lines",1200,195,p)


def anchor_image(asset, target, alt, width="100%"):
    return (f'<a href="{html.escape(target,quote=True)}">'
            f'<img src="./assets/{asset}" alt="{html.escape(alt,quote=True)}" '
            f'width="{width}" /></a>')


def horizontal_nav(rows, prefix):
    return ('<p align="center">\n' +
            '&nbsp;&nbsp;'.join(anchor_image(f"{prefix}-{key}.svg", dest, name, "23%")
                                   for key,name,dest in rows) +
            '\n</p>')


def produce(data):
    if data.get("schema_version")!=2 or data.get("identity_policy_version")!=3:
        raise ValueError("Current attribution policy v3 audit required; never publish legacy numbers")
    if data.get("coverage") not in ("partial","complete_for_enumerated_repos"):
        raise ValueError("Audit status not publishable")
    if data.get("repositories_scanned",0)<=0:
        raise ValueError("No valid scanned repository history")
    allrepos={r["name"]:r for r in data.get("repositories",[]) if not r.get("private")}
    ASSETS.mkdir(parents=True, exist_ok=True)
    files = {"profile-editorial.svg":hero(),
             "profile-engineering.svg":record_card(data),
             "profile-languages.svg":language_band(data)}
    for n,(key,name,dest) in enumerate(LINKS,1):
        files[f"link-{key}.svg"]=nav_svg(name,n)
    for n,(key,name,dest) in enumerate(AUDIT,1):
        files[f"doc-{key}.svg"]=audit_svg(name,n)
    blocks=[]
    for n,spec in enumerate(FEATURED,1):
        key,repo,name,category,description=spec
        record=allrepos.get(repo)
        files[f"project-{key}.svg"]=project_svg(spec,record,n)
        blocks.append('<p>'+anchor_image(f"project-{key}.svg","https://github.com/"+repo,
                                         f"Open {name} repository and review attributed statistics")+'</p>')
    for path,contents in files.items():
        (ASSETS/path).write_text(contents,encoding="utf-8")
    last=dt.datetime.fromisoformat(data["run_at_utc"].replace("Z","+00:00"))
    time=last.strftime("%d %b %Y / %H:%M UTC")
    coverage="Partial" if data["coverage"]=="partial" else "Complete for enumerated repositories"
    privacy="Private repository names are intentionally omitted from this public profile."
    verified = int(data.get("unique_attributed_sha_summary",{}).get("commits",0))-int(
        data.get("unique_attributed_sha_summary",{}).get("name_only_attributed",0))
    prose = f"""<!-- REFINED_PROFILE_V2 -->
<p align="center">
  <img src="./assets/profile-editorial.svg" alt="Christo John, AI Product Engineer" width="100%" />
</p>

{horizontal_nav(LINKS,"link")}

### Building with purpose.

I'm **Christo John**, an AI Product Engineer. I design interfaces, build full-stack systems, and put applied AI to work inside real products—from Figma and Next.js to Supabase, infrastructure, and automated workflows.

### The engineering record

<p>{anchor_image("profile-engineering.svg","./docs/github-audit/REPORT.md","Read the source-backed GitHub engineering report")}</p>

<sub>Last recalculated {time} · Coverage: {coverage}. {verified:,} exact-email attributed Git SHAs; any provisional Christo-name matches are disclosed in the audit. Code lines changed = cumulative additions + deletions in qualifying non-merge commits, not unique original code. All accessible remote refs are scanned. {privacy}</sub>

<p><img src="./assets/profile-languages.svg" alt="Current GitHub Linguist language bytes across all authors" width="100%" /></p>

{horizontal_nav(AUDIT,"doc")}

### Selected work

<sub>Public projects · Project figures reflect attributed Git history, not total upstream repository activity.</sub>

{chr(10).join(blocks)}

<details>
<summary><strong>How these project numbers are measured</strong></summary>

Commits are attributed using the account-linked Christo identity rules; unrelated upstream authors and standalone agents are excluded. Agent-assisted owner commits count once. Changed code lines include additions and deletions, not surviving source or work hours. The commit span is the calendar difference between first and last qualifying commit author dates—not time actively spent working. For detailed repository evidence and exclusions, open the linked audit using the navigation above.

</details>

### The toolkit

**Primary** · Next.js / Supabase / Figma / Claude Code / Codex

**Also working with** · TypeScript / React / Python / Django / PostgreSQL / Tailwind CSS / Docker / Vercel / AWS / Playwright

<sub>Technologies are self-reported experience; the language chart above is a current all-author repository snapshot.</sub>

---

<p align="center"><strong>Thoughtful interfaces. Serious engineering.</strong></p>

{horizontal_nav([LINKS[0],LINKS[1],LINKS[3]],"link")}

<sub>GitHub profile data regenerated from the strict lifetime audit. The layout intentionally uses static, accessible vector graphics; no flashing GIFs, fragile JavaScript, or decorative badges.</sub>
"""
    README.write_text(prose,encoding="utf-8")
    print("Refined, motion-free README generated from v3 audit:",time,"assets",len(files))


def main():
    produce(json.loads(DATA.read_text(encoding="utf-8")))


if __name__=="__main__":
    main()
