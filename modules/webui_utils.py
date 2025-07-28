# ~ webui_utils.py | by ANXETY - Enhanced with Complete 10WebUI Support ~

import json_utils as js
from pathlib import Path
import os

# Environment paths
osENV = os.environ
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME = PATHS['home_path']
SETTINGS_PATH = PATHS['settings_path']

# Default UI configuration
DEFAULT_UI = 'A1111'

# ENHANCED: Complete WebUI Path Configurations for 10 WebUIs
WEBUI_PATHS = {
    'A1111': ('models/Stable-diffusion', 'models/VAE', 'models/Lora', 'embeddings', 'extensions', 'models/ESRGAN', 'outputs'),
    'ComfyUI': ('models/checkpoints', 'models/vae', 'models/loras', 'models/embeddings', 'custom_nodes', 'models/upscale_models', 'output'),
    'Classic': ('models/Stable-diffusion', 'models/VAE', 'models/Lora', 'embeddings', 'extensions', 'models/ESRGAN', 'outputs'),
    'Lightning.ai': ('models/Stable-diffusion', 'models/VAE', 'models/Lora', 'embeddings', 'extensions', 'models/ESRGAN', 'outputs'),
    'Forge': ('models/Stable-diffusion', 'models/VAE', 'models/Lora', 'embeddings', 'extensions', 'models/ESRGAN', 'outputs'),
    'ReForge': ('models/Stable-diffusion', 'models/VAE', 'models/Lora', 'embeddings', 'extensions', 'models/ESRGAN', 'outputs'),
    'SD-UX': ('models/Stable-diffusion', 'models/VAE', 'models/Lora', 'embeddings', 'extensions', 'models/ESRGAN', 'outputs'),
    'FaceFusion': ('models/face_analyser', 'models/face_swapper', '', '', '', '', 'output'),
    'RoopUnleashed': ('models', 'models/gfpgan', '', '', '', '', 'output'),
    'DreamO': ('models/diffusion', 'models/vae', 'models/lora', 'assets', '', 'models/upscale', 'output')
}

# ENHANCED: WebUI Feature Detection Matrix
WEBUI_FEATURES = {
    'A1111': {
        'supports_extensions': True,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': True,
        'supports_vae': True,
        'supports_themes': True,
        'launch_script': 'launch.py',
        'config_files': ['config.json', 'ui-config.json'],
        'category': 'standard_sd',
        'installation_type': 'archive'
    },
    'ComfyUI': {
        'supports_extensions': True,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': True,
        'supports_vae': True,
        'supports_themes': False,
        'launch_script': 'main.py',
        'config_files': ['extra_model_paths.yaml'],
        'category': 'node_based',
        'installation_type': 'archive'
    },
    'Classic': {
        'supports_extensions': True,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': True,
        'supports_vae': True,
        'supports_themes': True,
        'launch_script': 'launch.py',
        'config_files': ['config.json', 'ui-config.json'],
        'category': 'standard_sd',
        'installation_type': 'archive'
    },
    'Lightning.ai': {
        'supports_extensions': True,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': True,
        'supports_vae': True,
        'supports_themes': True,
        'launch_script': 'launch.py',
        'config_files': ['config.json', 'ui-config.json'],
        'category': 'standard_sd',
        'installation_type': 'archive'
    },
    'Forge': {
        'supports_extensions': True,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': True,
        'supports_vae': True,
        'supports_themes': True,
        'launch_script': 'launch.py',
        'config_files': ['config.json', 'ui-config.json'],
        'category': 'enhanced_sd',
        'installation_type': 'git'
    },
    'ReForge': {
        'supports_extensions': True,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': True,
        'supports_vae': True,
        'supports_themes': True,
        'launch_script': 'launch.py',
        'config_files': ['config.json', 'ui-config.json'],
        'category': 'enhanced_sd',
        'installation_type': 'git'
    },
    'SD-UX': {
        'supports_extensions': True,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': True,
        'supports_vae': True,
        'supports_themes': True,
        'launch_script': 'launch.py',
        'config_files': ['config.json', 'ui-config.json'],
        'category': 'enhanced_sd',
        'installation_type': 'git'
    },
    'FaceFusion': {
        'supports_extensions': False,
        'supports_models': False,
        'supports_lora': False,
        'supports_controlnet': False,
        'supports_vae': False,
        'supports_themes': False,
        'launch_script': 'run.py',
        'config_files': ['facefusion.ini'],
        'category': 'face_swap',
        'installation_type': 'git'
    },
    'RoopUnleashed': {
        'supports_extensions': False,
        'supports_models': False,
        'supports_lora': False,
        'supports_controlnet': False,
        'supports_vae': False,
        'supports_themes': False,
        'launch_script': 'run.py',
        'config_files': ['config.yaml'],
        'category': 'face_swap',
        'installation_type': 'git'
    },
    'DreamO': {
        'supports_extensions': False,
        'supports_models': True,
        'supports_lora': True,
        'supports_controlnet': False,
        'supports_vae': True,
        'supports_themes': False,
        'launch_script': 'app.py',
        'config_files': ['config.yaml'],
        'category': 'specialized',
        'installation_type': 'git'
    }
}

# ENHANCED: WebUI Handlers
def update_current_webui(current_value: str) -> None:
    """Update the current WebUI value and save settings with validation."""
    # Validate WebUI selection
    if not validate_webui_selection(current_value):
        print(f"⚠️ Unknown WebUI: {current_value}, using {DEFAULT_UI}")
        current_value = DEFAULT_UI
    
    current_stored = js.read(SETTINGS_PATH, 'WEBUI.current')
    latest_value = js.read(SETTINGS_PATH, 'WEBUI.latest', None)

    if latest_value is None or current_stored != current_value:
        js.save(SETTINGS_PATH, 'WEBUI.latest', current_stored)
        js.save(SETTINGS_PATH, 'WEBUI.current', current_value)

    js.save(SETTINGS_PATH, 'WEBUI.webui_path', str(HOME / current_value))
    _set_webui_paths(current_value)

def _set_webui_paths(ui: str) -> None:
    """Configure paths for specified UI with comprehensive validation."""
    paths = WEBUI_PATHS.get(ui, WEBUI_PATHS[DEFAULT_UI])
    path_names = ['model_dir', 'vae_dir', 'lora_dir', 'embed_dir', 'extension_dir', 'upscale_dir', 'output_dir']
    
    webui_base = HOME / ui
    
    for i, folder in enumerate(paths):
        if i < len(path_names):
            if folder:  # Only set path if folder is defined and supported
                full_path = str(webui_base / folder)
                js.save(SETTINGS_PATH, f'WEBUI.{path_names[i]}', full_path)
            else:
                # Set empty path for unsupported features (e.g., VAE for face swap WebUIs)
                js.save(SETTINGS_PATH, f'WEBUI.{path_names[i]}', '')

# ENHANCED: WebUI Feature Detection Functions
def get_webui_features(ui: str) -> dict:
    """Get comprehensive feature support information for a WebUI."""
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

def get_installation_type(ui: str) -> str:
    """Get the installation type (archive/git) for a WebUI."""
    features = get_webui_features(ui)
    return features.get('installation_type', 'archive')

def validate_webui_selection(ui: str) -> bool:
    """Validate if the WebUI selection is supported."""
    return ui in WEBUI_PATHS

def get_webui_specific_paths(ui: str) -> dict:
    """Get WebUI-specific path mappings with validation."""
    if ui not in WEBUI_PATHS:
        print(f"⚠️ Unknown WebUI: {ui}, using {DEFAULT_UI} paths")
        ui = DEFAULT_UI
    
    paths = WEBUI_PATHS[ui]
    path_names = ['model_dir', 'vae_dir', 'lora_dir', 'embed_dir', 'extension_dir', 'upscale_dir', 'output_dir']
    
    webui_base = HOME / ui
    return {
        name: str(webui_base / folder) if folder else ''
        for name, folder in zip(path_names, paths)
    }

# ENHANCED: Utility Functions
def get_available_webuis() -> list:
    """Get list of all available WebUIs."""
    return list(WEBUI_PATHS.keys())

def get_webuis_by_category() -> dict:
    """Get WebUIs organized by category."""
    categories = {}
    for ui, features in WEBUI_FEATURES.items():
        category = features.get('category', 'standard_sd')
        if category not in categories:
            categories[category] = []
        categories[category].append(ui)
    return categories

def get_face_swap_webuis() -> list:
    """Get list of face-swapping capable WebUIs."""
    return [ui for ui, features in WEBUI_FEATURES.items() 
            if features.get('category') == 'face_swap']

def get_standard_sd_webuis() -> list:
    """Get list of standard Stable Diffusion WebUIs."""
    return [ui for ui, features in WEBUI_FEATURES.items() 
            if features.get('supports_models', False)]

def get_git_based_webuis() -> list:
    """Get list of git-based WebUIs."""
    return [ui for ui, features in WEBUI_FEATURES.items() 
            if features.get('installation_type') == 'git']

def get_archive_based_webuis() -> list:
    """Get list of archive-based WebUIs."""
    return [ui for ui, features in WEBUI_FEATURES.items() 
            if features.get('installation_type') == 'archive']

def should_skip_models(ui: str) -> bool:
    """Check if WebUI should skip standard SD model downloads."""
    return get_webui_category(ui) in ['face_swap']

def should_skip_extensions(ui: str) -> bool:
    """Check if WebUI should skip extension installation."""
    return not is_webui_supported(ui, 'extensions')

# ENHANCED: Timer and Setup Functions
def handle_setup_timer(settings_path: Path, timer_value: float) -> float:
    """Handle setup timer with WebUI-aware processing."""
    try:
        # Load current WebUI
        current_ui = js.read(settings_path, 'WEBUI.current', DEFAULT_UI)
        
        # Get WebUI-specific features
        features = get_webui_features(current_ui)
        
        # Adjust timer based on installation type
        if features.get('installation_type') == 'git':
            # Git-based WebUIs take longer to install
            adjusted_timer = timer_value * 1.5
        else:
            adjusted_timer = timer_value
        
        print(f"🎛️ Selected WebUI: {current_ui} ({features.get('category', 'unknown')})")
        
        if features.get('category') == 'face_swap':
            print("🎭 Face swap WebUI detected - SD models will be skipped")
        elif features.get('category') == 'node_based':
            print("🔗 Node-based WebUI detected - custom nodes will be installed")
        
        return adjusted_timer
    except Exception as e:
        print(f"⚠️ Timer handling error: {e}")
        return timer_value

# Enhanced error handling and logging
def log_webui_info(ui: str) -> None:
    """Log comprehensive WebUI information for debugging."""
    try:
        features = get_webui_features(ui)
        paths = get_webui_specific_paths(ui)
        
        print(f"\n🔍 WebUI Information: {ui}")
        print(f"  📂 Category: {features.get('category', 'unknown')}")
        print(f"  🚀 Launch Script: {features.get('launch_script', 'unknown')}")
        print(f"  💾 Installation: {features.get('installation_type', 'unknown')}")
        print(f"  🎯 Features: {', '.join([k.replace('supports_', '') for k, v in features.items() if k.startswith('supports_') and v])}")
        
        if any(paths.values()):
            print(f"  📁 Active Paths:")
            for name, path in paths.items():
                if path:
                    print(f"    {name}: {path}")
    except Exception as e:
        print(f"⚠️ Could not log WebUI info: {e}")
