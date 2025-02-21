import os
import signal
import readline
from insurgent.Build.build import build
from insurgent.Shell.builtins import *
from insurgent.Logging.terminal import *
from insurgent.Meta.version import about, help

def handle_sigint(sig, frame):
    print(f"\n{CYAN}Use 'exit' to quit the shell.{RESET}")

signal.signal(signal.SIGINT, handle_sigint)

readline.set_auto_history(True)
readline.parse_and_bind("tab: complete")
readline.set_completer_delims(" \t\n")

def shell():
    print(f"{CYAN}{BOLD}Welcome to the InsurgeNT Shell!{RESET}")
    print(f"Type {YELLOW}'help'{RESET} for commands or {YELLOW}'exit'{RESET} to quit.")

    history_file = os.path.expanduser("~/.insurgent_history")
    try:
        readline.read_history_file(history_file)
    except FileNotFoundError:
        pass

    while True:
        try:
            command = input(f"{GREEN}➜ InsurgeNT> {RESET}").strip().split()
        except EOFError:
            print(f"\n{MAGENTA}Exiting InsurgeNT Shell. Goodbye!{RESET}")
            break
        
        if not command:
            continue
        cmd = command[0].lower()

        if cmd == "about":
            about()
        elif cmd == "help":
            help()
        elif cmd == "exit":
            print(f"{MAGENTA}Goodbye!{RESET}")
            break
        elif cmd == "clear":
            os.system("cls" if os.name == "nt" else "clear")
        elif cmd == "ls":
            print(f"{CYAN}{BOLD}Listing files...{RESET}")
            print("\n".join(ls()))
        elif cmd == "cd":
            if len(command) < 2:
                print(f"{RED}cd: missing operand{RESET}")
            else:
                try:
                    cd(command[1])
                    print(f"{GREEN}Changed directory to {command[1]}{RESET}")
                except Exception as e:
                    print(f"{RED}cd: {str(e)}{RESET}")
        elif cmd == "mkdir":
            if len(command) < 2:
                print(f"{RED}mkdir: missing operand{RESET}")
            else:
                mkdir(command[1])
                print(f"{GREEN}Directory '{command[1]}' created{RESET}")
        elif cmd == "rm":
            if len(command) < 2:
                print(f"{RED}rm: missing operand{RESET}")
            else:
                rm(command[1])
                print(f"{GREEN}File '{command[1]}' removed{RESET}")
        elif cmd == "touch":
            if len(command) < 2:
                print(f"{RED}touch: missing operand{RESET}")
            else:
                touch(command[1])
                print(f"{GREEN}File '{command[1]}' created{RESET}")
        elif cmd == "cp":
            if len(command) < 3:
                print(f"{RED}cp: missing operand{RESET}")
            else:
                cp(command[1], command[2])
                print(f"{GREEN}Copied '{command[1]}' to '{command[2]}'{RESET}")
        elif cmd == "cat":
            if len(command) < 2:
                print(f"{RED}cat: missing operand{RESET}")
            else:
                print(f"{CYAN}{BOLD}Content of {command[1]}:{RESET}")
                print(cat(command[1]))
        elif cmd == "build":
            if len(command) <2:
                print(f"{RED}build: missing operand{RESET}")
            else:
                print(f"{CYAN}{BOLD}Building {command[1]}...{RESET}")
                build(command[1], command[2:])
        else:
            print(f"{RED}Unknown command: {command[0]}{RESET}")
            print(f"Type {YELLOW}'help'{RESET} for a list of available commands.")

        readline.set_history_length(1000)
        readline.write_history_file(history_file)
