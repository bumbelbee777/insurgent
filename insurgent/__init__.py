"""
InsurgeNT - A modern build system and shell
"""

import argparse
import asyncio
import datetime
import os
import shutil
import sys
from typing import Dict, List, Optional, Tuple

from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.syntax import Syntax
from rich.theme import Theme

from insurgent.build.BuildEngine import BuildEngine
from insurgent.build.BuildTask import BuildTask
from insurgent.build.ParallelBuildManager import ParallelBuildManager
from insurgent.logging.logger import error, info, log, success, warning
from insurgent.logging.terminal import *
from insurgent.meta.config import load_config, validate_config
from insurgent.meta.version import VERSION
from insurgent.meta.version import about as version_about
from insurgent.meta.version import help as print_help
from insurgent.rich_utils import (
    create_panel,
    create_table,
    print_panel,
    print_styled,
    print_table,
    style_text,
)
from insurgent.shell.shell import ShellInterface

__version__ = VERSION

# Custom theme for rich
INSURGENT_THEME = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "red",
        "success": "green",
        "prompt": "bold blue",
        "code": "bold green",
        "path": "bold cyan",
        "version": "bold yellow",
    }
)

# Language standards mapping
LANGUAGE_STANDARDS = {
    "c": ["ansi", "c89", "c90", "c99", "c11", "c17", "c23"],
    "cpp": ["c++11", "c++14", "c++17", "c++20", "c++23"],
    "asm": ["nasm", "gas", "masm"],
}

# Command symbols (ASCII-only for Windows consoles without UTF-8)
COMMAND_SYMBOLS = {
    "build": "*",
    "test": "T",
    "clean": "-",
    "rebuild": "R",
    "scorch": "X",
    "init": "+",
    "about": "@",
    "help": "?",
    "h": "?",
    "?": "?",
    "version": "V",
    "v": "v",
    "exit": "=",
}


def get_command_symbol(cmd: str) -> str:
    """Get the symbol for a command."""
    return COMMAND_SYMBOLS.get(cmd.split()[0], ">")


def parse_args(argv=None):
    """Top-level parser that knows about --version, --help, subcommands, or fallthrough to shell."""
    parser = argparse.ArgumentParser(prog="insurgent", add_help=False)
    parser.add_argument(
        "-v",
        "-V",
        "--version",
        action="store_true",
        dest="version",
        help="Print version and exit",
    )
    parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        dest="help",
        help="Show help and exit",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="CMD")

    # init
    subparsers.add_parser("init", aliases=["i"], help="Create a new project")

    # help / version (mirror common CLI tools)
    subparsers.add_parser(
        "help",
        aliases=["h"],
        help="Show this help text",
    )
    subparsers.add_parser(
        "version",
        aliases=["v"],
        help="Print version number",
    )

    # build
    build = subparsers.add_parser(
        "build", aliases=["b"], help="Build the project", add_help=False
    )
    build.add_argument("-h", "--help", action="store_true")
    build.add_argument("--component", default="all")
    build.add_argument("--incremental", action="store_true")
    build.add_argument("--no-incremental", dest="incremental", action="store_false")
    build.add_argument("--multi-threaded", action="store_true")
    build.add_argument(
        "--no-multi-threaded", dest="multi_threaded", action="store_false"
    )
    build.add_argument("--silent", action="store_true")
    build.add_argument("--no-silent", dest="silent", action="store_false")
    build.add_argument("--build-subprojects", action="store_true")
    build.add_argument(
        "--no-build-subprojects", dest="build_subprojects", action="store_false"
    )
    build.set_defaults(
        incremental=True,
        multi_threaded=True,
        silent=False,
        build_subprojects=True,
    )

    # test (unit tests)
    test_p = subparsers.add_parser(
        "test",
        aliases=["t"],
        help="Build and run the unit test executable",
        add_help=False,
    )
    test_p.add_argument("-h", "--help", action="store_true")
    test_p.add_argument("--incremental", action="store_true")
    test_p.add_argument("--no-incremental", dest="incremental", action="store_false")
    test_p.add_argument("--silent", action="store_true")
    test_p.set_defaults(incremental=True, silent=False)

    # clean
    subparsers.add_parser("clean", aliases=["c"], help="Clean build artifacts")

    # rebuild
    subparsers.add_parser(
        "rebuild", aliases=["rb"], help="Clean and rebuild the project"
    )

    # scorch
    subparsers.add_parser(
        "scorch", aliases=["s"], help="Remove all build artifacts and generated files"
    )

    # one-off dev shell (builtins like pwd, build, …) without starting the interactive REPL
    sh_parser = subparsers.add_parser(
        "shell",
        aliases=["sh"],
        help="Run one interactive-shell command line and exit",
        add_help=False,
    )
    sh_parser.add_argument("-h", "--help", action="store_true", dest="shell_help")
    sh_parser.add_argument(
        "invoke_argv",
        nargs=argparse.REMAINDER,
        help="Command and arguments passed to ShellInterface.execute",
    )

    return parser.parse_args(argv)


def get_language_standard(lang: str) -> str:
    """Get the standard for a language through interactive prompt."""
    console = Console(theme=INSURGENT_THEME)
    standards = LANGUAGE_STANDARDS[lang]

    # Show available standards
    console.print(f"\n[prompt]Available {lang.upper()} standards:[/]")
    for i, std in enumerate(standards, 1):
        console.print(f"  {i}. [code]{std}[/]")

    # Get user choice
    choice = IntPrompt.ask(
        f"\n[prompt]Select {lang.upper()} standard[/]",
        default=len(standards),  # Default to latest
        show_default=True,
    )

    # Validate and return choice
    if 1 <= choice <= len(standards):
        return standards[choice - 1]
    return standards[-1]  # Default to latest if invalid choice


async def run_init():
    """Interactive project initialization wizard."""
    console = Console(theme=INSURGENT_THEME)

    # Welcome message
    console.print(
        Panel.fit(
            "[bold green]Welcome to InsurgeNT Project Wizard[/]\n"
            "This will help you create a new project.",
            title="Project Initialization",
            border_style="green",
        )
    )

    # Get project details
    project_name = Prompt.ask("[prompt]Project name[/]", default="my-project")
    project_version = Prompt.ask("[prompt]Version[/]", default="0.0.1")
    project_description = Prompt.ask(
        "[prompt]Description[/]", default="An InsurgeNT-based project"
    )

    # Get project type
    project_type = Prompt.ask(
        "[prompt]Project type[/]",
        choices=["executable", "library"],
        default="executable",
    )

    # Get language preferences and standards
    languages = []
    standards = []

    if Confirm.ask("[prompt]Do you want to use C?[/]"):
        languages.append("c")
        standards.append(get_language_standard("c"))

    if Confirm.ask("[prompt]Do you want to use C++?[/]"):
        languages.append("cpp")
        standards.append(get_language_standard("cpp"))

    if Confirm.ask("[prompt]Do you want to use Assembly?[/]"):
        languages.append("asm")
        standards.append(get_language_standard("asm"))

    if not languages:
        console.print("[error]Error: At least one language must be selected[/]")
        return 1

    # Create project structure
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            # Create project directory
            task = progress.add_task("[cyan]Creating project structure...", total=100)

            os.makedirs(project_name, exist_ok=True)
            progress.update(task, advance=20)

            # Create project.yaml
            project_config = {
                "name": project_name,
                "version": project_version,
                "description": project_description,
                "type": project_type,
                "language": ",".join(languages),
                "standard": ",".join(standards),
                "output": (
                    f"bin/{project_name}"
                    if project_type == "executable"
                    else f"lib/lib{project_name}.a"
                ),
                "project_dirs": ["src", "include", "test"],
                "compiler_flags": {
                    "global": "-Wall -Wextra",
                    "c": "-std=c99",
                    "cpp": "-std=c++17",
                },
            }

            import yaml

            with open(os.path.join(project_name, "project.yaml"), "w") as f:
                yaml.dump(project_config, f, default_flow_style=False)
            progress.update(task, advance=20)

            # Create project structure
            for dir_name in ["src", "include", "test", "bin", "lib"]:
                os.makedirs(os.path.join(project_name, dir_name), exist_ok=True)
            progress.update(task, advance=20)

            # Create initial source files
            if "c" in languages:
                with open(os.path.join(project_name, "src", "main.c"), "w") as f:
                    f.write(
                        """#include <stdio.h>

int main(int argc, char** argv) {
    printf("Hello, InsurgeNT!\\n");
    return 0;
}
"""
                    )
            elif "cpp" in languages:
                with open(os.path.join(project_name, "src", "main.cpp"), "w") as f:
                    f.write(
                        """#include <iostream>

int main(int argc, char** argv) {
    std::cout << "Hello, InsurgeNT!" << std::endl;
    return 0;
}
"""
                    )
            progress.update(task, advance=40)

        console.print(f"\n[success]Project '{project_name}' created successfully.[/]")
        console.print("\n[prompt]Next steps:[/]")
        console.print(f"  1. [path]cd {project_name}[/]")
        console.print("  2. [code]insurgent build[/]")
        return 0

    except Exception as e:
        console.print(f"[error]Error creating project: {str(e)}[/]")
        return 1


async def run_test(args):
    """Build and run unit tests from the current directory."""
    engine = BuildEngine(os.getcwd())
    ok, detail = await engine.run_unit_tests(
        incremental=args.incremental,
        silent=args.silent,
    )
    console = Console(theme=INSURGENT_THEME)
    if ok:
        if detail:
            console.print(f"[success]{detail}[/]")
        else:
            console.print("[success]Tests passed.[/]")
        return 0
    console.print(f"[error]{detail}[/]")
    return 1


async def run_build(args):
    """Build the project."""
    # Load project configuration
    config = load_config(os.getcwd())
    if not config:
        console = Console(theme=INSURGENT_THEME)
        console.print("[error]Error: No project.yaml found in current directory.[/]")
        console.print("[prompt]Run `insurgent init` first.[/]")
        return 1

    engine = BuildEngine(config)
    build_kwargs = {
        "component": args.component,
        "incremental": args.incremental,
        "multi_threaded": args.multi_threaded,
        "silent": args.silent,
        "build_subprojects": args.build_subprojects,
    }
    success, _ = await engine.build(**build_kwargs)
    return 0 if success else 1


async def run_clean():
    engine = BuildEngine(os.getcwd())
    success = await engine.clean()
    if not success:
        console = Console(theme=INSURGENT_THEME)
        console.print("[error]Error: No project.yaml found in current directory.[/]")
        console.print("[prompt]Run `insurgent init` first.[/]")
    return 0 if success else 1


async def run_rebuild():
    """Clean and rebuild the project."""
    engine = BuildEngine(os.getcwd())
    if await engine.clean():
        success, _ = await engine.build()
        return 0 if success else 1
    return 1


async def run_scorch():
    """Remove all build artifacts and generated files."""
    engine = BuildEngine(os.getcwd())
    if await engine.clean(clean_subprojects=True):
        # Remove additional generated files
        for dir_name in ["bin", "lib", "obj"]:
            dir_path = os.path.join(os.getcwd(), dir_name)
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
        return 0
    return 1


def run_shell(cmd_args):
    """
    Execute a single dev-shell command line via ShellInterface.

    Mirrors what the interactive REPL runs for one input line; exits with the
    executor's last subprocess / builtin exit code when set.
    """
    shell = ShellInterface()
    line = " ".join(cmd_args).strip()
    out = shell.run_command(line)
    if out:
        print(out)
    code = shell.executor.get_last_exit_code()
    return 0 if code is None else int(code)


def main():
    args = parse_args(sys.argv[1:])
    stdout = getattr(sys.stdout, "reconfigure", None)
    if callable(stdout):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # top-level flags
    if args.version:
        console = Console(theme=INSURGENT_THEME)
        console.print(f"[version]InsurgeNT {VERSION}[/]")
        sys.exit(0)
    if args.help and not args.command:
        print_help()
        sys.exit(0)

    # dispatch
    if args.command in ("help", "h"):
        print_help()
        sys.exit(0)

    if args.command in ("version", "v"):
        console = Console(theme=INSURGENT_THEME)
        console.print(f"[version]InsurgeNT {VERSION}[/]")
        sys.exit(0)

    if args.command in ("init", "i"):
        sys.exit(asyncio.run(run_init()))

    if args.command in ("build", "b"):
        if args.help:
            parse_args(["build", "--help"])
            return
        sys.exit(asyncio.run(run_build(args)))

    if args.command in ("test", "t"):
        if getattr(args, "help", False):
            console = Console(theme=INSURGENT_THEME)
            console.print(
                "[prompt]insurgent test[/] - build and run the unit test executable "
                "configured under [code]unit_tests[/] in project.yaml."
            )
            console.print("  [code]--no-incremental[/]  Force recompile test sources")
            console.print("  [code]--silent[/]           Less build output")
            sys.exit(0)
        sys.exit(asyncio.run(run_test(args)))

    if args.command in ("clean", "c"):
        sys.exit(asyncio.run(run_clean()))

    if args.command in ("rebuild", "rb"):
        sys.exit(asyncio.run(run_rebuild()))

    if args.command in ("scorch", "s"):
        sys.exit(asyncio.run(run_scorch()))

    if args.command in ("shell", "sh"):
        if getattr(args, "shell_help", False):
            console = Console(theme=INSURGENT_THEME)
            console.print(
                "[prompt]insurgent shell[/] / [prompt]insurgent sh[/] — "
                "run one dev-shell line (examples: [code]pwd[/], "
                "[code]ls[/], [code]build --silent[/], [code]test[/]) and exit."
            )
            sys.exit(0)
        invoke = getattr(args, "invoke_argv", None) or []
        invoke = [t for t in invoke if t != "--"]
        if not invoke:
            console = Console(theme=INSURGENT_THEME)
            console.print(
                "[error]Missing command.[/] Usage: "
                "[code]insurgent shell <cmd>[/] (e.g. [code]insurgent sh pwd[/])."
            )
            sys.exit(2)
        sys.exit(run_shell(invoke))

    # Otherwise, start interactive shell
    shell = ShellInterface()

    # Print welcome message
    console = Console(theme=INSURGENT_THEME)
    console.print(
        Panel.fit(
            f"[bold green]InsurgeNT Shell v{VERSION}[/]\n"
            "[dim]Type 'help' or 'h' for commands; 'version' / 'v' for version; 'exit' to quit.[/]",
            title="Welcome",
            border_style="green",
        )
    )

    while True:
        try:
            # Get current directory
            cwd = os.getcwd()

            # Get command
            cmd = input(f"(int) [path]{cwd}[/]% ").strip()

            if not cmd:
                continue

            if cmd in ("exit", "quit"):
                console.print("[success]Goodbye.[/]")
                break

            # Execute command
            output = shell.run_command(cmd)
            if output:
                print(output)

        except KeyboardInterrupt:
            print()
            continue
        except EOFError:
            console.print("[success]Goodbye.[/]")
            break
        except Exception as e:
            console.print(f"[error]Error: {str(e)}[/]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
