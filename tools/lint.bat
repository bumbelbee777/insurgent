@echo off
REM Linting script for InsurgeNT on Windows

REM Change to the directory where this script is located
cd /d "%~dp0"

REM Default virtual environment path
set VENV_PATH=%CD%\..\.venv
set VENV_PATH=%VENV_PATH:"=%
set PROJECT_ROOT=%CD%\..
set FIX_MODE=false
set CHECK_MODE=false

REM Parse arguments
:parse_args
if "%~1"=="" goto :done_parsing
if "%~1"=="--help" goto :show_help
if "%~1"=="-h" goto :show_help
if "%~1:~0,7%"=="--venv=" (
    set VENV_PATH=%~1:~7%
    goto :next_arg
)
if "%~1"=="--fix" (
    set FIX_MODE=true
    goto :next_arg
)
if "%~1"=="--check" (
    set CHECK_MODE=true
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
echo   --fix             Auto-fix issues where possible
echo   --check           Only check for issues, don't fix (for CI)
echo   -h, --help        Show this help message
exit /b 0

:done_parsing

REM Check if venv exists
if not exist "%VENV_PATH%" (
    echo Virtual environment not found at %VENV_PATH%.
    echo Run setup.bat first to create a virtual environment.
    exit /b 1
)

REM Get the path to Python in the venv
if exist "%VENV_PATH%\Scripts\python.exe" (
    set PYTHON="%VENV_PATH%\Scripts\python.exe"
) else if exist "%VENV_PATH%\bin\python" (
    set PYTHON="%VENV_PATH%\bin\python"
) else (
    echo Could not find Python in the virtual environment at %VENV_PATH%.
    exit /b 1
)

echo Using Python at %PYTHON%

REM Set PYTHONPATH to include project root
set PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%

REM Run Black
if "%CHECK_MODE%"=="true" (
    echo Checking code formatting with Black...
    %PYTHON% -m black --check --config="%PROJECT_ROOT%\pyproject.toml" --target-version py310 "%PROJECT_ROOT%\insurgent" "%PROJECT_ROOT%\tests"
) else (
    echo Formatting code with Black...
    %PYTHON% -m black --config="%PROJECT_ROOT%\pyproject.toml" --target-version py310 "%PROJECT_ROOT%\insurgent" "%PROJECT_ROOT%\tests"
)
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM Run isort
if "%CHECK_MODE%"=="true" (
    echo Checking import sorting with isort...
    %PYTHON% -m isort --check --settings-path="%PROJECT_ROOT%\pyproject.toml" "%PROJECT_ROOT%\insurgent" "%PROJECT_ROOT%\tests"
) else (
    echo Sorting imports with isort...
    %PYTHON% -m isort --settings-path="%PROJECT_ROOT%\pyproject.toml" "%PROJECT_ROOT%\insurgent" "%PROJECT_ROOT%\tests"
)
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM Run flake8 (always in check mode)
echo Linting code with flake8...
%PYTHON% -m flake8 "%PROJECT_ROOT%\insurgent" "%PROJECT_ROOT%\tests" --count --select=E9,F63,F7,F82 --show-source --statistics
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

echo Linting complete! 