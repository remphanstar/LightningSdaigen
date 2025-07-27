# ~ download.py | by ANXETY - PATHING FIX ~

import sys
from pathlib import Path
import os

# --- CRITICAL PATH FIX ---
# The script needs to know where to find its own modules.
# This adds the project's root directory to the Python search path.
# This MUST be done before any other project modules are imported.
project_root = Path(os.getenv('scr_path', '/content/ANXETY'))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
# --- END OF FIX ---

import json_utils as js
import subprocess
import shutil
import re
import time

# Basic setup
osENV = os.environ
CD = os.chdir

# Constants and Paths (now that path is fixed, these will work)
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME, VENV, SCR_PATH = PATHS['home_path'], PATHS['venv_path'], PATHS['scr_path']
SETTINGS_PATH = PATHS['settings_path']
SCRIPTS = SCR_PATH / 'scripts'

# Load Settings
settings = js.read(SETTINGS_PATH)
UI = settings.get('WEBUI', {}).get('current', 'A1111')
WEBUI = settings.get('WEBUI', {}).get('webui_path', str(HOME / UI))
FORK_REPO = js.read(SETTINGS_PATH, 'ENVIRONMENT.fork')
BRANCH = js.read(SETTINGS_PATH, 'ENVIRONMENT.branch')

# Safe import of custom modules with fallback
try:
    from webui_utils import handle_setup_timer
    from Manager import m_download, m_clone
    from CivitaiAPI import CivitAiAPI
except ImportError as e:
    print(f"Warning: Could not import custom modules: {e}")
    # Create dummy functions if imports fail
    def handle_setup_timer(path, timer): return timer
    def m_download(cmd, **kwargs): subprocess.run(['wget', '-O', cmd.split()[-1], cmd.split()[0]], check=False)
    def m_clone(cmd, **kwargs): subprocess.run(['git', 'clone'] + cmd.split(), check=False)
    class CivitAiAPI:
        def __init__(self, token): pass
        def validate_download(self, url, filename=None): return None

# Load widget settings safely
widget_settings = settings.get('WIDGETS', {})
locals().update(widget_settings)


# --- VENV SETUP using requirements.txt ---
def setup_venv():
    """Create a fresh venv and install dependencies from requirements.txt."""
    CD(HOME)
    
    if VENV.exists():
        print(f"🗑️ Removing existing venv at {VENV}...")
        shutil.rmtree(VENV)

    print(f"🌱 Creating a new virtual environment at {VENV}...")
    try:
        subprocess.run([sys.executable, '-m', 'venv', str(VENV)], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FATAL: Failed to create venv. Error:\n{e.stderr}")

    requirements_url = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/requirements.txt"
    requirements_path = SCR_PATH / "requirements.txt"
    print(f"⬇️ Downloading requirements.txt...")
    try:
        subprocess.run(['curl', '-sLo', str(requirements_path), requirements_url], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FATAL: Failed to download requirements.txt. Error:\n{e.stderr}")

    pip_executable = VENV / 'bin' / 'pip'
    print(f"📦 Installing all dependencies from requirements.txt...")
    install_command = f"{pip_executable} install -r {requirements_path}"
    
    process = subprocess.Popen(install_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in iter(process.stdout.readline, ''):
        print(line, end='')
    
    if process.wait() != 0:
        raise RuntimeError("Failed to install dependencies from requirements.txt.")

    print("✅ Virtual environment setup complete.")

# Execute Venv Setup
setup_venv()

# WEBUI and EXTENSION INSTALLATION
if not Path(WEBUI).exists():
    from IPython import get_ipython
    ipyRun = get_ipython().run_line_magic
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
    model_list, vae_list, controlnet_list, lora_list = {}, {}, {}, {}

extension_repo = []
PREFIX_MAP = {
    'model': (widget_settings.get('model_dir', ''), '$ckpt'), 
    'vae': (widget_settings.get('vae_dir', ''), '$vae'), 
    'lora': (widget_settings.get('lora_dir', ''), '$lora'),
    'embed': (widget_settings.get('embed_dir', ''), '$emb'), 
    'extension': (widget_settings.get('extension_dir', ''), '$ext'), 
    'control': (widget_settings.get('control_dir', ''), '$cnet'),
}

for dir_path, _ in PREFIX_MAP.values():
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

@handle_errors
def download(line):
    for link in filter(None, map(str.strip, line.split(','))):
        if ':' in link:
            prefix, url = link.split(':', 1)
            if prefix in PREFIX_MAP:
                dir_path, _ = PREFIX_MAP[prefix]
                if prefix == 'extension':
                    extension_repo.append(url)
                    continue
                manual_download(url, dir_path)

@handle_errors
def manual_download(url, dst_dir):
    m_download(f"{url} {dst_dir}", log=True, unzip=True)

def handle_submodels(selection, model_dict, dst_dir, base_url):
    selected = []
    if selection and selection[0].lower() != 'none':
        if selection[0] == 'ALL':
            selected.extend(model_dict.values())
        else:
            for sel in selection:
                if sel in model_dict:
                    item = model_dict[sel]
                    selected.extend(item if isinstance(item, list) else [item])
    for model in selected:
        base_url += f"{model['url']} {dst_dir}, "
    return base_url

line = ""
line = handle_submodels(widget_settings.get('model', []), model_list, widget_settings.get('model_dir', ''), line)
line = handle_submodels(widget_settings.get('vae', []), vae_list, widget_settings.get('vae_dir', ''), line)
line = handle_submodels(widget_settings.get('lora', []), lora_list, widget_settings.get('lora_dir', ''), line)
line = handle_submodels(widget_settings.get('controlnet', []), controlnet_list, widget_settings.get('control_dir', ''), line)

download(line)

if extension_repo:
    print(f"✨ Installing custom extensions...")
    for repo_url in extension_repo:
        m_clone(f"{repo_url} {widget_settings.get('extension_dir', '')}")
    print(f"\r📦 Installed '{len(extension_repo)}' custom extensions!")

print('\r🏁 All downloads complete!')
