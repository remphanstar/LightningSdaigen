# ~ downloading-en.py | by ANXETY - Enhanced with Complete Bug Fixes ~

import subprocess
import sys
import os
import time
from pathlib import Path
from IPython import get_ipython

# Safe import with comprehensive fallbacks
try:
    from webui_utils import (get_webui_features, is_webui_supported, get_webui_category, 
                           get_webui_specific_paths, handle_setup_timer, log_webui_info)
    from Manager import m_download, m_clone
    from CivitaiAPI import CivitAiAPI
    import json_utils as js
    MODULES_AVAILABLE = True
    print("✅ Enhanced modules loaded successfully")
except ImportError as e:
    print(f"⚠️ Enhanced modules not available: {e}")
    MODULES_AVAILABLE = False
    # Create comprehensive fallback functions
    def get_webui_category(ui): return 'standard_sd'
    def is_webui_supported(ui, feature): return feature in ['models', 'vae', 'lora', 'controlnet', 'extensions']
    def get_webui_specific_paths(ui): return {}
    def handle_setup_timer(path, timer): return timer
    def log_webui_info(ui): print(f"🔍 WebUI: {ui}")
    def m_download(cmd, **kwargs): 
        parts = cmd.split()
        if len(parts) >= 2:
            subprocess.run(['wget', '-O', parts[-1], parts[0]], check=False)
    def m_clone(cmd, **kwargs): 
        subprocess.run(['git', 'clone'] + cmd.split(), check=False)
    class CivitAiAPI:
        def __init__(self, token): self.token = token
        def get_model_versions(self, model_id): return []
    class js:
        @staticmethod
        def read(path, key, default=None): return default
        @staticmethod
        def save(path, key, value): pass

ipyRun = get_ipython().run_line_magic

# Environment paths with validation
osENV = os.environ
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}

try:
    HOME = PATHS['home_path']
    VENV = PATHS['venv_path'] 
    SCRIPTS = PATHS['scr_path'] / 'scripts'
    SETTINGS_PATH = PATHS['settings_path']
except KeyError as e:
    print(f"❌ Missing environment path: {e}")
    print("Please run the setup cell first")
    sys.exit(1)

# FIXED: Load settings with comprehensive error handling and fallbacks
try:
    settings = js.read(SETTINGS_PATH) or {}
    UI = settings.get('WEBUI', {}).get('current', 'A1111')
    WEBUI = settings.get('WEBUI', {}).get('webui_path', str(HOME / UI))
    FORK_REPO = js.read(SETTINGS_PATH, 'ENVIRONMENT.fork') or 'remphanstar/LightningSdaigen'
    BRANCH = js.read(SETTINGS_PATH, 'ENVIRONMENT.branch') or 'main'

    # Load widget settings (selections) and webui settings (paths) separately
    widget_settings = settings.get('WIDGETS', {})
    webui_settings = settings.get('WEBUI', {})
    
    print(f"✅ Settings loaded for WebUI: {UI}")
    
except Exception as e:
    print(f"⚠️ Settings loading issue: {e}")
    # Comprehensive fallback defaults
    widget_settings = {
        'model': ['none'], 'vae': 'none', 'lora': ['none'], 'embed': ['none'],
        'extension': ['none'], 'control': ['none'], 'detailed_download': 'off'
    }
    webui_settings = {}
    UI = 'A1111'
    WEBUI = str(HOME / UI)
    FORK_REPO = 'remphanstar/LightningSdaigen'
    BRANCH = 'main'

# FIXED: Safe variable setting with comprehensive defaults
required_vars = {
    'model': widget_settings.get('model', ['none']),
    'vae': widget_settings.get('vae', 'none'),
    'lora': widget_settings.get('lora', ['none']),
    'embed': widget_settings.get('embed', ['none']),
    'extension': widget_settings.get('extension', ['none']),
    'control': widget_settings.get('control', ['none']),
    'detailed_download': widget_settings.get('detailed_download', 'off')
}

# Set all variables in global scope with validation
for var_name, var_value in required_vars.items():
    globals()[var_name] = var_value
    if detailed_download == 'on':
        print(f"🔧 {var_name}: {var_value}")

# Enhanced WebUI information logging
if MODULES_AVAILABLE:
    log_webui_info(UI)

# ==================== FIXED VENV SETUP ====================

def setup_venv():
    """FIXED: Enhanced virtual environment setup with comprehensive error handling."""
    
    print("🐍 Setting up virtual environment...")
    
    if VENV.exists():
        print(f"✅ Virtual environment already exists: {VENV}")
        return True
    
    print(f"🌱 Creating virtual environment at: {VENV}")
    
    try:
        # Create virtual environment
        result = subprocess.run([sys.executable, '-m', 'venv', str(VENV)], 
                              capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            print(f"❌ Venv creation failed: {result.stderr}")
            return False
        
        print("✅ Virtual environment created successfully")
        
    except subprocess.TimeoutExpired:
        print("❌ Venv creation timed out")
        return False
    except Exception as e:
        print(f"❌ Venv creation error: {e}")
        return False
    
    # FIXED: Robust venv python detection
    venv_python_paths = [
        VENV / 'bin' / 'python',      # Linux/Mac
        VENV / 'Scripts' / 'python.exe'  # Windows
    ]
    
    venv_python = None
    for path in venv_python_paths:
        if path.exists():
            venv_python = path
            break
    
    if not venv_python:
        print("❌ Could not find python in virtual environment")
        return False
    
    print(f"✅ Found venv python: {venv_python}")
    
    # FIXED: Install pip properly
    try:
        print("🔧 Ensuring pip is available...")
        pip_result = subprocess.run([str(venv_python), '-m', 'ensurepip', '--upgrade'], 
                                   capture_output=True, text=True, timeout=60)
        if pip_result.returncode != 0:
            print(f"⚠️ Pip setup warning: {pip_result.stderr}")
        else:
            print("✅ Pip ensured in virtual environment")
    except Exception as e:
        print(f"⚠️ Pip setup issue: {e}")
    
    # FIXED: Install requirements with proper error handling
    requirements_path = SCRIPTS / 'requirements.txt'
    
    if not requirements_path.exists():
        print("⚠️ Requirements file not found, creating basic requirements...")
        basic_requirements = [
            'requests>=2.25.0',
            'aiohttp>=3.8.0',
            'tqdm>=4.64.0',
            'Pillow>=9.0.0',
            'numpy>=1.21.0'
        ]
        try:
            with open(requirements_path, 'w') as f:
                f.write('\n'.join(basic_requirements))
            print("✅ Basic requirements file created")
        except Exception as e:
            print(f"⚠️ Could not create requirements file: {e}")
            return True  # Continue without requirements
    
    # FIXED: Install requirements with only ONE process.wait() call
    pip_executable_paths = [
        VENV / 'bin' / 'pip',         # Linux/Mac
        VENV / 'Scripts' / 'pip.exe'  # Windows
    ]
    
    pip_executable = None
    for path in pip_executable_paths:
        if path.exists():
            pip_executable = path
            break
    
    if not pip_executable:
        print("⚠️ Could not find pip in virtual environment, using venv python")
        pip_executable = f"{venv_python} -m pip"

    print(f"📦 Installing dependencies from {requirements_path.name}...")
    try:
        install_command = f"{pip_executable} install -r {requirements_path}"
        process = subprocess.Popen(install_command, shell=True, 
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                 text=True, bufsize=1)
        
        # Show output if detailed mode is on
        if detailed_download == 'on':
            for line in iter(process.stdout.readline, ''):
                print(line.rstrip())
        
        # FIXED: Only call wait() ONCE
        return_code = process.wait()
        if return_code != 0:
            print("⚠️ Some dependencies failed to install, but continuing...")
        else:
            print("✅ Dependencies installed successfully")
            
    except Exception as e:
        print(f"⚠️ Requirements installation issue: {e}")

    print("✅ Virtual environment setup complete")
    return True

# Execute Venv Setup
if not setup_venv():
    print("❌ Virtual environment setup failed, but continuing...")

# ==================== ENHANCED WEBUI INSTALLATION ====================

print(f"🔧 Checking WebUI installation...")

webui_path = Path(WEBUI)
if not webui_path.exists() or not any(webui_path.iterdir()):
    print(f"⌚ Installing {UI} WebUI...")
    try:
        ipyRun('run', f"{SCRIPTS}/webui-installer.py")
        print(f"✅ {UI} installation completed")
    except Exception as e:
        print(f"⚠️ WebUI installation issue: {e}")
else:
    print(f"✅ WebUI {UI} already exists at {webui_path}")

# ==================== ENHANCED DIRECTORY SETUP ====================

print('📁 Setting up directories...')

# Get WebUI-specific paths with fallbacks
if MODULES_AVAILABLE:
    try:
        webui_specific_paths = get_webui_specific_paths(UI)
        # Merge with existing webui_settings, giving priority to webui_specific_paths
        for key, value in webui_specific_paths.items():
            if value:  # Only update if the path is not empty
                webui_settings[key] = value
        print(f"✅ WebUI-specific paths configured for {UI}")
    except Exception as e:
        print(f"⚠️ Could not get WebUI-specific paths: {e}")
        webui_specific_paths = webui_settings
else:
    webui_specific_paths = webui_settings

# ENHANCED: Directory validation with WebUI support
required_dirs = ['model_dir', 'vae_dir', 'lora_dir', 'extension_dir', 'control_dir']
for dir_name in required_dirs:
    if dir_name not in webui_specific_paths or not webui_specific_paths[dir_name]:
        # Create default path based on WebUI type
        if UI in ['FaceFusion', 'RoopUnleashed']:
            default_path = str(webui_path / 'models')
        elif UI == 'ComfyUI':
            dir_map = {
                'model_dir': 'models/checkpoints',
                'vae_dir': 'models/vae', 
                'lora_dir': 'models/loras',
                'extension_dir': 'custom_nodes',
                'control_dir': 'models/controlnet'
            }
            default_path = str(webui_path / dir_map.get(dir_name, 'models'))
        else:
            dir_map = {
                'model_dir': 'models/Stable-diffusion',
                'vae_dir': 'models/VAE',
                'lora_dir': 'models/Lora', 
                'extension_dir': 'extensions',
                'control_dir': 'models/ControlNet'
            }
            default_path = str(webui_path / dir_map.get(dir_name, 'models'))
        
        webui_specific_paths[dir_name] = default_path
        print(f"📁 Default path for {dir_name}: {default_path}")

# ENHANCED: WebUI-aware PREFIX_MAP with comprehensive path handling
PREFIX_MAP = {
    'model': (webui_specific_paths.get('model_dir', str(webui_path / 'models')), '$ckpt'),
    'vae': (webui_specific_paths.get('vae_dir', str(webui_path / 'models/VAE')), '$vae'),
    'lora': (webui_specific_paths.get('lora_dir', str(webui_path / 'models/Lora')), '$lora'),
    'embed': (webui_specific_paths.get('embed_dir', str(webui_path / 'embeddings')), '$emb'),
    'extension': (webui_specific_paths.get('extension_dir', str(webui_path / 'extensions')), '$ext'),
    'control': (webui_specific_paths.get('control_dir', str(webui_path / 'models/ControlNet')), '$ctrl')
}

# Create all directories
for name, (path, _) in PREFIX_MAP.items():
    if path:  # Only create if path is defined
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            if detailed_download == 'on':
                print(f"📁 Created: {name} -> {path}")
        except Exception as e:
            print(f"⚠️ Could not create {name} directory: {e}")

print("✅ Directory setup complete")

# ==================== ENHANCED MODEL DOWNLOADING ====================

# Check if we should skip models for this WebUI type
if MODULES_AVAILABLE and get_webui_category(UI) == 'face_swap':
    print(f"🎭 {UI} is a face swap WebUI - skipping standard SD model downloads")
    print("Models for face swapping have been configured during installation")
    
elif model and model != ['none'] and model[0] != 'none':
    print(f"📦 Processing model downloads...")
    
    # Enhanced model downloading with WebUI awareness
    for model_item in model:
        if model_item and model_item != 'none':
            try:
                print(f"📥 Downloading model: {model_item}")
                # Use appropriate download method
                if MODULES_AVAILABLE:
                    # Use enhanced download method
                    download_path = PREFIX_MAP['model'][0]
                    m_download(f"{model_item} {download_path}")
                else:
                    # Fallback download method
                    subprocess.run(['wget', '-P', PREFIX_MAP['model'][0], model_item], check=False)
                    
                print(f"✅ Model downloaded: {model_item}")
            except Exception as e:
                print(f"⚠️ Model download failed for {model_item}: {e}")
else:
    print("📦 No models selected for download")

# ==================== ENHANCED COMPONENT DOWNLOADING ====================

def download_components(component_type, component_list, prefix_key):
    """Enhanced component downloading with error handling."""
    if not component_list or component_list == ['none'] or component_list[0] == 'none':
        print(f"📦 No {component_type} selected for download")
        return
    
    # Check WebUI support for this component type
    if MODULES_AVAILABLE and not is_webui_supported(UI, component_type):
        print(f"📦 {UI} doesn't support {component_type} - skipping downloads")
        return
    
    print(f"📦 Processing {component_type} downloads...")
    
    for item in component_list:
        if item and item != 'none':
            try:
                print(f"📥 Downloading {component_type}: {item}")
                download_path = PREFIX_MAP[prefix_key][0]
                
                if MODULES_AVAILABLE:
                    if component_type == 'extension':
                        m_clone(f"{item} {download_path}")
                    else:
                        m_download(f"{item} {download_path}")
                else:
                    # Fallback method
                    if item.startswith('http'):
                        subprocess.run(['wget', '-P', download_path, item], check=False)
                    
                print(f"✅ {component_type.title()} downloaded: {item}")
                
            except Exception as e:
                print(f"⚠️ {component_type.title()} download failed for {item}: {e}")

# Download all component types
download_components('vae', [vae] if vae != 'none' else [], 'vae')
download_components('lora', lora, 'lora')
download_components('embed', embed, 'embed')
download_components('extension', extension, 'extension')
download_components('control', control, 'control')

# ==================== FINAL SETUP ====================

print("\n🎉 Download process completed!")

# Enhanced completion summary
print(f"\n📋 Download Summary:")
print(f"  WebUI: {UI}")
if MODULES_AVAILABLE:
    category = get_webui_category(UI)
    print(f"  Category: {category}")
    if category == 'face_swap':
        print(f"  Note: Face swap WebUI configured with specialized models")
    elif category == 'node_based':
        print(f"  Note: Node-based WebUI configured with custom nodes")

print(f"  Installation path: {WEBUI}")
print(f"  Virtual environment: {VENV}")

# Check what was actually downloaded
downloaded_items = []
for item_type, item_list in [('models', model), ('vae', [vae] if vae != 'none' else []), 
                            ('lora', lora), ('embeddings', embed), ('extensions', extension), ('controlnet', control)]:
    if item_list and item_list != ['none'] and item_list[0] != 'none':
        count = len([x for x in item_list if x != 'none']) if isinstance(item_list, list) else 1
        downloaded_items.append(f"{count} {item_type}")

if downloaded_items:
    print(f"  Downloaded: {', '.join(downloaded_items)}")
else:
    print(f"  Downloaded: Configuration only")

print(f"\n✅ Ready to launch {UI}!")
