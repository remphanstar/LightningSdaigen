""" Enhanced WebUI Utilities Module | by ANXETY """

import json_utils as js

from pathlib import Path
import json
import os


osENV = os.environ


# ======================== CONSTANTS =======================

# Constants (auto-convert env vars to Path)
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}   # k -> key; v -> value

HOME = PATHS['home_path']
VENV = PATHS['venv_path']
SCR_PATH = PATHS['scr_path']
SETTINGS_PATH = PATHS['settings_path']

DEFAULT_UI = 'A1111'

# ENHANCED: Complete WebUI paths configuration
WEBUI_PATHS = {
    # Standard Stable Diffusion WebUIs (existing)
    'A1111': ('Stable-diffusion', 'VAE', 'Lora', 'embeddings', 'extensions', 'ESRGAN', 'outputs'),
    'ComfyUI': ('checkpoints', 'vae', 'loras', 'embeddings', 'custom_nodes', 'upscale_models', 'output'),
    'Classic': ('Stable-diffusion', 'VAE', 'Lora', 'embeddings', 'extensions', 'ESRGAN', 'output'),
    'Lightning.ai': ('Stable-diffusion', 'VAE', 'Lora', 'embeddings', 'extensions', 'ESRGAN', 'outputs'),
    
    # ENHANCED: Forge Variants with models subdirectory structure
    'Forge': ('models/Stable-diffusion', 'models/VAE', 'models/Lora', 'embeddings', 'extensions', 'models/ESRGAN', 'outputs'),
    'ReForge': ('models/Stable-diffusion', 'models/VAE', 'models/Lora', 'embeddings', 'extensions', 'models/ESRGAN', 'outputs'),
    'SD-UX': ('models/Stable-diffusion', 'models/VAE', 'models/Lora', 'embeddings', 'extensions', 'models/ESRGAN', 'outputs'),
    
    # ENHANCED: Face Manipulation WebUIs
    'FaceFusion': ('models/inswapper', 'models/gfpgan', 'models/gpen', 'faces', '', 'models/enhancer', 'output'),
    'RoopUnleashed': ('models', 'frames', 'faces', 'temp', '', 'enhancers', 'output'),
    
    # ENHANCED: Specialized WebUIs  
    'DreamO': ('models/diffusion', 'models/vae', 'models/lora', 'assets', 'custom_nodes', 'models/upscale', 'output')
}

# ENHANCED: WebUI feature support matrix
WEBUI_FEATURES = {
    'A1111': {
        'supports_extensions': True,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': True,
        'supports_vae': True,
        'launch_script': 'launch.py',
        'config_files': ['config.json', 'ui-config.json'],
        'category': 'standard_sd'
    },
    'ComfyUI': {
        'supports_extensions': False,  # Uses custom_nodes instead
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': True,
        'supports_vae': True,
        'launch_script': 'main.py',
        'config_files': ['extra_model_paths.yaml'],
        'category': 'node_based'
    },
    'Classic': {
        'supports_extensions': True,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': True,
        'supports_vae': True,
        'launch_script': 'launch.py',
        'config_files': ['config.json', 'ui-config.json'],
        'category': 'standard_sd'
    },
    'Lightning.ai': {
        'supports_extensions': True,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': True,
        'supports_vae': True,
        'launch_script': 'launch.py',
        'config_files': ['config.json', 'ui-config.json'],
        'category': 'standard_sd'
    },
    # ENHANCED: New WebUI features
    'Forge': {
        'supports_extensions': True,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': True,
        'supports_vae': True,
        'launch_script': 'launch.py',
        'config_files': ['config.json', 'ui-config.json'],
        'category': 'enhanced_sd'
    },
    'ReForge': {
        'supports_extensions': True,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': True,
        'supports_vae': True,
        'launch_script': 'launch.py',
        'config_files': ['config.json', 'ui-config.json'],
        'category': 'enhanced_sd'
    },
    'SD-UX': {
        'supports_extensions': True,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': True,
        'supports_vae': True,
        'launch_script': 'launch.py',
        'config_files': ['config.json', 'ui-config.json'],
        'category': 'enhanced_sd'
    },
    'FaceFusion': {
        'supports_extensions': False,
        'supports_models': False,  # Uses specialized face models
        'supports_lora': False,
        'supports_controlnet': False,
        'supports_vae': False,
        'launch_script': 'run.py',
        'config_files': ['facefusion.ini'],
        'category': 'face_swap'
    },
    'RoopUnleashed': {
        'supports_extensions': False,
        'supports_models': False,  # Uses specialized face models
        'supports_lora': False,
        'supports_controlnet': False,
        'supports_vae': False,
        'launch_script': 'run.py',
        'config_files': ['config.yaml'],
        'category': 'face_swap'
    },
    'DreamO': {
        'supports_extensions': False,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': False,
        'supports_vae': True,
        'launch_script': 'app.py',
        'config_files': ['config.yaml'],
        'category': 'specialized'
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
        if i < len(path_names):
            if folder:  # Only set path if folder is defined
                js.save(SETTINGS_PATH, f'WEBUI.{path_names[i]}', str(webui_base / folder))
            else:
                # Set empty path for unsupported features
                js.save(SETTINGS_PATH, f'WEBUI.{path_names[i]}', '')


# ENHANCED: WebUI feature detection functions
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


def get_webui_category(ui: str) -> str:
    """Get the category of a WebUI."""
    features = get_webui_features(ui)
    return features.get('category', 'standard_sd')


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


# ENHANCED: Utility functions
def get_available_webuis() -> list:
    """Get list of all available WebUIs."""
    return list(WEBUI_PATHS.keys())


def get_face_swap_webuis() -> list:
    """Get list of face-swapping capable WebUIs."""
    return [ui for ui, features in WEBUI_FEATURES.items() 
            if features.get('category') == 'face_swap']


def get_standard_sd_webuis() -> list:
    """Get list of standard Stable Diffusion WebUIs."""
    return [ui for ui, features in WEBUI_FEATURES.items() 
            if features.get('supports_models', False)]


def get_webuis_by_category() -> dict:
    """Get WebUIs organized by category."""
    categories = {}
    for ui, features in WEBUI_FEATURES.items():
        category = features.get('category', 'unknown')
        if category not in categories:
            categories[category] = []
        categories[category].append(ui)
    return categories


def setup_webui_environment(ui: str) -> dict:
    """Setup environment variables for a specific WebUI."""
    env_vars = {}
    
    category = get_webui_category(ui)
    
    if category == 'node_based':  # ComfyUI
        env_vars['COMFYUI_MODEL_PATH'] = str(HOME / ui / 'models')
    elif category == 'face_swap':  # FaceFusion, RoopUnleashed
        env_vars['ROOP_MODEL_PATH'] = str(HOME / ui / 'models')
        env_vars['CUDA_VISIBLE_DEVICES'] = '0'
    elif category == 'enhanced_sd':  # Forge variants
        env_vars['CUDA_LAUNCH_BLOCKING'] = '0'
        env_vars['TORCH_CUDNN_V8_API_ENABLED'] = '1'
    
    return env_vars


# ENHANCED: Backward compatibility function
def handle_setup_timer(path, timer):
    """Handle setup timer for downloads (backward compatibility)."""
    return timer


# ENHANCED: WebUI validation and migration helpers
def migrate_webui_settings(old_ui: str, new_ui: str) -> bool:
    """Migrate settings when switching WebUI types."""
    try:
        # Update current WebUI
        update_current_webui(new_ui)
        
        # Clear incompatible settings for face swap WebUIs
        if get_webui_category(new_ui) == 'face_swap':
            # Clear SD-specific model selections
            js.save(SETTINGS_PATH, 'WIDGETS.model', ['none'])
            js.save(SETTINGS_PATH, 'WIDGETS.vae', 'none')
            js.save(SETTINGS_PATH, 'WIDGETS.lora', ('none',))
            js.save(SETTINGS_PATH, 'WIDGETS.controlnet', ('none',))
            js.save(SETTINGS_PATH, 'WIDGETS.XL_models', False)
            
        return True
    except Exception as e:
        print(f"Migration error: {e}")
        return False


def get_recommended_args(ui: str) -> str:
    """Get recommended command line arguments for a WebUI."""
    recommendations = {
        'A1111': '--xformers --no-half-vae',
        'ComfyUI': '--dont-print-server',
        'Classic': '--persistent-patches --cuda-stream --pin-shared-memory',
        'Lightning.ai': '--xformers --no-half-vae',
        'Forge': '--xformers --cuda-stream --pin-shared-memory',
        'ReForge': '--xformers --cuda-stream --pin-shared-memory',
        'SD-UX': '--xformers --no-half-vae --theme dark',
        'FaceFusion': '--execution-provider cuda --face-analyser buffalo_l',
        'RoopUnleashed': '--execution-provider cuda --frame-processor face_swapper',
        'DreamO': '--device cuda --precision fp16'
    }
    return recommendations.get(ui, '--xformers --no-half-vae')
