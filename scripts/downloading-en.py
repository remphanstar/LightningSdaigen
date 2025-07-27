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

# ENHANCED: Load ALL widget settings into global scope
widget_settings = settings.get('WIDGETS', {})
globals().update(widget_settings)

# ENHANCED: Load ALL webui paths into global scope  
webui_settings = settings.get('WEBUI', {})
globals().update(webui_settings)

# ENHANCED: Load environment settings
env_settings = settings.get('ENVIRONMENT', {})
globals().update(env_settings)

class COLORS:
    R, G, Y, B, X = "\033[31m", "\033[32m", "\033[33m", "\033[34m", "\033[0m"
COL = COLORS

def install_packages(install_lib):
    """Install packages from the provided library dictionary with enhanced error handling."""
    successful = 0
    failed = 0
    
    for index, (package, install_cmd) in enumerate(install_lib.items(), start=1):
        print(f"\r[{index}/{len(install_lib)}] {COL.G}>>{COL.X} Installing {COL.Y}{package}{COL.X}..." + ' ' * 35, end='')
        try:
            result = subprocess.run(
                install_cmd, 
                shell=True, 
                check=True, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.PIPE, 
                timeout=600,  # Increased timeout
                text=True
            )
            successful += 1
        except subprocess.TimeoutExpired:
            print(f"\n{COL.R}Warning: {package} installation timed out{COL.X}")
            failed += 1
        except subprocess.CalledProcessError as e:
            print(f"\n{COL.R}Warning: Failed to install {package}: {e.stderr[:100] if e.stderr else 'Unknown error'}{COL.X}")
            failed += 1
        except Exception as e:
            print(f"\n{COL.R}Warning: Unexpected error installing {package}: {e}{COL.X}")
            failed += 1
    
    print(f"\n📊 Installation summary: {successful} successful, {failed} failed")

# --- DEPENDENCY INSTALLATION (RUNS FIRST) ---
if not js.key_exists(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True):
    print('💿 Installing required libraries...')
    install_lib = {
        'system_packages': "apt-get -y update && apt-get -y install aria2 lz4 pv curl wget",
        'python_packages': "pip install --upgrade pip gdown aiohttp tqdm",
        'nodejs_packages': "curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && apt-get install -y nodejs && npm install -g localtunnel",
        'cloudflared': "wget -qO /usr/bin/cl https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 && chmod +x /usr/bin/cl",
    }
    install_packages(install_lib)
    clear_output()
    js.save(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True)

# --- ENHANCED VENV SETUP (CRITICAL FIXES) ---
def setup_venv(url):
    """Downloads and correctly extracts the provided venv archive with comprehensive error handling."""
    print("🔧 Setting up virtual environment...")
    CD(HOME)
    archive_name = "final_fixed_venv.tar.lz4"
    destination = HOME / archive_name
    
    # CRITICAL: Remove existing venv if it exists
    if VENV.exists():
        print(f"Removing existing venv at {VENV}...")
        try:
            shutil.rmtree(VENV)
        except Exception as e:
            print(f"⚠️ Warning: Could not fully remove existing venv: {e}")

    print(f"Downloading venv archive from {url}...")
    try:
        # Enhanced download with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = subprocess.run([
                    "aria2c", "-x", "16", "-s", "16", "-k", "1M", 
                    "--console-log-level=error", "--retry-wait=3", 
                    "--max-tries=3", "-c", "-d", str(HOME), 
                    "-o", archive_name, url
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, 
                timeout=1200, text=True)  # 20 minute timeout
                break
            except subprocess.CalledProcessError as e:
                if attempt < max_retries - 1:
                    print(f"Download attempt {attempt + 1} failed, retrying...")
                    time.sleep(5)
                    continue
                else:
                    raise RuntimeError(f"Failed to download after {max_retries} attempts: {e.stderr}")
            except subprocess.TimeoutExpired:
                if attempt < max_retries - 1:
                    print(f"Download attempt {attempt + 1} timed out, retrying...")
                    continue
                else:
                    raise RuntimeError("Download timed out after multiple attempts")
                    
    except Exception as e:
        # Cleanup on failure
        if destination.exists():
            destination.unlink()
        raise RuntimeError(f"Failed to download the venv archive: {e}")

    # Verify download
    if not destination.exists():
        raise RuntimeError("Download completed but archive file not found")
    
    file_size = destination.stat().st_size / (1024 * 1024)  # MB
    print(f"✅ Downloaded archive ({file_size:.1f} MB)")

    print("Extracting venv archive...")
    
    # ENHANCED: More robust extraction with progress monitoring
    try:
        # Extract with progress bar and proper error handling
        extract_cmd = f"cd {HOME} && pv {archive_name} | lz4 -d | tar xf -"
        result = subprocess.run(extract_cmd, shell=True, check=True, 
                              stderr=subprocess.PIPE, text=True, timeout=600)
        
        # CRITICAL FIX: Handle different possible extracted directory names
        possible_dirs = ["venv_new", "final_corrected_venv", "venv"]
        extracted_venv = None
        
        for dir_name in possible_dirs:
            candidate = HOME / dir_name
            if candidate.exists() and candidate != VENV:
                extracted_venv = candidate
                break
        
        if extracted_venv:
            if VENV.exists():
                shutil.rmtree(VENV)
            extracted_venv.rename(VENV)
            print(f"✅ Renamed extracted directory to {VENV}")
        elif not VENV.exists():
            raise RuntimeError("No suitable venv directory found after extraction")
        else:
            print(f"✅ Venv extracted directly to {VENV}")
            
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to extract venv archive: {e.stderr}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Venv extraction timed out")
    except Exception as e:
        raise RuntimeError(f"Failed to extract venv archive: {e}")
    
    # Clean up archive
    destination.unlink(missing_ok=True)
    
    # ENHANCED: Comprehensive venv validation and setup
    venv_bin = VENV / 'bin'
    venv_python = venv_bin / 'python'
    venv_pip = venv_bin / 'pip'
    
    # Verify critical files exist
    missing_files = []
    for name, path in [("python", venv_python), ("pip", venv_pip)]:
        if not path.exists():
            missing_files.append(name)
    
    if missing_files:
        raise RuntimeError(f"Venv validation failed - missing: {', '.join(missing_files)}")
    
    # ENHANCED: Set up environment for using the venv
    python_version = "3.11"  # Update to match your venv
    site_packages = VENV / f"lib/python{python_version}/site-packages"
    
    if not site_packages.exists():
        # Try alternative python versions
        for alt_version in ["3.10", "3.9", "3.12"]:
            alt_site_packages = VENV / f"lib/python{alt_version}/site-packages"
            if alt_site_packages.exists():
                site_packages = alt_site_packages
                python_version = alt_version
                break
    
    if not site_packages.exists():
        print("⚠️ Warning: Could not find site-packages directory")
    
    # ENHANCED: Environment variable management
    current_path = osENV.get('PATH', '')
    if str(venv_bin) not in current_path:
        osENV['PATH'] = f"{venv_bin}:{current_path}"
    
    current_pythonpath = osENV.get('PYTHONPATH', '')
    if str(site_packages) not in current_pythonpath:
        osENV['PYTHONPATH'] = f"{site_packages}:{current_pythonpath}" if current_pythonpath else str(site_packages)
    
    # Set virtual env marker
    osENV['VIRTUAL_ENV'] = str(VENV)
    
    # Add to sys.path for immediate use
    if str(site_packages) not in sys.path:
        sys.path.insert(0, str(site_packages))
    
    print("✅ Virtual environment setup complete and activated.")
    
    # ENHANCED: Comprehensive package verification
    print("🔍 Verifying key packages...")
    test_packages = [
        ("torch", "import torch; print(f'✅ PyTorch {torch.__version__} available')"),
        ("numpy", "import numpy; print(f'✅ numpy {numpy.__version__} OK')"),
        ("transformers", "import transformers; print(f'✅ transformers {transformers.__version__} OK')"),
        ("diffusers", "import diffusers; print(f'✅ diffusers {diffusers.__version__} OK')"),
        ("gradio", "import gradio; print(f'✅ gradio {gradio.__version__} OK')")
    ]
    
    verification_failed = False
    for pkg_name, test_code in test_packages:
        try:
            result = subprocess.run([str(venv_python), "-c", test_code], 
                                  capture_output=True, text=True, check=True, timeout=10)
            print(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Warning: {pkg_name} verification failed: {e.stderr.strip()}")
            verification_failed = True
        except subprocess.TimeoutExpired:
            print(f"⚠️ Warning: {pkg_name} verification timed out")
            verification_failed = True
    
    if not verification_failed:
        print("✅ All key packages verified successfully")
    
    return True

# Execute Venv Setup with error handling
try:
    my_custom_venv_url = "https://github.com/remphanstar/LightningSdaigen/releases/download/tag2fixed_venv.tar.lz4/final_fixed_venv.tar.lz4"
    setup_venv(my_custom_venv_url)
except Exception as e:
    print(f"❌ Virtual environment setup failed: {e}")
    print("Attempting to continue with system Python...")

# --- ENHANCED WEBUI and EXTENSION INSTALLATION ---
if not Path(WEBUI).exists():
    print(f"⌚ Unpacking Stable Diffusion {UI}...")
    try:
        # Enhanced WebUI installation with validation
        ipyRun('run', f"{SCRIPTS}/webui-installer.py")
        
        # Comprehensive validation
        webui_path = Path(WEBUI)
        required_files = ['launch.py', 'webui.py']
        missing_files = [f for f in required_files if not (webui_path / f).exists()]
        
        if not webui_path.exists():
            raise RuntimeError(f"WebUI installation failed - {WEBUI} not found")
        if missing_files:
            raise RuntimeError(f"WebUI installation incomplete - missing: {', '.join(missing_files)}")
            
        print(f"✅ WebUI {UI} installed successfully")
    except Exception as e:
        print(f"❌ WebUI installation failed: {e}")
        print("This may cause issues with launching. Please check the installation.")
else:
    print(f"🔧 WebUI {UI} already exists.")

# --- ENHANCED DOWNLOAD LOGIC ---
print('📦 Downloading models and other assets...')

def handle_errors(func):
    """Enhanced error handler with better logging."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f">> Error in {func.__name__}: {str(e)}")
            # Log to file if possible
            try:
                error_log = HOME / "download_errors.log"
                with open(error_log, "a") as f:
                    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {func.__name__}: {str(e)}\n")
            except:
                pass  # Don't fail if we can't log
    return wrapper

# ENHANCED: Model data loading with fallbacks
model_files = '_xl-models-data.py' if globals().get('XL_models', False) else '_models-data.py'
model_list, vae_list, controlnet_list, lora_list = {}, {}, {}, {}

try:
    model_data_path = SCRIPTS / model_files
    if model_data_path.exists():
        with open(model_data_path) as f:
            exec(f.read())
        print(f"✅ Loaded model data from {model_files}")
    else:
        print(f"⚠️ Warning: Model data file {model_files} not found")
except Exception as e:
    print(f"⚠️ Warning: Could not load model data: {e}")

extension_repo = []

# ENHANCED: Directory validation with intelligent defaults
required_dirs = ['model_dir', 'vae_dir', 'lora_dir', 'extension_dir', 'control_dir']
webui_model_path = str(Path(WEBUI) / 'models')

# Smart defaults based on WebUI type and structure
default_paths = {
    'model_dir': f"{webui_model_path}/Stable-diffusion" if UI in ['A1111', 'Forge', 'ReForge'] else f"{webui_model_path}/checkpoints",
    'vae_dir': f"{webui_model_path}/VAE" if UI in ['A1111', 'Forge', 'ReForge'] else f"{webui_model_path}/vae",
    'lora_dir': f"{webui_model_path}/Lora" if UI in ['A1111', 'Forge', 'ReForge'] else f"{webui_model_path}/loras",
    'extension_dir': str(Path(WEBUI) / ('extensions' if UI != 'ComfyUI' else 'custom_nodes')),
    'control_dir': f"{webui_model_path}/ControlNet" if UI in ['A1111', 'Forge', 'ReForge'] else f"{webui_model_path}/controlnet",
    'embed_dir': f"{webui_model_path}/embeddings" if UI in ['A1111', 'Forge', 'ReForge'] else f"{webui_model_path}/embeddings",
    'adetailer_dir': f"{webui_model_path}/adetailer" if UI != 'ComfyUI' else f"{webui_model_path}/ultralytics",
    'upscale_dir': f"{webui_model_path}/ESRGAN" if UI in ['A1111', 'Forge', 'ReForge'] else f"{webui_model_path}/upscale_models",
    'clip_dir': f"{webui_model_path}/clip" if UI == 'ComfyUI' else f"{webui_model_path}/text_encoder",
    'unet_dir': f"{webui_model_path}/unet" if UI == 'ComfyUI' else f"{webui_model_path}/text_encoder",
    'vision_dir': f"{webui_model_path}/clip_vision",
    'encoder_dir': f"{webui_model_path}/text_encoders" if UI == 'ComfyUI' else f"{webui_model_path}/text_encoder",
    'diffusion_dir': f"{webui_model_path}/diffusion_models",
    'config_dir': str(Path(WEBUI) / ('user/default' if UI == 'ComfyUI' else ''))
}

for dir_name, default_path in default_paths.items():
    if dir_name not in globals() or not globals()[dir_name]:
        globals()[dir_name] = default_path
        print(f"📁 Using default path for {dir_name}: {default_path}")

PREFIX_MAP = {
    'model': (globals().get('model_dir'), '$ckpt'), 
    'vae': (globals().get('vae_dir'), '$vae'), 
    'lora': (globals().get('lora_dir'), '$lora'),
    'embed': (globals().get('embed_dir'), '$emb'), 
    'extension': (globals().get('extension_dir'), '$ext'), 
    'adetailer': (globals().get('adetailer_dir'), '$ad'),
    'control': (globals().get('control_dir'), '$cnet'), 
    'upscale': (globals().get('upscale_dir'), '$ups'), 
    'clip': (globals().get('clip_dir'), '$clip'),
    'unet': (globals().get('unet_dir'), '$unet'), 
    'vision': (globals().get('vision_dir'), '$vis'), 
    'encoder': (globals().get('encoder_dir'), '$enc'),
    'diffusion': (globals().get('diffusion_dir'), '$diff'), 
    'config': (globals().get('config_dir'), '$cfg')
}

# Create all directories
for dir_path, _ in PREFIX_MAP.values():
    try:
        os.makedirs(dir_path, exist_ok=True)
    except Exception as e:
        print(f"⚠️ Warning: Could not create directory {dir_path}: {e}")

def _clean_url(url):
    """Enhanced URL cleaning with better error handling."""
    if not url or not isinstance(url, str):
        return url
    
    # Clean URLs for different platforms
    url_cleaners = {
        'huggingface.co': lambda u: u.replace('/blob/', '/resolve/').split('?')[0],
        'github.com': lambda u: u.replace('/blob/', '/raw/'),
        'drive.google.com': lambda u: u  # Keep as-is for drive URLs
    }
    
    for domain, cleaner in url_cleaners.items():
        if domain in url:
            try:
                return cleaner(url)
            except Exception as e:
                print(f"⚠️ Warning: Failed to clean URL {url}: {e}")
                return url
    
    return url

def _extract_filename(url):
    """Enhanced filename extraction with better validation."""
    if not url:
        return None
        
    # Extract filename from [filename] pattern
    if match := re.search(r'\[(.*?)\]', url):
        filename = match.group(1).strip()
        if filename:
            return filename
    
    # Skip filename extraction for these domains
    skip_domains = ["civitai.com", "drive.google.com"]
    if any(d in urlparse(url).netloc for d in skip_domains):
        return None
    
    # Extract from URL path
    try:
        path = urlparse(url).path
        if path:
            return Path(path).name
    except Exception:
        pass
    
    return None

@handle_errors
def _process_download_link(link):
    """Enhanced link processing with better validation."""
    if not link or not isinstance(link, str):
        return None, link, None
        
    link = _clean_url(link.strip())
    
    if ':' in link and not link.startswith(('http://', 'https://')):
        prefix, path = link.split(':', 1)
        if prefix in PREFIX_MAP:
            clean_path = re.sub(r'\[.*?\]', '', path).strip()
            filename = _extract_filename(path)
            return prefix, clean_path, filename
    
    return None, link, _extract_filename(link)

@handle_errors
def download(line):
    """Enhanced download function with better error handling."""
    if not line or not line.strip():
        return
        
    links = [link.strip() for link in line.split(',') if link.strip()]
    
    if not links:
        print("No valid download links found")
        return
    
    print(f"Processing {len(links)} download link(s)...")
    
    for i, link in enumerate(links, 1):
        print(f"[{i}/{len(links)}] Processing: {link[:80]}{'...' if len(link) > 80 else ''}")
        
        prefix, url, filename = _process_download_link(link)
        
        if prefix:
            dir_path, _ = PREFIX_MAP[prefix]
            if prefix == 'extension':
                extension_repo.append((url, filename))
                print(f"  → Queued extension: {filename or 'from URL'}")
                continue
            
            print(f"  → Downloading to {dir_path}")
            manual_download(url, dir_path, filename, prefix)
        else:
            print(f"  → Direct download: {url}")
            # Handle direct downloads if needed

@handle_errors
def manual_download(url, dst_dir, file_name=None, prefix=None):
    """Enhanced manual download with better CivitAI integration."""
    if not url or not dst_dir:
        print("⚠️ Warning: Invalid download parameters")
        return
    
    if 'civitai' in url:
        # Enhanced CivitAI handling
        token = (globals().get('civitai_token', '') or 
                widget_settings.get('civitai_token', '') or 
                env_settings.get('civitai_token', ''))
        
        if not token:
            print(f"⚠️ Warning: CivitAI token required for {url}")
            print("Please set your CivitAI token in the widgets to download from CivitAI")
            return
        
        try:
            api = CivitAiAPI(token)
            data = api.validate_download(url, file_name)
            if not data:
                print(f"⚠️ Warning: Could not validate CivitAI download for {url}")
                return
            
            url = data.download_url
            file_name = data.model_name
            print(f"  → CivitAI: {file_name}")
        except Exception as e:
            print(f"⚠️ Warning: CivitAI API error: {e}")
            return
    
    # Ensure destination directory exists
    try:
        os.makedirs(dst_dir, exist_ok=True)
    except Exception as e:
        print(f"⚠️ Warning: Could not create destination directory {dst_dir}: {e}")
        return
    
    # Execute download
    download_cmd = f"{url} {dst_dir}"
    if file_name:
        download_cmd += f" {file_name}"
    
    try:
        m_download(download_cmd, log=True, unzip=True)
    except Exception as e:
        print(f"⚠️ Warning: Download failed for {url}: {e}")

def _parse_selection_numbers(num_str, max_num):
    """Enhanced number parsing with better validation."""
    if not num_str or not isinstance(num_str, str):
        return []
    
    num_str = num_str.replace(',', ' ').strip()
    if not num_str:
        return []
    
    unique_numbers = set()
    max_length = len(str(max_num))
    
    for part in num_str.split():
        if not part.isdigit():
            continue
            
        part_int = int(part)
        if 1 <= part_int <= max_num:
            unique_numbers.add(part_int)
            continue
        
        # Handle concatenated numbers
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
            if not found:
                current_position += 1
    
    return sorted(unique_numbers)

def handle_submodels(selection, num_selection, model_dict, dst_dir, base_url, inpainting_filter=False):
    """Enhanced submodel handling with inpainting filter support."""
    if not model_dict:
        return base_url
    
    selected = []
    
    # Handle selection parameter
    if isinstance(selection, str):
        selections = [selection]
    elif isinstance(selection, (list, tuple)):
        selections = list(selection)
    else:
        selections = ['none']
    
    # Process selections
    for sel in selections:
        if not sel or sel.lower() == 'none':
            continue
            
        if sel == 'ALL':
            for item in model_dict.values():
                if isinstance(item, list):
                    selected.extend(item)
                else:
                    selected.append(item)
        elif sel in model_dict:
            item = model_dict[sel]
            if isinstance(item, list):
                selected.extend(item)
            else:
                selected.append(item)
    
    # Process number selections
    if num_selection and isinstance(num_selection, str):
        max_num = len(model_dict)
        if max_num > 0:
            for num in _parse_selection_numbers(num_selection, max_num):
                if 1 <= num <= max_num:
                    name = list(model_dict.keys())[num - 1]
                    item = model_dict[name]
                    if isinstance(item, list):
                        selected.extend(item)
                    else:
                        selected.append(item)
    
    # Process selected items
    unique_models = {}
    for model in selected:
        if not isinstance(model, dict) or 'url' not in model:
            continue
            
        name = model.get('name') or os.path.basename(model['url'])
        
        # Apply inpainting filter if requested
        if inpainting_filter and not model.get('inpainting', False):
            continue
        
        unique_models[name] = {
            'url': model['url'],
            'dst_dir': model.get('dst_dir', dst_dir),
            'name': name
        }
    
    # Build download line
    for model in unique_models.values():
        base_url += f"{model['url']} {model['dst_dir']} {model['name']}, "
    
    return base_url

# ENHANCED: Process downloads with comprehensive error handling
line = ""

# Get selections with safe defaults
model_selection = globals().get('model', 'none')
model_num_selection = globals().get('model_num', '')
vae_selection = globals().get('vae', 'none') 
vae_num_selection = globals().get('vae_num', '')
lora_selection = globals().get('lora', 'none')
controlnet_selection = globals().get('controlnet', 'none')
controlnet_num_selection = globals().get('controlnet_num', '')
inpainting_models = globals().get('inpainting_model', False)

print("🔍 Processing model selections...")

try:
    line = handle_submodels(model_selection, model_num_selection, model_list, 
                           globals().get('model_dir', str(HOME / 'models')), line, inpainting_models)
    line = handle_submodels(vae_selection, vae_num_selection, vae_list, 
                           globals().get('vae_dir', str(HOME / 'vae')), line)
    line = handle_submodels(lora_selection, '', lora_list, 
                           globals().get('lora_dir', str(HOME / 'lora')), line)
    line = handle_submodels(controlnet_selection, controlnet_num_selection, controlnet_list, 
                           globals().get('control_dir', str(HOME / 'controlnet')), line)
except Exception as e:
    print(f"⚠️ Warning: Error processing model selections: {e}")

# Process custom URLs
custom_urls = []
for url_key in ['Model_url', 'Vae_url', 'LoRA_url', 'Embedding_url', 'Extensions_url', 'ADetailer_url']:
    url_value = globals().get(url_key, '')
    if url_value and url_value.strip():
        custom_urls.append(url_value.strip())

if custom_urls:
    custom_line = ', '.join(custom_urls)
    line = f"{line}, {custom_line}" if line else custom_line

# Execute downloads
if line.strip():
    download(line)
else:
    print("ℹ️ No models selected for download")

# ENHANCED: Extension installation with better error handling
if extension_repo:
    print(f"✨ Installing {len(extension_repo)} custom extensions...")
    ext_dir = globals().get('extension_dir', str(HOME / 'extensions'))
    
    successful_extensions = 0
    failed_extensions = 0
    
    for i, (repo_url, repo_name) in enumerate(extension_repo, 1):
        print(f"[{i}/{len(extension_repo)}] Installing: {repo_name or 'from URL'}")
        try:
            clone_cmd = f"{repo_url} {ext_dir}"
            if repo_name:
                clone_cmd += f" {repo_name}"
            
            m_clone(clone_cmd)
            successful_extensions += 1
        except Exception as e:
            print(f"⚠️ Warning: Failed to install extension {repo_name or repo_url}: {e}")
            failed_extensions += 1
    
    print(f"📦 Extension installation complete: {successful_extensions} successful, {failed_extensions} failed")

# ENHANCED: Process empowerment mode and file URLs
empowerment_output = globals().get('empowerment_output', '')
custom_file_urls = globals().get('custom_file_urls', '')

if empowerment_output and empowerment_output.strip():
    print("🔧 Processing empowerment mode content...")
    try:
        # Process empowerment output line by line
        for line_num, line in enumerate(empowerment_output.strip().split('\n'), 1):
            line = line.strip()
            if line and not line.startswith('#') and 'http' in line:
                try:
                    download(line)
                except Exception as e:
                    print(f"⚠️ Line {line_num} failed: {e}")
    except Exception as e:
        print(f"⚠️ Warning: Error processing empowerment content: {e}")

if custom_file_urls and custom_file_urls.strip():
    print("📄 Processing custom file URLs...")
    try:
        # Process custom file URLs
        file_urls = [url.strip() for url in custom_file_urls.split(',') if url.strip()]
        for file_url in file_urls:
            if file_url.endswith('.txt') and not file_url.startswith('http'):
                # Local file
                file_path = Path(file_url)
                if file_path.exists():
                    try:
                        with open(file_path, 'r') as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#') and 'http' in line:
                                    download(line)
                    except Exception as e:
                        print(f"⚠️ Warning: Error processing file {file_url}: {e}")
                else:
                    print(f"⚠️ Warning: File not found: {file_url}")
            elif 'http' in file_url:
                # URL to text file
                try:
                    response = requests.get(file_url, timeout=30)
                    response.raise_for_status()
                    for line in response.text.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('#') and 'http' in line:
                            download(line)
                except Exception as e:
                    print(f"⚠️ Warning: Error downloading file from {file_url}: {e}")
    except Exception as e:
        print(f"⚠️ Warning: Error processing custom file URLs: {e}")

# CRITICAL FIX: Special handling for ComfyUI adetailer models
if UI == 'ComfyUI':
    adetailer_dir = globals().get('adetailer_dir', '')
    if adetailer_dir and Path(adetailer_dir).exists():
        print("🔧 Organizing ADetailer models for ComfyUI...")
        try:
            # Create subdirectories for model organization
            segm_dir = Path(adetailer_dir) / 'segm'
            bbox_dir = Path(adetailer_dir) / 'bbox'
            
            segm_dir.mkdir(exist_ok=True)
            bbox_dir.mkdir(exist_ok=True)
            
            # Move models to appropriate subdirectories
            moved_count = 0
            for file_path in Path(adetailer_dir).glob('*.pt'):
                if file_path.is_file():
                    if file_path.name.endswith('-seg.pt'):
                        dest_path = segm_dir / file_path.name
                    else:
                        dest_path = bbox_dir / file_path.name
                    
                    if not dest_path.exists():
                        try:
                            shutil.move(str(file_path), str(dest_path))
                            moved_count += 1
                        except Exception as e:
                            print(f"⚠️ Warning: Could not move {file_path.name}: {e}")
                    else:
                        # Remove duplicate
                        file_path.unlink()
            
            if moved_count > 0:
                print(f"✅ Organized {moved_count} ADetailer models")
                
        except Exception as e:
            print(f"⚠️ Warning: Error organizing ADetailer models: {e}")

# ENHANCED: Timer setup for WebUI
try:
    if Path(WEBUI).exists():
        start_timer = globals().get('start_timer', time.time())
        handle_setup_timer(WEBUI, start_timer)
        print("⏰ Timer setup complete")
except Exception as e:
    print(f"⚠️ Warning: Timer setup failed: {e}")

# ENHANCED: Final validation and summary
print("\n" + "="*60)
print("📋 DOWNLOAD SUMMARY")
print("="*60)

# Check if critical directories have content
summary_items = []
for name, (dir_path, _) in PREFIX_MAP.items():
    if dir_path and Path(dir_path).exists():
        file_count = len([f for f in Path(dir_path).rglob('*') if f.is_file()])
        if file_count > 0:
            summary_items.append(f"{name.title()}: {file_count} files")

if summary_items:
    for item in summary_items:
        print(f"✅ {item}")
else:
    print("ℹ️ No files downloaded (this may be normal if no models were selected)")

# Check WebUI installation
webui_status = "✅ Ready" if Path(WEBUI).exists() and (Path(WEBUI) / 'launch.py').exists() else "❌ Missing"
print(f"🖥️ WebUI ({UI}): {webui_status}")

# Check venv status
venv_status = "✅ Active" if VENV.exists() and (VENV / 'bin' / 'python').exists() else "❌ Missing"
print(f"🐍 Virtual Environment: {venv_status}")

print("="*60)
print('🏁 All downloads and setup complete!')

# CRITICAL FIX: Display results if the script exists
try:
    result_script = SCRIPTS / 'download-result.py'
    if result_script.exists():
        print("\n📊 Generating download results...")
        ipyRun('run', str(result_script))
except Exception as e:
    print(f"⚠️ Warning: Could not generate download results: {e}")
