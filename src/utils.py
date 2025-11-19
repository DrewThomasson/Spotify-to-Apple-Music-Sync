import os
import sys
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def log_info(msg):
    print(f"{Fore.CYAN}ℹ️  {msg}{Style.RESET_ALL}")

def log_success(msg):
    print(f"{Fore.GREEN}✅ {msg}{Style.RESET_ALL}")

def log_warning(msg):
    print(f"{Fore.YELLOW}⚠️  {msg}{Style.RESET_ALL}")

def log_error(msg):
    print(f"{Fore.RED}❌ {msg}{Style.RESET_ALL}")

def ensure_dir(path):
    """Ensures a directory exists, creates it if not."""
    expanded_path = os.path.expanduser(path)
    if not os.path.exists(expanded_path):
        os.makedirs(expanded_path)
    return expanded_path

def ask_user(question, default='y'):
    """Simple Y/N prompt."""
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    prompt = " [Y/n] " if default == 'y' else " [y/N] "
    
    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' (or 'y'/'n').\n")
