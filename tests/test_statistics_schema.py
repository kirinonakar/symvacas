"""Keep all generated forms, examples and bilingual catalogs in sync with authorship."""
import json
import runpy
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from statistics_schema import build_schema
from statistics_schema.build import render_catalog_help
from statistics_comparison_schema import EXAMPLE_ALIASES
from statistics_help import USES


class StatisticsSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets = ROOT / 'app/src/main/assets'
        cls.schema = json.loads((cls.assets / 'advanced_statistics.json').read_text(encoding='utf-8'))

    def test_all_generated_definitions_match_android_asset_including_order(self):
        actual = build_schema()
        self.assertEqual(actual, self.schema)
        # Also retain property order and exact serialization in the readable Android asset.
        self.assertEqual(json.dumps(actual, ensure_ascii=False, indent=2) + '\n',
                         (self.assets / 'advanced_statistics.json').read_text(encoding='utf-8'))

    def test_repeated_builds_are_independent_and_do_not_mutate_help_registry(self):
        uses = deepcopy(USES)
        first = build_schema()
        first[0]['controls'][0]['default'] = 'changed'
        comparison = next(item for item in first if item['id'] == 'modelcompare')
        comparison['exampleRowsByFamily']['cfa'][0][0] = 'changed'
        self.assertEqual(build_schema(), self.schema)
        self.assertEqual(USES, uses)

    def test_shared_family_examples_preserve_values_and_order(self):
        actual = next(item for item in build_schema() if item['id'] == 'modelcompare')['exampleRowsByFamily']
        expected = next(item for item in self.schema if item['id'] == 'modelcompare')['exampleRowsByFamily']
        self.assertEqual(list(actual), list(expected))
        self.assertEqual(actual, expected)
        for alias, source in EXAMPLE_ALIASES.items():
            with self.subTest(family=alias):
                self.assertIs(actual[alias], actual[source])

    def test_bilingual_catalog_regeneration_is_identical_and_idempotent(self):
        schema = build_schema()
        uses = deepcopy(USES)
        for korean, filename in [(False, 'catalog_help.md'), (True, 'catalog_help_ko.md')]:
            with self.subTest(language=filename):
                expected = (self.assets / filename).read_text(encoding='utf-8')
                actual = render_catalog_help(expected, schema, korean)
                self.assertEqual(actual, expected)
                self.assertEqual(render_catalog_help(actual, schema, korean), actual)
        self.assertEqual(USES, uses)

    def test_importing_cli_does_not_write_assets(self):
        with patch.object(Path, 'write_text', side_effect=AssertionError('import wrote an asset')):
            runpy.run_path(str(ROOT / 'scripts/build_advanced_statistics_schema.py'))


if __name__ == '__main__':
    unittest.main()
