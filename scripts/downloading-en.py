# ~ download.py | by ANXETY - Enhanced with Multiple WebUI Support ~

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

# ENHANCED: Add dependency verification first
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

# ENHANCED: Import order - after dependency verification
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

# ENHANCED: Load settings with better error handling and WebUI detection
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

# ENHANCED: Import WebUI utilities for feature detection
try:
    from webui_utils import (get_webui_features, is_webui_supported, get_webui_category, 
                           get_webui_specific_paths, handle_setup_timer)
    from Manager import m_download, m_clone
    from CivitaiAPI import CivitAiAPI
    WEBUI_UTILS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import enhanced modules: {e}")
    WEBUI_UTILS_AVAILABLE = False
    # Create fallback functions
    def get_webui_category(ui): return 'standard_sd'
    def is_webui_supported(ui, feature): return feature in ['models', 'vae', 'lora', 'controlnet', 'extensions']
    def get_webui_specific_paths(ui): return webui_settings
    def handle_setup_timer(path, timer): return timer
    def m_download(cmd, **kwargs): subprocess.run(['wget', '-O', cmd.split()[-1], cmd.split()[0]], check=False)
    def m_clone(cmd, **kwargs): subprocess.run(['git', 'clone'] + cmd.split(), check=False)
    class CivitAiAPI:
        def __init__(self, token): pass
        def validate_download(self, url, filename=None): return None

# ENHANCED: WebUI-aware debug output
print("=== ENHANCED DEBUG: Settings Content ===")
print("WIDGETS keys:", list(widget_settings.keys()))
print("WEBUI keys:", list(webui_settings.keys()))
print(f"Current WebUI: {UI}")

if WEBUI_UTILS_AVAILABLE:
    webui_category = get_webui_category(UI)
    print(f"WebUI Category: {webui_category}")
    
    # Feature detection
    supported_features = []
    for feature in ['models', 'vae', 'lora', 'controlnet', 'extensions']:
        if is_webui_supported(UI, feature):
            supported_features.append(feature)
    print(f"Supported Features: {supported_features}")

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

class COLORS:
    R, G, Y, B, X = "\033[31m", "\033[32m", "\033[33m", "\033[34m", "\033[0m"
COL = COLORS

# ENHANCED: WebUI-aware venv setup
def setup_venv():
    """Enhanced virtual environment setup with WebUI-specific requirements."""
    CD(HOME)

    if VENV.exists():
        print(f"✅ Virtual environment already exists at {VENV}")
        return

    print(f"🌱 Creating virtual environment for {UI}...")
    try:
        subprocess.run([sys.executable, '-m', 'venv', str(VENV), '--without-pip'], 
                      check=True, capture_output=True, text=True)
        
        # Install pip
        get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
        get_pip_path = SCR_PATH / "get-pip.py"
        subprocess.run(['curl', '-sLo', str(get_pip_path), get_pip_url], check=True)
        
        venv_python = VENV / 'bin' / 'python'
        subprocess.run([str(venv_python), str(get_pip_path)], check=True, capture_output=True, text=True)
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FATAL: Failed to create virtual environment. Error:\n{e.stderr}")

    # ENHANCED: WebUI-specific requirements installation
    requirements_files = [
        SCRIPTS / "requirements.txt",  # Base requirements
    ]
    
    # Add WebUI-specific requirements if available
    webui_req_file = SCRIPTS / f"requirements_{UI.lower()}.txt"
    if webui_req_file.exists():
        requirements_files.append(webui_req_file)
    
    pip_executable = VENV / 'bin' / 'pip'
    
    for req_file in requirements_files:
        if req_file.exists():
            print(f"📦 Installing dependencies from {req_file.name}...")
            install_command = f"{pip_executable} install -r {req_file}"
            
            process = subprocess.Popen(install_command, shell=True, 
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                     text=True, bufsize=1)
            
            if detailed_download == 'on':
                for line in iter(process.stdout.readline, ''):
                    print(line.rstrip())
            else:
                process.wait()
            
            return_code = process.wait()
            if return_code != 0:
                print(f"⚠️ Some dependencies from {req_file.name} failed to install")

    print("✅ Virtual environment setup complete.")

# Execute Venv Setup
setup_venv()

# ENHANCED: WebUI and Extension Installation with detection
webui_path = Path(WEBUI)
if not webui_path.exists():
    print(f"⌚ Installing {UI} WebUI...")
    ipyRun('run', f"{SCRIPTS}/webui-installer.py")
else:
    print(f"🔧 WebUI {UI} already exists at {webui_path}")

# ENHANCED: WebUI-aware directory setup
print('📁 Setting up directories...')

# Get WebUI-specific paths
if WEBUI_UTILS_AVAILABLE:
    webui_specific_paths = get_webui_specific_paths(UI)
    # Merge with existing webui_settings
    webui_specific_paths.update(webui_settings)
else:
    webui_specific_paths = webui_settings

# ENHANCED: Directory validation with WebUI support
required_dirs = ['model_dir', 'vae_dir', 'lora_dir', 'extension_dir', 'control_dir']
for dir_name in required_dirs:
    if dir_name not in webui_specific_paths or not webui_specific_paths[dir_name]:
        default_path = str(HOME / dir_name.replace('_dir', ''))
        webui_specific_paths[dir_name] = default_path
        print(f"⚠️ Using default path for {dir_name}: {default_path}")

# ENHANCED: WebUI-aware PREFIX_MAP with better path handling
PREFIX_MAP = {
    'model': (webui_specific_paths.get('model_dir', ''), '$ckpt'),
    'vae': (webui_specific_paths.get('vae_dir', ''), '$vae'),
    'lora': (webui_specific_paths.get('lora_dir', ''), '$lora'),
    'embed': (webui_specific_paths.get('embed_dir', str(HOME / 'embeddings')), '$emb'),
    'extension': (webui_specific_paths.get('extension_dir', ''), '$ext'),
    'adetailer': (webui_specific_paths.get('adetailer_dir', str(HOME / 'adetailer')), '$ad'),
    'control': (webui_specific_paths.get('control_dir', ''), '$cnet'),
    'upscale': (webui_specific_paths.get('upscale_dir', str(HOME / 'upscale')), '$ups'),
    'clip': (webui_specific_paths.get('clip_dir', ''), '$clip'),
    'unet': (webui_specific_paths.get('unet_dir', ''), '$unet'),
    'vision': (webui_specific_paths.get('vision_dir', ''), '$vis'),
    'encoder': (webui_specific_paths.get('encoder_dir', ''), '$enc'),
    'diffusion': (webui_specific_paths.get('diffusion_dir', ''), '$diff'),
    'config': (webui_specific_paths.get('config_dir', ''), '$cfg')
}

print("=== ENHANCED DEBUG: WebUI-Specific Paths ===")
print(f"WebUI: {UI}")
if WEBUI_UTILS_AVAILABLE:
    print(f"Category: {get_webui_category(UI)}")
for key, (path, prefix) in PREFIX_MAP.items():
    if path:  # Only show configured paths
        print(f"{key}: {path}")
print("===========================================")

# Create directories for supported features only
for dir_path, _ in PREFIX_MAP.values():
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
        print(f"📁 Created directory: {dir_path}")

# ======================== DOWNLOAD LOGIC ========================

print('📦 Downloading models and assets...')

def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f">> An error occurred in {func.__name__}: {str(e)}")
    return wrapper

# ENHANCED: WebUI-aware model data loading
if WEBUI_UTILS_AVAILABLE and is_webui_supported(UI, 'models'):
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
else:
    webui_category = get_webui_category(UI) if WEBUI_UTILS_AVAILABLE else 'unknown'
    print(f"ℹ️ {UI} ({webui_category}) doesn't support traditional SD models, skipping model data loading")
    model_list, vae_list, controlnet_list, lora_list = {}, {}, {}, {}

extension_repo = []

def _clean_url(url):
    url = url.replace('/blob/', '/resolve/') if 'huggingface.co' in url else url
    url = url.replace('/blob/', '/raw/') if 'github.com' in url else url
    return url

def _extract_filename(url):
    if match := re.search(r'\[(.*?)\]', url):
        return match.group(1)
    return None

def handle_file_processing(url, prefix, dir_path):
    """Enhanced file processing with WebUI awareness."""
    try:
        filename = _extract_filename(url)
        clean_url = _clean_url(url)
        
        if filename:
            # Custom filename specified
            output_path = f"{dir_path}/{filename}"
            print(f"📥 Downloading: {filename}")
        else:
            # Use original filename
            output_path = dir_path
            print(f"📥 Downloading from: {clean_url}")
        
        # Use appropriate download method
        if 'civitai.com' in url and civitai_token:
            # CivitAI download with authentication
            api = CivitAiAPI(civitai_token)
            api.validate_download(clean_url, filename)
        else:
            # Standard download
            m_download(f"{clean_url} {output_path}")
            
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")

# ENHANCED: Download processing with WebUI feature checking
def process_downloads():
    """Process downloads based on WebUI capabilities."""
    
    # Only process model downloads for WebUIs that support them
    if WEBUI_UTILS_AVAILABLE and not is_webui_supported(UI, 'models'):
        print(f"ℹ️ {UI} doesn't support traditional SD models, skipping model downloads")
        return
    
    # Process model downloads
    if model and model != ['none']:
        model_dir = PREFIX_MAP['model'][0]
        if model_dir:
            print(f"🎨 Processing model downloads to: {model_dir}")
            for selected_model in model:
                if selected_model in model_list:
                    model_url = model_list[selected_model]
                    handle_file_processing(model_url, '$ckpt', model_dir)
    
    # Process VAE downloads (if supported)
    if WEBUI_UTILS_AVAILABLE and is_webui_supported(UI, 'vae') and vae and vae != 'none':
        vae_dir = PREFIX_MAP['vae'][0]
        if vae_dir and vae in vae_list:
            print(f"🎭 Processing VAE download to: {vae_dir}")
            vae_url = vae_list[vae]
            handle_file_processing(vae_url, '$vae', vae_dir)
    
    # Process LoRA downloads (if supported)
    if WEBUI_UTILS_AVAILABLE and is_webui_supported(UI, 'lora') and lora and lora != ('none',):
        lora_dir = PREFIX_MAP['lora'][0]
        if lora_dir:
            print(f"✨ Processing LoRA downloads to: {lora_dir}")
            for selected_lora in lora:
                if selected_lora in lora_list:
                    lora_url = lora_list[selected_lora]
                    handle_file_processing(lora_url, '$lora', lora_dir)
    
    # Process ControlNet downloads (if supported)
    if WEBUI_UTILS_AVAILABLE and is_webui_supported(UI, 'controlnet') and controlnet and controlnet != ('none',):
        control_dir = PREFIX_MAP['control'][0]
        if control_dir:
            print(f"🎮 Processing ControlNet downloads to: {control_dir}")
            for selected_controlnet in controlnet:
                if selected_controlnet in controlnet_list:
                    controlnet_url = controlnet_list[selected_controlnet]
                    handle_file_processing(controlnet_url, '$cnet', control_dir)

# ENHANCED: Custom URL processing with WebUI awareness
def process_custom_urls():
    """Process custom URLs with WebUI feature checking."""
    
    custom_url_map = {
        'Model_url': ('model', '$ckpt'),
        'Vae_url': ('vae', '$vae'),
        'LoRA_url': ('lora', '$lora'),
        'Embedding_url': ('embed', '$emb'),
        'Extensions_url': ('extension', '$ext'),
        'ADetailer_url': ('adetailer', '$ad'),
        'custom_file_urls': ('', '')  # Special case
    }
    
    for url_key, (dir_key, prefix) in custom_url_map.items():
        if url_key in widget_settings and widget_settings[url_key]:
            urls = widget_settings[url_key].strip()
            if urls:
                # Check if feature is supported
                feature_map = {
                    'Model_url': 'models',
                    'Vae_url': 'vae', 
                    'LoRA_url': 'lora',
                    'Extensions_url': 'extensions'
                }
                
                if url_key in feature_map:
                    feature = feature_map[url_key]
                    if WEBUI_UTILS_AVAILABLE and not is_webui_supported(UI, feature):
                        print(f"⚠️ Skipping {url_key}: {UI} doesn't support {feature}")
                        continue
                
                # Process URLs
                if dir_key and dir_key in PREFIX_MAP:
                    target_dir = PREFIX_MAP[dir_key][0]
                    if target_dir:
                        print(f"📦 Processing custom {url_key} to: {target_dir}")
                        for url in urls.split():
                            if url.strip():
                                handle_file_processing(url.strip(), prefix, target_dir)

# Execute download processing
if not get_webui_category(UI) == 'face_swap' or not WEBUI_UTILS_AVAILABLE:
    process_downloads()
else:
    print(f"ℹ️ {UI} is a face swapping WebUI, skipping traditional model downloads")

# Process custom URLs
if empowerment:
    print("⚡ Empowerment mode enabled - processing custom URLs")
    process_custom_urls()

print("✅ Enhanced downloading complete!")
print(f"🎯 Configured for {UI} with appropriate feature support")

# ENHANCED: WebUI-specific post-download setup
if WEBUI_UTILS_AVAILABLE:
    webui_category = get_webui_category(UI)
    if webui_category == 'face_swap':
        print("🎭 Face swap WebUI detected - ensure face models are in correct directories")
    elif webui_category == 'enhanced_sd':
        print("⚒️ Enhanced SD WebUI detected - optimizations ready")
    elif webui_category == 'node_based':
        print("🖼️ Node-based WebUI detected - custom nodes ready")
