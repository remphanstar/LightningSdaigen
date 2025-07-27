# ~ launch.py | by ANXETY - Modular Fix Version ~

import json_utils as js
from IPython import get_ipython
from pathlib import Path
import os
import sys

# --- Environment and Settings ---
osENV = os.environ
CD = os.chdir
ipySys = get_ipython().system

PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME, VENV_PATH, SETTINGS_PATH = PATHS['home_path'], PATHS['venv_path'], PATHS['settings_path']

# --- Load settings from JSON ---
settings = js.read(SETTINGS_PATH)
UI = settings.get('WEBUI', {}).get('current', 'A1111')
WEBUI_PATH = HOME / UI
commandline_arguments = settings.get('WIDGETS', {}).get('commandline_arguments', '')
theme_accent = settings.get('WIDGETS', {}).get('theme_accent', 'anxety')
ENV_NAME = settings.get('ENVIRONMENT', {}).get('env_name')

class COLORS:
    B, X = "\033[34m", "\033[0m"
COL = COLORS

# --- Main Launch Logic ---
print("✅ Preparing to launch...")

# *** THE FIX: Explicitly define the path to the venv's Python executable ***
python_executable = VENV_PATH / 'bin' / 'python3'

if not python_executable.exists():
    raise FileNotFoundError(f"FATAL: Python executable not found at {python_executable}. The venv may be corrupted.")

# --- Construct the full, robust launch command ---
# Combine user-defined arguments with essential ones
base_args = commandline_arguments.split()
essential_args = [
    "--enable-insecure-extension-access",
    "--disable-console-progressbars",
    "--theme", "dark",
    "--skip-prepare-environment" # Prevents webui from trying to reinstall packages
]

# Add Kaggle-specific arguments if needed
if ENV_NAME == 'Kagle':
    essential_args.append('--encrypt-pass=emoy4cnkm6imbysp84zmfiz1opahooblh7j34sgh')

# Add custom theme argument if not the default
if theme_accent != 'anxety':
    essential_args.append(f'--anxety-{theme_accent}')

# Combine and remove duplicates, keeping the user's args first
final_args = list(dict.fromkeys(base_args + essential_args))

launch_command = f"{python_executable} launch.py {' '.join(final_args)}"

print(f"🔧 WebUI: {COL.B}{UI}{COL.X}")
print(f"🚀 Launching with robust command: {launch_command}")

try:
    # Change to the WebUI directory before launching
    CD(WEBUI_PATH)
    # Execute the command
    ipySys(launch_command)
except KeyboardInterrupt:
    print("\nProcess interrupted by user.")
except Exception as e:
    print(f"\nAn error occurred during launch: {e}")
