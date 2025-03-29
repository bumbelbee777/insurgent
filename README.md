# InsurgeNT

![Build Status](https://github.com/bumbelbee777/insurgent/workflows/InsurgeNT%20CI%2FCD/badge.svg)
[![codecov](https://codecov.io/gh/bumbelbee777/insurgent/branch/main/graph/badge.svg)](https://codecov.io/gh/bumbelbee777/insurgent)
[![PyPI version](https://badge.fury.io/py/insurgent.svg)](https://badge.fury.io/py/insurgent)

A modern shell and self-contained build system for developers, designed to simplify project management and enhance developer experience.

## Features

- Custom shell with tab completion
- Command history management
- File manipulation utilities
- Self-contained build system for C/C++ projects (no Make dependency)
- Project configuration via YAML
- Cross-platform support (Windows, macOS, Linux)

## Installation

```bash
pip install insurgent
```

## Quick Start

After installation, you can start the InsurgeNT dev shell:

```bash
insurgent # Or 'int', which is a default alias.
```

Or build without the shell directly:

```bash
insurgent build
```

### Available Commands

- `about` - Display information about InsurgeNT
- `help` - Show available commands
- `exit` - Exit the shell
- `clear` - Clear the terminal
- `ls` - List files in the current directory
- `cd <dir>` - Change directory
- `mkdir <dir>` - Create a directory
- `rm <file>` - Remove a file
- `touch <file>` - Create an empty file
- `cp <source> <dest>` - Copy a file
- `cat <file>` - Display file contents
- `build <project> [options]` - Build a project
- `history` - Show command history

## Creating a Project

InsurgeNT uses YAML configuration for project definitions. Here's an example:

```yaml
project: example
description: An example project
authors: Your Name
license: MIT
version: 0.1.0
language: c++
standard: c++20
compiler: g++
compiler_flags:
  global: "-fPIC"
  common: "-O2 -Wall -Wextra"
  cpp: "-std=c++20"
  ld: "-lstdc++"
project_dirs:
  - sources
project_type: executable
output: bin/example

# Optional bootstrap step
bootstrap:
  task: prepare
  command: "mkdir -p bin"
```

## Build System

InsurgeNT features a self-contained build system that does not rely on external build tools like Make. It:

- Auto-detects C, C++, and assembly source files
- Handles incremental builds by tracking file changes
- Supports parallel compilation
- Manages project dependencies and subprojects
- Generates executables or libraries based on project configuration

### Build Options

```bash
insurgent build [options]
```

Available options:
- `--incremental` - Only rebuild changed files
- `--verbose` - Show detailed build information
- `--silent` - Suppress most output
- `--no-subprojects` - Don't build subprojects
- `--debug` - Show debug information on failures

## Development

Clone the repository:

```bash
git clone https://github.com/bumbelbee777/insurgent.git
cd insurgent
```

Then install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest tests/
```

## License

InsurgeNT is licensed under the MIT License. See [LICENSE](LICENSE) for details.