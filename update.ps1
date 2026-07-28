<#
.SYNOPSIS
    Updates an existing DUST install: pulls the latest code (if this is a
    git checkout), upgrades dependencies, regenerates brand assets, and
    rewrites DUST.bat so the launcher always matches the current app.
.USAGE
    Right-click -> Run with PowerShell, or:  powershell -ExecutionPolicy Bypass -File update.ps1
#>

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Output "== DUST update =="

# 1. Pull latest code, if this checkout is a git repo
if (Test-Path (Join-Path $PSScriptRoot ".git")) {
    Write-Output "Pulling latest changes from git..."
    & git pull
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "git pull reported an error - continuing with dependency/asset refresh anyway."
    }
} else {
    Write-Output "Not a git checkout - skipping 'git pull' (only refreshing dependencies/assets/launcher)."
}

# 2. Dependencies
try {
    & py -3.11 --version | Out-Null
} catch {
    Write-Error "Python 3.11 was not found via the 'py' launcher. Run install.ps1 first."
    exit 1
}
Write-Output "Upgrading dependencies from requirements.txt..."
& py -3.11 -m pip install -r (Join-Path $PSScriptRoot "requirements.txt") --upgrade
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip install failed - see output above."
    exit 1
}

# 3. Brand assets
Write-Output "Regenerating brand assets..."
& py -3.11 (Join-Path $PSScriptRoot "make_logo.py")

# 4. Launcher .bat (same template as install.ps1, rewritten so it always
#    matches the current app even if this template changes upstream)
$batPath = Join-Path $PSScriptRoot "DUST.bat"
$batContent = @'
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
'@
Set-Content -Path $batPath -Value $batContent -Encoding ascii
Write-Output "Launcher refreshed: $batPath"

Write-Output ""
Write-Output "Update complete."
