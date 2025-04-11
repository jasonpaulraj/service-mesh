@echo off

REM Check if venv directory exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment
call .\venv\Scripts\activate

REM Check if dependencies are installed by trying to import one of the required packages
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -e .
) else (
    echo Dependencies already installed
)

REM Start the FastAPI server
echo Starting FastAPI server...
uvicorn app.main:app --reload --port 6001