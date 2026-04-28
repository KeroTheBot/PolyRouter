@echo off
setlocal

set VPS_IP=45.125.64.244
set VPS_PORT=56777
set VPS_USER=kerothebot
set SOCKS_PORT=1080
set API_PORT=8080

if "%~1"=="start" goto start
if "%~1"=="stop" goto stop
if "%~1"=="status" goto status

echo Usage: tunnel.bat start ^| stop ^| status
exit /b 1

:start
tasklist /FI "WINDOWTITLE eq polyrouter-tunnel" 2>nul | find "ssh" >nul
if %errorlevel%==0 (
    echo Tunnel already running.
    exit /b 0
)
echo Starting tunnel to %VPS_IP%:%VPS_PORT% (user: %VPS_USER%)...
echo.
echo Forwards:
echo   SOCKS5 proxy:    127.0.0.1:%SOCKS_PORT% (browser routing)
echo   poly-router API: 127.0.0.1:%API_PORT% -^> VPS:%API_PORT%
echo.
echo Press Ctrl+C to stop.
echo.
ssh -D %SOCKS_PORT% -L %API_PORT%:localhost:%API_PORT% -p %VPS_PORT% -N %VPS_USER%@%VPS_IP%
echo Tunnel closed.
exit /b 0

:stop
taskkill /FI "WINDOWTITLE eq polyrouter-tunnel" /F >nul 2>&1
if %errorlevel%==0 (
    echo Tunnel stopped.
) else (
    echo No tunnel running.
)
exit /b 0

:status
tasklist /FI "WINDOWTITLE eq polyrouter-tunnel" 2>nul | find "ssh" >nul
if %errorlevel%==0 (
    echo Tunnel running (SOCKS:%SOCKS_PORT%, API:%API_PORT%)
) else (
    echo Tunnel not running.
)
exit /b 0
