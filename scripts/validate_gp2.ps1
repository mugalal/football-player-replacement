$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Virtual environment not found. Run scripts\rebuild_venv.ps1 first."
}

$env:PYTHONIOENCODING = "utf-8"
& $python -m src.gp2.evaluation.mane_case_validation
