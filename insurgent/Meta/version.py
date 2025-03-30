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

VERSION = "0.1.0"


def about():
    print(f"		{CYAN}{BOLD}✦ InsurgeNT ✦{RESET}")
    print(f"	{GREEN}Integrated Native Toolkit version {VERSION}{RESET}")
    print(
        f"	{YELLOW}InsurgeNT is a build environment for C/C++ projects, aimed for user-friendliness and compactness.{RESET}"
    )
    print()


def help():
    about()
    print(f"{BOLD}Usage:{RESET} insurgent.py [command] [options]")
    print(
        f"{BOLD}Note:{RESET} Running InsurgeNT without commands will launch the interactive shell."
    )
    print()
    print(f"{MAGENTA}Commands:{RESET}")
    print(
        f"  {GREEN}build{RESET} [component] [options] - Build the project/specified subproject."
    )
    print(f"      {YELLOW}Options:{RESET}")
    print(
        "        "
        + f"{BLUE}-C{RESET}          Clean the build directory before building."
    )
    print("        " + f"{BLUE}-v{RESET}          Verbose logging during building.")
    print("        " + f"{BLUE}-s{RESET}          Build silently.")
    print("        " + f"{BLUE}-j=[jobs]{RESET}   Number of jobs to run in parallel.")
    print(
        "        "
        + f"{BLUE}--no-log{RESET}    Do not log the build output to a file (default is logging enabled)."
    )
    print()
    print(f"  {GREEN}clean{RESET} [component] - Clean the specified subproject.")
    print(
        f"  {GREEN}scorch{RESET} [component] - Scorch the entire project (remove all build artifacts and untracked files, reset the project to the initial state)."
    )
    print(f"  {GREEN}depmgr{RESET} [operation] - Run the dependency manager.")
    print("      Options:")
    print(
        "        add [name] [config]    Add a dependency (configuration YAML file is optional)."
    )
    print("        remove [name]          Remove a depency.")
    print("	       list                   List all project dependencies.")
    print(
        f"  {GREEN}test{RESET} [component] [options] - Run tests for the specified component."
    )
    print("      Options:")
    print("        " + f"{BLUE}-v{RESET}          Run tests in verbose mode.")
    print()
