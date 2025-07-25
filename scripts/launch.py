# ~ launch.py | by ANXETY - FINAL CORRECTED VERSION ~

from TunnelHub import Tunnel    # Tunneling
import json_utils as js         # JSON

from IPython.display import clear_output
from IPython import get_ipython
from datetime import timedelta
from pathlib import Path
import nest_asyncio
import subprocess
import requests
import argparse
import logging
import asyncio
import aiohttp
import shlex
import time
import json
import yaml
import sys
import os
import re


osENV = os.environ
CD = os.chdir
ipySys = get_ipython().system

# Constants (auto-convert env vars to Path)
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}   # k -> key; v -> value

HOME = PATHS['home_path']
VENV = PATHS['venv_path']
SCR_PATH = PATHS['scr_path']
SETTINGS_PATH = PATHS['settings_path']

ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')
UI = js.read(SETTINGS_PATH, 'WEBUI.current')
WEBUI = js.read(SETTINGS_PATH, 'WEBUI.webui_path')
EXTS = Path(js.read(SETTINGS_PATH, 'WEBUI.extension_dir'))


nest_asyncio.apply()  # Async support for Jupyter


BIN = str(VENV / 'bin')
PYTHON_VERSION = '3.11' if UI == 'Classic' else '3.10'
PKG = str(VENV / f'lib/python{PYTHON_VERSION}/site-packages')

osENV.update({
    'PATH': f"{BIN}:{osENV['PATH']}" if BIN not in osENV['PATH'] else osENV['PATH'],
    'PYTHONPATH': f"{PKG}:{osENV['PYTHONPATH']}" if PKG not in osENV['PYTHONPATH'] else osENV['PYTHONPATH']
})
# sys.path.insert(0, PKG)


# Text Colors (\033)
class COLORS:
    R  =  "\033[31m"     # Red
    G  =  "\033[32m"     # Green
    Y  =  "\033[33m"     # Yellow
    B  =  "\033[34m"     # Blue
    lB =  "\033[36m"     # lightBlue
    X  =  "\033[0m"      # Reset

COL = COLORS


# =================== loading settings V5 ==================

def load_settings(path):
    """Load settings from a JSON file."""
    try:
        return {
            **js.read(path, 'ENVIRONMENT'),
            **js.read(path, 'WIDGETS'),
            **js.read(path, 'WEBUI')
        }
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading settings: {e}")
        return {}

# Load settings
settings = load_settings(SETTINGS_PATH)
locals().update(settings)


# ==================== Helper Functions ====================

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--log', action='store_true', help='Show failed tunnel details')
    return parser.parse_args()

def _trashing():
    dirs = ['A1111', 'ComfyUI', 'Forge', 'Classic', 'ReForge', 'SD-UX']
    paths = [Path(HOME) / name for name in dirs]

    for path in paths:
        cmd = f"find {path} -type d -name .ipynb_checkpoints -exec rm -rf {{}} +"
        subprocess.run(shlex.split(cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def find_latest_tag_file(target='danbooru'):
    """Find the latest tag file for specified target in TagComplete extension."""
    from datetime import datetime

    possible_names = [
        'a1111-sd-webui-tagcomplete',
        'sd-webui-tagcomplete',
        'webui-tagcomplete',
        'tag-complete',
        'tagcomplete'
    ]

    # Find TagComplete extension directory
    tagcomplete_dir = None
    if EXTS.exists():
        for ext_dir in EXTS.iterdir():
            if ext_dir.is_dir():
                dir_name_lower = ext_dir.name.lower()
                for possible_name in possible_names:
                    if dir_name_lower == possible_name.lower():
                        tagcomplete_dir = ext_dir
                        break
                if tagcomplete_dir:
                    break

    if not tagcomplete_dir:
        return None

    tags_dir = tagcomplete_dir / 'tags'
    if not tags_dir.exists():
        return None

    # Find files matching target pattern
    latest_file = None
    latest_date = None

    for file_path in tags_dir.glob(f"{target}_*.csv"):
        # Extract date from filename
        date_match = re.search(rf"{re.escape(target)}_(\d{{4}}-\d{{2}}-\d{{2}})\.csv$", file_path.name)
        if date_match:
            try:
                file_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                if latest_date is None or file_date > latest_date:
                    latest_date = file_date
                    latest_file = file_path.name
            except ValueError:
                continue

    return latest_file

def _update_config_paths():
    """Update configuration paths in WebUI config file"""
    config_mapping = {
        'tac_tagFile': find_latest_tag_file() or 'danbooru.csv',
        'tagger_hf_cache_dir': f"{WEBUI}/models/interrogators/",
        'ad_extra_models_dir': adetailer_dir,
        # 'sd_checkpoint_hash': '',
        # 'sd_model_checkpoint': '',
        # 'sd_vae': 'None'
    }

    config_file = f"{WEBUI}/config.json"
    for key, value in config_mapping.items():
        if js.key_exists(config_file, key):
            js.update(config_file, key, str(value))
        else:
            js.save(config_file, key, str(value))

def get_launch_command():
    """Construct launch command based on configuration"""
    base_args = commandline_arguments
    password = 'emoy4cnkm6imbysp84zmfiz1opahooblh7j34sgh'

    common_args = ' --enable-insecure-extension-access --disable-console-progressbars --theme dark'
    if ENV_NAME == 'Kaggle':
        common_args += f" --encrypt-pass={password}"

    # Accent Color For Anxety-Theme
    if theme_accent != 'anxety':
        common_args += f" --anxety {theme_accent}"

    if UI == 'ComfyUI':
        return f"python3 main.py {base_args}"
    elif UI == 'FaceFusion':
        return "python run.py"
    elif UI == 'DreamO':
        return "python app.py"
    else:
        return f"python3 launch.py {base_args}{common_args}"


# ======================== Tunneling =======================

class TunnelManager:
    """Class for managing tunnel services"""

    def __init__(self, tunnel_port):
        self.tunnel_port = tunnel_port
        self.tunnels = []
        self.error_reasons = []
        self.public_ip = self._get_public_ip()
        self.checking_queue = asyncio.Queue()
        self.timeout = 10

    def _get_public_ip(self) -> str:
        """Retrieve and cache public IPv4 address"""
        cached_ip = js.read(SETTINGS_PATH, 'ENVIRONMENT.public_ip')
        if cached_ip:
            return cached_ip

        try:
            response = requests.get('https://api64.ipify.org?format=json&ipv4=true', timeout=5)
            public_ip = response.json().get('ip', 'N/A')
            js.update(SETTINGS_PATH, 'ENVIRONMENT.public_ip', public_ip)
            return public_ip
        except Exception as e:
            print(f"Error getting public IP address: {e}")
            return 'N/A'

    async def _print_status(self):
        """Async status printer"""
        print(f"{COL.Y}>> Tunnels:{COL.X}")
        while True:
            service_name = await self.checking_queue.get()
            print(f"- 🕒 Checking {COL.lB}{service_name}{COL.X}...")
            self.checking_queue.task_done()

    async def _test_tunnel(self, name, config):
        """Async tunnel testing"""
        await self.checking_queue.put(name)
        try:
            process = await asyncio.create_subprocess_exec(
                *shlex.split(config['command']),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            start_time = time.time()
            output = []
            pattern_found = False
            check_interval = 0.5

            while time.time() - start_time < self.timeout:
                try:
                    line = await asyncio.wait_for(
                        process.stdout.readline(),
                        timeout=check_interval
                    )
                    if not line:
                        continue

                    line = line.decode().strip()
                    output.append(line)

                    if config['pattern'].search(line):
                        pattern_found = True
                        break

                except asyncio.TimeoutError:
                    continue

            if process.returncode is None:
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=2)
                except:
                    pass

            if pattern_found:
                return True, None

            error_msg = '\n'.join(output[-3:]) or 'No output received'
            return False, f"{error_msg[:300]}..."

        except Exception as e:
            return False, f"Process error: {str(e)}"

    async def setup_tunnels(self):
        """Async tunnel configuration"""
        services = [
            ('Gradio', {
                'command': f"gradio-tun {self.tunnel_port}",
                'pattern': re.compile(r'[\w-]+\.gradio\.live')
            }),
            ('Pinggy', {
                'command': f"ssh -o StrictHostKeyChecking=no -p 80 -R0:localhost:{self.tunnel_port} a.pinggy.io",
                'pattern': re.compile(r'[\w-]+\.a\.free\.pinggy\.link')
            }),
            ('Cloudflared', {
                'command': f"cl tunnel --url localhost
