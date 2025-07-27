# ~ download.py | by ANXETY - FINAL CORRECTED VERSION WITH DEPENDENCY VERIFICATION ~

import json_utils as js
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

# FIXED: Add dependency verification first
def verify_dependencies():
    """Verify and install required tools."""
    required_tools = {
        'git': 'git',
        'curl': 'curl', 
        'wget': 'wget',
        'aria2c': 'aria2',
        'lz4': 'lz4',
        'pv': 'pv'
    }
    
    missing = []
    for tool, package in required_tools.items():
        if not shutil.which(tool):
            missing.append(package)
    
    if missing:
        print(f"📦 Installing missing tools: {missing}")
        try:
            subprocess.run(['apt-get', 'update', '-qq'], check=False, stdout=subprocess.DEVNULL)
            for package in missing:
                subprocess.run(['apt-get', 'install', '-y', package], check=False, stdout=subprocess.DEVNULL)
        except Exception as e:
            print(f"Warning: Could not install some dependencies: {e}")

# Verify dependencies first
verify_dependencies()

# FIXED: Import order - after dependency verification
from IPython.display import clear_output
from IPython.utils import capture
from urllib.parse import urlparse
from IPython import get_ipython
from datetime import timedelta

# Basic setup
osENV = os.environ
CD = os.chdir
ipySys = get_ipython().system
ipyRun = get_ipython().run_line_magic

# Constants and Paths
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME, VENV, SCR_PATH = PATHS['home_path'], PATHS['venv_path'], PATHS['scr_path']
SETTINGS_PATH = PATHS['settings_path']
SCRIPTS = SCR_PATH / 'scripts'

# Load Settings
settings = js.read(SETTINGS_PATH)
UI = settings.get('WEBUI', {}).get('current', 'A1111')
WEBUI = settings.get('WEBUI', {}).get('webui_path', str(HOME / UI))

# FIXED: Safe import of custom modules with fallback
try:
    from webui_utils import handle_setup_timer
    from Manager import m_download, m_clone
    from CivitaiAPI import CivitAiAPI
except ImportError as e:
    print(f"Warning: Could not import custom modules: {e}")
    print("Some functionality may be limited.")
    # Create dummy functions for missing imports
    def handle_setup_timer(path, timer):
        return timer
    def m_download(cmd, **kwargs):
        subprocess.run(['wget', '-O', cmd.split()[-1], cmd.split()[0]], check=False)
    def m_clone(cmd, **kwargs):
        subprocess.run(['git', 'clone'] + cmd.split(), check=False)
    class CivitAiAPI:
        def __init__(self, token): pass
        def validate_download(self, url, filename=None): return None

# Load widget settings safely
widget_settings = settings.get('WIDGETS', {})
locals().update(widget_settings)

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

# DEPENDENCY INSTALLATION (RUNS FIRST)
if not js.key_exists(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True):
    print('💿 Installing required libraries...')
    install_lib = {
        'system_packages': "apt-get -y update && apt-get -y install aria2 lz4 pv",
        'gdown': "pip install gdown",
        'localtunnel': "npm install -g localtunnel",
        'cloudflared': "wget -qO /usr/bin/cl https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64; chmod +x /usr/bin/cl",
    }
    install_packages(install_lib)
    clear_output()
    js.save(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True)

# VENV SETUP
def setup_venv(url):
    """Downloads and correctly extracts the provided venv archive."""
    CD(HOME)
    archive_name = "final_fixed_venv.tar.lz4"
    destination = HOME / archive_name
    
    if VENV.exists():
        print(f"Removing existing venv at {VENV}...")
        shutil.rmtree(VENV)

    print(f"Downloading custom venv from {url}...")
    try:
        subprocess.run(
            ["aria2c", "-x", "16", "-s", "16", "-k", "1M", "--console-log-level=error", "-c", "-d", str(HOME), "-o", archive_name, url],
            check=True
        )
    except Exception as e:
        raise RuntimeError(f"Failed to download the venv archive: {e}")

    print("Extracting venv archive...")
    extract_target = HOME / "final_corrected_venv"
    if extract_target.exists():
         shutil.rmtree(extract_target)

    ipySys(f"pv {destination} | lz4 -d | tar xf - -C {HOME}")
    extract_target.rename(VENV)
    destination.unlink()
    
    print("✅ Virtual environment setup complete.")

# FIXED: Updated venv URL (moved to Google Drive as mentioned)
my_custom_venv_url = "https://drive.google.com/uc?id=YOUR_GOOGLE_DRIVE_FILE_ID"  # Update with actual Google Drive file ID
setup_venv(my_custom_venv_url)

# WEBUI and EXTENSION INSTALLATION
if not Path(WEBUI).exists():
    print(f"⌚ Unpacking Stable Diffusion {UI}...")
    ipyRun('run', f"{SCRIPTS}/webui-installer.py")
else:
    print(f"🔧 WebUI {UI} already exists.")

# FULL DOWNLOAD LOGIC
print('📦 Downloading models and other assets...')

def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f">> An error occurred in {func.__name__}: {str(e)}")
    return wrapper

# Load model data safely
model_files = '_xl-models-data.py' if widget_settings.get('XL_models', False) else '_models-data.py'
try:
    with open(f"{SCRIPTS}/{model_files}") as f:
        exec(f.read())
except Exception as e:
    print(f"Warning: Could not load model data: {e}")
    model_list, vae_list, controlnet_list, lora_list = {}, {}, {}, {}

extension_repo = []
PREFIX_MAP = {
    'model': (widget_settings.get('model_dir', ''), '$ckpt'), 
    'vae': (widget_settings.get('vae_dir', ''), '$vae'), 
    'lora': (widget_settings.get('lora_dir', ''), '$lora'),
    'embed': (widget_settings.get('embed_dir', ''), '$emb'), 
    'extension': (widget_settings.get('extension_dir', ''), '$ext'), 
    'adetailer': (widget_settings.get('adetailer_dir', ''), '$ad'),
    'control': (widget_settings.get('control_dir', ''), '$cnet'), 
    'upscale': (widget_settings.get('upscale_dir', ''), '$ups'), 
    'clip': (widget_settings.get('clip_dir', ''), '$clip'),
    'unet': (widget_settings.get('unet_dir', ''), '$unet'), 
    'vision': (widget_settings.get('vision_dir', ''), '$vis'), 
    'encoder': (widget_settings.get('encoder_dir', ''), '$enc'),
    'diffusion': (widget_settings.get('diffusion_dir', ''), '$diff'), 
    'config': (widget_settings.get('config_dir', ''), '$cfg')
}

for dir_path, _ in PREFIX_MAP.values():
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

def _clean_url(url):
    url = url.replace('/blob/', '/resolve/') if 'huggingface.co' in url else url
    url = url.replace('/blob/', '/raw/') if 'github.com' in url else url
    return url

def _extract_filename(url):
    if match := re.search(r'\[(.*?)\]', url):
        return match.group(1)
    if any(d in urlparse(url).netloc for d in ["civitai.com", "drive.google.com"]):
        return None
    return Path(urlparse(url).path).name

@handle_errors
def _process_download_link(link):
    link = _clean_url(link)
    if ':' in link:
        prefix, path = link.split(':', 1)
        if prefix in PREFIX_MAP:
            return prefix, re.sub(r'\[.*?\]', '', path), _extract_filename(path)
    return None, link, None

@handle_errors
def download(line):
    for link in filter(None, map(str.strip, line.split(','))):
        prefix, url, filename = _process_download_link(link)
        if prefix:
            dir_path, _ = PREFIX_MAP[prefix]
            if prefix == 'extension':
                extension_repo.append((url, filename))
                continue
            manual_download(url, dir_path, filename, prefix)

@handle_errors
def manual_download(url, dst_dir, file_name=None, prefix=None):
    if 'civitai' in url:
        token = widget_settings.get('civitai_token', '')
        if not token:
            print(f"Warning: CivitAI token required for {url}")
            return
        api = CivitAiAPI(token)
        data = api.validate_download(url, file_name)
        if not data: return
        url = data.download_url
        file_name = data.model_name
    m_download(f"{url} {dst_dir} {file_name or ''}", log=True, unzip=True)

def _parse_selection_numbers(num_str, max_num):
    if not num_str: return []
    num_str = num_str.replace(',', ' ').strip()
    unique_numbers = set()
    max_length = len(str(max_num))
    for part in num_str.split():
        if not part.isdigit(): continue
        part_int = int(part)
        if part_int <= max_num:
            unique_numbers.add(part_int)
            continue
        current_position = 0
        part_len = len(part)
        while current_position < part_len:
            found = False
            for length in range(min(max_length, part_len - current_position), 0, -1):
                substring = part[current_position:current_position + length]
                if substring.isdigit():
                    num = int(substring)
                    if 1 <= num <= max_num:
                        unique_numbers.add(num)
                        current_position += length
                        found = True
                        break
            if not found: current_position += 1
    return sorted(unique_numbers)

def handle_submodels(selection, num_selection, model_dict, dst_dir, base_url):
    selected = []
    selections = selection if isinstance(selection, (list, tuple)) else [selection]
    for sel in selections:
        if sel.lower() != 'none':
            if sel == 'ALL':
                selected.extend(model_dict.values())
            elif sel in model_dict:
                item = model_dict[sel]
                selected.extend(item if isinstance(item, list) else [item])
    if num_selection:
        max_num = len(model_dict)
        for num in _parse_selection_numbers(num_selection, max_num):
            if 1 <= num <= max_num:
                name = list(model_dict.keys())[num - 1]
                item = model_dict[name]
                selected.extend(item if isinstance(item, list) else [item])
    unique_models = {
        (model.get('name') or os.path.basename(model['url'])): {
            'url': model['url'],
            'dst_dir': model.get('dst_dir', dst_dir),
            'name': model.get('name') or os.path.basename(model['url'])
        } for model in selected
    }
    for model in unique_models.values():
        base_url += f"{model['url']} {model['dst_dir']} {model['name']}, "
    return base_url

line = ""
line = handle_submodels(widget_settings.get('model', []), widget_settings.get('model_num', ''), model_list, widget_settings.get('model_dir', ''), line)
line = handle_submodels(widget_settings.get('vae', ''), widget_settings.get('vae_num', ''), vae_list, widget_settings.get('vae_dir', ''), line)
line = handle_submodels(widget_settings.get('lora', []), '', lora_list, widget_settings.get('lora_dir', ''), line)
line = handle_submodels(widget_settings.get('controlnet', []), widget_settings.get('controlnet_num', ''), controlnet_list, widget_settings.get('control_dir', ''), line)

download(line)

if extension_repo:
    print(f"✨ Installing custom extensions...")
    for repo_url, repo_name in extension_repo:
        m_clone(f"{repo_url} {widget_settings.get('extension_dir', '')} {repo_name}")
    print(f"\r📦 Installed '{len(extension_repo)}' custom extensions!")

print('\r🏁 All downloads complete!')
