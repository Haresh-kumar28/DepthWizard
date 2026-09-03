$ErrorActionPreference='Stop'
Set-Location "$PSScriptRoot\..\backend"
if (!(Test-Path .venv)) { py -3.12 -m venv .venv }
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
$env:PYTHONPATH='.'
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
