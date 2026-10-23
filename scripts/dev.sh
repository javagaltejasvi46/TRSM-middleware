#!/usr/bin/env bash
# Development script for Linux/macOS
echo "Starting TRSM Backend API..."
(cd backend && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000) &

echo "Starting TRSM Frontend Playground..."
(cd frontend && npm run dev) &

wait
