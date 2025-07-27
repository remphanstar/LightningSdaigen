# ~ launch.py | by ANXETY - FINAL CLEAN VERSION ~

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

# --- CRITICAL VENV ACTIVATION ---
def activate_venv():
    """Properly activate the virtual environment"""
    venv_python = VENV / 'bin' / 'python'
    venv_pip = VENV / 'bin' / 'pip'
    
    # Verify venv exists and has the required executables
    if not venv_python.exists():
        raise RuntimeError(f"Virtual environment Python not found at {venv_python}")
    if not venv_pip.exists():
        raise RuntimeError(f"Virtual environment pip not found at {venv_pip}")
    
    print(f"🐍 Activating virtual environment at {VENV}")
    
    # Set up environment variables
    venv_bin = str(VENV / 'bin')
    python_version = "3.11"  # Match your venv version
    site_packages = str(VENV / f"lib/python{python_version}/site-packages")
    
    # Update PATH to prioritize venv
    current_path = osENV.get('PATH', '')
    osENV['PATH'] = f"{venv_bin}:{current_path}"
    
    # Update PYTHONPATH
    current_pythonpath = osENV.get('PYTHONPATH', '')
    osENV['PYTHONPATH'] = f"{site_packages}:{current_pythonpath}"
    
    # Set VIRTUAL_ENV environment variable
    osENV['VIRTUAL_ENV'] = str(VENV)
    
    # Remove PYTHONHOME if set (can interfere with venv)
    if 'PYTHONHOME' in osENV:
        del osENV['PYTHONHOME']
    
    # Update sys.path to use venv packages
    if site_packages not in sys.path:
        sys.path.insert(0, site_packages)
    
    # Verify PyTorch is available in the venv
    try:
        result = subprocess.run([str(venv_python), "-c", "import torch; print(f'PyTorch {torch.__version__} available')"], 
                              capture_output=True, text=True, check=True)
        print(f"✅ {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"❌ PyTorch verification failed: {e.stderr}")
        raise RuntimeError("PyTorch not found in virtual environment")
    
    # Test other critical packages
    test_packages = ['numpy', 'transformers', 'diffusers', 'gradio']
    for pkg in test_packages:
        try:
            result = subprocess.run([str(venv_python), "-c", f"import {pkg}; print(f'{pkg} OK')"], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ {result.stdout.strip()}")
        except subprocess.CalledProcessError:
            print(f"⚠️  Warning: {pkg} not found in venv")
    
    print("✅ Virtual environment activated successfully")

# --- HELPER FUNCTIONS ---
def get_launch_command():
    """Construct the final launch command using venv python."""
    # Use the venv Python explicitly
    venv_python = VENV / 'bin' / 'python'
    
    # Remove duplicate arguments for a clean command
    base_args = commandline_arguments.split()
    unique_args = []
    for arg in base_args:
        if arg not in unique_args:
            unique_args.append(arg)
    
    final_args = " ".join(unique_args)
    
    common_args = ' --enable-insecure-extension-access --disable-console-progressbars --theme dark'
    if ENV_NAME == 'Kaggle':
        common_args += ' --encrypt-pass=emoy4cnkm6imbysp84zmfiz1opahooblh7j34sgh'
    if theme_accent != 'anxety':
        common_args += f" --anxety {theme_accent}"
    
    # CRITICAL: Use venv python instead of system python
    return f"{venv_python} launch.py {final_args}{common_args}"

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    print("🔧 Preparing environment for launch...")
    
    # Activate virtual environment first
    try:
        activate_venv()
    except Exception as e:
        print(f"❌ Failed to activate virtual environment: {e}")
        print("🔍 Checking venv structure...")
        print(f"VENV path: {VENV}")
        print(f"VENV exists: {VENV.exists()}")
        if VENV.exists():
            print(f"VENV contents: {list(VENV.iterdir())}")
            bin_path = VENV / 'bin'
            if bin_path.exists():
                print(f"bin/ contents: {list(bin_path.iterdir())}")
        sys.exit(1)
    
    LAUNCHER = get_launch_command()
    
    print(f"🔧 WebUI: {COL.B}{UI}{COL.X}")
    print(f"🚀 Launching with command: {LAUNCHER}")

    try:
        CD(WEBUI)
        # Execute using subprocess to maintain venv environment
        process = subprocess.Popen(LAUNCHER, shell=True, env=osENV)
        process.wait()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        if 'process' in locals():
            process.terminate()
    except Exception as e:
        print(f"\nAn error occurred during launch: {e}")
        sys.exit(1)
