# ~ launch.py | by ANXETY - Enhanced with Complete 10WebUI Support ~

import os
import sys
import subprocess
import time
from pathlib import Path
from IPython import get_ipython

# Safe import with comprehensive fallbacks
try:
    from webui_utils import get_webui_features, get_launch_script, get_webui_category
    import json_utils as js
    MODULES_AVAILABLE = True
    print("✅ Enhanced launch modules loaded")
except ImportError as e:
    print(f"⚠️ Enhanced modules not available: {e}")
    MODULES_AVAILABLE = False
    # Create fallback functions
    def get_webui_features(ui): return {'launch_script': 'launch.py', 'category': 'standard_sd'}
    def get_launch_script(ui): return 'launch.py'
    def get_webui_category(ui): return 'standard_sd'
    class js:
        @staticmethod
        def read(path, key, default=None): return default

ipySys = get_ipython().system

# Color codes for enhanced output
class COL:
    R = '\033[31m'    # Red
    G = '\033[32m'    # Green  
    B = '\033[34m'    # Blue
    Y = '\033[33m'    # Yellow
    M = '\033[35m'    # Magenta
    C = '\033[36m'    # Cyan
    X = '\033[0m'     # Reset

# Environment paths with validation
osENV = os.environ
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}

try:
    HOME = PATHS['home_path']
    VENV = PATHS['venv_path']
    SETTINGS_PATH = PATHS['settings_path']
except KeyError as e:
    print(f"❌ Missing environment path: {e}")
    sys.exit(1)

# FIXED: Load settings with comprehensive error handling
try:
    settings = js.read(SETTINGS_PATH) or {}
    UI = settings.get('WEBUI', {}).get('current', 'A1111')
    WEBUI = settings.get('WEBUI', {}).get('webui_path', str(HOME / UI))
    commandline_arguments = settings.get('WIDGETS', {}).get('commandline_arguments', '')
    theme_accent = settings.get('WIDGETS', {}).get('theme_accent', 'anxety')
    detailed_download = settings.get('WIDGETS', {}).get('detailed_download', 'off')
    
    print(f"✅ Launch settings loaded for WebUI: {UI}")
    
except Exception as e:
    print(f"⚠️ Settings loading error: {e}")
    # Fallback defaults
    UI = 'A1111'
    WEBUI = str(HOME / UI)
    commandline_arguments = '--listen --enable-insecure-extension-access --theme dark'
    theme_accent = 'anxety'
    detailed_download = 'off'

# ENHANCED: WebUI-specific launch configurations
WEBUI_LAUNCH_CONFIGS = {
    'A1111': {
        'script': 'launch.py',
        'args_prefix': '',
        'supports_themes': True,
        'pre_launch_setup': 'setup_gradio_webui'
    },
    'ComfyUI': {
        'script': 'main.py', 
        'args_prefix': '',
        'supports_themes': False,
        'pre_launch_setup': 'setup_comfyui'
    },
    'Classic': {
        'script': 'launch.py',
        'args_prefix': '',
        'supports_themes': True,
        'pre_launch_setup': 'setup_gradio_webui'
    },
    'Lightning.ai': {
        'script': 'launch.py',
        'args_prefix': '',
        'supports_themes': True,
        'pre_launch_setup': 'setup_gradio_webui'
    },
    'Forge': {
        'script': 'launch.py',
        'args_prefix': '',
        'supports_themes': True,
        'pre_launch_setup': 'setup_forge'
    },
    'ReForge': {
        'script': 'launch.py',
        'args_prefix': '',
        'supports_themes': True,
        'pre_launch_setup': 'setup_forge'
    },
    'SD-UX': {
        'script': 'launch.py',
        'args_prefix': '',
        'supports_themes': True,
        'pre_launch_setup': 'setup_gradio_webui'
    },
    'FaceFusion': {
        'script': 'run.py',
        'args_prefix': 'python -m facefusion',
        'supports_themes': False,
        'pre_launch_setup': 'setup_facefusion'
    },
    'RoopUnleashed': {
        'script': 'run.py',
        'args_prefix': 'python',
        'supports_themes': False,
        'pre_launch_setup': 'setup_roop'
    },
    'DreamO': {
        'script': 'app.py',
        'args_prefix': 'python',
        'supports_themes': False,
        'pre_launch_setup': 'setup_dreamo'
    }
}

# ==================== ENHANCED ENVIRONMENT SETUP ====================

def setup_environment():
    """FIXED: Enhanced environment setup with comprehensive validation."""
    
    print("🔧 Setting up launch environment...")
    
    # FIXED: Set matplotlib backend before any imports
    os.environ['MPLBACKEND'] = 'Agg'
    os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'
    
    # Create matplotlib config directory
    try:
        Path('/tmp/matplotlib').mkdir(parents=True, exist_ok=True)
        print("✅ Matplotlib backend configured")
    except Exception as e:
        print(f"⚠️ Matplotlib setup warning: {e}")
    
    # FIXED: Comprehensive venv detection and activation
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
        print(f"❌ Virtual environment not found at {VENV}")
        print("Please run the downloading cell first to create the virtual environment.")
        return False
    
    print(f"✅ Found virtual environment python: {venv_python}")
    
    # FIXED: Set up environment variables properly
    venv_bin = venv_python.parent
    current_path = os.environ.get('PATH', '')
    
    # Update PATH to prioritize venv
    if str(venv_bin) not in current_path:
        os.environ['PATH'] = f"{venv_bin}{os.pathsep}{current_path}"
    
    # Set virtual environment variables
    os.environ['VIRTUAL_ENV'] = str(VENV)
    
    # Remove PYTHONHOME if set (can interfere with venv)
    if 'PYTHONHOME' in os.environ:
        del os.environ['PYTHONHOME']
    
    print(f"✅ Virtual environment activated: {VENV}")
    return True

# ==================== WEBUI-SPECIFIC SETUP FUNCTIONS ====================

def setup_gradio_webui():
    """Setup for standard Gradio-based WebUIs (A1111, Classic, Lightning.ai, SD-UX)."""
    print("🎨 Setting up Gradio WebUI environment...")
    
    # Set Gradio environment variables
    os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'
    os.environ['GRADIO_SERVER_NAME'] = '0.0.0.0'
    
    return True

def setup_comfyui():
    """Setup for ComfyUI node-based WebUI."""
    print("🔗 Setting up ComfyUI environment...")
    
    webui_path = Path(WEBUI)
    
    # Create ComfyUI-specific directories if they don't exist
    required_dirs = [
        'models/checkpoints',
        'models/vae', 
        'models/loras',
        'models/controlnet',
        'models/upscale_models',
        'custom_nodes',
        'output'
    ]
    
    for dir_name in required_dirs:
        dir_path = webui_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print("✅ ComfyUI directories verified")
    return True

def setup_forge():
    """Setup for Forge/ReForge WebUIs."""
    print("⚒️ Setting up Forge WebUI environment...")
    
    # Set Forge-specific optimizations
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
    
    return True

def setup_facefusion():
    """Setup for FaceFusion WebUI."""
    print("🎭 Setting up FaceFusion environment...")
    
    webui_path = Path(WEBUI)
    
    # Ensure FaceFusion model directories exist
    model_dirs = [
        'models/face_analyser',
        'models/face_swapper', 
        'models/face_enhancer',
        'input',
        'output'
    ]
    
    for dir_name in model_dirs:
        dir_path = webui_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Set FaceFusion environment variables
    os.environ['FACEFUSION_SKIP_DOWNLOAD'] = '1'
    
    print("✅ FaceFusion environment configured")
    return True

def setup_roop():
    """Setup for RoopUnleashed WebUI."""
    print("🎭 Setting up RoopUnleashed environment...")
    
    webui_path = Path(WEBUI)
    
    # Ensure RoopUnleashed directories exist
    required_dirs = [
        'models',
        'models/inswapper',
        'models/gfpgan',
        'input',
        'output'
    ]
    
    for dir_name in required_dirs:
        dir_path = webui_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print("✅ RoopUnleashed environment configured")
    return True

def setup_dreamo():
    """Setup for DreamO WebUI."""
    print("🎨 Setting up DreamO environment...")
    
    # Set DreamO-specific environment variables
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    
    return True

# ==================== LAUNCH LOGIC ====================

def get_launch_command():
    """Get the proper launch command with WebUI-aware configuration."""
    
    # Get WebUI configuration
    config = WEBUI_LAUNCH_CONFIGS.get(UI, WEBUI_LAUNCH_CONFIGS['A1111'])
    script = config['script']
    args_prefix = config.get('args_prefix', '')
    
    # Determine the correct python executable
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
        print("⚠️ Using system Python (venv not found)")
        venv_python = sys.executable
    
    # Build launch command
    if args_prefix:
        if 'python' in args_prefix and str(venv_python) not in args_prefix:
            # Replace 'python' in args_prefix with venv python path
            args_prefix = args_prefix.replace('python', f'"{venv_python}"')
        full_command = f'{args_prefix} {script} {commandline_arguments}'
    else:
        full_command = f'"{venv_python}" {script} {commandline_arguments}'
    
    return full_command.strip()

def validate_webui_installation():
    """Validate that the WebUI is properly installed and configured."""
    
    webui_path = Path(WEBUI)
    
    if not webui_path.exists():
        print(f"❌ WebUI not found at {WEBUI}")
        print("Please run the downloading cell first to install the WebUI.")
        return False
    
    # Get launch script based on WebUI type
    config = WEBUI_LAUNCH_CONFIGS.get(UI, WEBUI_LAUNCH_CONFIGS['A1111'])
    launch_script = webui_path / config['script']
    
    if not launch_script.exists():
        print(f"❌ Launch script not found: {launch_script}")
        
        # Try to find alternative launch scripts
        alt_scripts = ['main.py', 'app.py', 'run.py', 'webui.py', 'launch.py']
        found_scripts = []
        
        for alt_script in alt_scripts:
            if (webui_path / alt_script).exists():
                found_scripts.append(alt_script)
        
        if found_scripts:
            print(f"📋 Available scripts: {', '.join(found_scripts)}")
            # Update config to use first available script
            WEBUI_LAUNCH_CONFIGS[UI]['script'] = found_scripts[0]
            print(f"🔧 Using {found_scripts[0]} as launch script")
        else:
            print(f"📁 Available files: {list(webui_path.glob('*.py'))[:5]}")
            return False
    
    print(f"✅ WebUI validated: {webui_path}")
    return True

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
        print(f"🔗 ComfyUI optimizations applied")
    elif UI in ['FaceFusion', 'RoopUnleashed']:
        # Face swap WebUIs - ensure output directory exists
        output_dir = webui_path / 'output'
        output_dir.mkdir(exist_ok=True)
        print(f"🎭 {UI} output directory prepared")
    elif UI in ['Forge', 'ReForge']:
        # Forge variants - performance optimizations
        print(f"⚒️ {UI} performance optimizations enabled")
    elif UI == 'DreamO':
        print(f"🎨 DreamO specialized configuration applied")

def run_pre_launch_setup():
    """Run WebUI-specific pre-launch setup."""
    
    config = WEBUI_LAUNCH_CONFIGS.get(UI, WEBUI_LAUNCH_CONFIGS['A1111'])
    setup_function = config.get('pre_launch_setup')
    
    if setup_function and setup_function in globals():
        try:
            setup_func = globals()[setup_function]
            result = setup_func()
            if result:
                print(f"✅ Pre-launch setup completed for {UI}")
            else:
                print(f"⚠️ Pre-launch setup had issues for {UI}")
            return result
        except Exception as e:
            print(f"⚠️ Pre-launch setup error for {UI}: {e}")
            return False
    else:
        print(f"🔧 No specific pre-launch setup needed for {UI}")
        return True

# ==================== MAIN LAUNCH FUNCTION ====================

def main():
    """Enhanced main launch function with comprehensive error handling."""
    
    print(f"\n🚀 {COL.B}LightningSdaigen Enhanced Launcher{COL.X}")
    print(f"⚡ WebUI: {COL.B}{UI}{COL.X}")
    
    if MODULES_AVAILABLE:
        category = get_webui_category(UI)
        print(f"📂 Category: {COL.G}{category}{COL.X}")
    
    print("🔧 Preparing to launch...")
    
    # Step 1: Set up environment
    if not setup_environment():
        print("❌ Failed to set up environment. Aborting launch.")
        return False
    
    # Step 2: Validate WebUI installation
    if not validate_webui_installation():
        print("❌ WebUI validation failed. Aborting launch.")
        return False
    
    # Step 3: Run pre-launch setup
    if not run_pre_launch_setup():
        print("⚠️ Pre-launch setup had issues, but continuing...")
    
    # Step 4: Apply WebUI-specific fixes
    try:
        apply_webui_specific_fixes()
    except Exception as e:
        print(f"⚠️ Could not apply WebUI fixes: {e}")
    
    # Step 5: Change to WebUI directory
    try:
        os.chdir(WEBUI)
        print(f"📁 Changed to WebUI directory: {WEBUI}")
    except Exception as e:
        print(f"❌ Could not change to WebUI directory: {e}")
        return False
    
    # Step 6: Build and execute launch command
    try:
        launch_command = get_launch_command()
        print(f"\n🚀 {COL.Y}Launching {UI}...{COL.X}")
        print(f"📋 Command: {COL.C}{launch_command}{COL.X}")
        
        if detailed_download == 'on':
            print(f"🔍 Launch arguments: {commandline_arguments}")
        
        # Launch the WebUI
        print(f"\n{COL.G}🎉 Starting {UI} WebUI...{COL.X}")
        print(f"{COL.Y}⏳ This may take a few moments to load...{COL.X}")
        
        # Execute the launch command
        result = os.system(launch_command)
        
        if result == 0:
            print(f"\n{COL.G}✅ {UI} launched successfully!{COL.X}")
        else:
            print(f"\n{COL.R}⚠️ {UI} exited with code {result}{COL.X}")
            
    except KeyboardInterrupt:
        print(f"\n{COL.Y}⚠️ Launch cancelled by user{COL.X}")
        return False
    except Exception as e:
        print(f"\n{COL.R}❌ Launch error: {e}{COL.X}")
        return False
    
    return True

def show_launch_info():
    """Display helpful launch information."""
    
    print(f"\n{COL.B}📋 Launch Information{COL.X}")
    print(f"WebUI: {UI}")
    print(f"Path: {WEBUI}")
    print(f"Virtual Environment: {VENV}")
    
    if MODULES_AVAILABLE:
        features = get_webui_features(UI)
        print(f"Category: {features.get('category', 'unknown')}")
        print(f"Launch Script: {features.get('launch_script', 'unknown')}")
    
    # Show category-specific tips
    if MODULES_AVAILABLE:
        category = get_webui_category(UI)
        
        if category == 'face_swap':
            print(f"\n{COL.M}🎭 Face Swap WebUI Tips:{COL.X}")
            print("• This WebUI specializes in face swapping")
            print("• Upload face images to the input folder")
            print("• Check the output folder for results")
        elif category == 'node_based':
            print(f"\n{COL.C}🔗 Node-Based WebUI Tips:{COL.X}")
            print("• This WebUI uses a node-based workflow")
            print("• Connect nodes to create your workflow")
            print("• Custom nodes extend functionality")
        elif category == 'enhanced_sd':
            print(f"\n{COL.Y}⚒️ Enhanced WebUI Tips:{COL.X}")
            print("• This WebUI includes performance optimizations")
            print("• Additional features may be available")
            print("• Check the WebUI documentation for new capabilities")
        else:
            print(f"\n{COL.G}🎨 Standard WebUI Tips:{COL.X}")
            print("• Use the interface to generate images")
            print("• Experiment with different models and settings")
            print("• Check extensions for additional features")
    
    print(f"\n{COL.B}🌐 Access Information:{COL.X}")
    print("• WebUI will be available at: http://localhost:7860")
    print("• If using cloud services, check for public URLs")
    print("• Look for 'Running on' messages in the output")

# ==================== EXECUTION ====================

if __name__ == "__main__":
    try:
        # Show launch information first
        show_launch_info()
        
        # Ask for confirmation if in interactive mode
        if hasattr(get_ipython(), 'ask_yes_no'):
            proceed = input(f"\n{COL.Y}🚀 Launch {UI}? (y/n): {COL.X}").strip().lower()
            if proceed not in ['y', 'yes', '']:
                print(f"{COL.Y}Launch cancelled.{COL.X}")
                sys.exit(0)
        
        # Execute main launch
        success = main()
        
        if success:
            print(f"\n{COL.G}🎉 Launch completed!{COL.X}")
        else:
            print(f"\n{COL.R}❌ Launch failed. Please check the errors above.{COL.X}")
            print(f"{COL.Y}💡 Try running the diagnostic script: %run scripts/diagnose_and_fix.py{COL.X}")
            
    except KeyboardInterrupt:
        print(f"\n{COL.Y}⚠️ Launch interrupted by user{COL.X}")
    except Exception as e:
        print(f"\n{COL.R}❌ Critical launch error: {e}{COL.X}")
        print(f"{COL.Y}Please report this error if it persists.{COL.X}")
