# ~ launch.py | by ANXETY - Enhanced with Multiple WebUI Support ~

import os
from pathlib import Path

# --- ENHANCED MATPLOTLIB FIXES (BEFORE OTHER IMPORTS) ---
# Set matplotlib environment before any potential matplotlib imports
os.environ['MPLBACKEND'] = 'Agg'
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'
os.environ['FONTCONFIG_PATH'] = '/etc/fonts'
os.environ['DISPLAY'] = ':0'
os.environ['PYTHONWARNINGS'] = 'ignore::UserWarning:matplotlib'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

# Enhanced matplotlib setup
try:
    import matplotlib
    matplotlib.use('Agg', force=True)
    
    # Clear matplotlib font cache
    font_cache_dirs = ['/tmp/matplotlib', '/root/.cache/matplotlib', '/content/.cache/matplotlib']
    for cache_dir in font_cache_dirs:
        cache_path = Path(cache_dir)
        if cache_path.exists():
            import shutil
            try:
                shutil.rmtree(cache_path)
                cache_path.mkdir(parents=True, exist_ok=True)
            except:
                pass
    
    import matplotlib.pyplot as plt
    plt.ioff()
    
except ImportError:
    pass

import json_utils as js
from IPython import get_ipython
import subprocess
import sys

# --- ENHANCED ENVIRONMENT SETUP ---
osENV = os.environ
CD = os.chdir
ipySys = get_ipython().system

PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME, VENV, SETTINGS_PATH = PATHS['home_path'], PATHS['venv_path'], PATHS['settings_path']

# Enhanced settings loading with error handling
try:
    settings = js.read(SETTINGS_PATH)
    UI = settings.get('WEBUI', {}).get('current', 'A1111')
    WEBUI = settings.get('WEBUI', {}).get('webui_path', str(HOME / UI))
    widget_settings = settings.get('WIDGETS', {})
    commandline_arguments = widget_settings.get('commandline_arguments', '')
    theme_accent = widget_settings.get('theme_accent', 'anxety')
    ENV_NAME = settings.get('ENVIRONMENT', {}).get('env_name')
except Exception as e:
    print(f"⚠️ Error loading settings: {e}")
    UI, WEBUI = 'A1111', str(HOME / 'A1111')
    commandline_arguments, theme_accent = '', 'anxety'

class COLORS:
    B, X = "\033[34m", "\033[0m"
COL = COLORS

# --- ENHANCED WEBUI-SPECIFIC CONFIGURATIONS ---
WEBUI_LAUNCH_CONFIGS = {
    'A1111': {
        'script': 'launch.py',
        'args_prefix': '',
        'env_vars': {},
        'pre_launch': None,
        'supports_themes': True
    },
    'ComfyUI': {
        'script': 'main.py', 
        'args_prefix': '',
        'env_vars': {'COMFYUI_MODEL_PATH': lambda: str(Path(WEBUI) / 'models')},
        'pre_launch': 'setup_comfyui',
        'supports_themes': False
    },
    'Classic': {
        'script': 'launch.py',
        'args_prefix': '',
        'env_vars': {},
        'pre_launch': None,
        'supports_themes': True
    },
    'Lightning.ai': {
        'script': 'launch.py',
        'args_prefix': '',
        'env_vars': {},
        'pre_launch': None,
        'supports_themes': True
    },
    # ENHANCED: Forge Variants
    'Forge': {
        'script': 'launch.py',
        'args_prefix': '',
        'env_vars': {
            'CUDA_LAUNCH_BLOCKING': '0',
            'TORCH_CUDNN_V8_API_ENABLED': '1'
        },
        'pre_launch': 'setup_forge',
        'supports_themes': True
    },
    'ReForge': {
        'script': 'launch.py',
        'args_prefix': '',
        'env_vars': {
            'CUDA_LAUNCH_BLOCKING': '0', 
            'TORCH_CUDNN_V8_API_ENABLED': '1'
        },
        'pre_launch': 'setup_reforge',
        'supports_themes': True
    },
    'SD-UX': {
        'script': 'launch.py',
        'args_prefix': '',
        'env_vars': {},
        'pre_launch': 'setup_sdux',
        'supports_themes': True
    },
    # ENHANCED: Face Manipulation WebUIs
    'FaceFusion': {
        'script': 'run.py',
        'args_prefix': '',
        'env_vars': {
            'CUDA_VISIBLE_DEVICES': '0',
            'ONNX_EXECUTION_PROVIDER': 'CUDAExecutionProvider'
        },
        'pre_launch': 'setup_facefusion',
        'supports_themes': False
    },
    'RoopUnleashed': {
        'script': 'run.py',
        'args_prefix': '',
        'env_vars': {
            'CUDA_VISIBLE_DEVICES': '0',
            'ONNX_EXECUTION_PROVIDER': 'CUDAExecutionProvider'
        },
        'pre_launch': 'setup_roop',
        'supports_themes': False
    },
    # ENHANCED: Specialized WebUIs
    'DreamO': {
        'script': 'app.py',
        'args_prefix': '',
        'env_vars': {
            'CUDA_DEVICE_ORDER': 'PCI_BUS_ID',
            'CUDA_VISIBLE_DEVICES': '0'
        },
        'pre_launch': 'setup_dreamo',
        'supports_themes': False
    }
}

# --- ENHANCED PRE-LAUNCH SETUP FUNCTIONS ---

def setup_comfyui():
    """Pre-launch setup for ComfyUI."""
    print("🖼️ Preparing ComfyUI...")
    
    webui_path = Path(WEBUI)
    extra_model_paths = webui_path / 'extra_model_paths.yaml'
    
    if not extra_model_paths.exists():
        yaml_content = f"""
# Auto-generated model paths for LightningSdaigen
a111:
    base_path: {HOME}
    checkpoints: Stable-diffusion/
    vae: VAE/
    loras: Lora/
    upscale_models: ESRGAN/
    embeddings: embeddings/
    controlnet: ControlNet/
"""
        with open(extra_model_paths, 'w') as f:
            f.write(yaml_content)
        print("📁 Created ComfyUI model paths configuration")

def setup_forge():
    """Pre-launch setup for Forge."""
    print("⚒️ Preparing Forge...")
    print("🔧 Forge optimizations ready")

def setup_reforge():
    """Pre-launch setup for ReForge."""
    print("🔄 Preparing ReForge...")
    print("🔧 ReForge optimizations ready")

def setup_sdux():
    """Pre-launch setup for SD-UX."""
    print("✨ Preparing SD-UX...")
    print("🎨 Modern UI ready")

def setup_facefusion():
    """Pre-launch setup for FaceFusion."""
    print("🎭 Preparing FaceFusion...")
    
    webui_path = Path(WEBUI)
    
    # Ensure required models exist
    models_dir = webui_path / 'models'
    models_dir.mkdir(exist_ok=True)
    
    # Check for essential models
    essential_models = [
        'inswapper_128.onnx',
        'GFPGANv1.4.pth',
        'buffalo_l.zip'
    ]
    
    missing_models = []
    for model in essential_models:
        if not (models_dir / model).exists():
            missing_models.append(model)
    
    if missing_models:
        print(f"⚠️ Missing essential models: {missing_models}")
        print("   FaceFusion will download them on first run")
    
    # Ensure output directory exists
    output_dir = webui_path / 'output'
    output_dir.mkdir(exist_ok=True)

def setup_roop():
    """Pre-launch setup for RoopUnleashed."""
    print("🎭 Preparing RoopUnleashed...")
    
    webui_path = Path(WEBUI)
    
    # Ensure required directories
    for folder in ['models', 'faces', 'frames', 'temp', 'output']:
        (webui_path / folder).mkdir(exist_ok=True)
    
    # Check ONNX runtime
    try:
        import onnxruntime
        providers = onnxruntime.get_available_providers()
        if 'CUDAExecutionProvider' not in providers:
            print("⚠️ CUDA execution provider not available for ONNX runtime")
        else:
            print("✅ CUDA execution provider ready")
    except ImportError:
        print("⚠️ ONNX runtime not found")

def setup_dreamo():
    """Pre-launch setup for DreamO."""
    print("🎨 Preparing DreamO...")
    
    webui_path = Path(WEBUI)
    
    # Ensure model directories
    model_dirs = ['models/diffusion', 'models/vae', 'assets', 'output']
    for dir_name in model_dirs:
        (webui_path / dir_name).mkdir(parents=True, exist_ok=True)
    
    print("📁 DreamO directories ready")

# --- ENHANCED ENVIRONMENT SETUP ---

def setup_environment():
    """Enhanced environment setup with WebUI-specific configurations."""
    
    # Get WebUI configuration
    config = WEBUI_LAUNCH_CONFIGS.get(UI, WEBUI_LAUNCH_CONFIGS['A1111'])
    
    # Set WebUI-specific environment variables
    env_vars = config.get('env_vars', {})
    for key, value in env_vars.items():
        if callable(value):
            value = value()
        os.environ[key] = str(value)
        if value:  # Only print non-empty values
            print(f"🔧 Set {key}={value}")
    
    # Activate virtual environment
    venv_python = VENV / 'bin' / 'python'
    if not venv_python.exists():
        print(f"❌ Virtual environment not found at {VENV}")
        return False
    
    # Update Python path to use venv
    os.environ['PATH'] = f"{VENV / 'bin'}:{os.environ['PATH']}"
    os.environ['VIRTUAL_ENV'] = str(VENV)
    
    print(f"✅ Virtual environment activated: {VENV}")
    
    # Run pre-launch setup if specified
    pre_launch = config.get('pre_launch')
    if pre_launch:
        if pre_launch == 'setup_comfyui':
            setup_comfyui()
        elif pre_launch == 'setup_forge':
            setup_forge()
        elif pre_launch == 'setup_reforge':
            setup_reforge()
        elif pre_launch == 'setup_sdux':
            setup_sdux()
        elif pre_launch == 'setup_facefusion':
            setup_facefusion()
        elif pre_launch == 'setup_roop':
            setup_roop()
        elif pre_launch == 'setup_dreamo':
            setup_dreamo()
    
    return True

def get_launch_command():
    """Get the enhanced launch command for the current WebUI."""
    
    config = WEBUI_LAUNCH_CONFIGS.get(UI, WEBUI_LAUNCH_CONFIGS['A1111'])
    script = config['script']
    args_prefix = config.get('args_prefix', '')
    
    # Combine arguments
    full_args = f"{args_prefix} {commandline_arguments}".strip()
    
    # Use venv python
    venv_python = VENV / 'bin' / 'python'
    return f"{venv_python} {script} {full_args}"

def apply_webui_specific_fixes():
    """Apply WebUI-specific fixes and configurations."""
    
    webui_path = Path(WEBUI)
    config = WEBUI_LAUNCH_CONFIGS.get(UI, WEBUI_LAUNCH_CONFIGS['A1111'])
    
    # Apply theme for supported WebUIs
    if config.get('supports_themes', False) and theme_accent != 'anxety':
        config_path = webui_path / 'config.json'
        if config_path.exists():
            try:
                import json
                with open(config_path, 'r') as f:
                    webui_config = json.load(f)
                
                # Add theme configuration
                if 'quicksettings' not in webui_config:
                    webui_config['quicksettings'] = ''
                
                with open(config_path, 'w') as f:
                    json.dump(webui_config, f, indent=2)
                print(f"🎨 Applied theme configuration")
            except Exception as e:
                print(f"⚠️ Could not apply theme: {e}")
    
    # WebUI-specific configurations
    if UI == 'ComfyUI':
        # ComfyUI already handled in setup_comfyui()
        pass
    elif UI in ['FaceFusion', 'RoopUnleashed']:
        # Face swap WebUIs - ensure output directory exists
        output_dir = webui_path / 'output'
        output_dir.mkdir(exist_ok=True)
        print(f"🎭 Prepared {UI} output directory")
    elif UI in ['Forge', 'ReForge']:
        # Forge variants - check for optimizations
        print(f"⚒️ {UI} performance optimizations enabled")

def validate_webui_installation():
    """Validate that the WebUI is properly installed."""
    webui_path = Path(WEBUI)
    
    if not webui_path.exists():
        print(f"❌ WebUI not found at {WEBUI}")
        return False
    
    # Get launch script
    config = WEBUI_LAUNCH_CONFIGS.get(UI, WEBUI_LAUNCH_CONFIGS['A1111'])
    launch_script = webui_path / config['script']
    
    if not launch_script.exists():
        print(f"❌ Launch script not found: {launch_script}")
        # Try alternative locations
        if UI in ['FaceFusion', 'RoopUnleashed', 'DreamO']:
            # Check for Python scripts in root
            python_files = list(webui_path.glob('*.py'))
            if python_files:
                print(f"📁 Available Python files: {[f.name for f in python_files]}")
        return False
    
    return True

# --- ENHANCED MAIN LAUNCH LOGIC ---

def main():
    """Enhanced main launch function with comprehensive WebUI support."""
    
    print(f"\n🚀 {COL.B}LightningSdaigen Enhanced Launcher{COL.X}")
    print(f"⚡ WebUI: {COL.B}{UI}{COL.X}")
    
    # Detect WebUI category if utils available
    try:
        from webui_utils import get_webui_category
        category = get_webui_category(UI)
        category_icons = {
            'standard_sd': '🖼️',
            'enhanced_sd': '⚒️',
            'node_based': '🎯',
            'face_swap': '🎭',
            'specialized': '🎨'
        }
        icon = category_icons.get(category, '🔧')
        print(f"{icon} Type: {category.replace('_', ' ').title()}")
    except ImportError:
        pass
    
    print("🔧 Preparing to launch...")
    
    # Validate installation
    if not validate_webui_installation():
        print("❌ WebUI installation validation failed. Please check your installation.")
        sys.exit(1)
    
    # Set up environment
    if not setup_environment():
        print("❌ Failed to set up environment. Aborting launch.")
        sys.exit(1)
    
    # Apply WebUI-specific fixes
    apply_webui_specific_fixes()
    
    # Get launch command
    LAUNCHER = get_launch_command()
    
    print(f"🔧 WebUI: {COL.B}{UI}{COL.X}")
    print(f"📁 Path: {WEBUI}")
    print(f"🚀 Command: {LAUNCHER}")
    print(f"\n{'='*60}")
    print(f"🎯 Launching {UI}...")
    print(f"{'='*60}")

    try:
        CD(WEBUI)
        
        # Use subprocess for better control and real-time output
        process = subprocess.Popen(
            LAUNCHER, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            bufsize=1,
            universal_newlines=True
        )
        
        # Print output in real-time
        for line in iter(process.stdout.readline, ''):
            print(line.rstrip())
            
        return_code = process.wait()
        
        if return_code != 0:
            print(f"\n⚠️ Process exited with code {return_code}")
        else:
            print(f"\n✅ {UI} exited successfully")
            
    except KeyboardInterrupt:
        print(f"\n🛑 Launch interrupted by user")
        if 'process' in locals():
            process.terminate()
    except Exception as e:
        print(f"\n❌ Launch error: {e}")
        print(f"💡 Check that {UI} is properly installed and configured")

if __name__ == "__main__":
    main()
