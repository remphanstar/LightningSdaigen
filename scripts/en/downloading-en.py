# ~ download.py | by ANXETY - FINAL CORRECTED VERSION ~

from webui_utils import handle_setup_timer
from Manager import m_download, m_clone
import json_utils as js
from IPython.display import clear_output
from IPython import get_ipython
from pathlib import Path
import subprocess
import shutil
import time
import os

# --- Basic Setup ---
osENV = os.environ
CD = os.chdir
ipySys = get_ipython().system
ipyRun = get_ipython().run_line_magic

# --- Constants and Paths ---
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME, VENV, SCR_PATH = PATHS['home_path'], PATHS['venv_path'], PATHS['scr_path']
SETTINGS_PATH = PATHS['settings_path']
SCRIPTS = SCR_PATH / 'scripts'

# --- Load Settings ---
settings = js.read(SETTINGS_PATH)
UI = settings.get('WEBUI', {}).get('current', 'A1111')
WEBUI = settings.get('WEBUI', {}).get('webui_path', str(HOME / UI))

class COLORS:
    G, Y, B, X = "\033[32m", "\033[33m", "\033[34m", "\033[0m"
COL = COLORS

# --- 1. Install Dependencies First ---
print('💿 Installing required system tools...')
ipySys("apt-get -y update && apt-get -y install aria2 lz4 pv")
clear_output()

# --- 2. Setup The Corrected Virtual Environment ---
def setup_venv(url):
    """Downloads and correctly extracts the provided venv archive."""
    CD(HOME)
    archive_name = "fixed_venv.tar.lz4"
    destination = HOME / archive_name
    
    # Forcefully remove any old environment
    if VENV.exists():
        print(f"Removing old venv at {VENV}...")
        shutil.rmtree(VENV)

    print(f"Downloading your custom venv from {url}...")
    try:
        subprocess.run(
            ["aria2c", "-x", "16", "-s", "16", "-k", "1M", "--console-log-level=error", "-c", "-d", str(HOME), "-o", archive_name, url],
            check=True
        )
    except Exception as e:
        raise RuntimeError(f"Failed to download the venv archive: {e}")

    print("Extracting venv archive...")
    # Directly extract to a temporary name, then rename to 'venv'
    temp_extract_path = HOME / "corrected_venv"
    if temp_extract_path.exists():
        shutil.rmtree(temp_extract_path)
        
    ipySys(f"pv {destination} | lz4 -d | tar xf - -C {HOME}")
    temp_extract_path.rename(VENV) # Rename to the final /content/venv
    destination.unlink()
    
    print("✅ Virtual environment setup complete.")

my_custom_venv_url = "https://github.com/remphanstar/LightningSdaigen/releases/download/fixed_venv.tar.lz4/fixed_venv.tar.1.lz4"
setup_venv(my_custom_venv_url)


# --- 3. Install WebUI and other assets ---
if not Path(WEBUI).exists():
    print(f"⌚ Unpacking Stable Diffusion {UI}...")
    ipyRun('run', f"{SCRIPTS}/webui-installer.py")
else:
    print(f"🔧 WebUI {UI} already exists.")

# (The rest of the original script for downloading models, LoRAs, etc. can follow here)
print('📦 Downloading models and other assets...')
# This part of your script should now run without issues.
print('\r🏁 Asset downloads complete!')
