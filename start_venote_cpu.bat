@echo off
cd /d "%~dp0" || exit /b 1

docker compose -f docker-compose.cpu.yml up -d --build
if errorlevel 1 (
    echo Could not start VeNote CPU. Check the Docker output above.
    pause
    exit /b 1
)

echo Waiting for VeNote CPU...
for /l %%i in (1,1,120) do (
    curl.exe --silent --fail --max-time 2 --output NUL http://127.0.0.1:48725/
    if not errorlevel 1 goto ready
    timeout /t 2 /nobreak >nul
)

echo VeNote CPU did not become ready. Recent backend logs:
docker compose -f docker-compose.cpu.yml logs --tail 40 backend
pause
exit /b 1

:ready
start "" "http://127.0.0.1:48725/ui/home"