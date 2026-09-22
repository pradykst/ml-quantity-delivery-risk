@echo off
echo Starting IC-AMMA 2026 Reproducibility Pipeline...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
python scripts/download_data.py
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
python -m pytest
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
python -m src.run_final_audit
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
echo Pipeline complete.
