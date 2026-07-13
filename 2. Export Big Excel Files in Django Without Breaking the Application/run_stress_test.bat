@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

where docker >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Docker is not installed or is not available in PATH.
    exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Docker Desktop is not running.
    exit /b 1
)

set "VERSION=%~1"
if not defined VERSION (
    echo Select the endpoint to stress test:
    echo   1. V1 - in-memory export ^(expected to exhaust memory^)
    echo   2. V2 - memory-efficient export
    set /p "SELECTION=Selection [1/2]: "
    if "!SELECTION!"=="1" set "VERSION=v1"
    if "!SELECTION!"=="2" set "VERSION=v2"
)

if /i "%VERSION%"=="1" set "VERSION=v1"
if /i "%VERSION%"=="2" set "VERSION=v2"

if /i not "%VERSION%"=="v1" if /i not "%VERSION%"=="v2" (
    echo [ERROR] Invalid version. Use v1 or v2.
    echo Usage: run_stress_test.bat [v1^|v2]
    exit /b 2
)

set "SCRIPT=scripts\stress_concurrent.ps1"
set "METRICS=%VERSION%-5m-concurrent-metrics.csv"

if not exist "%SCRIPT%" (
    echo [ERROR] Missing stress script: %SCRIPT%
    exit /b 3
)

echo.
echo ============================================================
echo Stress test: %VERSION% endpoint
echo Requests:    4 concurrent exports
echo Dataset:     5,000,000 rows
echo Container:   4 GB memory, 4 Gunicorn workers
echo ============================================================
echo.
for /f "delims=" %%I in ('powershell.exe -NoProfile -Command "(Get-Date).ToUniversalTime().ToString('o')"') do set "LOG_SINCE=%%I"

echo Restarting the web container to clear retained memory...
docker compose restart web
if errorlevel 1 exit /b 4

echo Waiting for Gunicorn...
powershell.exe -NoProfile -Command ^
    "$deadline=(Get-Date).AddSeconds(30); do { try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 'http://localhost:8000/csv/examples/lightweight/v1/'; if ($r.StatusCode -eq 200) { exit 0 } } catch {}; Start-Sleep 1 } while ((Get-Date) -lt $deadline); exit 1"
if errorlevel 1 (
    echo [ERROR] Gunicorn did not become ready within 30 seconds.
    docker compose logs --tail=30 web
    exit /b 5
)

echo Starting the stress test and Docker metrics capture...
echo This can take approximately five minutes.
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" -Version "%VERSION%"
set "TEST_EXIT=%ERRORLEVEL%"

echo.
echo ====================== METRICS SUMMARY ======================
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "scripts\summarize_stress_metrics.ps1" -MetricsFile "%METRICS%" -Version "%VERSION%"
set "SUMMARY_EXIT=%ERRORLEVEL%"

echo.
echo ===================== GUNICORN EVENTS =======================
docker compose logs --since "%LOG_SINCE%" web 2>&1 | findstr /i /c:"GET /csv/examples/export" /c:"SIGKILL" /c:"OUT OF MEMORY" /c:"WORKER TIMEOUT" /c:"Booting worker"

echo.
echo Full metrics: %CD%\%METRICS%
echo Output files: %CD%\%VERSION%-5m-concurrent-*.csv
echo Error logs:   %CD%\%VERSION%-5m-concurrent-*-error.log

if not "%TEST_EXIT%"=="0" (
    echo.
    echo [WARNING] The stress runner exited with code %TEST_EXIT%.
)
if not "%SUMMARY_EXIT%"=="0" exit /b %SUMMARY_EXIT%

exit /b %TEST_EXIT%
