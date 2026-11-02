"""Dependency-free positional contracts shared by runtime errors and generated help."""


def argument(position, name, kind, description, description_ko, **options):
    return dict(position=position, name=name, type=kind, description=description,
                descriptionKo=description_ko, **options)


CONTRACTS = {
    'survivalanalysis': {
        'signature': 'survivalanalysis(data,coxEnabled,ties,entryColumn,phCheck)',
        'minimumArguments': 1,
        'arguments': [
            argument(1, 'data', 'table', 'Survival table; see rowLayouts.', '생존 자료 표. rowLayouts의 열 순서를 따릅니다.'),
            argument(2, 'coxEnabled', 'integer', '0 = KM/log-rank only; 1 = also fit Cox.', '0 = KM·로그순위만, 1 = Cox 회귀도 실행.', default=0, allowed=[0, 1]),
            argument(3, 'ties', 'symbol', 'Cox tied-event handling: efron or breslow.', 'Cox 동률 처리: efron 또는 breslow.', default='efron', allowed=['efron', 'breslow']),
            argument(4, 'entryColumn', 'integer', 'Zero-based column index: -1 = no entry time; 2 = third column is entry time. This is not the group column.', '0부터 세는 열 번호. -1 = 진입시간 없음, 2 = 세 번째 열이 진입시간. 그룹 열 번호가 아닙니다.', default=-1, allowed=[-1, 2]),
            argument(5, 'phCheck', 'integer', '1 = PH assumption check; 0 = skip. Used only when coxEnabled=1.', '1 = 비례위험 가정 검정, 0 = 생략. coxEnabled=1일 때만 사용합니다.', default=1, allowed=[0, 1]),
        ],
        'rowLayouts': [
            {'entryColumn': -1, 'columns': ['time', 'event', 'group', 'optional predictors...']},
            {'entryColumn': 2, 'columns': ['time', 'event', 'entry', 'group', 'optional predictors...']},
        ],
        'description': 'Kaplan–Meier curves, log-rank and optional Cox regression. Positional order: survivalanalysis(data,coxEnabled,ties,entryColumn,phCheck). Defaults after data: 0,efron,-1,1 (Cox is OFF). To fit Cox without delayed entry: survivalanalysis(data,1,efron,-1,1). Numeric flags are 0/1; ties is the symbol efron/breslow. entryColumn is zero-based: -1 means none, 2 means the third column is entry time, NOT the group index. Rows with -1: [time,event,group,predictors...]; with 2: [time,event,entry,group,predictors...]. event: 1=event, 0=censored. Keep earlier option placeholders when setting a later option; phCheck is last and only used with Cox on. The first encountered group is the Cox reference group.',
        'descriptionKo': 'Kaplan–Meier 곡선·로그순위·선택적 Cox 회귀. 위치 인수 순서: survivalanalysis(data,coxEnabled,ties,entryColumn,phCheck). 데이터 뒤 기본값은 0,efron,-1,1이며 Cox는 기본 꺼짐입니다. 진입시간 없이 Cox 실행: survivalanalysis(data,1,efron,-1,1). 실행·검정 여부는 숫자 0/1, ties는 efron/breslow 기호입니다. entryColumn은 0부터 세는 열 번호로 -1=없음, 2=세 번째 열이 진입시간이며 그룹 열 번호가 아닙니다. -1일 때 행: [시간,사건,그룹,설명변수...], 2일 때: [시간,사건,진입시간,그룹,설명변수...]. 사건 1=발생, 0=중도절단. 뒤 옵션을 지정할 때 앞 옵션 자리도 채우세요. 마지막 phCheck는 Cox 실행 시에만 적용되며 첫 등장 그룹이 Cox 기준 그룹입니다.',
    },
    'cox': {
        'signature': 'cox(data,ties,entryColumn,phCheck)',
        'minimumArguments': 1,
        'arguments': [
            argument(1, 'data', 'table', 'Rows: time,event,predictors; no automatic group column.', '행: 시간,사건,설명변수. 자동 그룹 열은 없습니다.'),
            argument(2, 'ties', 'symbol', 'efron or breslow. No coxEnabled flag in this function.', 'efron 또는 breslow. 이 함수에는 coxEnabled 인수가 없습니다.', default='efron', allowed=['efron', 'breslow']),
            argument(3, 'entryColumn', 'integer', 'Zero-based entry-time column index; -1 = none. Any existing column from 2 onward; time/event columns 0/1 are not allowed.', '0부터 세는 진입시간 열 번호. -1=없음, 2 이상인 실제 열 번호만 가능하며 시간·사건 열 0/1은 지정할 수 없습니다.', default=-1, minimum=2, sentinel=-1),
            argument(4, 'phCheck', 'integer', '1 = PH assumption check; 0 = skip.', '1 = 비례위험 가정 검정, 0 = 생략.', default=1, allowed=[0, 1]),
        ],
        'rowLayouts': [
            {'entryColumn': -1, 'columns': ['time', 'event', 'predictors...']},
            {'entryColumn': 2, 'columns': ['time', 'event', 'entry', 'predictors...']},
        ],
        'description': 'Cox proportional-hazards regression. Positional order: cox(data,ties,entryColumn,phCheck); defaults after data: efron,-1,1. Unlike survivalanalysis, there is NO Cox on/off argument: cox(data,1,...) is invalid. Use cox(data,efron,-1,1). Rows: [time,event,predictors...], event 1=event/0=censored. entryColumn is a zero-based entry-time column index (-1=none, otherwise an existing column >=2), excluded from predictors. For entryColumn=2 use [time,event,entry,predictors...]. phCheck: 1=PH check, 0=skip. This function has no automatic group encoding: group IDs supplied here are predictors; use survivalanalysis for group/reference encoding.',
        'descriptionKo': 'Cox 비례위험 회귀. 위치 인수 순서: cox(data,ties,entryColumn,phCheck), 데이터 뒤 기본값: efron,-1,1. survivalanalysis와 달리 Cox 실행 여부 인수가 없으므로 cox(data,1,...)은 잘못된 호출입니다. cox(data,efron,-1,1)을 사용하세요. 행: [시간,사건,설명변수...], 사건 1=발생/0=중도절단. entryColumn은 0부터 세는 진입시간 열 번호(-1=없음, 그 외 2 이상인 실제 열)이며 설명변수에서 제외됩니다. entryColumn=2일 때 [시간,사건,진입시간,설명변수...]입니다. phCheck: 1=PH 검정, 0=생략. 자동 그룹 인코딩이 없으므로 그룹 ID도 설명변수로 취급합니다. 그룹·기준 그룹 인코딩에는 survivalanalysis를 사용하세요.',
    },
}


def usage(name):
    contract = CONTRACTS[name]
    defaults = ','.join(str(arg['default']) for arg in contract['arguments'][1:])
    extra = ('coxEnabled=0/1; ' if name == 'survivalanalysis' else 'no coxEnabled flag; ')
    entry = '-1 or 2' if name == 'survivalanalysis' else '-1 or an existing column index >=2'
    return (f"Expected {contract['signature']}; defaults after data: {defaults}. "
            f"{extra}ties=efron/breslow; entryColumn={entry} (zero-based, NOT the group column); "
            'phCheck=0/1. Keep earlier positional placeholders.')
