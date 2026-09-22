#!/bin/bash
set -e
echo "Starting IC-AMMA 2026 Reproducibility Pipeline..."
pip install -r requirements.txt
python -m pytest tests/
python -m src.run_final_audit
echo "Pipeline complete."
