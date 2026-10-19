"""Generate shared advanced-analysis presets and bilingual catalog help."""
import json
from pathlib import Path
from statistics_schema import build_schema
from statistics_schema.build import render_catalog_help
from statistics_schema.guidance import build_general_help
from statistics_schema.interpretation import build_interpretation

ROOT = Path(__file__).resolve().parents[1]


def main():
    schema = build_schema()
    assets = ROOT / 'app/src/main/assets'
    (assets / 'advanced_statistics.json').write_text(
        json.dumps(schema, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (assets / 'statistics_analysis_help.json').write_text(
        json.dumps(build_general_help(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (assets / 'statistics_interpretation.json').write_text(
        json.dumps(build_interpretation(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for korean in (False, True):
        path = assets / ('catalog_help_ko.md' if korean else 'catalog_help.md')
        path.write_text(render_catalog_help(path.read_text(encoding='utf-8'), schema, korean), encoding='utf-8')


if __name__ == '__main__':
    main()
