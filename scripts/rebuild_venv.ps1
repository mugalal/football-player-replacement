param(
    [switch]$WithNotebooks
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $projectRoot ".venv"
$tmpRoot = Join-Path $projectRoot ".tmp"
$pipTemp = Join-Path $tmpRoot "pip-temp"
$pipCache = Join-Path $tmpRoot "pip-cache"

New-Item -ItemType Directory -Path $pipTemp -Force | Out-Null
New-Item -ItemType Directory -Path $pipCache -Force | Out-Null

$env:TEMP = $pipTemp
$env:TMP = $pipTemp
$env:PIP_CACHE_DIR = $pipCache

if (Test-Path -LiteralPath $venvPath) {
    Remove-Item -LiteralPath $venvPath -Recurse -Force
}

py -3.11 -m venv $venvPath

$python = Join-Path $venvPath "Scripts\python.exe"

& $python -m pip install --upgrade pip
& $python -m pip install -r (Join-Path $projectRoot "requirements.txt")
& $python -m pip install -e $projectRoot --no-deps

if ($WithNotebooks) {
    & $python -m pip install -r (Join-Path $projectRoot "requirements-notebooks.txt")
}
