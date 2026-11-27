@echo off
cd /d "%~dp0" || exit /b 1

docker compose -f docker-compose.cpu.yml down
if errorlevel 1 (
    echo Could not stop VeNote CPU. Check the Docker output above.
    pause
    exit /b 1
)