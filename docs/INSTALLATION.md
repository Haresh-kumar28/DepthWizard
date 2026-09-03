# Installation

## Backend (Windows)

Use Python 3.12. From the repository root:

```powershell
py -3.12 -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
```

Run:

```powershell
cd backend
$env:PYTHONPATH='.'
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Model

The first depth-processing run downloads the Hugging Face Transformers checkpoint unless it is already cached. To pre-cache it:

```powershell
python scripts\download_model.py
```

The model is about 100 MB for the Small checkpoint; the repository intentionally does not bundle model weights into the ZIP.

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.
