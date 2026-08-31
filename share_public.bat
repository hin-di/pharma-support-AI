@echo off
chcp 65001 > nul
echo ========================================================
echo   PharmaSupport AI - 共有用公開URL発行ツール
echo ========================================================
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0share.ps1"
pause
