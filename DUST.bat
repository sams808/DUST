@echo off
rem Double-click launcher for DUST.
rem Uses the Windows py launcher to pick Python 3.11 explicitly.
rem Starts windowless (pyw); if that fails, falls back to a visible
rem console run so any error is readable instead of silently vanishing.
cd /d "%~dp0"

where pyw >nul 2>nul
if errorlevel 1 goto :console

start "" pyw -3.11 app.py
exit /b 0

:console
py -3.11 app.py
if errorlevel 1 pause
