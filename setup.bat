@echo off
title InsurgeNT Environment Setup
REM Setup script for InsurgeNT development environment on Windows

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH. Please install Python 3.8 or higher.
    exit /b 1
)

REM Change to the directory where this script is located
cd /d "%~dp0"

REM Default virtual environment path
set VENV_PATH=%CD%\.venv
set VENV_PATH=%VENV_PATH:"=%

REM Parse arguments
set EDITABLE=true
set SETUP_HOOKS=false
set RUN_LINT=false

:parse_args
if "%~1"=="" goto :done_parsing
if "%~1"=="--help" goto :show_help
if "%~1"=="-h" goto :show_help
if "%~1:~0,7%"=="--venv=" (
    set VENV_PATH=%~1:~7%
    goto :next_arg
)
if "%~1"=="--no-editable" (
    set EDITABLE=false
    goto :next_arg
)
if "%~1"=="--hooks" (
    set SETUP_HOOKS=true
    goto :next_arg
)
if "%~1"=="--lint" (
    set RUN_LINT=true
    goto :next_arg
)
echo Unknown option: %~1
echo Use --help to see available options.
exit /b 1

:next_arg
shift
goto :parse_args

:show_help
echo Usage: %~nx0 [OPTIONS]
echo.
echo Options:
echo   --venv=PATH       Path to virtual environment (default: .venv)
echo   --no-editable     Don't install package in editable mode
echo   --hooks           Set up git hooks for linting
echo   --lint            Run linting tools after setup
echo   -h, --help        Show this help message
exit /b 0

:done_parsing

REM Check if tools/setup_dev.py exists
if not exist "tools\setup_dev.py" (
    echo Error: tools\setup_dev.py not found. Make sure you're running this script from the project root.
    exit /b 1
)

REM Build the command
set CMD=python tools\setup_dev.py --venv="%VENV_PATH%"

if "%EDITABLE%"=="false" (
    set CMD=%CMD% --no-editable
)

if "%SETUP_HOOKS%"=="true" (
    set CMD=%CMD% --hooks
)

if "%RUN_LINT%"=="true" (
    set CMD=%CMD% --lint
)

REM Run the setup script
echo Running: %CMD%
%CMD%

echo.
echo To activate this virtual environment in PowerShell, run:
echo     .\.venv\Scripts\Activate.ps1
echo.
echo To activate in CMD, run:
echo     .venv\Scripts\activate.bat
echo. 