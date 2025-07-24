""" WebUI Utilities Module | by ANXETY """

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

WEBUI_PATHS = {
    'A1111': ('Stable-diffusion', 'VAE', 'Lora', 'embeddings', 'extensions', 'ESRGAN', 'outputs'),
    'ComfyUI': ('checkpoints', 'vae', 'loras', 'embeddings', 'custom_nodes', 'upscale_models', 'output'),
    'Classic': ('Stable-diffusion', 'VAE', 'Lora', 'embeddings', 'extensions', 'ESRGAN', 'output'),
    'FaceFusion': ('', '', '', '', '', '', 'output'), # Paths can be adjusted as needed
    'DreamO': ('', '', '', '', '', '', 'output') # Paths can be adjusted as needed
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
    selected_ui = ui if ui in WEBUI_PATHS else DEFAULT_UI
    webui_root = HOME / ui
    models_root = webui_root / 'models'

    # Get path components for selected UI
    paths = WEBUI_PATHS[selected_ui]
    checkpoint, vae, lora, embed, extension, upscale, output = paths

    # Configure special paths
    is_comfy = selected_ui == 'ComfyUI'
    is_classic = selected_ui == 'Classic'
    control_dir = 'controlnet' if is_comfy else 'ControlNet'
    embed_root = models_root if (is_comfy or is_classic) else webui_root
    config_root = webui_root / 'user/default' if is_comfy else webui_root

    path_config = {
        'model_dir': str(models_root / checkpoint) if checkpoint else str(webui_root),
        'vae_dir': str(models_root / vae) if vae else str(webui_root),
        'lora_dir': str(models_root / lora) if lora else str(webui_root),
        'embed_dir': str(embed_root / embed) if embed else str(webui_root),
        'extension_dir': str(webui_root / extension) if extension else str(webui_root),
        'control_dir': str(models_root / control_dir),
        'upscale_dir': str(models_root / upscale) if upscale else str(webui_root),
        'output_dir': str(webui_root / output) if output else str(webui_root),
        'config_dir': str(config_root),
        # Additional directories
        'adetailer_dir': str(models_root / ('ultralytics' if is_comfy else 'adetailer')),
        'clip_dir': str(models_root / ('clip' if is_comfy else 'text_encoder')),
        'unet_dir': str(models_root / ('unet' if is_comfy else 'text_encoder')),
        'vision_dir': str(models_root / 'clip_vision'),
        'encoder_dir': str(models_root / ('text_encoders' if is_comfy else 'text_encoder')),
        'diffusion_dir': str(models_root / 'diffusion_models')
    }

    js.update(SETTINGS_PATH, 'WEBUI', path_config)


def handle_setup_timer(webui_path: str, timer_webui: float) -> float:
    """Manage timer persistence for WebUI instances."""
    timer_file = Path(webui_path) / 'static' / 'timer.txt'
    timer_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with timer_file.open('r') as f:
            timer_webui = float(f.read())
    except FileNotFoundError:
        pass

    with timer_file.open('w') as f:
        f.write(str(timer_webui))

    return timer_webui
