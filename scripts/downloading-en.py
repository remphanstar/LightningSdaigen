# ~ downloading-en.py | by ANXETY - Modular Fix Version ~

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
from tqdm import tqdm
import subprocess
import requests
import shutil
import shlex
import time
import json
import sys
import re
import os

# --- Basic Setup ---
osENV = os.environ
CD = os.chdir
ipySys = get_ipython().system
ipyRun = get_ipython().run_line_magic

# --- Constants and Paths ---
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME, VENV_PATH, SCR_PATH = PATHS['home_path'], PATHS['venv_path'], PATHS['scr_path']
SETTINGS_PATH = PATHS['settings_path']
SCRIPTS = SCR_PATH / 'scripts'

# --- Load Settings ---
settings = js.read(SETTINGS_PATH)
UI = settings.get('WEBUI', {}).get('current', 'A1111')
WEBUI_PATH = HOME / UI
locals().update(settings.get('WIDGETS', {}))

# --- FIX: Load Directory Path Variables ---
webui_settings = settings.get('WEBUI', {})
model_dir = webui_settings.get('model_dir')
vae_dir = webui_settings.get('vae_dir')
lora_dir = webui_settings.get('lora_dir')
embed_dir = webui_settings.get('embed_dir')
extension_dir = webui_settings.get('extension_dir')
control_dir = webui_settings.get('control_dir')
upscale_dir = webui_settings.get('upscale_dir')
clip_dir = webui_settings.get('clip_dir')
unet_dir = webui_settings.get('unet_dir')
vision_dir = webui_settings.get('vision_dir')
encoder_dir = webui_settings.get('encoder_dir')
diffusion_dir = webui_settings.get('diffusion_dir')
config_dir = webui_settings.get('config_dir')
adetailer_dir = webui_settings.get('adetailer_dir')


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

# --- DEPENDENCY INSTALLATION (RUNS FIRST) ---
if not js.key_exists(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True):
    print('💿 Installing required libraries...')
    install_lib = {
        'system_packages': "apt-get -y update && apt-get -y install aria2 lz4 pv",
        'gdown': "pip install gdown",
        'tqdm': "pip install tqdm",
        'localtunnel': "npm install -g localtunnel",
        'cloudflared': "wget -qO /usr/bin/cl https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64; chmod +x /usr/bin/cl",
    }
    install_packages(install_lib)
    clear_output()
    js.save(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True)


# --- VENV SETUP (CRITICAL FIX) ---
def setup_venv(drive_url):
    """Downloads, extracts, and correctly renames the venv archive."""
    CD(HOME)
    archive_name = "updated_venv.tar.lz4"
    destination = HOME / archive_name
    extracted_name = HOME / "venv_new"  # This is the actual name inside the archive

    if VENV_PATH.exists():
        print(f"✅ Virtual environment already exists at {VENV_PATH}.")
        return

    # If an old extraction exists, just rename it
    if extracted_name.exists():
        print(f"    Found existing '{extracted_name.name}', renaming to '{VENV_PATH.name}'...")
        shutil.move(extracted_name, VENV_PATH)
        print("✅ Virtual environment setup complete.")
        return

    print("Downloading virtual environment from Google Drive...")
    # Use gdown for reliable Google Drive downloads
    ipySys(f"gdown --fuzzy -O {destination} '{drive_url}'")

    if not destination.exists() or destination.stat().st_size < 1000000:
         raise RuntimeError("Download failed. The venv archive is missing or too small.")

    print("Extracting venv archive...")
    ipySys(f"pv {destination} | lz4 -d | tar xf - -C {HOME}")
    destination.unlink()

    # *** THE FIX: Rename the extracted folder to what the script expects ***
    if extracted_name.exists():
        print(f"    Renaming '{extracted_name.name}' to '{VENV_PATH.name}'...")
        shutil.move(extracted_name, VENV_PATH)
    else:
        # This will now correctly check for VENV_PATH after the potential rename
        if not VENV_PATH.exists():
            raise RuntimeError("Venv extraction failed, target directory not found.")

    print("✅ Virtual environment setup complete.")


# --- Execute Venv Setup with the Corrected Link ---
gdrive_url = "https://drive.google.com/uc?id=19IbRWRE9QZLJMt90kGb6oiWhUdsOTp8r"
setup_venv(gdrive_url)


# --- WEBUI and EXTENSION INSTALLATION ---
if not WEBUI_PATH.exists():
    print(f"⌚ Unpacking Stable Diffusion {UI}...")
    ipyRun('run', f"{SCRIPTS}/webui-installer.py")
else:
    print(f"🔧 WebUI {UI} already exists.")


# --- FULL DOWNLOAD LOGIC ---
print('📦 Downloading models and other assets...')

def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f">>An error occurred in {func.__name__}: {str(e)}")
    return wrapper

model_files = '_xl-models-data.py' if XL_models else '_models-data.py'
try:
    with open(f"{SCRIPTS}/{model_files}") as f:
        exec(f.read())
except Exception as e:
    model_list, vae_list, controlnet_list, lora_list = {}, {}, {}, {}

extension_repo = []
PREFIX_MAP = {
    'model': (model_dir, '$ckpt'), 'vae': (vae_dir, '$vae'), 'lora': (lora_dir, '$lora'),
    'embed': (embed_dir, '$emb'), 'extension': (extension_dir, '$ext'), 'adetailer': (adetailer_dir, '$ad'),
    'control': (control_dir, '$cnet'), 'upscale': (upscale_dir, '$ups'), 'clip': (clip_dir, '$clip'),
    'unet': (unet_dir, '$unet'), 'vision': (vision_dir, '$vis'), 'encoder': (encoder_dir, '$enc'),
    'diffusion': (diffusion_dir, '$diff'), 'config': (config_dir, '$cfg')
}
for dir_path, _ in PREFIX_MAP.values():
    if dir_path: # Ensure the path is not None before creating
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
        token = locals().get('civitai_token', '')
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
        base_url += f"lora:{model['url']} {model['dst_dir']} {model['name']},"
    return base_url

line = ""
line = handle_submodels(model, model_num, model_list, model_dir, line)
line = handle_submodels(vae, vae_num, vae_list, vae_dir, line)
# --- FIX: Corrected the arguments for the lora handle_submodels call ---
line = handle_submodels(lora, None, lora_list, lora_dir, line)
line = handle_submodels(controlnet, controlnet_num, controlnet_list, control_dir, line)

download(line)

if extension_repo:
    print(f"✨ Installing custom extensions...")
    for repo_url, repo_name in extension_repo:
        m_clone(f"{repo_url} {extension_dir} {repo_name}")
    print(f"\r📦 Installed '{len(extension_repo)}' custom extensions!")

print('\r🏁 All downloads complete!')
