"""Assemble the public schema and render catalog help without writing files."""
from .definitions import build_definitions, CORRELATION_SPECS
from .forms import build_forms
from .examples import add_example_rows
from .help import build_form_help, append_cluster_help, append_research_help, catalog_uses, enrich_help


def build_schema():
    """Build a fresh schema; importing or calling this function never writes assets."""
    schema = build_definitions()
    definitions = {item['id']: item for item in schema}
    forms = build_forms()
    form_help = build_form_help(definitions, CORRELATION_SPECS)
    for item in schema:
        if item['id'] not in forms:
            continue
        item['controls'] = forms[item['id']]
        item['formHelp'], item['formHelpKo'] = form_help[item['id']]
        append_cluster_help(item)
    add_example_rows(schema)
    append_research_help(schema)
    return schema


def render_catalog_help(existing, schema, korean=False):
    """Replace the generated advanced-statistics section, keeping the base catalog."""
    uses = catalog_uses(CORRELATION_SPECS)
    text = existing.split('\n## Advanced statistics')[0].split('\n## 고급 통계')[0]
    heading='고급 통계' if korean else 'Advanced statistics'
    intro=('현재 데이터·예제·직접 입력한 분석 식 중 입력 방식을 선택합니다. 대응 분석은 완전한 쌍을 사용하며 대상 ID로 연결할 수 있습니다. 반복측정은 대상별 완전한 행을 입력하세요. 결측 셀은 impute에서 NA로 처리합니다.' if korean else 'Choose current data, example parameters or an editable analysis expression. Paired comparisons use complete pairs and support subject-ID matching. Enter complete subject rows for repeated measurements; impute treats missing cells as NA.')
    text+='\n## '+heading+'\n\n'+intro+'\n\n'
    previous_group = None
    for item in schema:
        group = (item['section'], item['group'])
        if group != previous_group:
            text += '### ' + (item['groupKo'] if korean else item['group']) + '\n\n'
            previous_group = group
        text+=f"`{item['id']}` — {uses[item['id']][int(bool(korean))]} {item['helpKo'] if korean else item['help']}\nExample: {item['example']}\n\n"
    text = enrich_help(text, korean, uses=uses)
    return text.rstrip() + '\n'
