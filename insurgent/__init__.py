import sys

from insurgent.Logging.logger import error
from insurgent.Meta.version import VERSION
from insurgent.Shell.Shell import Shell

__version__ = VERSION


def main():
    """Main entry point for the shell"""

    if len(sys.argv) > 1 and (sys.argv[1] == "--version" or sys.argv[1] == "-v"):
        print(f"InsurgeNT version {VERSION}")
        return 0

    if len(sys.argv) > 1:
        # Run a single command
        from insurgent.Shell.Executor import run_command

        command_line = " ".join(sys.argv[1:])
        return 0 if run_command(command_line) else 1

    # Run interactive shell
    from insurgent.Shell.Executor import run_shell

    try:
        return run_shell()
    except KeyboardInterrupt:
        print()
        return 0
    except Exception as e:
        error(f"Shell error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
