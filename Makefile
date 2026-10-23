.PHONY: help install backend-dev frontend-dev test test-backend test-frontend demo clean

help:
	@echo "TRSM Middleware Development Commands:"
	@echo "  make install         Install backend and frontend dependencies"
	@echo "  make backend-dev     Run FastAPI backend with live reloading"
	@echo "  make frontend-dev    Run Vite frontend development server"
	@echo "  make test            Run all test suites"
	@echo "  make test-backend    Run pytest suite"
	@echo "  make demo            Execute deterministic demo slice"
	@echo "  make clean           Clean caches, logs, and temporary run files"

install:
	cd backend && python -m pip install -r requirements.txt
	cd frontend && npm install

backend-dev:
	cd backend && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

frontend-dev:
	cd frontend && npm run dev

test-backend:
	cd backend && pytest -v

test: test-backend

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
