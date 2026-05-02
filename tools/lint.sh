#!/bin/bash

set -e

# Directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default virtual environment path
VENV_PATH=".venv"
FIX_MODE="false"
CHECK_MODE="false"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --venv=*)
            VENV_PATH="${1#*=}"
            shift
            ;;
        --fix)
            FIX_MODE="true"
            shift
            ;;
        --check)
            CHECK_MODE="true"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --venv=PATH       Path to virtual environment (default: .venv)"
            echo "  --fix             Auto-fix issues where possible"
            echo "  --check           Only check for issues, don't fix (for CI)"
            echo "  -h, --help        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help to see available options."
            exit 1
            ;;
    esac
done

# Check if venv exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Virtual environment not found at $VENV_PATH."
    echo "Run ./setup.sh first to create a virtual environment."
    exit 1
fi

# Get the path to Python in the venv
if [ -f "$VENV_PATH/bin/python" ]; then
    PYTHON="$VENV_PATH/bin/python"
elif [ -f "$VENV_PATH/Scripts/python.exe" ]; then
    PYTHON="$VENV_PATH/Scripts/python.exe"
else
    echo "Could not find Python in the virtual environment at $VENV_PATH."
    exit 1
fi

echo "Using Python at $PYTHON"

# Run Black
if [ "$CHECK_MODE" = "true" ]; then
    echo "Checking code formatting with Black..."
    $PYTHON -m black --check --config=pyproject.toml --target-version py310 insurgent tests
else
    echo "Formatting code with Black..."
    $PYTHON -m black --config=pyproject.toml --target-version py310 insurgent tests
fi

# Run isort
if [ "$CHECK_MODE" = "true" ]; then
    echo "Checking import sorting with isort..."
    $PYTHON -m isort --check insurgent tests
else
    echo "Sorting imports with isort..."
    $PYTHON -m isort insurgent tests
fi

# Run flake8 (always in check mode)
echo "Linting code with flake8..."
$PYTHON -m flake8 insurgent tests --count --select=E9,F63,F7,F82 --show-source --statistics

echo "Linting complete!" 