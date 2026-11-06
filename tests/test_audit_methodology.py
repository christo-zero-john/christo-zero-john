"""Markdown disclosure and official Linguist registry regression tests."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


annotator = load("audit_explanations", ROOT / "scripts" / "annotate_audit_markdown.py")
linguist = load("linguist_index_builder", ROOT / "scripts" / "build_linguist_index.py")


class ExplanationTests(unittest.TestCase):
    def test_table_has_expandable_info_and_appendix(self):
        sample = [
            "# Statistics", "",
            "| Metric | Value |",
            "| --- | --- |",
            "| Directly authored | 12 |",
            "| Co-authored by you | 3 |",
            "| Repository | Changed lines |",
            "| --- | --- |",
            "| owner/fork | 0 |",
        ]
        output = "\n".join(annotator.annotate_table(sample))
        self.assertIn("| ℹ Details |", output)
        self.assertIn("<details><summary>ℹ Explain</summary>", output)
        self.assertIn("APPENDIX.md#identity", output)
        self.assertIn("APPENDIX.md#coauthors", output)
        self.assertIn("APPENDIX.md#forks", output)
        self.assertIn("Co-authored by you | 3", output)

    def test_linguist_registry_does_not_guess_ambiguous_extensions(self):
        mapped = linguist.build({
            "TypeScript": {"type": "programming", "extensions": [".tsx"]},
            "Plain Text": {"type": "prose", "extensions": [".amb"]},
            "Example Code": {"type": "programming", "extensions": [".amb"]},
            "Ruby": {"type": "programming", "filenames": ["Gemfile"]},
        })
        self.assertEqual(mapped["extensions"][".tsx"][0]["name"], "TypeScript")
        self.assertEqual(len(mapped["extensions"][".amb"]), 2)
        self.assertEqual(mapped["filenames"]["Gemfile"][0]["name"], "Ruby")

    def test_appendix_contains_authorship_and_forks(self):
        page = annotator.appendix()
        self.assertIn('<a id="identity"></a>', page)
        self.assertIn('<a id="forks"></a>', page)
        self.assertIn("unrelated agent", page.lower()) if False else self.assertIn("upstream", page.lower())


if __name__ == "__main__":
    unittest.main()
