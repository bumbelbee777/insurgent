#!/bin/bash
# Setup script for InsurgeNT development environment on Unix-like systems

set -e

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default virtual environment path
VENV_PATH=".venv"

# Parse arguments
EDITABLE="true"
SETUP_HOOKS="false"
RUN_LINT="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        --venv=*)
            VENV_PATH="${1#*=}"
            shift
            ;;
        --no-editable)
            EDITABLE="false"
            shift
            ;;
        --hooks)
            SETUP_HOOKS="true"
            shift
            ;;
        --lint)
            RUN_LINT="true"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --venv=PATH       Path to virtual environment (default: .venv)"
            echo "  --no-editable     Don't install package in editable mode"
            echo "  --hooks           Set up git hooks for linting"
            echo "  --lint            Run linting tools after setup"
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

# Check if tools/setup_dev.py exists
if [ ! -f "tools/setup_dev.py" ]; then
    echo "Error: tools/setup_dev.py not found. Make sure you're running this script from the project root."
    exit 1
fi

# Build the command
CMD="python3 tools/setup_dev.py --venv=$VENV_PATH"

if [ "$EDITABLE" = "false" ]; then
    CMD="$CMD --no-editable"
fi

if [ "$SETUP_HOOKS" = "true" ]; then
    CMD="$CMD --hooks"
fi

if [ "$RUN_LINT" = "true" ]; then
    CMD="$CMD --lint"
fi

# Run the setup script
echo "Running: $CMD"
eval "$CMD" 