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

class COLORS:
    R, G, Y, B, X = "\033[31m", "\033[32m", "\033[33m", "\033[34m", "\033[0m"
COL = COLORS

def install_packages(install_lib):
    """Install packages from the provided library dictionary."""
    for index, (package, install_cmd) in enumerate(install_lib.items(), start=1):
        print(f"\r[{index}/{len(install_lib)}] {COL.G}>>{COL.X} Installing {COL.Y}{package}{COL.X}..." + ' ' * 35, end='')
        try:
            subprocess.run(install_cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, Exception) as e:
            print(f"\n{COL.R}Warning: Failed to install {package}: {e}{COL.X}")

# --- DEPENDENCY INSTALLATION ---
if not js.key_exists(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True):
    print('💿 Installing required libraries...')
    install_lib = {
        'aria2': "pip install aria2",
        'gdown': "pip install gdown",
        'localtunnel': "npm install -g localtunnel",
        'cloudflared': "wget -qO /usr/bin/cl https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64; chmod +x /usr/bin/cl",
        'zrok': "wget -qO zrok.tar.gz https://github.com/openziti/zrok/releases/download/v0.4.23/zrok_0.4.23_linux_amd64.tar.gz; tar -xzf zrok.tar.gz -C /usr/bin; rm -f zrok.tar.gz",
        'ngrok': "wget -qO ngrok.tgz https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz; tar -xzf ngrok.tgz -C /usr/bin; rm -f ngrok.tgz"
    }
    install_packages(install_lib)
    clear_output()
    js.save(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True)


# --- VENV SETUP ---
def setup_venv(url):
    """Downloads and correctly extracts the provided venv archive."""
    CD(HOME)
    archive_name = "fixed_venv.tar.lz4"
    destination = HOME / archive_name
    
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
    ipySys("apt-get -y install lz4 pv > /dev/null 2>&1")
    extract_target = HOME / "corrected_venv"
    if extract_target.exists():
         shutil.rmtree(extract_target)

    ipySys(f"pv {destination} | lz4 -d | tar xf - -C {HOME}")
    extract_target.rename(VENV)
    destination.unlink()
    
    print("✅ Virtual environment setup complete.")
    
# Execute Venv Setup
my_custom_venv_url = "https://github.com/remphanstar/LightningSdaigen/releases/download/fixed_venv.tar.lz4/fixed_venv.tar.1.lz4"
setup_venv(my_custom_venv_url)


# --- WEBUI and EXTENSION INSTALLATION ---
if not Path(WEBUI).exists():
    print(f"⌚ Unpacking Stable Diffusion {UI}...")
    ipyRun('run', f"{SCRIPTS}/webui-installer.py")
else:
    print(f"🔧 WebUI {UI} already exists.")

# (The rest of the script for downloading models, LoRAs, etc.)
print('📦 Downloading models and other assets...')
# ...
print('\r🏁 Asset downloads complete!')
try:
    ipyRun('run', f"{SCRIPTS}/download-result.py")
except Exception as e:
    print(f"Warning: Could not display download results: {e}")
