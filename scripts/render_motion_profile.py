#!/usr/bin/env python3
"""Render a GitHub-compatible motion-first engineering profile.

GitHub's README sandbox does not execute JavaScript. Animated GIFs provide actual
pixel animation on GitHub, unlike the previous CSS-only animated SVGs. Navigation
remains native linked <a><img></a>; disclosure uses GitHub-native <details>.
Only strict identity policy v3 JSON is accepted. No guessed contribution data.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import math
import os
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(".")
DATA = ROOT / "docs/github-audit/audit.json"
README = ROOT / "README.md"
ASSETS = ROOT / "assets"
W = 1200
BG = (11, 18, 20)
PANEL = (16, 27, 28)
INK = (236, 242, 237)
MUTED = (153, 177, 166)
QUIET = (102, 128, 119)
MINT = (188, 244, 207)
BORDER = (52, 74, 69)
DARK_MINT = (49, 92, 74)
FRAMES = max(5, min(35, int(os.getenv("PROFILE_MOTION_FRAMES", "23"))))
PAUSE_MS = max(250, int(os.getenv("PROFILE_MOTION_PAUSE_MS", "2600")))
FONTS = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
)
BOLDS = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
)


def font(size: int, bold: bool = False):
    for path in (BOLDS if bold else FONTS):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def text(draw: ImageDraw.ImageDraw, x: int, y: int, value,
         size: int = 21, color=INK, bold=False, spacing=0) -> None:
    value = str(value)
    ft = font(size, bold)
    if not spacing:
        draw.text((x, y), value, font=ft, fill=color, anchor="lt")
        return
    offset = x
    for ch in value:
        draw.text((round(offset), y), ch, font=ft, fill=color, anchor="lt")
        offset += draw.textlength(ch, font=ft) + spacing


def fmt(value: int) -> str:
    return f"{max(0, int(value)):,}"


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def count(value: int, t: float) -> str:
    return fmt(round(int(value) * ease(t)))


def init_frame(width, height, edition: str, step: float) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGB", (width, height), BG)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((1, 1, width-2, height-2), radius=12, outline=BORDER, width=2)
    # Architectural rule lines, not a generic glowing/neon texture.
    d.line((36, 60, width-36, 60), fill=BORDER, width=1)
    d.line((36, height-40, width-36, height-40), fill=BORDER, width=1)
    d.ellipse((40, 29, 47, 36), fill=MINT)
    text(d, 60, 25, edition, 13, INK, True, 2)
    # A single running indicator is deliberately subtle.
    phase = round((width-76) * step)
    d.rounded_rectangle((37, height-41, 37+phase, height-38),
                        radius=1, fill=DARK_MINT)
    return im, d


def save_motion(name: str, painter) -> None:
    frames: list[Image.Image] = []
    for i in range(FRAMES):
        t = i / (FRAMES-1)
        img = painter(ease(t), i, FRAMES)
        # Adaptive 96-color palette keeps animation downloads small.
        frames.append(img.quantize(colors=96, method=Image.Quantize.MEDIANCUT,
                                   dither=Image.Dither.NONE))
    durations = [66] * (FRAMES - 1) + [PAUSE_MS]
    ASSETS.mkdir(parents=True, exist_ok=True)
    dest = ASSETS / name
    frames[0].save(dest, format="GIF", save_all=True,
                   append_images=frames[1:], optimize=True, duration=durations,
                   loop=0, disposal=2)
    with Image.open(dest) as opened:
        if opened.format != "GIF" or getattr(opened, "n_frames", 1) < 5:
            raise RuntimeError(f"{name} did not encode as an animated GIF")
    print(f"GIF: {name} ({dest.stat().st_size // 1024} KB)")


def hero(t, _index, _total):
    im, d = init_frame(W, 362, "CHRISTO JOHN   /   AI PRODUCT ENGINEER", t)
    text(d, 945, 29, "INDEPENDENT BUILDER", 12, MUTED, True, 1)
    a = "Product thinking."
    b = "Production engineering."
    a = a[:round(len(a) * min(1, t * 1.65))]
    b = b[:round(len(b) * max(0, min(1, (t-.26) * 1.45)))]
    text(d, 44, 104, a, 71, INK, True)
    text(d, 44, 197, b, 64, MINT, True)
    # Typing cursor moves with final displayed line.
    active = b if t >= .26 else a
    base_x, baseline = (44, 197) if t >= .26 else (44, 104)
    d.rectangle((base_x + round(d.textlength(active, font=font(64 if t >= .26 else 71, True))) + 8,
                 baseline + 7, base_x + round(d.textlength(active, font=font(64 if t >= .26 else 71, True))) + 12,
                 baseline + 73), fill=MINT if t >= .26 else INK)
    text(d, 44, 314, "DESIGN     /     BUILD     /     AUTOMATE     /     SHIP",
         14, MUTED, True, 2)
    return im


def engineering(data: dict):
    unique, total = data["unique_attributed_sha_summary"], data["summary"]
    columns = [
        ("REPOSITORIES", int(data["repositories_scanned"]), "Complete scanned histories"),
        ("ATTRIBUTED COMMITS", int(unique["commits"]), "Unique Git SHAs, across forks"),
        ("CODE LINES CHANGED", int(unique["code_lines_changed"]), "Cumulative additions + deletions"),
        ("AI-ASSISTED", int(total["agent_assisted"]), "Your commits with agent metadata"),
    ]
    label = "PARTIAL COVERAGE" if data["coverage"] == "partial" else "ENUMERATED SOURCES COMPLETE"
    if data.get("name_only_attributed_commits", 0):
        label = "PARTIAL / PROVISIONAL ATTRIBUTION"
    def render(t, _index, _total):
        im, d = init_frame(W, 304, "ENGINEERING RECORD   /   LIFETIME", t)
        text(d, 1000, 29, label, 11, MUTED, True)
        for i, (heading, value, subtitle) in enumerate(columns):
            x = 41 + 292*i
            if i:
                d.line((x-14, 83, x-14, 235), fill=BORDER, width=1)
            text(d, x, 95, heading, 13, MUTED, True, 1)
            size = 47 if len(fmt(value)) <= 7 else 38
            text(d, x, 136, count(value, t), size, MINT if i == 1 else INK, True)
            text(d, x, 206, subtitle, 12, QUIET)
        date = dt.datetime.fromisoformat(data["run_at_utc"].replace("Z","+00:00"))
        text(d, 41, 267, f"UPDATED {date.strftime('%d %b %Y  /  %H:%M UTC').upper()}", 12, MUTED, True)
        return im
    return render


def languages(data: dict):
    values = [(str(k), int(v)) for k, v in (data.get("current_language_bytes") or {}).items()
              if type(v) is int and v > 0]
    values.sort(key=lambda z:-z[1])
    values = values[:5]
    if not values:
        raise ValueError("No GitHub Linguist data for language animation")
    maximum = values[0][1]
    total_bytes = sum(v for v in (data.get("current_language_bytes") or {}).values()
                      if type(v) is int and v > 0)
    def render(t, _index, _total):
        im, d = init_frame(W, 384, "LANGUAGE LANDSCAPE   /   CURRENT SOURCE FOOTPRINT", t)
        text(d, 910, 29, "GITHUB LINGUIST / ALL AUTHORS", 12, MUTED, True)
        for i, (name, amount) in enumerate(values):
            y = 98 + 50*i
            text(d, 41, y, name, 20, INK, True)
            d.rounded_rectangle((285, y+3, 1010, y+18), radius=7, fill=BORDER)
            width = max(2, round(725 * (amount / maximum) * t))
            d.rounded_rectangle((285, y+3, 285+width, y+18), radius=7, fill=MINT)
            text(d, 1046, y, f"{amount*100/total_bytes:.1f}%", 19, INK, True)
        text(d, 41, 348,
             "DEFAULT-BRANCH BYTES, INCLUDING OTHER CONTRIBUTORS. NOT YOUR PERSONAL HISTORICAL LOC.",
             12, QUIET, True)
        return im
    return render


def span_days(repo: dict) -> tuple[str, str]:
    start, end = repo.get("first_commit"), repo.get("last_commit")
    if not start or not end:
        return "—", "UNAVAILABLE"
    try:
        first, last = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    except ValueError:
        return "—", "UNAVAILABLE"
    if last < first:
        return "—", "INVALID DATE"
    return f"{(last-first).days}D", f"{first.strftime('%b %Y').upper()} — {last.strftime('%b %Y').upper()}"


def project(spec: dict, repo: dict | None):
    title = spec["title"]
    stats = (repo or {}).get("metrics") or {}
    qualified = bool(repo and repo.get("status") == "ok" and not repo.get("private"))
    commits = int(stats.get("commits", 0)) if qualified else 0
    lines = int(stats.get("code_lines_changed", 0)) if qualified else 0
    duration, dates = span_days(repo or {})
    months = sorted(((str(k), int(v.get("commits", 0)))
                     for k,v in (repo or {}).get("months", {}).items()))
    month_values = [n for _,n in months[-9:]]
    max_month = max(month_values or [1])
    def render(t, _index, _total):
        im, d = init_frame(770, 345, spec["kind"], t)
        text(d, 620, 27, "OPEN PROJECT   ↗", 12, MINT, True)
        size = 32 if len(title) < 32 else 26
        text(d, 39, 87, title, size, INK, True)
        text(d, 39, 146, spec["description"][0], 16, MUTED)
        text(d, 39, 170, spec["description"][1], 16, MUTED)
        d.line((38, 214, 730, 214), fill=BORDER)
        for i, (head, value) in enumerate([
            ("YOUR COMMITS", count(commits,t) if qualified else "—"),
            ("CODE LINES  Δ", count(lines,t) if qualified else "—"),
            ("COMMIT SPAN", duration if qualified else "—"),
        ]):
            x = 38 + i*241
            if i:
                d.line((x-13, 236, x-13, 299), fill=BORDER)
            text(d, x, 237, head, 12, MUTED, True, 1)
            text(d, x, 263, value, 30 if len(value) < 9 else 24,
                 MINT if i == 1 else INK, True)
        text(d, 39, 313, dates if qualified else "AUDIT DATA UNAVAILABLE", 11, QUIET, True, 1)
        if month_values:
            offset = 570
            for i, amount in enumerate(month_values[-9:]):
                height = max(2, round(26 * amount/max_month * t))
                x=offset+i*17
                d.rectangle((x, 203-height, x+7, 203), fill=DARK_MINT)
        return im
    return render


def xmltext(x, y, value, size, fill="#EAF3ED", weight=500, spacing=0, anchor=None):
    extra = (f' letter-spacing="{spacing}"' if spacing else "")
    extra += (f' text-anchor="{anchor}"' if anchor else "")
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" '
            f'font-family="DejaVu Sans, Arial, sans-serif" font-weight="{weight}"'
            f'{extra}>{escape(str(value))}</text>')


def navigation_svg(index: int, name: str, caption: str, target: str, broad: bool):
    # Editorial index panel rather than the previous faux-button graphics.
    width, height = (584, 138) if broad else (584, 132)
    title_size = 30 if len(name) <= 18 else 23
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{escape(name + ": " + caption)}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="5" fill="#101A1B"/>',
        f'<path d="M1 1 H{width-1} V{height-1} H1 Z" fill="none" stroke="#3F554E"/>',
        f'<path d="M25 22 H{width-25}" stroke="#3F554E"/>',
        f'<path d="M25 {height-23} H{width-25}" stroke="#3F554E" opacity=".65"/>',
        f'<rect x="1" y="1" width="5" height="{height-2}" fill="#BCEFCF"/>',
        xmltext(25, 17, f"{index:02d}  /  {target}", 11, "#BCEFCF", 700, 1.5),
        xmltext(25, 76, name, title_size, "#F1F6F0", 700),
        xmltext(27, height-35, caption, 13, "#A2BBB0", 450),
        f'<circle cx="{width-49}" cy="75" r="24" fill="none" stroke="#5F8775"/>',
        xmltext(width-49, 84, "↗", 25, "#BCEFCF", 500, anchor="middle"),
        "</svg>",
    ]
    result="\n".join(lines)+"\n"
    ET.fromstring(result)
    return result


def rewrite(content: str, original: str, replacement: str) -> str:
    if original not in content:
        raise ValueError(f"README is missing required path {original}")
    return content.replace(original, replacement)


def replace_section(s: str, key: str, inner: str) -> str:
    a, b=f"<!-- {key}:START -->",f"<!-- {key}:END -->"
    if s.count(a)!=1 or s.count(b)!=1 or s.index(b)<s.index(a):
        raise ValueError(f"Missing or duplicated README markers: {key}")
    start=s.index(a)+len(a)
    end=s.index(b)
    return s[:start]+"\n\n"+inner.strip()+"\n\n"+s[end:]


def image_link(path: str, url: str, label: str) -> str:
    return f'<a href="{html.escape(url,quote=True)}"><img src="./assets/{path}" width="100%" alt="{html.escape(label,quote=True)}" /></a>'


def grid(items, columns: int):
    out=["<table>"]
    for i in range(0,len(items),columns):
        out.append("<tr>")
        for item in items[i:i+columns]:
            out.append(f'<td width="{100//columns}%" valign="top">{item}</td>')
        out.append("</tr>")
    out.append("</table>")
    return "\n".join(out)


def make_nav(assets, prefix, columns=2):
    for i,(key,name,caption,url,kicker) in enumerate(assets):
        (ASSETS/f"{prefix}-{key}.svg").write_text(
            navigation_svg(i+1,name,caption,kicker,prefix=="audit"),encoding="utf-8")
    return grid([image_link(f"{prefix}-{key}.svg",url,f"{name}: {caption}")
                 for key,name,caption,url,kicker in assets], columns)


def run() -> None:
    import render_interactive_profile as profile
    data=json.loads(DATA.read_text(encoding="utf-8"))
    if data.get("identity_policy_version")!=3 or data.get("schema_version")!=2:
        raise ValueError("Only fresh Christo attribution policy-v3 audit data can animate")
    repos={r["name"]:r for r in data.get("repositories",[]) if not r.get("private")}
    original=README.read_text(encoding="utf-8")
    if "PROFILE_STATS:START" not in original:
        raise ValueError("Expected refreshed profile")
    ASSETS.mkdir(exist_ok=True)
    save_motion("profile-motion.gif",hero)
    save_motion("engineering-motion.gif",engineering(data))
    save_motion("languages-motion.gif",languages(data))
    for spec in profile.PROJECTS:
        save_motion(f'feature-{spec["id"]}-motion.gif',project(spec,repos.get(spec["repo"])))
    actions=make_nav(profile.ACTIONS,"action")
    docs=make_nav(profile.AUDIT_LINKS,"audit")
    s=original
    s=replace_section(s,"PREMIUM_ACTIONS",actions)
    s=replace_section(s,"PREMIUM_AUDIT_NAV",docs)
    footer=grid([
        image_link("action-portfolio.svg",profile.ACTIONS[0][3],"Portfolio"),
        image_link("action-email.svg",profile.ACTIONS[3][3],"Contact"),
        image_link("audit-audit.svg",profile.AUDIT_LINKS[0][3],"Full audit"),
    ],3)
    s=replace_section(s,"PREMIUM_FOOTER",footer)
    for a,b in [
        ("profile-cover.svg","profile-motion.gif"),
        ("lifetime-engineering.svg","engineering-motion.gif"),
        ("language-landscape.svg","languages-motion.gif"),
    ]:
        s=rewrite(s,a,b)
    for spec in profile.PROJECTS:
        s=rewrite(s,f'feature-{spec["id"]}.svg',f'feature-{spec["id"]}-motion.gif')
    # Drop obsolete preview warning after the validated, current audit is used.
    s=s.replace(
        "<strong>Project cards currently show PREVIOUS-SCAN numbers and require "
        "regeneration under identity policy v3. They are visual previews, not final totals.</strong>",
        "<sub>Project cards use the latest verified-identity audit. Commits may contain "
        "agent-assisted work; cumulative changed code lines are not distinct authored lines.</sub>")
    # Keep disclosures as real interactive GitHub controls.
    if "<details>" not in s or s.count("feature-") < 4:
        raise RuntimeError("Project disclosures missing")
    README.write_text(s,encoding="utf-8")
    print("Motion profile generated: hero, counters, language bars, four project card animations; "
          "navigation rebuilt with editorial links.",flush=True)


if __name__=="__main__":
    run()
