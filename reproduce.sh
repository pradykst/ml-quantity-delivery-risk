#!/bin/bash
set -e
echo "Starting IC-AMMA 2026 Reproducibility Pipeline..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/download_data.py
python -m pytest
python -m src.run_final_audit
echo "Pipeline complete."
