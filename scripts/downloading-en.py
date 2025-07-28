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

# FIXED: Load both WIDGETS and WEBUI settings
settings = js.read(SETTINGS_PATH)
UI = settings.get('WEBUI', {}).get('current', 'A1111')
WEBUI = settings.get('WEBUI', {}).get('webui_path', str(HOME / UI))
FORK_REPO = js.read(SETTINGS_PATH, 'ENVIRONMENT.fork')
BRANCH = js.read(SETTINGS_PATH, 'ENVIRONMENT.branch')

# Load widget settings (selections) and webui settings (paths) separately
widget_settings = settings.get('WIDGETS', {})
webui_settings = settings.get('WEBUI', {})

# DEBUG: Print what we found
print("=== DEBUG: Settings Content ===")
print("WIDGETS keys:", list(widget_settings.keys()))
print("WEBUI keys:", list(webui_settings.keys()))
print("")
print("=== SELECTIONS MADE ===")
print("Selected models:", widget_settings.get('model', 'NOT_FOUND'))
print("Model numbers:", widget_settings.get('model_num', 'NOT_FOUND'))
print("Selected VAE:", widget_settings.get('vae', 'NOT_FOUND'))
print("VAE numbers:", widget_settings.get('vae_num', 'NOT_FOUND'))
print("Selected LoRAs:", widget_settings.get('lora', 'NOT_FOUND'))
print("Selected ControlNets:", widget_settings.get('controlnet', 'NOT_FOUND'))
print("ControlNet numbers:", widget_settings.get('controlnet_num', 'NOT_FOUND'))
print("SDXL mode:", widget_settings.get('XL_models', 'NOT_FOUND'))
print("Inpainting mode:", widget_settings.get('inpainting_model', 'NOT_FOUND'))
print("")
print("=== TOKENS & AUTHENTICATION ===")
civitai_token = widget_settings.get('civitai_token', '')
hf_token = widget_settings.get('huggingface_token', '')
print(f"CivitAI token: {'✅ Set (' + civitai_token[:8] + '...)' if civitai_token else '❌ Not set'}")
print(f"HuggingFace token: {'✅ Set (' + hf_token[:8] + '...)' if hf_token else '❌ Not set'}")
print("")
print("=== DIRECTORY PATHS ===")
print("Model directory:", webui_settings.get('model_dir', 'NOT_FOUND'))
print("VAE directory:", webui_settings.get('vae_dir', 'NOT_FOUND'))
print("LoRA directory:", webui_settings.get('lora_dir', 'NOT_FOUND'))
print("ControlNet directory:", webui_settings.get('control_dir', 'NOT_FOUND'))
print("")
print("=== CUSTOM URLS ===")
print("Empowerment mode:", widget_settings.get('empowerment', 'NOT_FOUND'))
print("Empowerment output:", widget_settings.get('empowerment_output', 'NOT_FOUND'))
print("Custom Model URLs:", widget_settings.get('Model_url', 'NOT_FOUND'))
print("Custom VAE URLs:", widget_settings.get('Vae_url', 'NOT_FOUND'))
print("Custom LoRA URLs:", widget_settings.get('LoRA_url', 'NOT_FOUND'))
print("Custom Extension URLs:", widget_settings.get('Extensions_url', 'NOT_FOUND'))
print("Custom file URLs:", widget_settings.get('custom_file_urls', 'NOT_FOUND'))
print("================================")

# Apply widget settings to local scope for backward compatibility
locals().update(widget_settings)

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

class COLORS:
    R, G, Y, B, X = "\033[31m", "\033[32m", "\033[33m", "\033[34m", "\033[0m"
COL = COLORS

# --- VENV SETUP using requirements.txt ---
def setup_venv():
    """Create a virtual environment if it doesn't exist and install dependencies."""
    CD(HOME)

    if VENV.exists():
        print(f"✅ Virtual environment already exists at {VENV}. Skipping creation.")
        return

    print(f"🌱 Creating a new virtual environment at {VENV}...")
    try:
        # Create venv without pip to avoid ensurepip errors in some environments
        subprocess.run([sys.executable, '-m', 'venv', str(VENV), '--without-pip'], check=True, capture_output=True, text=True)

        # Manually install pip using get-pip.py
        get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
        get_pip_path = SCR_PATH / "get-pip.py"

        # Download get-pip.py
        subprocess.run(['curl', '-sLo', str(get_pip_path), get_pip_url], check=True)

        # Run get-pip.py with the venv's python
        venv_python = VENV / 'bin' / 'python'
        subprocess.run([str(venv_python), str(get_pip_path)], check=True, capture_output=True, text=True)

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FATAL: Failed to create the virtual environment. Error:\n{e.stderr}")

    requirements_path = SCRIPTS / "requirements.txt"
    if not requirements_path.exists():
        raise RuntimeError(f"FATAL: requirements.txt not found at {requirements_path}")

    pip_executable = VENV / 'bin' / 'pip'
    print(f"📦 Installing all dependencies from {requirements_path}...")
    install_command = f"{pip_executable} install -r {requirements_path}"

    process = subprocess.Popen(install_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in iter(process.stdout.readline, ''):
        print(line, end='')

    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError("Failed to install dependencies from requirements.txt.")

    print("✅ Virtual environment setup complete.")


# Execute Venv Setup
setup_venv()

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
    print(f"✅ Loaded model data from {model_files}")
    print(f"   Models available: {len(model_list)} - {list(model_list.keys())[:3]}...")
    print(f"   VAEs available: {len(vae_list)} - {list(vae_list.keys())[:3]}...")
    print(f"   LoRAs available: {len(lora_list)} - {list(lora_list.keys())[:3]}...")
    print(f"   ControlNets available: {len(controlnet_list)} - {list(controlnet_list.keys())[:3]}...")
except Exception as e:
    print(f"Warning: Could not load model data: {e}")
    model_list, vae_list, controlnet_list, lora_list = {}, {}, {}, {}

extension_repo = []

# FIXED: Use webui_settings for directory paths
PREFIX_MAP = {
    'model': (webui_settings.get('model_dir', ''), '$ckpt'),
    'vae': (webui_settings.get('vae_dir', ''), '$vae'),
    'lora': (webui_settings.get('lora_dir', ''), '$lora'),
    'embed': (webui_settings.get('embed_dir', ''), '$emb'),
    'extension': (webui_settings.get('extension_dir', ''), '$ext'),
    'adetailer': (webui_settings.get('adetailer_dir', ''), '$ad'),
    'control': (webui_settings.get('control_dir', ''), '$cnet'),
    'upscale': (webui_settings.get('upscale_dir', ''), '$ups'),
    'clip': (webui_settings.get('clip_dir', ''), '$clip'),
    'unet': (webui_settings.get('unet_dir', ''), '$unet'),
    'vision': (webui_settings.get('vision_dir', ''), '$vis'),
    'encoder': (webui_settings.get('encoder_dir', ''), '$enc'),
    'diffusion': (webui_settings.get('diffusion_dir', ''), '$diff'),
    'config': (webui_settings.get('config_dir', ''), '$cfg')
}

# DEBUG: Print directory paths
print("=== DEBUG: Directory Paths ===")
for key, (path, prefix) in PREFIX_MAP.items():
    print(f"{key}: {path}")
print("===============================")

for dir_path, _ in PREFIX_MAP.values():
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
        print(f"📁 Created directory: {dir_path}")

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
def manual_download(url, dst_dir, file_name=None, prefix=None):
    print(f"🔧 manual_download called with:")
    print(f"   URL: {url}")
    print(f"   Directory: {dst_dir}")
    print(f"   Filename: {file_name}")
    print(f"   Prefix: {prefix}")

    if 'civitai' in url:
        token = widget_settings.get('civitai_token', '')
        if not token:
            print(f"Warning: CivitAI token required for {url}")
            return
        print(f"🎯 Processing CivitAI URL...")
        api = CivitAiAPI(token)
        data = api.validate_download(url, file_name)
        if not data:
            print(f"❌ Failed to get CivitAI download data for {url}")
            return
        url = data.download_url
        file_name = data.model_name
        print(f"✅ CivitAI processed: {file_name}")

    print(f"⬇️ Downloading: {file_name or 'file'} to {dst_dir}")
    download_cmd = f"{url} {dst_dir} {file_name or ''}"
    print(f"📋 m_download command: '{download_cmd}'")
    m_download(download_cmd, log=widget_settings.get('detailed_download') == 'on', unzip=True)

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

    print(f"🔍 Processing selection: {selections}")
    print(f"📊 Available in {type(model_dict).__name__}: {list(model_dict.keys())[:5]}..." if model_dict else "Empty model dict")

    for sel in selections:
        if sel.lower() != 'none':
            if sel == 'ALL':
                selected.extend(model_dict.values())
                print(f"✅ Selected ALL items ({len(model_dict)} total)")
            elif sel in model_dict:
                item = model_dict[sel]
                selected.extend(item if isinstance(item, list) else [item])
                print(f"✅ Selected: {sel}")
            else:
                print(f"⚠️ Selection '{sel}' not found in model dictionary")

    if num_selection:
        max_num = len(model_dict)
        numbers = _parse_selection_numbers(num_selection, max_num)
        print(f"🔢 Processing numbers: {numbers}")
        for num in numbers:
            if 1 <= num <= max_num:
                name = list(model_dict.keys())[num - 1]
                item = model_dict[name]
                selected.extend(item if isinstance(item, list) else [item])
                print(f"✅ Selected by number {num}: {name}")

    unique_models = {
        (model.get('name') or os.path.basename(model['url'])): {
            'url': model['url'],
            'dst_dir': model.get('dst_dir', dst_dir),
            'name': model.get('name') or os.path.basename(model['url'])
        } for model in selected
    }

    print(f"📋 Final selection: {len(unique_models)} unique models")

    # Build download entries list instead of string concatenation
    download_entries = []
    for model in unique_models.values():
        entry = f"{model['url']} {model['dst_dir']} {model['name']}"
        download_entries.append(entry)
        print(f"   - {model['name']} -> {model['dst_dir']}")

    # Join entries with proper comma separation
    if download_entries:
        if base_url:
            base_url += ", " + ", ".join(download_entries)
        else:
            base_url = ", ".join(download_entries)

    return base_url

# Process downloads
line = ""

# Quick check if anything is selected
if not any([
    widget_settings.get('model'),
    widget_settings.get('vae'),
    widget_settings.get('lora'),
    widget_settings.get('controlnet'),
    any(widget_settings.get(url_key, '') for url_key in ['Model_url', 'Vae_url', 'LoRA_url', 'Extensions_url'])
]):
    print("⚠️ WARNING: No models, VAEs, LoRAs, or custom URLs appear to be selected!")
    print("Please check your selections in Cell 2 (widgets) before running this cell.")
else:
    print("✅ Found selections, processing downloads...")

# FIXED: Use webui_settings for directory paths in downloads
print("\n🎯 Processing model selections...")
line = handle_submodels(
    widget_settings.get('model', []),
    widget_settings.get('model_num', ''),
    model_list,
    webui_settings.get('model_dir', ''),
    line
)

print("\n🎨 Processing VAE selections...")
line = handle_submodels(
    widget_settings.get('vae', ''),
    widget_settings.get('vae_num', ''),
    vae_list,
    webui_settings.get('vae_dir', ''),
    line
)

print("\n✨ Processing LoRA selections...")
line = handle_submodels(
    widget_settings.get('lora', []),
    '',
    lora_list,
    webui_settings.get('lora_dir', ''),
    line
)

print("\n🎮 Processing ControlNet selections...")
line = handle_submodels(
    widget_settings.get('controlnet', []),
    widget_settings.get('controlnet_num', ''),
    controlnet_list,
    webui_settings.get('control_dir', ''),
    line
)

print(f"\n📦 Final download line: {line[:200]}..." if len(line) > 200 else f"\n📦 Final download line: {line}")

if line.strip():
    print("🚀 Starting downloads...")
    # Use m_download directly since line is in "URL DIR FILENAME" format
    m_download(line, log=True, unzip=True)
else:
    print("⚠️ No models selected for download")

# Handle custom URLs
custom_downloads = []

# Check empowerment mode first
if widget_settings.get('empowerment', False):
    empowerment_text = widget_settings.get('empowerment_output', '')
    if empowerment_text:
        print("🚀 Processing empowerment mode content...")
        # Parse empowerment text for special tags
        lines = empowerment_text.strip().split('\n')
        current_prefix = None

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Check for short tags ($ckpt, $vae, etc.)
            for prefix, (_, short_tag) in PREFIX_MAP.items():
                if line.startswith(short_tag):
                    current_prefix = prefix
                    continue

            # Check for long tags
            if line.lower() in ['model', 'ckpt']:
                current_prefix = 'model'
                continue
            elif line.lower() in ['vae']:
                current_prefix = 'vae'
                continue
            elif line.lower() in ['lora']:
                current_prefix = 'lora'
                continue
            elif line.lower() in ['embed', 'emb']:
                current_prefix = 'embed'
                continue
            elif line.lower() in ['extension', 'ext']:
                current_prefix = 'extension'
                continue
            elif line.lower() in ['adetailer', 'ad']:
                current_prefix = 'adetailer'
                continue
            elif line.lower() in ['control', 'cnet']:
                current_prefix = 'control'
                continue
            elif line.lower() in ['upscale', 'ups']:
                current_prefix = 'upscale'
                continue
            elif line.lower() in ['clip']:
                current_prefix = 'clip'
                continue
            elif line.lower() in ['unet']:
                current_prefix = 'unet'
                continue
            elif line.lower() in ['vision', 'vis']:
                current_prefix = 'vision'
                continue
            elif line.lower() in ['encoder', 'enc']:
                current_prefix = 'encoder'
                continue
            elif line.lower() in ['diffusion', 'diff']:
                current_prefix = 'diffusion'
                continue
            elif line.lower() in ['config', 'cfg']:
                current_prefix = 'config'
                continue

            # If it's a URL and we have a prefix, add it
            if line.startswith('http') and current_prefix:
                custom_downloads.append(f"{current_prefix}:{line}")
                print(f"   📎 Added {current_prefix}: {line}")
            elif line.startswith('http'):
                custom_downloads.append(line)
                print(f"   📎 Added: {line}")
else:
    # Regular custom URL processing
    custom_downloads = [
        widget_settings.get('Model_url', ''),
        widget_settings.get('Vae_url', ''),
        widget_settings.get('LoRA_url', ''),
        widget_settings.get('Embedding_url', ''),
        widget_settings.get('Extensions_url', ''),
        widget_settings.get('ADetailer_url', ''),
        widget_settings.get('custom_file_urls', '')
    ]

custom_line = ', '.join(filter(None, custom_downloads))
if custom_line:
    print("🌐 Processing custom URLs...")
    # Process custom URLs with prefix handling
    for link in filter(None, map(str.strip, custom_line.split(','))):
        prefix, url, filename = _process_download_link(link)
        if prefix:
            dir_path, _ = PREFIX_MAP[prefix]
            if prefix == 'extension':
                extension_repo.append((url, filename))
                continue
            manual_download(url, dir_path, filename, prefix)
        else:
            # Handle raw URLs without prefix
            manual_download(link, '')

if extension_repo:
    print(f"✨ Installing custom extensions...")
    for repo_url, repo_name in extension_repo:
        m_clone(f"{repo_url} {webui_settings.get('extension_dir', '')} {repo_name}")
    print(f"\r📦 Installed '{len(extension_repo)}' custom extensions!")

print('\r🏁 All downloads complete!')
