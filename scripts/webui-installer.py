# ~ webui-installer.py | by ANXETY - Enhanced with Multiple WebUI Support ~

from Manager import m_download   # Every Download
import json_utils as js          # JSON

from IPython.display import clear_output
from IPython.utils import capture
from IPython import get_ipython
from pathlib import Path
import subprocess
import asyncio
import aiohttp
import os


osENV = os.environ
CD = os.chdir
ipySys = get_ipython().system
ipyRun = get_ipython().run_line_magic

# Constants (auto-convert env vars to Path)
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}   # k -> key; v -> value

HOME = PATHS['home_path']
VENV = PATHS['venv_path']
SCR_PATH = PATHS['scr_path']
SETTINGS_PATH = PATHS['settings_path']

UI = js.read(SETTINGS_PATH, 'WEBUI.current')
WEBUI = HOME / UI
EXTS = Path(js.read(SETTINGS_PATH, 'WEBUI.extension_dir'))
ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')
FORK_REPO = js.read(SETTINGS_PATH, 'ENVIRONMENT.fork')
BRANCH = js.read(SETTINGS_PATH, 'ENVIRONMENT.branch')

REPO_URL = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI}.zip"
CONFIG_URL = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/__configs__"

CD(HOME)

# ENHANCED: WebUI-specific repository URLs
WEBUI_REPOSITORIES = {
    'Forge': 'https://github.com/lllyasviel/stable-diffusion-webui-forge',
    'ReForge': 'https://github.com/Panchovix/stable-diffusion-webui-reForge', 
    'SD-UX': 'https://github.com/anapnoe/stable-diffusion-webui-ux',
    'FaceFusion': 'https://github.com/X-croot/facefusion-uncensored',
    'RoopUnleashed': 'https://github.com/C0untFloyd/roop-unleashed',
    'DreamO': 'https://github.com/bytedance/DreamO'
}

# ENHANCED: WebUI-specific requirements
WEBUI_REQUIREMENTS = {
    'FaceFusion': ['onnxruntime-gpu', 'insightface>=0.7.3'],
    'RoopUnleashed': ['onnxruntime-gpu', 'opencv-python>=4.7.0', 'ffmpeg-python'],
    'DreamO': ['diffusers>=0.21.0', 'transformers>=4.25.0', 'accelerate>=0.20.0'],
    'Forge': ['torch>=2.0.0', 'torchvision>=0.15.0'],
    'ReForge': ['torch>=2.0.0', 'torchvision>=0.15.0'],
    'SD-UX': ['gradio>=3.50.0']
}


# ==================== WEBUI OPERATIONS ====================

async def _download_file(url, directory=WEBUI, filename=None):
    """Download single file."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    file_path = directory / (filename or Path(url).name)

    if file_path.exists():
        file_path.unlink()

    process = await asyncio.create_subprocess_shell(
        f"curl -sLo {file_path} {url}",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    await process.communicate()

async def get_extensions_list():
    """Fetch list of extensions from config file."""
    config_file = CONFIG_URL + f"/{UI}/_extensions.txt"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(config_file) as response:
                if response.status == 200:
                    text = await response.text()
                    urls = [line.strip() for line in text.splitlines() 
                           if line.strip() and not line.strip().startswith('#')]
                    return urls
        except Exception:
            pass
    return []

async def download_configuration():
    """Download WebUI configuration files."""
    try:
        config_files = [
            f"config.json",
            f"ui-config.json"
        ]
        
        for config_file in config_files:
            config_url = f"{CONFIG_URL}/{UI}/{config_file}"
            await _download_file(config_url, WEBUI, config_file)
            
    except Exception as e:
        print(f"Note: Could not download configuration: {e}")

async def install_extensions():
    """Install WebUI extensions."""
    extensions = await get_extensions_list()
    EXTS.mkdir(parents=True, exist_ok=True)
    CD(EXTS)

    tasks = [
        asyncio.create_subprocess_shell(
            f"git clone --depth 1 {ext}",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        ) for ext in extensions
    ]
    await asyncio.gather(*tasks)


# ENHANCED: Git-based WebUI installation
def install_git_webui(ui_name, repo_url):
    """Install WebUI from git repository."""
    print(f"🔧 Installing {ui_name} from git repository...")
    
    # Clone the repository
    ipySys(f"git clone --depth 1 {repo_url} {WEBUI}")
    CD(WEBUI)
    
    # Install WebUI-specific requirements
    if ui_name in WEBUI_REQUIREMENTS:
        requirements = WEBUI_REQUIREMENTS[ui_name]
        for req in requirements:
            print(f"📦 Installing {req}...")
            ipySys(f"pip install {req}")
    
    # Install from requirements.txt if available
    if Path(WEBUI / 'requirements.txt').exists():
        print(f"📦 Installing requirements from requirements.txt...")
        ipySys("pip install -r requirements.txt")

def setup_webui_environment(ui_name):
    """Setup WebUI-specific environment and directories."""
    webui_path = Path(WEBUI)
    
    # Create WebUI-specific directories
    if ui_name in ['FaceFusion', 'RoopUnleashed']:
        # Face swap WebUIs
        for folder in ['models', 'faces', 'output']:
            (webui_path / folder).mkdir(exist_ok=True)
            
        if ui_name == 'FaceFusion':
            # Create FaceFusion-specific directories
            for folder in ['models/inswapper', 'models/gfpgan', 'models/gpen']:
                (webui_path / folder).mkdir(parents=True, exist_ok=True)
                
    elif ui_name == 'DreamO':
        # DreamO-specific directories
        for folder in ['models/diffusion', 'models/vae', 'assets']:
            (webui_path / folder).mkdir(parents=True, exist_ok=True)
            
    elif ui_name in ['Forge', 'ReForge', 'SD-UX']:
        # Forge variants - use models subdirectory structure
        for folder in ['models/Stable-diffusion', 'models/VAE', 'models/Lora', 'embeddings', 'extensions']:
            (webui_path / folder).mkdir(parents=True, exist_ok=True)

# =================== WEBUI SETUP & FIXES ==================

def unpack_webui():
    """Download and extract WebUI archive."""
    zip_path = HOME / f"{UI}.zip"
    m_download(f"{REPO_URL} {HOME} {UI}.zip")
    ipySys(f"unzip -q -o {zip_path} -d {WEBUI} && rm -rf {zip_path}")

def apply_classic_fixes():
    """Apply specific fixes for Classic UI."""
    if UI != 'Classic':
        return

    cmd_args_path = WEBUI / 'modules/cmd_args.py'
    if not cmd_args_path.exists():
        return

    marker = '# Arguments added by ANXETY'
    with cmd_args_path.open('r+', encoding='utf-8') as f:
        if marker in f.read():
            return
        f.write(f"\n\n{marker}\n")
        f.write('parser.add_argument("--hypernetwork-dir", type=normalized_filepath, '
               'default=os.path.join(models_path, \'hypernetworks\'), help="hypernetwork directory")')

def run_tagcomplete_tag_parser():
    """Run tagcomplete tag parser for supported WebUIs."""
    parser_script = WEBUI / 'tagcomplete-tags-parser.py'
    if parser_script.exists():
        ipyRun('run', str(parser_script))

# ENHANCED: WebUI detection and installation logic
def is_git_based_webui(ui_name):
    """Check if WebUI should be installed from git."""
    return ui_name in WEBUI_REPOSITORIES

def should_use_archive(ui_name):
    """Check if WebUI should use archive-based installation."""
    archive_webuis = ['A1111', 'ComfyUI', 'Classic', 'Lightning.ai']
    return ui_name in archive_webuis

# ======================== MAIN CODE =======================

async def main():
    """Enhanced main installation logic with WebUI detection."""
    
    print(f"🚀 Installing WebUI: {UI}")
    
    # ENHANCED: Git-based installation for new WebUIs
    if is_git_based_webui(UI):
        repo_url = WEBUI_REPOSITORIES[UI]
        install_git_webui(UI, repo_url)
        setup_webui_environment(UI)
        
        # Install extensions if configuration exists
        extensions = await get_extensions_list()
        if extensions:
            print(f"🔌 Installing {len(extensions)} extensions...")
            await install_extensions()
            
    # Original archive-based installation for traditional WebUIs
    elif should_use_archive(UI):
        unpack_webui()
        await download_configuration()
        await install_extensions()
        apply_classic_fixes()

        if UI != 'ComfyUI':
            run_tagcomplete_tag_parser()
            
    # Legacy support for partially implemented WebUIs
    elif UI == 'FaceFusion':
        install_git_webui('FaceFusion', 'https://github.com/X-croot/facefusion-uncensored')
        setup_webui_environment('FaceFusion')
        
    elif UI == 'DreamO':
        install_git_webui('DreamO', 'https://github.com/bytedance/DreamO')
        setup_webui_environment('DreamO')
        
    else:
        print(f"⚠️ Unknown WebUI: {UI}, attempting archive installation...")
        unpack_webui()
        await download_configuration()
        await install_extensions()

    print(f"✅ {UI} installation complete!")

if __name__ == '__main__':
    with capture.capture_output():
        asyncio.run(main())
