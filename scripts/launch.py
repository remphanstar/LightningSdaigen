# ~ launch.py | by ANXETY - ENHANCED VERSION with venv support and matplotlib fixes ~

import json_utils as js
from IPython import get_ipython
from pathlib import Path
import os
import sys
import subprocess

# --- MATPLOTLIB FIXES (BEFORE OTHER IMPORTS) ---
# FIXED: Set matplotlib environment before any potential matplotlib imports
os.environ['MPLBACKEND'] = 'Agg'  # Use non-interactive backend
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'  # Use temp directory for config
os.environ['FONTCONFIG_PATH'] = '/etc/fonts'  # Set font config path
os.environ['DISPLAY'] = ':0'  # Set display for headless environments
os.environ['PYTHONWARNINGS'] = 'ignore::UserWarning:matplotlib'  # Suppress matplotlib warnings
os.environ['OMP_NUM_THREADS'] = '1'  # Prevent threading issues
os.environ['MKL_NUM_THREADS'] = '1'  # Prevent Intel MKL threading issues

# FIXED: Import matplotlib early and configure it properly
try:
    import matplotlib
    matplotlib.use('Agg', force=True)  # Force non-interactive backend
    
    # Clear matplotlib font cache to prevent font-related errors
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
                
    # Import pyplot and turn off interactive mode
    import matplotlib.pyplot as plt
    plt.ioff()  # Turn off interactive mode
    
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
    G, Y, R = "\033[32m", "\033[33m", "\033[31m"
COL = COLORS

# --- VENV MANAGEMENT FUNCTIONS ---
def detect_and_setup_venv():
    """Detect and setup virtual environment for proper package usage."""
    venv_python = VENV / 'bin' / 'python'
    venv_activate = VENV / 'bin' / 'activate'
    
    print(f"🔍 Checking virtual environment at: {VENV}")
    
    if not VENV.exists():
        print(f"{COL.Y}⚠️  Virtual environment not found at {VENV}{COL.X}")
        return False, sys.executable
    
    if not venv_python.exists():
        print(f"{COL.Y}⚠️  Python executable not found in venv{COL.X}")
        return False, sys.executable
    
    # Verify venv Python works
    try:
        result = subprocess.run([str(venv_python), "--version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"{COL.G}✅ Found working venv Python: {result.stdout.strip()}{COL.X}")
        else:
            print(f"{COL.R}❌ Venv Python verification failed{COL.X}")
            return False, sys.executable
    except Exception as e:
        print(f"{COL.R}❌ Error checking venv Python: {e}{COL.X}")
        return False, sys.executable
    
    # Setup venv environment variables
    os.environ['VIRTUAL_ENV'] = str(VENV)
    os.environ['PATH'] = f"{VENV / 'bin'}:{os.environ.get('PATH', '')}"
    
    # Add venv site-packages to Python path
    python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    site_packages = VENV / 'lib' / python_version / 'site-packages'
    if site_packages.exists():
        sys.path.insert(0, str(site_packages))
        print(f"{COL.G}✅ Added venv site-packages to Python path{COL.X}")
    
    return True, str(venv_python)

def check_venv_packages():
    """Check key packages in venv to ensure compatibility."""
    venv_python = VENV / 'bin' / 'python'
    
    if not venv_python.exists():
        return False
    
    key_packages = ['torch', 'diffusers', 'gradio', 'xformers']
    missing_packages = []
    
    print(f"{COL.B}📦 Checking key packages in venv:{COL.X}")
    
    for package in key_packages:
        try:
            result = subprocess.run([str(venv_python), '-c', f'import {package}; print(f"{package}: {{" + package + ".__version__}}")'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"  {COL.G}✅ {result.stdout.strip()}{COL.X}")
            else:
                print(f"  {COL.R}❌ {package}: Not found{COL.X}")
                missing_packages.append(package)
        except Exception:
            print(f"  {COL.R}❌ {package}: Check failed{COL.X}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"{COL.Y}⚠️  Missing packages: {', '.join(missing_packages)}{COL.X}")
        return False
    
    return True

# --- HELPER FUNCTIONS (Enhanced) ---
def get_launch_command(python_executable):
    """Construct the final launch command with proper Python executable."""
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
    
    # Use the specific Python executable (venv or system)
    python_cmd = python_executable if python_executable != sys.executable else "python3"
    
    return f"{python_cmd} launch.py {final_args}{common_args}"

def setup_python_path():
    """Setup Python path to avoid import issues."""
    # Add venv site-packages to Python path (already done in detect_and_setup_venv)
    # This function is kept for compatibility
    pass

def clear_problematic_caches():
    """Clear caches that might cause issues."""
    cache_dirs = [
        '/tmp/__pycache__',
        '/content/__pycache__',
        str(HOME / '__pycache__'),
        str(WEBUI / '__pycache__')  # WEBUI is now a Path object
    ]
    
    for cache_dir in cache_dirs:
        cache_path = Path(cache_dir)
        if cache_path.exists():
            import shutil
            try:
                shutil.rmtree(cache_path)
                print(f"{COL.G}🧹 Cleared cache: {cache_dir}{COL.X}")
            except:
                pass

def disable_problematic_extensions():
    """Temporarily disable extensions that cause import conflicts."""
    extensions_dir = WEBUI / 'extensions'
    
    if not extensions_dir.exists():
        return
    
    problematic_extensions = [
        "Supermerger",           # diffusers import error
        "clothseg",              # missing rembg
        "sd-webui-inpaint-anything",  # diffusers import error  
        "sd-webui-stripper"      # diffusers import error
    ]
    
    disabled_any = False
    for ext_name in problematic_extensions:
        ext_path = extensions_dir / ext_name
        disabled_path = extensions_dir / f"{ext_name}.disabled"
        
        if ext_path.exists() and not disabled_path.exists():
            try:
                ext_path.rename(disabled_path)
                print(f"{COL.Y}🔧 Temporarily disabled extension: {ext_name}{COL.X}")
                disabled_any = True
            except Exception as e:
                print(f"{COL.R}❌ Failed to disable {ext_name}: {e}{COL.X}")
    
    if disabled_any:
        print(f"{COL.B}💡 Extensions can be re-enabled later by removing .disabled suffix{COL.X}")

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    print("✅ Environment is ready. Preparing to launch...")
    
    # Setup environment fixes
    setup_python_path()
    clear_problematic_caches()
    
    # Detect and setup venv
    using_venv, python_executable = detect_and_setup_venv()
    
    if using_venv:
        print(f"{COL.G}🐍 Using virtual environment Python{COL.X}")
        venv_packages_ok = check_venv_packages()
        if not venv_packages_ok:
            print(f"{COL.Y}⚠️  Some packages missing in venv, but continuing...{COL.X}")
    else:
        print(f"{COL.Y}🐍 Using system Python (venv not available){COL.X}")
        # Disable problematic extensions when using system Python
        disable_problematic_extensions()
    
    LAUNCHER = get_launch_command(python_executable)
    
    print(f"🔧 WebUI: {COL.B}{UI}{COL.X}")
    print(f"🚀 Launching with command: {LAUNCHER}")
    print("📊 Matplotlib backend set to 'Agg' for compatibility")

    try:
        CD(WEBUI)
        
        # Set additional environment variables before launch
        os.environ['CUDA_LAUNCH_BLOCKING'] = '1'  # Better CUDA error reporting
        os.environ['TORCH_USE_CUDA_DSA'] = '1'    # Enable CUDA device-side assertions
        
        # Additional venv-specific environment setup
        if using_venv:
            os.environ['PYTHONPATH'] = f"{VENV / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'}:{os.environ.get('PYTHONPATH', '')}"
        
        # Launch with proper error handling
        print(f"\n{COL.B}{'='*60}{COL.X}")
        print(f"{COL.B}🌟 Starting WebUI... This may take a few minutes...{COL.X}")
        print(f"{COL.B}{'='*60}{COL.X}\n")
        
        ipySys(LAUNCHER)
        
    except KeyboardInterrupt:
        print(f"\n{COL.Y}⚠️  Process interrupted by user.{COL.X}")
    except Exception as e:
        print(f"\n{COL.R}❌ An error occurred during launch: {e}{COL.X}")
        print(f"{COL.B}🔧 Trying alternative launch method...{COL.X}")
        
        # Alternative launch method if primary fails
        try:
            # Try launching with reduced arguments and proper Python
            fallback_cmd = f"{python_executable} launch.py --theme dark --enable-insecure-extension-access"
            print(f"🔄 Fallback command: {fallback_cmd}")
            ipySys(fallback_cmd)
        except Exception as fallback_error:
            print(f"{COL.R}❌ Fallback launch also failed: {fallback_error}{COL.X}")
            print(f"{COL.B}💡 Troubleshooting suggestions:{COL.X}")
            print(f"   1. Check if venv is properly set up")
            print(f"   2. Verify all required packages are installed")
            print(f"   3. Try restarting runtime and re-running setup")
            print(f"   4. Check WebUI logs for detailed error information")
