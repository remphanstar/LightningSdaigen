# ~ launch.py | by ANXETY - FINAL CLEAN VERSION ~

import json_utils as js
from IPython import get_ipython
from pathlib import Path
import os
import sys

# --- ENVIRONMENT SETUP ---
osENV = os.environ
CD = os.chdir
ipySys = get_ipython().system

PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME, VENV, SETTINGS_PATH = PATHS['home_path'], PATHS['venv_path'], PATHS['settings_path']

# Load settings from JSON
settings = js.read(SETTINGS_PATH)
UI = settings.get('WEBUI', {}).get('current', 'A1111')
WEBUI = settings.get('WEBUI', {}).get('webui_path', str(HOME / UI))
commandline_arguments = settings.get('WIDGETS', {}).get('commandline_arguments', '')
theme_accent = settings.get('WIDGETS', {}).get('theme_accent', 'anxety')
ENV_NAME = settings.get('ENVIRONMENT', {}).get('env_name')

class COLORS:
    B, X = "\033[34m", "\033[0m"
COL = COLORS

# --- HELPER FUNCTIONS ---
def get_launch_command():
    """Construct the final launch command."""
    common_args = ' --xformers --no-half-vae --enable-insecure-extension-access --disable-console-progressbars --theme dark'
    if ENV_NAME == 'Kaggle':
        common_args += ' --encrypt-pass=emoy4cnkm6imbysp84zmfiz1opahooblh7j34sgh'
    if theme_accent != 'anxety':
        common_args += f" --anxety {theme_accent}"
        
    return f"python3 launch.py {commandline_arguments}{common_args}"

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    print("✅ Environment is ready. Preparing to launch...")
    
    LAUNCHER = get_launch_command()
    
    print(f"🔧 WebUI: {COL.B}{UI}{COL.X}")
    print(f"🚀 Launching with command: {LAUNCHER}")

    try:
        CD(WEBUI)
        ipySys(LAUNCHER)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except Exception as e:
        print(f"\nAn error occurred during launch: {e}")
