# ~ launch.py | by ANXETY - FIXED VERSION with matplotlib fixes ~

import json_utils as js
from IPython import get_ipython
from pathlib import Path
import os
import sys

# --- MATPLOTLIB FIXES ---
# Fix matplotlib backend issues before any imports that might use it
os.environ['MPLBACKEND'] = 'Agg'  # Use non-interactive backend
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'  # Use temp directory for config
os.environ['FONTCONFIG_PATH'] = '/etc/fonts'  # Set font config path
os.environ['DISPLAY'] = ':0'  # Set display for headless environments

# Additional environment fixes for common issues
os.environ['PYTHONWARNINGS'] = 'ignore::UserWarning:matplotlib'  # Suppress matplotlib warnings
os.environ['OMP_NUM_THREADS'] = '1'  # Prevent threading issues
os.environ['MKL_NUM_THREADS'] = '1'  # Prevent Intel MKL threading issues

# Clear matplotlib font cache to prevent font-related errors
import matplotlib
matplotlib.use('Agg')  # Force non-interactive backend
try:
    import matplotlib.pyplot as plt
    plt.ioff()  # Turn off interactive mode
    # Clear font cache if it exists
    font_cache_dirs = [
        '/tmp/matplotlib',
        '/root/.cache/matplotlib',
        '/content/.cache/matplotlib'
    ]
    for cache_dir in font_cache_dirs:
        cache_path = Path(cache_dir)
        if cache_path.exists():
            import shutil
            try:
                shutil.rmtree(cache_path)
                cache_path.mkdir(parents=True, exist_ok=True)
            except:
                pass
except ImportError:
    pass  # matplotlib not available, skip

# --- ENVIRONMENT SETUP ---
osENV = os.environ
CD = os.chdir
ipySys = get_ipython().system

PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME, VENV, SETTINGS_PATH = PATHS['home_path'], PATHS['venv_path'], PATHS['settings_path']

# Load settings from JSON
settings = js.read(SETTINGS_PATH)
UI = settings.get('WEBUI', {}).get('current', 'A1111')
WEBUI_PATH = settings.get('WEBUI', {}).get('webui_path', str(HOME / UI))
WEBUI = Path(WEBUI_PATH)  # Convert to Path object
commandline_arguments = settings.get('WIDGETS', {}).get('commandline_arguments', '')
theme_accent = settings.get('WIDGETS', {}).get('theme_accent', 'anxety')
ENV_NAME = settings.get('ENVIRONMENT', {}).get('env_name')

class COLORS:
    B, X = "\033[34m", "\033[0m"
COL = COLORS

# --- HELPER FUNCTIONS ---
def get_launch_command():
    """Construct the final launch command."""
    # Remove duplicate arguments for a clean command
    base_args = commandline_arguments.split()
    unique_args = []
    for arg in base_args:
        if arg not in unique_args:
            unique_args.append(arg)
    
    final_args = " ".join(unique_args)
    
    # Add matplotlib-specific fixes to launch arguments
    common_args = ' --enable-insecure-extension-access --disable-console-progressbars --theme dark'
    common_args += ' --skip-version-check --no-half --precision full'  # Additional stability flags
    
    if ENV_NAME == 'Kaggle':
        common_args += ' --encrypt-pass=emoy4cnkm6imbysp84zmfiz1opahooblh7j34sgh'
    if theme_accent != 'anxety':
        common_args += f" --anxety {theme_accent}"
        
    return f"python3 launch.py {final_args}{common_args}"

def setup_python_path():
    """Setup Python path to avoid import issues."""
    # Add venv site-packages to Python path
    if VENV.exists():
        python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
        site_packages = VENV / 'lib' / python_version / 'site-packages'
        if site_packages.exists():
            sys.path.insert(0, str(site_packages))

def clear_problematic_caches():
    """Clear caches that might cause issues."""
    cache_dirs = [
        '/tmp/__pycache__',
        '/content/__pycache__',
        str(HOME / '__pycache__'),
        str(WEBUI / '__pycache__')  # Now WEBUI is a Path object
    ]
    
    for cache_dir in cache_dirs:
        cache_path = Path(cache_dir)
        if cache_path.exists():
            import shutil
            try:
                shutil.rmtree(cache_path)
            except:
                pass

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    print("✅ Environment is ready. Preparing to launch...")
    
    # Setup environment fixes
    setup_python_path()
    clear_problematic_caches()
    
    LAUNCHER = get_launch_command()
    
    print(f"🔧 WebUI: {COL.B}{UI}{COL.X}")
    print(f"🚀 Launching with command: {LAUNCHER}")
    print("📊 Matplotlib backend set to 'Agg' for compatibility")

    try:
        CD(WEBUI)  # WEBUI is now a Path object, but CD() will convert it to string
        
        # Set additional environment variables before launch
        os.environ['CUDA_LAUNCH_BLOCKING'] = '1'  # Better CUDA error reporting
        os.environ['TORCH_USE_CUDA_DSA'] = '1'    # Enable CUDA device-side assertions
        
        # Launch with proper error handling
        ipySys(LAUNCHER)
        
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ An error occurred during launch: {e}")
        print("🔧 Trying alternative launch method...")
        
        # Alternative launch method if primary fails
        try:
            # Try launching with reduced arguments
            fallback_cmd = f"python3 launch.py --theme dark --enable-insecure-extension-access"
            print(f"🔄 Fallback command: {fallback_cmd}")
            ipySys(fallback_cmd)
        except Exception as fallback_error:
            print(f"❌ Fallback launch also failed: {fallback_error}")
            print("💡 Please check the WebUI logs for more detailed error information.")
