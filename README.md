# InsurgeNT

[![PyPI version](https://badge.fury.io/py/insurgent.svg)](https://badge.fury.io/py/insurgent)

A modern, powerful development shell and build system for C/C++ projects.

## Features

- Intelligent code completion for seamless C/C++ development
- Powerful build pipeline with incremental compilation
- Multiple toolchain support for cross-platform development
- Smart project management with dependency tracking
- **Parallel builds** across multiple projects and components for maximum performance
- Custom shell with tab completion
- Command history management
- Project configuration via YAML
- Cross-platform support (Windows, macOS, Linux)

## Getting Started

To start using InsurgeNT, run the shell:

```
python -m insurgent.shell
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

## Installation

```
pip install insurgent
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
- Parallel compilation for maximum performance
- Cross-platform compatibility

## License

MIT