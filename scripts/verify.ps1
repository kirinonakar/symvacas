$ErrorActionPreference='Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    & .\gradlew.bat :math:test :math:exportCases :app:testDebugUnitTest :app:assembleDebug :app:lintDebug --console=plain
    if($LASTEXITCODE -ne 0) { throw 'Gradle verification failed' }
    $taskPython=Join-Path (Get-Location) '.venv\Scripts\python.exe'
    if(!(Test-Path -LiteralPath $taskPython)) { throw 'Create .venv and install sympy==1.14.0 first (see README).' }
    & $taskPython -X utf8 -m unittest discover -s tests -v
    if($LASTEXITCODE -ne 0) { throw 'Mathematical integration tests failed' }
} finally { Pop-Location }
