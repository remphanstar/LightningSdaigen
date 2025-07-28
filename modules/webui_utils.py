# Enhanced webui_utils.py with complete implementations

""" Enhanced WebUI Utilities Module | by ANXETY """

import json_utils as js
from pathlib import Path
import json
import os

osENV = os.environ

# ======================== CONSTANTS =======================

# Constants (auto-convert env vars to Path)
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}

HOME = PATHS['home_path']
VENV = PATHS['venv_path']
SCR_PATH = PATHS['scr_path']
SETTINGS_PATH = PATHS['settings_path']

DEFAULT_UI = 'A1111'

# Enhanced WEBUI_PATHS with complete configurations
WEBUI_PATHS = {
    # Standard Stable Diffusion WebUIs
    'A1111': ('Stable-diffusion', 'VAE', 'Lora', 'embeddings', 'extensions', 'ESRGAN', 'outputs'),
    'ComfyUI': ('checkpoints', 'vae', 'loras', 'embeddings', 'custom_nodes', 'upscale_models', 'output'),
    'Classic': ('Stable-diffusion', 'VAE', 'Lora', 'embeddings', 'extensions', 'ESRGAN', 'output'),
    'Lightning.ai': ('Stable-diffusion', 'VAE', 'Lora', 'embeddings', 'extensions', 'ESRGAN', 'outputs'),
    
    # Enhanced Forge Variants
    'Forge': ('models/Stable-diffusion', 'models/VAE', 'models/Lora', 'embeddings', 'extensions', 'models/ESRGAN', 'outputs'),
    'ReForge': ('models/Stable-diffusion', 'models/VAE', 'models/Lora', 'embeddings', 'extensions', 'models/ESRGAN', 'outputs'),
    'SD-UX': ('models/Stable-diffusion', 'models/VAE', 'models/Lora', 'embeddings', 'extensions', 'models/ESRGAN', 'outputs'),
    
    # Face Manipulation WebUIs
    'FaceFusion': ('models/inswapper', 'models/gfpgan', 'models/gpen', 'faces', '', 'models/enhancer', 'output'),
    'RoopUnleashed': ('models', 'frames', 'faces', 'temp', '', 'enhancers', 'output'),
    
    # Specialized WebUIs
    'DreamO': ('models/diffusion', 'models/vae', 'models/lora', 'assets', 'custom_nodes', 'models/upscale', 'output')
}

# Enhanced WebUI-specific settings
WEBUI_FEATURES = {
    'A1111': {
        'supports_extensions': True,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': True,
        'supports_vae': True,
        'launch_script': 'launch.py',
        'config_files': ['config.json', 'ui-config.json']
    },
    'ComfyUI': {
        'supports_extensions': False,  # Uses custom_nodes instead
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': True,
        'supports_vae': True,
        'launch_script': 'main.py',
        'config_files': ['extra_model_paths.yaml']
    },
    'Forge': {
        'supports_extensions': True,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': True,
        'supports_vae': True,
        'launch_script': 'launch.py',
        'config_files': ['config.json', 'ui-config.json']
    },
    'ReForge': {
        'supports_extensions': True,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': True,
        'supports_vae': True,
        'launch_script': 'launch.py',
        'config_files': ['config.json', 'ui-config.json']
    },
    'SD-UX': {
        'supports_extensions': True,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': True,
        'supports_vae': True,
        'launch_script': 'launch.py',
        'config_files': ['config.json', 'ui-config.json']
    },
    'FaceFusion': {
        'supports_extensions': False,
        'supports_models': False,  # Uses specialized face models
        'supports_lora': False,
        'supports_controlnet': False,
        'supports_vae': False,
        'launch_script': 'run.py',
        'config_files': ['facefusion.ini']
    },
    'RoopUnleashed': {
        'supports_extensions': False,
        'supports_models': False,  # Uses specialized face models
        'supports_lora': False,
        'supports_controlnet': False,
        'supports_vae': False,
        'launch_script': 'run.py',
        'config_files': ['config.yaml']
    },
    'DreamO': {
        'supports_extensions': False,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': False,
        'supports_vae': True,
        'launch_script': 'app.py',
        'config_files': ['config.yaml']
    },
    'Classic': {
        'supports_extensions': True,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': True,
        'supports_vae': True,
        'launch_script': 'launch.py',
        'config_files': ['config.json', 'ui-config.json']
    }
}


# ===================== WEBUI HANDLERS =====================

def update_current_webui(current_value: str) -> None:
    """Update the current WebUI value and save settings."""
    current_stored = js.read(SETTINGS_PATH, 'WEBUI.current')
    latest_value = js.read(SETTINGS_PATH, 'WEBUI.latest', None)

    if latest_value is None or current_stored != current_value:
        js.save(SETTINGS_PATH, 'WEBUI.latest', current_stored)
        js.save(SETTINGS_PATH, 'WEBUI.current', current_value)

    js.save(SETTINGS_PATH, 'WEBUI.webui_path', str(HOME / current_value))
    _set_webui_paths(current_value)


def _set_webui_paths(ui: str) -> None:
    """Configure paths for specified UI, fallback to A1111 for unknown UIs."""
    paths = WEBUI_PATHS.get(ui, WEBUI_PATHS[DEFAULT_UI])
    path_names = ['model_dir', 'vae_dir', 'lora_dir', 'embed_dir', 'extension_dir', 'upscale_dir', 'output_dir']
    
    webui_base = HOME / ui
    for i, folder in enumerate(paths):
        if i < len(path_names) and folder:
            js.save(SETTINGS_PATH, f'WEBUI.{path_names[i]}', str(webui_base / folder))
        elif i < len(path_names):
            # Set empty path for unsupported features
            js.save(SETTINGS_PATH, f'WEBUI.{path_names[i]}', '')


def get_webui_features(ui: str) -> dict:
    """Get feature support information for a WebUI."""
    return WEBUI_FEATURES.get(ui, WEBUI_FEATURES[DEFAULT_UI])


def is_webui_supported(ui: str, feature: str) -> bool:
    """Check if a WebUI supports a specific feature."""
    features = get_webui_features(ui)
    return features.get(f'supports_{feature}', False)


def get_launch_script(ui: str) -> str:
    """Get the correct launch script for a WebUI."""
    features = get_webui_features(ui)
    return features.get('launch_script', 'launch.py')


def get_config_files(ui: str) -> list:
    """Get list of configuration files for a WebUI."""
    features = get_webui_features(ui)
    return features.get('config_files', [])


def validate_webui_selection(ui: str) -> bool:
    """Validate if the WebUI selection is supported."""
    return ui in WEBUI_PATHS


def get_webui_specific_paths(ui: str) -> dict:
    """Get WebUI-specific path mappings."""
    if ui not in WEBUI_PATHS:
        ui = DEFAULT_UI
    
    paths = WEBUI_PATHS[ui]
    path_names = ['model_dir', 'vae_dir', 'lora_dir', 'embed_dir', 'extension_dir', 'upscale_dir', 'output_dir']
    
    webui_base = HOME / ui
    return {
        name: str(webui_base / folder) if folder else ''
        for name, folder in zip(path_names, paths)
    }


# ===================== UTILITY FUNCTIONS =====================

def get_available_webuis() -> list:
    """Get list of all available WebUIs."""
    return list(WEBUI_PATHS.keys())


def get_face_swap_webuis() -> list:
    """Get list of face-swapping capable WebUIs."""
    return ['FaceFusion', 'RoopUnleashed']


def get_standard_sd_webuis() -> list:
    """Get list of standard Stable Diffusion WebUIs."""
    return [ui for ui in WEBUI_PATHS.keys() if is_webui_supported(ui, 'models')]


def get_webui_category(ui: str) -> str:
    """Get the category of a WebUI."""
    if ui in get_face_swap_webuis():
        return 'face_swap'
    elif ui in ['ComfyUI']:
        return 'node_based'
    elif ui in ['Forge', 'ReForge', 'SD-UX']:
        return 'enhanced_sd'
    elif ui in ['DreamO']:
        return 'specialized'
    else:
        return 'standard_sd'


def setup_webui_environment(ui: str) -> dict:
    """Setup environment variables for a specific WebUI."""
    env_vars = {}
    
    if ui == 'ComfyUI':
        env_vars['COMFYUI_MODEL_PATH'] = str(HOME / ui / 'models')
    elif ui in get_face_swap_webuis():
        env_vars['ROOP_MODEL_PATH'] = str(HOME / ui / 'models')
    
    return env_vars
