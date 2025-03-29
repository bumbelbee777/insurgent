import os
import signal
from insurgent.Build.build import build
from insurgent.Shell.builtins import *
from insurgent.Logging.terminal import *
from insurgent.Meta.version import about, help
from insurgent.Shell.completions import handle_tab, get_completions

# Custom history implementation
command_history = []
MAX_HISTORY_SIZE = 1000
history_index = -1  # For navigating history

def handle_sigint(sig, frame):
    print(f"\n{CYAN}Use 'exit' to quit the shell.{RESET}")

signal.signal(signal.SIGINT, handle_sigint)

# Removed readline dependencies

def save_history(history_file):
    """Save command history to file"""
    try:
        with open(history_file, 'w') as f:
            for cmd in command_history:
                f.write(f"{cmd}\n")
    except Exception:
        pass

def load_history(history_file):
    """Load command history from file"""
    try:
        with open(history_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and line not in command_history:
                    command_history.append(line)
    except FileNotFoundError:
        pass

def add_to_history(cmd):
    """Add command to history"""
    if cmd and (not command_history or cmd != command_history[-1]):
        command_history.append(cmd)
        if len(command_history) > MAX_HISTORY_SIZE:
            command_history.pop(0)

def custom_input(prompt):
    """Custom input function with tab completion and history navigation"""
    current_input = ""
    cursor_pos = 0
    history_pos = len(command_history)
    saved_current = ""
    tab_count = 0
    tab_last_press = 0
    
    print(prompt, end="", flush=True)
    
    while True:
        # Get a single character
        try:
            import msvcrt  # Windows
            ch = msvcrt.getch()
            # Convert bytes to string
            ch = ch.decode('utf-8', errors='replace')
        except ImportError:
            try:
                import tty, termios, sys  # Unix
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(fd)
                    ch = sys.stdin.read(1)
                    # Already a string in Unix
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            except ImportError:
                # Fallback to regular input if we can't get single character input
                return input(prompt)
        
        # Handle special keys
        if ch == '\r' or ch == '\n':  # Enter
            print()
            return current_input
        elif ch == '\x03':  # Ctrl+C
            raise KeyboardInterrupt
        elif ch == '\x04':  # Ctrl+D
            raise EOFError
        elif ch == '\x7f' or ch == '\b':  # Backspace
            if cursor_pos > 0:
                current_input = current_input[:cursor_pos-1] + current_input[cursor_pos:]
                cursor_pos -= 1
                # Redraw the line
                print(f"\r{' ' * (len(prompt) + len(current_input) + 1)}", end="\r", flush=True)
                print(f"{prompt}{current_input}", end="", flush=True)
                if cursor_pos < len(current_input):
                    # Move cursor back to position
                    print(f"\033[{len(current_input) - cursor_pos}D", end="", flush=True)
        elif ch == '\t':  # Tab
            import time
            current_time = time.time()
            
            # Reset tab count if it's been a while since last tab
            if current_time - tab_last_press > 0.5:
                tab_count = 0
            
            tab_count += 1
            tab_last_press = current_time
            
            # Handle tab completion
            new_input, should_redisplay = handle_tab(current_input, tab_count)
            
            if new_input != current_input:
                current_input = new_input
                cursor_pos = len(current_input)
            
            if should_redisplay:
                # Redisplay prompt
                print(f"\r{prompt}", end="", flush=True)
            
            # Display the new input
            print(f"\r{' ' * (len(prompt) + len(current_input) + 1)}", end="\r", flush=True)
            print(f"{prompt}{current_input}", end="", flush=True)
        elif ch == '\x1b':  # Escape sequence (arrows, etc.)
            # Read two more characters
            try:
                import msvcrt  # Windows
                next1 = msvcrt.getch()
                next2 = msvcrt.getch()
                # Convert bytes to string
                next1 = next1.decode('utf-8', errors='replace')
                next2 = next2.decode('utf-8', errors='replace')
            except ImportError:
                try:
                    import tty, termios, sys  # Unix
                    fd = sys.stdin.fileno()
                    old_settings = termios.tcgetattr(fd)
                    try:
                        tty.setraw(fd)
                        next1 = sys.stdin.read(1)
                        next2 = sys.stdin.read(1)
                        # Already strings in Unix
                    finally:
                        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                except ImportError:
                    next1 = ""
                    next2 = ""
            
            if next1 == '[':
                if next2 == 'A':  # Up arrow
                    if history_pos > 0:
                        # Save current input when starting to navigate history
                        if history_pos == len(command_history):
                            saved_current = current_input
                        
                        history_pos -= 1
                        current_input = command_history[history_pos]
                        cursor_pos = len(current_input)
                        
                        # Redraw the line
                        print(f"\r{' ' * (len(prompt) + len(current_input) + 10)}", end="\r", flush=True)
                        print(f"{prompt}{current_input}", end="", flush=True)
                
                elif next2 == 'B':  # Down arrow
                    if history_pos < len(command_history):
                        history_pos += 1
                        if history_pos == len(command_history):
                            current_input = saved_current
                        else:
                            current_input = command_history[history_pos]
                        cursor_pos = len(current_input)
                        
                        # Redraw the line
                        print(f"\r{' ' * (len(prompt) + len(current_input) + 10)}", end="\r", flush=True)
                        print(f"{prompt}{current_input}", end="", flush=True)
                
                elif next2 == 'C':  # Right arrow
                    if cursor_pos < len(current_input):
                        cursor_pos += 1
                        print("\033[1C", end="", flush=True)  # Move cursor right
                
                elif next2 == 'D':  # Left arrow
                    if cursor_pos > 0:
                        cursor_pos -= 1
                        print("\033[1D", end="", flush=True)  # Move cursor left
        else:  # Regular character
            current_input = current_input[:cursor_pos] + ch + current_input[cursor_pos:]
            cursor_pos += 1
            
            # Redraw the line
            print(f"\r{' ' * (len(prompt) + len(current_input) + 1)}", end="\r", flush=True)
            print(f"{prompt}{current_input}", end="", flush=True)
            if cursor_pos < len(current_input):
                # Move cursor back to position
                print(f"\033[{len(current_input) - cursor_pos}D", end="", flush=True)

def shell():
    print(f"{CYAN}{BOLD}Welcome to the InsurgeNT Shell!{RESET}")
    print(f"Type {YELLOW}'help'{RESET} for commands or {YELLOW}'exit'{RESET} to quit.")

    history_file = os.path.expanduser("~/.insurgent_history")
    load_history(history_file)

    while True:
        try:
            user_input = custom_input(f"{GREEN}➜ InsurgeNT> {RESET}").strip()
            command = user_input.split()
            if user_input:
                add_to_history(user_input)
        except EOFError:
            print(f"\n{MAGENTA}Exiting InsurgeNT Shell. Goodbye!{RESET}")
            break
        except KeyboardInterrupt:
            print(f"\n{CYAN}Use 'exit' to quit the shell.{RESET}")
            continue
        
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
        elif cmd == "history":
            print(f"{CYAN}{BOLD}Command History:{RESET}")
            for i, hist_cmd in enumerate(command_history):
                print(f"{i+1}: {hist_cmd}")
        else:
            print(f"{RED}Unknown command: {command[0]}{RESET}")
            print(f"Type {YELLOW}'help'{RESET} for a list of available commands.")

        save_history(history_file)
