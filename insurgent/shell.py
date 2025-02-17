import os
import re
import yaml
import subprocess
from build import build, load_config
from terminal import *
from version import about, help

def parse_options(command):
    options = load_config()
    if options is None:
        options = {}

    for arg in command[1:]:
        if arg.startswith('-') and not arg.startswith('--'):
            combined_flags = re.findall(r'-(\w)', arg)
            for flag in combined_flags:
                if flag == 'D':
                    options['debug'] = True
                elif flag == 'C':
                    options['clean'] = True
                elif flag == 'v':
                    options['verbose'] = True
                elif flag == 's':
                    options['silent'] = True
        elif arg.startswith('-j='):
            try:
                options['jobs'] = int(arg.split('=')[1])
            except ValueError:
                print(f"{RED}Error: Invalid value for '-j'. It should be an integer.{RESET}")
                return {}
        elif arg == '--no-log':
            options['no_log'] = True

    return options

def shell():
    print(f"{CYAN}{BOLD}Welcome to the InsurgeNT Shell!{RESET}")
    print(f"Type {YELLOW}'help'{RESET} for commands or {YELLOW}'exit'{RESET} to quit.")
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
        elif cmd == "build":
            options = parse_options(command)
            component = command[1] if len(command) > 1 else "all"
            build(component, options)
        elif cmd == "clean":
            component = command[1] if len(command) > 1 else "all"
            # clean(component)
        elif cmd == "exit":
            print(f"{MAGENTA}Goodbye!{RESET}")
            break
        else:
            print(f"{RED}Unknown command: {command[0]}{RESET}")
            print(f"Type {YELLOW}'help'{RESET} for a list of available commands.")
