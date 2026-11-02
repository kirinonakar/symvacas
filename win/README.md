# SymvaCAS Windows

웹 버전 UI와 공통 Python 계산 엔진을 사용하는 Tauri 2 Windows 앱입니다. 계산에 WASM/Pyodide를 사용하지 않습니다. Android/Web 소스는 그대로 유지하고 빌드할 때 UI를 복사합니다.

## 빌드

Windows x64, Rust MSVC 도구 체인, Visual Studio C++ Build Tools, Node.js 22+, 빌드용 Python 3.10+, WebView2 Runtime이 필요합니다. 실행할 PC에는 시스템 Python이나 Node.js가 필요하지 않습니다.

```powershell
cd win
npm ci
npm run dev
npm run build
```

`release/SymvaCAS/`에 `symvacas.exe`, `symvacas-cli.exe`, `skills/symvacas/`와 문서를 묶습니다. **폴더 전체**를 쓰기 가능한 위치에 복사하세요. `symvacas.exe`는 GUI, `symvacas-cli.exe`는 콘솔/MCP용입니다. 개발 실행 시에는 실제 개발 EXE가 있는 `src-tauri/target/debug/python_embeded`에 설치됩니다.

앱 버전은 Android의 `app/build.gradle.kts`에 있는 **`versionName` 하나를 기준으로 사용**합니다. `npm run dev`·`npm run build` 실행 시 Tauri가 설정을 읽기 전에 npm·Cargo·Tauri 버전과 잠금 파일을 자동 동기화합니다. 앱 정보·실행 파일 버전·CLI `--version`·MCP `serverInfo.version`도 같은 버전입니다. 예를 들어 Android를 `1.6.5`로 올리면 다음 Windows 빌드도 `1.6.5`가 됩니다. 웹을 별도로 빌드할 필요는 없습니다. Cargo를 직접 실행하려면 먼저 `npm run prepare:app`을 실행하세요. 버전이 다르면 직접 Cargo 빌드는 오류로 중단됩니다.

## Python 설치

앱의 **Python / MCP → Python 의존성 설치**를 누르면 실행 파일 폴더의 **`python_embeded`**에 CPython 3.14.10 x64, SymPy 1.14.0, mpmath 1.3.0, pip 26.2.2를 설치합니다. 다운로드 URL/버전/SHA-256은 `runtime-lock.json`에 고정되어 있습니다. 다운로드 후 해시를 검사하고 임시 폴더에서 import 검사까지 성공한 경우에만 설치를 전환합니다. 실패하면 기존 폴더를 유지하며, 불완전한 기존 설치를 교체할 때는 백업 폴더를 남깁니다. 다른 앱 인스턴스의 동시 설치는 차단됩니다.

최초 설치에는 인터넷과 실행 파일 폴더 쓰기 권한이 필요합니다. Program Files 등 쓰기 권한이 없는 위치에서는 앱 폴더를 사용자 소유 폴더로 옮겨주세요. 이후 계산은 오프라인으로 작동합니다. 환율 새로 고침에는 인터넷이 필요합니다. 추가 패키지는 필요할 때 다음처럼 로컬 Python에 설치할 수 있습니다.

```powershell
.\python_embeded\python.exe -m pip install PACKAGE
```

계산용 Python 프로세스는 유지되며 중지 시 종료하고 새로 시작합니다. Python `input()` 대기 중에는 실행 시간 제한을 일시 중지합니다. Python 스크립트는 현재 사용자 권한으로 실행됩니다.

## CLI

```powershell
.\symvacas-cli.exe status
.\symvacas-cli.exe install
.\symvacas-cli.exe eval '1/3+1/6'
.\symvacas-cli.exe eval 'solve(x^2-5*x+6=0,x)'
.\symvacas-cli.exe eval 'sin(30)' --angle DEG --precision 50
.\symvacas-cli.exe catalog '회귀' --limit 5
.\symvacas-cli.exe catalog ttest2
.\symvacas-cli.exe solve 'x^2-5*x+6=0'
.\symvacas-cli.exe solve 'x+y=3' 'x-y=1' --variables x,y
.\symvacas-cli.exe solve 'cos(x)=x' --method nsolve --guess 0.5
.\symvacas-cli.exe stats 'ttest2(0,[1,2,3,4],[2,4,6,8])'
.\symvacas-cli.exe stats 'regression(data,linear)' --data trial.json
.\symvacas-cli.exe dataset save cohort cohort.csv
.\symvacas-cli.exe dataset list
.\symvacas-cli.exe dataset show cohort
.\symvacas-cli.exe stats 'stats(cohort)'
.\symvacas-cli.exe request request.json
.\symvacas-cli.exe python script.py --input 'Alice' --input '10'
.\symvacas-cli.exe --help
```

출력은 공통 계산 엔진 JSON입니다. 실패 시 종료 코드는 1입니다. CLI/MCP 기본 각도는 RAD이며 GUI 설정과 독립적입니다. 웹 파서를 실행 파일 안에 포함하므로 LaTeX·암시적 곱셈·계산기 문법도 동일하게 처리합니다. `request`는 AST·변수·함수를 포함한 웹 엔진 요청 JSON을 받습니다. `-`를 파일명으로 지정하면 stdin을 사용합니다.

`catalog`는 함수명·범주·한/영 설명·예제를 검색하고 함수 시그니처와 실행 가능한 예제를 반환합니다. `--category`, `--limit 1..100`, `--offset`으로 결과를 좁힐 수 있습니다. Python을 설치하지 않아도 검색할 수 있습니다.

`stats`는 기술통계·검정·ANOVA·회귀·고급 통계 카탈로그 수식을 실행합니다. `--data` JSON은 `{"a":[1,2,3],"b":[2,4,6]}`처럼 이름 있는 데이터셋이나, `data`라는 이름으로 사용하는 벡터/행렬입니다. 큰 데이터셋도 웹 통계 경로로 분리해 전달합니다. 정확한 소수는 JSON 문자열로 지정하세요. 결과에 제공되는 `statisticsReport`, `regression`, `statisticsCopyReport`를 그대로 반환합니다.

`solve`는 기본적으로 기호해와 가능한 단계별 풀이를 반환합니다. 연립방정식은 인수를 여러 개 주거나 stdin에 한 줄씩 입력하고 `--variables x,y`로 미지수를 지정하세요. `--method nsolve --guess 0.5`는 수치해, `--method dsolve --variables 'y(x)' --independent x`는 상미분방정식, `pdsolve`는 편미분방정식에 사용합니다. `--initial`은 ODE 초기조건, `--hint`는 PDE 힌트, `--no-steps`는 풀이 설명 해제입니다. 함수별 인수는 `catalog solve`, `catalog dsolve` 등으로 확인하세요.

### 공유 통계 데이터

`dataset save NAME FILE`은 CSV/TSV 또는 JSON 벡터/행렬을 등록합니다. JSON 확장자가 아닌 stdin 등에는 `--format json`을 지정하세요. 기존 이름을 바꾸려면 `--replace`를 명시해야 합니다. `dataset list`·`show`로 등록 데이터를 확인하고 `stats 'mean(cohort)'`·`eval 'mean(cohort)'`처럼 이름으로 계산합니다. 분석에 사용하는 이름은 `cohort`처럼 수식에서 하나의 기호로 인식되는 이름을 권장합니다.

등록 데이터는 실행 파일 옆 `data/statistics-datasets.json`에 저장하며 **Windows GUI의 저장 데이터·CLI·MCP가 공유**합니다. 업데이트 후 GUI를 한 번 열면 기존 저장 데이터가 공유 레지스트리로 옮겨집니다. 외부에서 변경한 데이터는 GUI를 다시 열면 표시되며, 같은 데이터를 동시에 수정하면 충돌을 알리고 덮어쓰지 않습니다. `stats --data`의 일회성 데이터는 등록 데이터를 변경하지 않고 같은 이름을 해당 요청에서만 대체합니다. GUI 기록·일반 변수·사용자 함수는 별도로 유지됩니다. 배포 폴더를 옮길 때 `data` 폴더도 함께 복사하세요.

## MCP / Skill

앱의 **Python / MCP**에서 실제 설치 경로가 반영된 MCP 설정을 복사하거나 `.\symvacas-cli.exe mcp-config`를 실행하세요.

```json
{
  "mcpServers": {
    "symvacas": {
      "command": "C:\\Tools\\SymvaCAS\\symvacas-cli.exe",
      "args": ["mcp"]
    }
  }
}
```

stdio MCP 서버는 GUI 없이 실행됩니다. `search_catalog`에서 함수와 예제를 찾고 `statistics`·`solve_equations`로 분석과 방정식을 실행할 수 있습니다. 데이터 등록·조회 도구는 `save_statistics_dataset`, `list_statistics_datasets`, `get_statistics_dataset`이며 등록한 이름을 분석식에서 바로 사용합니다. 기존 `evaluate`, `engine_request`, `python`, `runtime_status`도 제공합니다. MCP 2024-11-05, 2025-03-26, 2025-06-18, 2025-11-25 초기화 프로토콜과 요청 취소를 지원합니다. stdout에는 JSON-RPC 메시지만 기록합니다. Python 도구에는 로컬 코드 실행 권한이 있습니다.

**MCP만 등록해도 skill 없이 사용할 수 있습니다.** 서버 초기화의 `instructions`에 도구 선택과 분석 흐름을 전달하고, 각 도구 설명·입력 스키마에 형식과 JSON 예제를 포함합니다. `get_usage` 도구는 `overview`, `catalog`, `datasets`, `statistics`, `equations`, `runtime`, `all` 중 원하는 설명을 반환합니다. 전체 [MCP 사용 가이드](MCP_GUIDE.md)는 `symvacas://guide` 리소스로도 제공합니다. Python을 설치하기 전에도 사용법·함수 검색·데이터 등록은 가능합니다.

`skills/symvacas` 폴더를 사용하는 에이전트의 skills 폴더에 복사하세요. Codex에서는 `%USERPROFILE%\.codex\skills\symvacas\SKILL.md`로 설치할 수 있습니다. MCP에서도 `symvacas://skill` 리소스로 읽을 수 있고 CLI의 `skill` 명령으로 출력할 수 있습니다.

## 검증

```powershell
npm test
cargo test --manifest-path src-tauri/Cargo.toml
npm run build
python tests/smoke_native.py release/SymvaCAS/symvacas-cli.exe --install
python tests/smoke_analysis.py release/SymvaCAS/symvacas-cli.exe
$env:SYMVACAS_TEST_HOME = (Resolve-Path release/SymvaCAS).Path
cargo test --manifest-path src-tauri/Cargo.toml -- --include-ignored
```

`smoke_native.py --install`은 실행 파일 옆에 실제 Python 의존성을 설치하고 CLI·Python input·MCP 계산을 검증합니다. `--include-ignored` 테스트는 해당 런타임으로 비동기 input 응답·취소·재시작도 검사합니다. GUI 수동 검증과는 별개입니다. 배포 후에는 첫 설치, 각 계산 탭, 중지, input 대화상자, 파일 저장/내보내기를 수동 확인하세요. 데이터·스크립트·그래프 내보내기는 Windows 저장 대화상자를 사용합니다.

기술 참고: [Tauri IPC](https://v2.tauri.app/develop/calling-rust/), [Python embeddable distribution](https://docs.python.org/3/using/windows.html#the-embeddable-package), [MCP stdio](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports).
