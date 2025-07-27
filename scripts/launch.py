# ~ launch.py | by ANXETY - FIXED VERSION ~

import json_utils as js
from IPython import get_ipython
from pathlib import Path
import subprocess
import sys
import os

# --- ENVIRONMENT SETUP ---
osENV = os.environ
CD = os.chdir
ipySys = get_ipython().system

PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME, VENV, SETTINGS_PATH = PATHS['home_path'], PATHS['venv_path'], PATHS['settings_path']

# Load settings from JSON
settings = js.read(SETTINGS_PATH)
UI = settings.get('WEBUI', {}).get('current', 'A1111')
WEBUI = settings.get('WEBUI', {}).get('webui_path', str(HOME / UI))
commandline_arguments = settings.get('WIDGETS', {}).get('commandline_arguments', '')
theme_accent = settings.get('WIDGETS', {}).get('theme_accent', 'anxety')
ENV_NAME = settings.get('ENVIRONMENT', {}).get('env_name')

class COLORS:
    B, X = "\033[34m", "\033[0m"
COL = COLORS

# --- ENVIRONMENT ACTIVATION ---
def setup_environment():
    """Properly set up the virtual environment."""
    print("🔧 Preparing environment for launch...")
    
    # Check if venv exists
    if not VENV.exists():
        print(f"❌ Virtual environment not found at {VENV}")
        return False
    
    python_exe = VENV / 'bin' / 'python'
    if not python_exe.exists():
        print(f"❌ Python executable not found at {python_exe}")
        return False
    
    print(f"🐍 Activating virtual environment at {VENV}")
    
    # Set up environment variables for the venv
    bin_path = str(VENV / 'bin')
    lib_path = str(VENV / 'lib' / 'python3.11' / 'site-packages')
    
    # Update environment
    osENV['VIRTUAL_ENV'] = str(VENV)
    osENV['PATH'] = f"{bin_path}:{osENV.get('PATH', '')}"
    osENV['PYTHONPATH'] = f"{lib_path}:{osENV.get('PYTHONPATH', '')}"
    
    # Test the environment
    try:
        result = subprocess.run([str(python_exe), '-c', 'import torch; print(f"✅ PyTorch {torch.__version__} available")'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(result.stdout.strip())
        else:
            print(f"⚠️ PyTorch test failed: {result.stderr}")
            
        # Test other key packages
        test_packages = ['numpy', 'transformers', 'diffusers', 'gradio']
        for pkg in test_packages:
            result = subprocess.run([str(python_exe), '-c', f'import {pkg}; print("✅ {pkg} OK")'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(result.stdout.strip())
            else:
                print(f"⚠️ {pkg} test failed")
                
        print("✅ Virtual environment activated successfully")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Environment test timed out")
        return False
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False

def get_launch_command():
    """Construct the final launch command."""
    python_exe = VENV / 'bin' / 'python'
    
    # Remove duplicate arguments for a clean command
    base_args = commandline_arguments.split() if commandline_arguments else []
    unique_args = []
    seen = set()
    for arg in base_args:
        if arg not in seen:
            unique_args.append(arg)
            seen.add(arg)
    
    final_args = " ".join(unique_args)
    
    common_args = ' --enable-insecure-extension-access --disable-console-progressbars --theme dark'
    if ENV_NAME == 'Kaggle':
        common_args += ' --encrypt-pass=emoy4cnkm6imbysp84zmfiz1opahooblh7j34sgh'
    if theme_accent != 'anxety':
        common_args += f" --anxety {theme_accent}"
        
    return f"{python_exe} launch.py {final_args}{common_args}"

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    print("✅ Environment is ready. Preparing to launch...")
    
    # Set up environment first
    if not setup_environment():
        print("❌ Failed to set up environment. Aborting launch.")
        sys.exit(1)
    
    # Check if WebUI exists
    webui_path = Path(WEBUI)
    if not webui_path.exists():
        print(f"❌ WebUI not found at {WEBUI}")
        sys.exit(1)
    
    launch_py = webui_path / 'launch.py'
    if not launch_py.exists():
        print(f"❌ launch.py not found at {launch_py}")
        sys.exit(1)
    
    LAUNCHER = get_launch_command()
    
    print(f"🔧 WebUI: {COL.B}{UI}{COL.X}")
    print(f"🚀 Launching with command: {LAUNCHER}")

    try:
        CD(WEBUI)
        # Use subprocess instead of ipySys for better control
        process = subprocess.Popen(LAUNCHER, shell=True, stdout=subprocess.PIPE, 
                                 stderr=subprocess.STDOUT, text=True, bufsize=1)
        
        # Print output in real-time
        for line in process.stdout:
            print(line.rstrip())
            
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        if 'process' in locals():
            process.terminate()
    except Exception as e:
        print(f"\nAn error occurred during launch: {e}")
