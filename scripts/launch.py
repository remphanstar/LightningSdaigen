# ~ launch.py | by ANXETY ~

from TunnelHub import Tunnel    # Tunneling
import json_utils as js         # JSON

# ... (imports remain the same)

# ... (constants and helper functions remain the same)

def get_launch_command():
    """Construct launch command based on configuration"""
    base_args = commandline_arguments
    password = 'emoy4cnkm6imbysp84zmfiz1opahooblh7j34sgh'

    common_args = ' --enable-insecure-extension-access --disable-console-progressbars --theme dark'
    if ENV_NAME == 'Kaggle':
        common_args += f" --encrypt-pass={password}"

    # Accent Color For Anxety-Theme
    if theme_accent != 'anxety':
        common_args += f" --anxety {theme_accent}"

    if UI == 'ComfyUI':
        return f"python3 main.py {base_args}"
    elif UI == 'FaceFusion':
        return "python run.py"
    elif UI == 'DreamO':
        return "python app.py"
    else:
        return f"python3 launch.py {base_args}{common_args}"


# ======================== Tunneling =======================
# ... (TunnelManager class remains the same)

# ========================== Main ==========================

if __name__ == '__main__':
    """Main execution flow"""
    # ... (rest of the script is the same)
