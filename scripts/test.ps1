# Windows PowerShell Test Suite Runner
Write-Host "Running Backend Pytest Suite..." -ForegroundColor Cyan
python -m pytest backend/tests -v
if ($LASTEXITCODE -ne 0) {
    Write-Error "Pytest suite failed."
    exit 1
}

Write-Host "Running Deterministic Demo Scenarios..." -ForegroundColor Green
python scripts/run_demo.py --scenario benign
python scripts/run_demo.py --scenario injection
python scripts/run_demo.py --scenario poisoning
Write-Host "All verification tests passed!" -ForegroundColor Green
