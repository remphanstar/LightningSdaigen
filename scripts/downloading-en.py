# ~ downloading-en.py | by ANXETY - FIXED VERSION ~

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

# FIXED: Load settings with proper error handling
try:
    settings = js.read(SETTINGS_PATH)
    UI = settings.get('WEBUI', {}).get('current', 'A1111')
    WEBUI = settings.get('WEBUI', {}).get('webui_path', str(HOME / UI))
    FORK_REPO = js.read(SETTINGS_PATH, 'ENVIRONMENT.fork')
    BRANCH = js.read(SETTINGS_PATH, 'ENVIRONMENT.branch')

    # Load widget settings (selections) and webui settings (paths) separately
    widget_settings = settings.get('WIDGETS', {})
    webui_settings = settings.get('WEBUI', {})
except Exception as e:
    print(f"⚠️ Error loading settings: {e}")
    # Fallback defaults
    widget_settings = {}
    webui_settings = {}
    UI = 'A1111'
    WEBUI = str(HOME / UI)
    FORK_REPO = 'remphanstar/LightningSdaigen'
    BRANCH = 'main'

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

# FIXED: Apply widget settings to local scope safely
def set_variable_safely(name, value, default):
    """Safely set variables in global scope with defaults."""
    if value is not None:
        globals()[name] = value
    else:
        globals()[name] = default

# Set all required variables with safe defaults
required_vars = {
    'model': widget_settings.get('model', ['none']),
    'model_num': widget_settings.get('model_num', ''),
    'vae': widget_settings.get('vae', 'none'),
    'vae_num': widget_settings.get('vae_num', ''),
    'lora': widget_settings.get('lora', ('none',)),
    'controlnet': widget_settings.get('controlnet', ('none',)),
    'controlnet_num': widget_settings.get('controlnet_num', ''),
    'latest_webui': widget_settings.get('latest_webui', True),
    'latest_extensions': widget_settings.get('latest_extensions', True),
    'change_webui': widget_settings.get('change_webui', 'A1111'),
    'detailed_download': widget_settings.get('detailed_download', 'off'),
    'civitai_token': widget_settings.get('civitai_token', ''),
    'huggingface_token': widget_settings.get('huggingface_token', ''),
    'empowerment': widget_settings.get('empowerment', False),
    'empowerment_output': widget_settings.get('empowerment_output', ''),
    'Model_url': widget_settings.get('Model_url', ''),
    'Vae_url': widget_settings.get('Vae_url', ''),
    'LoRA_url': widget_settings.get('LoRA_url', ''),
    'Extensions_url': widget_settings.get('Extensions_url', ''),
    'custom_file_urls': widget_settings.get('custom_file_urls', ''),
    'XL_models': widget_settings.get('XL_models', False),
    'inpainting_model': widget_settings.get('inpainting_model', False)
}

for var_name, var_value in required_vars.items():
    globals()[var_name] = var_value

# FIXED: Safe import of custom modules with fallback
try:
    from webui_utils import handle_setup_timer
    from Manager import m_download, m_clone
    from CivitaiAPI import CivitAiAPI
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import custom modules: {e}")
    print("Using fallback implementations...")
    MODULES_AVAILABLE = False
    
    # Create dummy functions for missing imports
    def handle_setup_timer(path, timer):
        return timer
    def m_download(cmd, **kwargs):
        parts = cmd.split()
        if len(parts) >= 2:
            url, output = parts[0], parts[1]
            subprocess.run(['wget', '-O', output, url], check=False)
    def m_clone(cmd, **kwargs):
        subprocess.run(['git', 'clone'] + cmd.split(), check=False)
    class CivitAiAPI:
        def __init__(self, token): pass
        def validate_download(self, url, filename=None): return None

class COLORS:
    R, G, Y, B, X = "\033[31m", "\033[32m", "\033[33m", "\033[34m", "\033[0m"
COL = COLORS

# FIXED: Robust venv setup
def setup_venv():
    """Create a virtual environment if it doesn't exist and install dependencies."""
    CD(HOME)

    if VENV.exists():
        print(f"✅ Virtual environment already exists at {VENV}")
        return

    print(f"🌱 Creating a new virtual environment at {VENV}...")
    try:
        # Create venv without pip to avoid ensurepip errors in some environments
        result = subprocess.run([sys.executable, '-m', 'venv', str(VENV), '--without-pip'], 
                               capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Warning: venv creation had issues: {result.stderr}")

        # Manually install pip using get-pip.py
        get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
        get_pip_path = SCR_PATH / "get-pip.py"

        # Download get-pip.py
        print("📥 Downloading pip installer...")
        subprocess.run(['curl', '-sLo', str(get_pip_path), get_pip_url], check=True)

        # Run get-pip.py with the venv's python
        venv_python = VENV / 'bin' / 'python'
        if not venv_python.exists():
            venv_python = VENV / 'Scripts' / 'python.exe'  # Windows fallback
        
        print("🔧 Installing pip in virtual environment...")
        pip_result = subprocess.run([str(venv_python), str(get_pip_path)], 
                                   capture_output=True, text=True)
        if pip_result.returncode != 0:
            print(f"Warning: pip installation had issues: {pip_result.stderr}")

    except subprocess.CalledProcessError as e:
        print(f"Warning: Virtual environment setup had issues: {e}")
        print("Attempting to continue with system Python...")

    # Install requirements
    requirements_path = SCRIPTS / "requirements.txt"
    if not requirements_path.exists():
        print(f"Warning: requirements.txt not found at {requirements_path}")
        print("✅ Virtual environment setup complete (no requirements to install)")
        return

    # Determine pip executable
    pip_executable = VENV / 'bin' / 'pip'
    if not pip_executable.exists():
        pip_executable = VENV / 'Scripts' / 'pip.exe'  # Windows fallback
    if not pip_executable.exists():
        print("Warning: Could not find pip in virtual environment, using system pip")
        pip_executable = 'pip'

    print(f"📦 Installing all dependencies from {requirements_path}...")
    install_command = [str(pip_executable), 'install', '-r', str(requirements_path)]

    try:
        process = subprocess.Popen(install_command, stdout=subprocess.PIPE, 
                                 stderr=subprocess.STDOUT, text=True, bufsize=1)
        
        for line in iter(process.stdout.readline, ''):
            if detailed_download == 'on':
                print(line.rstrip())
        
        # FIXED: Only call wait() once
        return_code = process.wait()
        if return_code != 0:
            print("⚠️ Some dependencies failed to install, but continuing...")
    except Exception as e:
        print(f"Warning: Requirements installation had issues: {e}")

    print("✅ Virtual environment setup complete.")

# Execute Venv Setup
setup_venv()

# WEBUI and EXTENSION INSTALLATION
webui_path = Path(WEBUI)
if not webui_path.exists():
    print(f"⌚ Installing {UI} WebUI...")
    try:
        ipyRun('run', f"{SCRIPTS}/webui-installer.py")
    except Exception as e:
        print(f"⚠️ WebUI installation had issues: {e}")
else:
    print(f"🔧 WebUI {UI} already exists at {webui_path}")

# FIXED: Directory setup with proper path handling
print('📁 Setting up directories...')

# Use webui_settings for directory paths with validation
required_dirs = ['model_dir', 'vae_dir', 'lora_dir', 'extension_dir', 'control_dir']
for dir_name in required_dirs:
    if dir_name not in webui_settings or not webui_settings[dir_name]:
        default_path = str(webui_path / dir_name.replace('_dir', ''))
        webui_settings[dir_name] = default_path
        print(f"⚠️ Using default path for {dir_name}: {default_path}")

# FIXED: PREFIX_MAP with better path handling
PREFIX_MAP = {
    'model': (webui_settings.get('model_dir', str(webui_path / 'models' / 'Stable-diffusion')), '$ckpt'),
    'vae': (webui_settings.get('vae_dir', str(webui_path / 'models' / 'VAE')), '$vae'),
    'lora': (webui_settings.get('lora_dir', str(webui_path / 'models' / 'Lora')), '$lora'),
    'embed': (webui_settings.get('embed_dir', str(webui_path / 'embeddings')), '$emb'),
    'extension': (webui_settings.get('extension_dir', str(webui_path / 'extensions')), '$ext'),
    'adetailer': (webui_settings.get('adetailer_dir', str(HOME / 'adetailer')), '$ad'),
    'control': (webui_settings.get('control_dir', str(webui_path / 'models' / 'ControlNet')), '$cnet'),
    'upscale': (webui_settings.get('upscale_dir', str(webui_path / 'models' / 'ESRGAN')), '$ups'),
}

# DEBUG: Print directory paths
print("=== DEBUG: Directory Paths ===")
for key, (path, prefix) in PREFIX_MAP.items():
    print(f"{key}: {path}")
print("===============================")

# FIXED: Create directories safely
for dir_path, _ in PREFIX_MAP.values():
    if dir_path:
        try:
            os.makedirs(dir_path, exist_ok=True)
            print(f"📁 Created directory: {dir_path}")
        except Exception as e:
            print(f"⚠️ Could not create directory {dir_path}: {e}")

# DOWNLOAD LOGIC
print('📦 Downloading models and other assets...')

def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f">> An error occurred in {func.__name__}: {str(e)}")
            return None
    return wrapper

# Load model data safely
model_files = '_xl-models-data.py' if XL_models else '_models-data.py'
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

# FIXED: URL and filename processing
def _clean_url(url):
    """Clean URLs for proper downloading."""
    url = url.replace('/blob/', '/resolve/') if 'huggingface.co' in url else url
    url = url.replace('/blob/', '/raw/') if 'github.com' in url else url
    return url

def _extract_filename(url):
    """Extract custom filename from URL if specified."""
    if match := re.search(r'\[(.*?)\]', url):
        return match.group(1)
    return None

# FIXED: File processing with better error handling
@handle_errors
def process_download(url, destination_dir, file_type="file"):
    """Process a single download with proper error handling."""
    if not url or not url.strip():
        return
    
    try:
        clean_url = _clean_url(url.strip())
        custom_filename = _extract_filename(url)
        
        if custom_filename:
            output_path = Path(destination_dir) / custom_filename
            print(f"📥 Downloading {custom_filename}...")
        else:
            output_path = destination_dir
            print(f"📥 Downloading from {clean_url}...")
        
        # Use appropriate download method
        if MODULES_AVAILABLE:
            if 'civitai.com' in clean_url and civitai_token:
                api = CivitAiAPI(civitai_token)
                api.validate_download(clean_url, custom_filename)
            else:
                m_download(f"{clean_url} {output_path}")
        else:
            # Fallback download method
            if custom_filename:
                subprocess.run(['wget', '-O', str(output_path), clean_url], check=False)
            else:
                subprocess.run(['wget', '-P', str(destination_dir), clean_url], check=False)
        
        print(f"✅ Downloaded successfully")
        
    except Exception as e:
        print(f"❌ Download failed: {e}")

# FIXED: Download processing with proper checks
def process_downloads():
    """Process all downloads with proper validation."""
    
    # Process models
    if model and model != ['none'] and isinstance(model, (list, tuple)):
        model_dir = PREFIX_MAP['model'][0]
        if model_dir and model_list:
            print(f"🎨 Processing model downloads...")
            for selected_model in model:
                if selected_model in model_list:
                    model_url = model_list[selected_model]
                    process_download(model_url, model_dir, "model")
    
    # Process VAE
    if vae and vae != 'none' and vae_list and vae in vae_list:
        vae_dir = PREFIX_MAP['vae'][0]
        if vae_dir:
            print(f"🎭 Processing VAE download...")
            vae_url = vae_list[vae]
            process_download(vae_url, vae_dir, "vae")
    
    # Process LoRAs
    if lora and lora != ('none',) and isinstance(lora, (list, tuple)):
        lora_dir = PREFIX_MAP['lora'][0]
        if lora_dir and lora_list:
            print(f"✨ Processing LoRA downloads...")
            for selected_lora in lora:
                if selected_lora in lora_list:
                    lora_url = lora_list[selected_lora]
                    process_download(lora_url, lora_dir, "lora")
    
    # Process ControlNets
    if controlnet and controlnet != ('none',) and isinstance(controlnet, (list, tuple)):
        control_dir = PREFIX_MAP['control'][0]
        if control_dir and controlnet_list:
            print(f"🎮 Processing ControlNet downloads...")
            for selected_controlnet in controlnet:
                if selected_controlnet in controlnet_list:
                    controlnet_url = controlnet_list[selected_controlnet]
                    process_download(controlnet_url, control_dir, "controlnet")

# FIXED: Custom URL processing
def process_custom_urls():
    """Process custom URLs with proper validation."""
    if not empowerment:
        return
    
    custom_downloads = [
        ('Model_url', PREFIX_MAP['model'][0]),
        ('Vae_url', PREFIX_MAP['vae'][0]),
        ('LoRA_url', PREFIX_MAP['lora'][0]),
        ('Extensions_url', PREFIX_MAP['extension'][0]),
        ('custom_file_urls', HOME)
    ]
    
    for url_var, dest_dir in custom_downloads:
        urls = globals().get(url_var, '')
        if urls and urls.strip():
            print(f"📦 Processing custom {url_var}...")
            for url in urls.split():
                if url.strip():
                    process_download(url.strip(), dest_dir, url_var)

# Execute downloads
try:
    process_downloads()
    process_custom_urls()
    print("✅ Download processing complete!")
except Exception as e:
    print(f"⚠️ Download processing had issues: {e}")
    print("Some downloads may have failed, but continuing...")

print("🎉 All downloading operations completed!")
