# Windows PowerShell Development Runner for TRSM

Write-Host "Starting TRSM Backend API Server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

Write-Host "Starting TRSM Frontend Vite Server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"
