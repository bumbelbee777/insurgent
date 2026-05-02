# InsurgeNT ⚙️✨  
**Integrated Native Toolkit (InsurgeNT)** – a beautiful, modern devshell + build system for C/C++ projects.

[![PyPI version](https://badge.fury.io/py/insurgent.svg)](https://badge.fury.io/py/insurgent)

> A clean, expressive, and fast workflow for native development.  
> **Simple YAML configs. Stunning output. No boilerplate. No stress.**

## ✨ Features

- ⚡️ **Incremental builds** with parallel + async compilation
- 📦 **project.yaml**-based config with automatic source/include detection
- 🧠 **Intelligent project layout** and dependency tracking
- 💻 **Interactive shell** with tab completion, history, and file ops
- 🔧 **Multi-compiler** + cross-platform support (Linux, macOS, Windows)
- 🎨 **Beautiful TUI feedback** with emoji, colors, and clean symbols

## Getting Started

To start using InsurgeNT, run the shell:

```
python -m insurgent # or python -m int
```

### Build Commands

InsurgeNT now supports parallel builds by default for maximum performance.

```
# Build all targets in parallel
build

# Build specific target
build myapp

# Build with debug symbols
build --debug mylib

# Build sequentially (non-parallel)
build --sequential
```

## Creating a Project

InsurgeNT uses YAML configuration for project definitions. Here's an example:

```yaml
project: example
description: An example project
authors: ["John Doe", "Jane Doe"]
license: MIT
version: 0.1.0
language: c++
standard: c++20
compiler: g++
compiler_flags:
  - global: "-fPIC"
  - common: "-O2 -Wall -Wextra"
  - cpp: "-std=c++20"
  - ld: "-lstdc++"
project_dirs: ["sources"]
project_type: executable
output: bin/example

# Optional bootstrap step
bootstrap:
  - task: prepare
  - command: "mkdir -p bin"
```

## Installation

```
pip install insurgent
```

### Development Setup

For development, InsurgeNT provides setup scripts to create a virtual environment and install dependencies:

#### On Linux/macOS:

```bash
# Setup development environment
./setup.sh

# With additional options
./setup.sh --venv=custom_venv --hooks --lint
```

#### On Windows:

```cmd
# Setup development environment
setup.bat

# With additional options
setup.bat --venv=custom_venv --hooks --lint
```

### Linting

To run linting tools on your code:

#### On Linux/macOS:

```bash
# Check and format code
./lint.sh

# Only check code (for CI)
./lint.sh --check
```

#### On Windows:

```cmd
# Check and format code
lint.bat

# Only check code (for CI)
lint.bat --check
```

## Usage

After installation, you can run the development shell by executing:

```
python -m insurgent.shell
```

### Available Commands

- `ls`, `cd`, `pwd` - File navigation
- `mkdir`, `touch`, `rm`, `cp` - File operations
- `build <project> [options]` - Build a project
- `history` - Show command history

## Build System

InsurgeNT includes a powerful build system for C/C++ projects with features like:

- Incremental builds
- Dependency tracking
- Multiple compiler support
- Parallel and fully asynchronous compilation for maximum performance
- Cross-platform compatibility

## License

InsurgeNT is licensed under the [MIT License](LICENSE)