# ~ launch.py | by ANXETY - FINAL CORRECTED VERSION ~

import os
import sys
from pathlib import Path
import shlex
from IPython import get_ipython

# --- MATPLOTLIB FIXES ---
os.environ['MPLBACKEND'] = 'Agg'
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'
os.environ['PYTHONWARNINGS'] = 'ignore::UserWarning:matplotlib'

# --- SETUP PATHS AND MODULES ---
sys.path.insert(0, str(Path(os.environ.get('scr_path', '')) / 'modules'))
try:
    import json_utils as js
except ImportError:
    print("FATAL: Could not import json_utils. Please ensure the setup script ran correctly.")
    sys.exit(1)

# --- ENVIRONMENT & SETTINGS ---
osENV = os.environ
CD = os.chdir
ipySys = get_ipython().system

PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME, VENV, SETTINGS_PATH = PATHS['home_path'], PATHS['venv_path'], PATHS['settings_path']

settings = js.read(SETTINGS_PATH)
UI = settings.get('WEBUI', {}).get('current', 'A1111')
WEBUI = settings.get('WEBUI', {}).get('webui_path', str(HOME / UI))
commandline_arguments = settings.get('WIDGETS', {}).get('commandline_arguments', '')
theme_accent = settings.get('WIDGETS', {}).get('theme_accent', 'anxety')
ENV_NAME = settings.get('ENVIRONMENT', {}).get('env_name')

class COLORS:
    B, X = "\033[34m", "\033[0m"
COL = COLORS

def get_launch_command_str():
    """Construct the final launch command as a shell-executable string."""
    python_exe = str(VENV / 'bin' / 'python')
    launch_script = 'launch.py'
    
    args_dict = {}

    # 1. Set default/essential arguments
    args_dict['--enable-insecure-extension-access'] = None
    args_dict['--disable-console-progressbars'] = None
    args_dict['--theme'] = 'dark'
    
    # 2. Parse user-provided arguments, allowing overrides
    user_args = shlex.split(commandline_arguments)
    i = 0
    while i < len(user_args):
        arg = user_args[i]
        if arg.startswith('--'):
            if i + 1 < len(user_args) and not user_args[i+1].startswith('--'):
                args_dict[arg] = user_args[i+1]
                i += 2
            else:
                args_dict[arg] = None
                i += 1
        else:
            i += 1
            
    # 3. Add environment-specific arguments
    if ENV_NAME == 'Kaggle':
        args_dict['--encrypt-pass'] = 'emoy4cnkm6imbysp84zmfiz1opahooblh7j34sgh'
        
    if theme_accent != 'anxety':
        args_dict['--anxety'] = theme_accent
        
    # 4. Construct the final command string
    command_parts = [python_exe, launch_script]
    for arg, value in args_dict.items():
        command_parts.append(arg)
        if value is not None:
            command_parts.append(shlex.quote(value)) # Use shlex.quote for safety
            
    return ' '.join(command_parts)

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    print("✅ Environment is ready. Preparing to launch...")
    
    webui_path = Path(WEBUI)
    if not webui_path.exists() or not (webui_path / 'launch.py').exists():
        print(f"❌ WebUI launch script not found at {webui_path / 'launch.py'}")
        sys.exit(1)
        
    LAUNCHER_COMMAND = get_launch_command_str()
    
    print(f"🔧 WebUI: {COL.B}{UI}{COL.X}")
    print(f"🚀 Launching with command: {LAUNCHER_COMMAND}")

    try:
        # Change to the WebUI directory
        CD(WEBUI)
        
        # Use the IPython system call, which is equivalent to '!' and provides direct output
        ipySys(LAUNCHER_COMMAND)
            
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except Exception as e:
        print(f"\nAn error occurred during launch: {e}")
