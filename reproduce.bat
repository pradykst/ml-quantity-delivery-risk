@echo off
echo Starting IC-AMMA 2026 Reproducibility Pipeline...
pip install -r requirements.txt
python -m pytest tests/
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
python -m src.run_final_audit
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
echo Pipeline complete.
