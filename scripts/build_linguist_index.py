#!/usr/bin/env python3
"""Build a filename/extension index from GitHub Linguist's official definitions.

This is a metadata-driven historical classification only. It cannot replace
Linguist's content, heuristics, shebang, Git attribute or Bayesian stages.
Current repository bytes are independently read via GitHub's Linguist API.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import urllib.request
import yaml

URL = "https://raw.githubusercontent.com/github-linguist/linguist/main/lib/linguist/languages.yml"
DEST = Path(os.environ.get("AUDIT_LINGUIST_INDEX", "/tmp/github-linguist-languages.json"))


def build(source):
    extensions, filenames = {}, {}
    for language, spec in source.items():
        if not isinstance(spec, dict):
            continue
        item = {"name": language, "type": spec.get("type", "unknown")}
        for extension in spec.get("extensions", []) or []:
            extensions.setdefault(extension.casefold(), []).append(item)
        for filename in spec.get("filenames", []) or []:
            filenames.setdefault(filename, []).append(item)
    return {"source": URL, "method": "official GitHub Linguist filename and extension registry",
            "extensions": extensions, "filenames": filenames}


def main():
    request = urllib.request.Request(URL, headers={"User-Agent": "github-lifetime-audit/2"})
    with urllib.request.urlopen(request, timeout=60) as response:
        definitions = yaml.safe_load(response.read())
    if not isinstance(definitions, dict) or len(definitions) < 300:
        raise RuntimeError("GitHub Linguist registry is incomplete; refusing unverified language results.")
    result = build(definitions)
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    print("Loaded official GitHub Linguist language definitions:", len(definitions),
          "languages,", len(result["extensions"]), "extensions.", flush=True)


if __name__ == "__main__":
    main()
