#!/usr/bin/env python3
"""Render the profile's live engineering record from the strict Git audit.

This script owns only the PROFILE_STATS markers in README.md and two small
self-contained SVG assets. It never changes the surrounding editorial layout.

Run *after* github_lifetime_audit.py and annotate_audit_markdown.py. A missing,
legacy, invalidated, or zero-coverage audit raises an error instead of publishing
guessed statistics. Includes the report's PARTIAL/COMPLETE coverage label.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

ROOT = Path(os.environ.get("PROFILE_REPO_ROOT", "."))
DATA = ROOT / "docs/github-audit/audit.json"
README = ROOT / "README.md"
ASSETS = ROOT / "assets"
OPEN = "<!-- PROFILE_STATS:START -->"
CLOSE = "<!-- PROFILE_STATS:END -->"
COLORS = {
    "bg": "#101416",
    "border": "#3C4848",
    "warm": "#F0F4EE",
    "secondary": "#A9B9B3",
    "muted": "#81918B",
    "accent": "#C2ECD1",
    "bar": "#556863",
}


def integer(obj: dict, key: str) -> int:
    value = obj.get(key)
    if type(value) is not int or value < 0:
        raise ValueError(f"Audit metric '{key}' is missing or invalid")
    return value


def load_audit() -> dict:
    if not DATA.is_file():
        raise ValueError("Cannot update profile: docs/github-audit/audit.json is missing")
    data = json.loads(DATA.read_text(encoding="utf-8"))
    if data.get("schema_version") != 2:
        raise ValueError("Profile stats require strict attribution schema_version=2")
    if data.get("coverage") not in ("partial", "complete_for_enumerated_repos"):
        raise ValueError("Profile stats cannot publish invalidated or unverified audit data")
    scanned = integer(data, "repositories_scanned")
    found = integer(data, "repositories_enumerated")
    if scanned == 0 or scanned > found:
        raise ValueError("No valid scanned repository inventory")
    metrics = data.get("summary")
    unique = data.get("unique_attributed_sha_summary")
    if not isinstance(metrics, dict) or not isinstance(unique, dict):
        raise ValueError("Strict audit summary is missing")
    if integer(unique, "commits") > integer(metrics, "commits"):
        raise ValueError("Unique commit count cannot exceed repo/SHA occurrence count")
    for key in ("code_lines_changed", "lines_changed"):
        if integer(unique, key) > integer(metrics, key):
            raise ValueError(f"Invalid deduplicated {key} total")
    integer(metrics, "agent_assisted")
    date = dt.datetime.fromisoformat(str(data["run_at_utc"]).replace("Z", "+00:00"))
    if date.tzinfo is None:
        raise ValueError("Audit timestamp must contain an explicit timezone")
    return data


def xtext(x: int, y: int, content: str, *, size=18, fill=None, weight=400,
          anchor=None, spacing=None, family=None) -> str:
    attrs = [
        f'x="{x}"', f'y="{y}"', f'font-size="{size}"',
        f'fill="{fill or COLORS["warm"]}"', f'font-weight="{weight}"',
        'font-family="' + (family or 'Inter, Segoe UI, Arial, sans-serif') + '"'
    ]
    if anchor:
        attrs.append(f'text-anchor="{anchor}"')
    if spacing is not None:
        attrs.append(f'letter-spacing="{spacing}"')
    return f'<text {" ".join(attrs)}>{escape(str(content))}</text>'


def format_int(n: int) -> str:
    return f"{n:,}"


def date_label(data: dict) -> str:
    when = dt.datetime.fromisoformat(data["run_at_utc"].replace("Z", "+00:00"))
    return when.astimezone(dt.timezone.utc).strftime("%d %b %Y · %H:%M UTC").upper()


def stat_svg(data: dict) -> str:
    unique, total = data["unique_attributed_sha_summary"], data["summary"]
    scanned = integer(data, "repositories_scanned")
    items = [
        ("REPOSITORIES SCANNED", format_int(scanned), "Accessible Git histories"),
        ("ATTRIBUTED GIT SHAs", format_int(integer(unique, "commits")), "Deduplicated across forks"),
        ("CODE LINES CHANGED", format_int(integer(unique, "code_lines_changed")), "Additions + deletions*"),
        ("AI-TAGGED COMMITS", format_int(integer(total, "agent_assisted")), "Repo/SHA occurrences†"),
    ]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 304" role="img" '
        'aria-label="Current lifetime engineering Git audit statistics">',
        f'<rect width="1200" height="304" rx="14" fill="{COLORS["bg"]}"/>',
        f'<rect x="1" y="1" width="1198" height="302" rx="13" fill="none" stroke="{COLORS["border"]}"/>',
        f'<line x1="38" y1="73" x2="1162" y2="73" stroke="{COLORS["border"]}"/>',
        f'<circle cx="48" cy="36" r="4" fill="{COLORS["accent"]}"/>',
        xtext(64, 42, "THE ENGINEERING RECORD", size=15, weight=700, spacing=2.2),
        xtext(1156, 42, "ALL-TIME / STRICT GIT ATTRIBUTION", size=12,
              fill=COLORS["secondary"], anchor="end", spacing=1.3),
    ]
    for i, (label, value, subtitle) in enumerate(items):
        x = 48 + 291 * i
        if i:
            parts.append(
                f'<line x1="{x - 21}" y1="102" x2="{x - 21}" y2="232" '
                f'stroke="{COLORS["border"]}"/>'
            )
        font_size = 56 if len(value) <= 6 else (46 if len(value) <= 8 else 40)
        parts.extend([
            xtext(x, 120, label, size=12, fill=COLORS["secondary"], weight=650, spacing=1.3),
            xtext(x, 185, value, size=font_size,
                  fill=COLORS["accent"] if i == 1 else COLORS["warm"], weight=700),
            xtext(x, 216, subtitle, size=13, fill=COLORS["muted"]),
        ])
    coverage = "PARTIAL COVERAGE" if data["coverage"] == "partial" else "ENUMERATED SOURCES COMPLETE"
    parts.extend([
        f'<line x1="38" y1="241" x2="1162" y2="241" stroke="{COLORS["border"]}"/>',
        xtext(48, 275, "REFRESHED " + date_label(data), size=12, fill=COLORS["muted"], spacing=.5),
        xtext(1152, 275, coverage, size=12, fill=COLORS["secondary"], anchor="end", spacing=1),
        '</svg>',
    ])
    svg = "\n".join(parts) + "\n"
    ET.fromstring(svg)
    return svg


def language_svg(data: dict) -> str:
    langs = data.get("current_language_bytes") or {}
    items = []
    for label, raw in langs.items():
        if isinstance(label, str) and type(raw) is int and raw > 0:
            items.append((label, raw))
    items.sort(key=lambda pair: pair[1], reverse=True)
    items = items[:5]
    if not items:
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 120">'
            '<rect width="1200" height="120" rx="14" fill="#101416"/>'
            '<text x="48" y="65" font-size="20" fill="#F0F4EE">'
            'Current language data unavailable</text></svg>\n'
        )
    peak = items[0][1]
    total = sum(v for v in langs.values() if type(v) is int and v > 0)
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 380" role="img" '
        'aria-label="Most prevalent current codebase languages across accessible repositories">',
        f'<rect width="1200" height="380" rx="14" fill="{COLORS["bg"]}"/>',
        f'<rect x="1" y="1" width="1198" height="378" rx="13" fill="none" stroke="{COLORS["border"]}"/>',
        xtext(48, 44, "LANGUAGE LANDSCAPE", size=16, spacing=1.8, weight=700),
        xtext(1153, 44, "CURRENT DEFAULT-BRANCH BYTES · ALL AUTHORS", size=12,
              fill=COLORS["muted"], anchor="end", spacing=.8),
        f'<line x1="46" y1="67" x2="1153" y2="67" stroke="{COLORS["border"]}"/>',
    ]
    for idx, (label, raw) in enumerate(items):
        y = 104 + idx * 51
        length = max(3, round((raw / peak) * 666))
        pct = (raw / total) * 100 if total else 0
        parts.extend([
            xtext(50, y + 9, label, size=17, weight=550),
            f'<rect x="270" y="{y - 7}" width="666" height="14" rx="7" fill="{COLORS["bar"]}" opacity=".30"/>',
            f'<rect x="270" y="{y - 7}" width="{length}" height="14" rx="7" fill="{COLORS["accent"]}" opacity="{1 - idx * .12:.2f}"/>',
            xtext(1152, y + 9, f"{pct:.1f}%", size=17, weight=550, anchor="end"),
        ])
    parts.extend([
        xtext(50, 363, "Linguist snapshots include contributors other than you; not historical authored LOC.",
              size=12, fill=COLORS["muted"]),
        '</svg>',
    ])
    svg = "\n".join(parts) + "\n"
    ET.fromstring(svg)
    return svg


def stats_markdown(data: dict) -> str:
    unique, summary = data["unique_attributed_sha_summary"], data["summary"]
    coverage = "Partial — some discovery or fork comparisons require review" \
        if data["coverage"] == "partial" else "Complete for enumerated accessible sources"
    updated = date_label(data)
    languages = sorted(
        ((name, v) for name, v in (data.get("current_language_bytes") or {}).items()
         if type(v) is int and v > 0),
        key=lambda item: item[1], reverse=True
    )[:5]
    lang_line = " · ".join(f"**{name}**" for name, _ in languages) or "Unavailable"
    return f'''{OPEN}

<p align="center">
  <a href="./docs/github-audit/REPORT.md">
    <img src="./assets/lifetime-engineering.svg" width="100%" alt="Live lifetime engineering record: repositories, unique attributed commits, code lines changed and AI-tagged commit activity" />
  </a>
</p>

**{format_int(integer(unique, "commits"))} verified-identity Git SHAs** · **{format_int(integer(unique, "code_lines_changed"))} code lines changed** · **{format_int(integer(data, "repositories_scanned"))} repositories scanned**.

<sub>Updated {updated} · {coverage}. Code LOC is cumulative added + deleted programming/markup lines, not unique code written. AI-tagged commits are repository/SHA occurrences, not confirmed autonomous agent-authored commits. Private repository identities are withheld.</sub>

**Current language footprint** — {lang_line}

<img src="./assets/language-landscape.svg" width="100%" alt="Current top language shares across accessible default branches, as reported by GitHub Linguist" />

[Full methodology &amp; audit](./docs/github-audit/REPORT.md) · [Repository evidence](./docs/github-audit/repositories.md) · [Language history](./docs/github-audit/languages.md) · [AI attribution and definitions](./docs/github-audit/APPENDIX.md)

{CLOSE}'''


def update_readme(data: dict) -> bool:
    if not README.is_file():
        raise ValueError("README.md missing; refusing to invent a profile")
    original = README.read_text(encoding="utf-8")
    if original.count(OPEN) != 1 or original.count(CLOSE) != 1:
        raise ValueError("README must contain exactly one matching pair of PROFILE_STATS markers")
    start = original.index(OPEN)
    end = original.index(CLOSE)
    if end <= start:
        raise ValueError("README profile markers are in the wrong order")
    updated = original[:start] + stats_markdown(data) + original[end + len(CLOSE):]
    if updated != original:
        README.write_text(updated, encoding="utf-8")
        return True
    return False


def main():
    data = load_audit()
    ASSETS.mkdir(parents=True, exist_ok=True)
    first = stat_svg(data)
    second = language_svg(data)
    # Validate the target markers before writing anything.
    original = README.read_text(encoding="utf-8")
    if original.count(OPEN) != 1 or original.count(CLOSE) != 1:
        raise ValueError("README profile markers missing or duplicated")
    (ASSETS / "lifetime-engineering.svg").write_text(first, encoding="utf-8")
    (ASSETS / "language-landscape.svg").write_text(second, encoding="utf-8")
    changed = update_readme(data)
    print("Profile dashboard refreshed:", date_label(data),
          "coverage:", data["coverage"], "README updated:", changed, flush=True)


if __name__ == "__main__":
    main()
