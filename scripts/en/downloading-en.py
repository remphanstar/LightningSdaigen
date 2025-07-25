# ~ download.py | by ANXETY - FINAL CORRECTED VERSION ~

from webui_utils import handle_setup_timer
from Manager import m_download, m_clone
from CivitaiAPI import CivitAiAPI
import json_utils as js

from IPython.display import clear_output
from IPython.utils import capture
from urllib.parse import urlparse
from IPython import get_ipython
from datetime import timedelta
from pathlib import Path
import subprocess
import requests
import shutil
import shlex
import time
import json
import sys
import re
import os

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
locals().update(settings.get('WIDGETS', {}))

# --- VENV SETUP ---
def setup_venv(url):
    """Downloads and correctly extracts the provided venv archive."""
    CD(HOME)
    archive_name = "fixed_venv.tar.lz4"
    destination = HOME / archive_name
    
    # Forcefully remove any old environment to ensure a clean slate
    if VENV.exists():
        print(f"Removing existing venv at {VENV}...")
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
    # Extract and then move to the correct final destination
    extract_target = HOME / "temp_venv_extraction"
    if extract_target.exists():
        shutil.rmtree(extract_target)
    extract_target.mkdir()

    ipySys(f"pv {destination} | lz4 -d | tar xf - -C {extract_target}")
    
    # Find the extracted directory (should only be one)
    extracted_dirs = [d for d in extract_target.iterdir() if d.is_dir()]
    if not extracted_dirs:
        raise RuntimeError("Extraction failed: No directory found inside the archive.")
    
    # Move the extracted content to the final venv path
    extracted_dirs[0].rename(VENV)
    
    # Cleanup
    shutil.rmtree(extract_target)
    destination.unlink()
    
    print("✅ Virtual environment setup complete.")
    
# Execute Venv Setup
my_custom_venv_url = "https://github.com/remphanstar/LightningSdaigen/releases/download/fixed_venv.tar.lz4/fixed_venv.tar.1.lz4"
setup_venv(my_custom_venv_url)


# --- WEBUI and EXTENSION INSTALLATION (Simplified) ---
if not Path(WEBUI).exists():
    print(f"⌚ Unpacking Stable Diffusion {UI}...")
    ipyRun('run', f"{SCRIPTS}/webui-installer.py")
else:
    print(f"🔧 WebUI {UI} already exists.")

# (The rest of the script for downloading models, LoRAs, etc. remains the same)
print('📦 Downloading models and other assets...')
# ... existing download logic for models ...
print('\r🏁 Asset downloads complete!')
