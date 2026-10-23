#!/usr/bin/env bash
set -e

echo "Running Backend Tests..."
python -m pytest backend/tests -v

echo "Running Deterministic Demo Scenarios..."
python scripts/run_demo.py --scenario benign
python scripts/run_demo.py --scenario injection
python scripts/run_demo.py --scenario poisoning

echo "All tests passed successfully!"
