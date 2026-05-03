import os
import sys

# Define ANSI color codes directly to avoid circular imports
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"

root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root not in sys.path:
    sys.path.insert(0, root)

VERSION = "0.1.1"


def about():
    print(f"		{CYAN}{BOLD} InsurgeNT {RESET}")
    print(f"	{GREEN}Integrated Native Toolkit version {VERSION}{RESET}")
    print(
        f"	{YELLOW}InsurgeNT is a build environment for C/C++ projects, aimed for user-friendliness and compactness.{RESET}"
    )
    print()


def help():
    about()
    print(f"{BOLD}Usage:{RESET} insurgent [-h | --help] [-v | -V | --version]")
    print(
        "       insurgent "
        "{help|h|version|v|init|build|test|clean|rebuild|scorch|shell|sh} ..."
    )
    print(f"       insurgent shell <command>...")
    print(f"       insurgent sh <command>...")
    print()
    print(
        f"{BOLD}Note:{RESET} Running InsurgeNT with no subcommand starts the interactive shell."
    )
    print()
    print(f"{MAGENTA}Global options:{RESET}")
    print(f"  {GREEN}-h, --help{RESET}      Show this message and exit.")
    print(f"  {GREEN}-v, -V, --version{RESET}  Print version and exit.")
    print()
    print(f"{MAGENTA}Commands:{RESET}")
    print(f"  {GREEN}help{RESET}, {GREEN}h{RESET}       Same as -h (CLI help text).")
    print(
        f"  {GREEN}version{RESET}, {GREEN}v{RESET}  Same as --version (print version)."
    )
    print(f"  {GREEN}init{RESET}, {GREEN}i{RESET}       Create a new project (wizard).")
    print(
        f"  {GREEN}build{RESET}, {GREEN}b{RESET}     Build the project (needs project.yaml)."
    )
    print(
        f"  {GREEN}test{RESET}, {GREEN}t{RESET}       Build and run unit tests (see unit_tests in project.yaml)."
    )
    print(f"  {GREEN}clean{RESET}, {GREEN}c{RESET}     Remove build artifacts.")
    print(f"  {GREEN}rebuild{RESET}, {GREEN}rb{RESET}  Clean then build.")
    print(
        f"  {GREEN}scorch{RESET}, {GREEN}s{RESET}    Clean and remove bin/lib/obj under the project."
    )
    print(
        f"  {GREEN}shell{RESET}, {GREEN}sh{RESET}  Run one dev-shell line ({GREEN}pwd{RESET}, {GREEN}build{RESET}, …) "
        "and exit."
    )
    print()
