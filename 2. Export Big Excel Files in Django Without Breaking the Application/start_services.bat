@echo off
setlocal

cd /d "%~dp0"

where docker >nul 2>nul
if errorlevel 1 (
    echo Docker is not installed or is not available in PATH.
    exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
    echo Docker Desktop is not running.
    exit /b 1
)

echo Starting Redis, Celery worker, and Gunicorn...
docker compose up --build redis worker web

endlocal
