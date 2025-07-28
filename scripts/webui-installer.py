# ~ webui-installer.py | by ANXETY - Enhanced with Complete 10WebUI Support ~

from IPython.display import clear_output
from IPython.utils import capture
from IPython import get_ipython
from pathlib import Path
import subprocess
import asyncio
import aiohttp
import os

# Safe import with fallbacks
try:
    from Manager import m_download
    import json_utils as js
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import custom modules: {e}")
    MODULES_AVAILABLE = False
    # Create fallback functions
    def m_download(url_cmd): 
        parts = url_cmd.split()
        if len(parts) >= 2:
            subprocess.run(['wget', '-O', parts[-1], parts[0]], check=False)
    class js:
        @staticmethod
        def read(path, key, default=None): 
            return default

osENV = os.environ
CD = os.chdir
ipySys = get_ipython().system
ipyRun = get_ipython().run_line_magic

# Constants with proper Path handling
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME = PATHS['home_path']
VENV = PATHS['venv_path']
SCR_PATH = PATHS['scr_path']
SETTINGS_PATH = PATHS['settings_path']

# Get current WebUI selection
try:
    UI = js.read(SETTINGS_PATH, 'WEBUI.current') or 'A1111'
    WEBUI = HOME / UI
    EXTS = Path(js.read(SETTINGS_PATH, 'WEBUI.extension_dir')) if js.read(SETTINGS_PATH, 'WEBUI.extension_dir') else WEBUI / 'extensions'
    ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name') or 'Unknown'
    FORK_REPO = js.read(SETTINGS_PATH, 'ENVIRONMENT.fork') or 'remphanstar/LightningSdaigen'
    BRANCH = js.read(SETTINGS_PATH, 'ENVIRONMENT.branch') or 'main'
except Exception as e:
    print(f"⚠️ Settings loading warning: {e}")
    UI = 'A1111'
    WEBUI = HOME / UI
    EXTS = WEBUI / 'extensions'
    ENV_NAME = 'Unknown'
    FORK_REPO = 'remphanstar/LightningSdaigen'
    BRANCH = 'main'

REPO_URL = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI}.zip"
CONFIG_URL = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/__configs__"

CD(HOME)

# ENHANCED: Git-based WebUI Repository URLs
WEBUI_REPOSITORIES = {
    'Forge': 'https://github.com/lllyasviel/stable-diffusion-webui-forge',
    'ReForge': 'https://github.com/Panchovix/stable-diffusion-webui-reForge', 
    'SD-UX': 'https://github.com/anapnoe/stable-diffusion-webui-ux',
    'FaceFusion': 'https://github.com/facefusion/facefusion',
    'RoopUnleashed': 'https://github.com/C0untFloyd/roop-unleashed',
    'DreamO': 'https://github.com/huggingface/diffusers'  # Custom DreamO implementation
}

# ENHANCED: WebUI-specific requirements
WEBUI_REQUIREMENTS = {
    'Forge': ['torch>=2.0.0', 'torchvision>=0.15.0', 'xformers'],
    'ReForge': ['torch>=2.0.0', 'torchvision>=0.15.0', 'xformers'],
    'SD-UX': ['gradio>=3.50.0', 'torch>=2.0.0'],
    'FaceFusion': ['onnxruntime-gpu', 'insightface>=0.7.3', 'opencv-python>=4.7.0'],
    'RoopUnleashed': ['onnxruntime-gpu', 'opencv-python>=4.7.0', 'ffmpeg-python', 'gfpgan'],
    'DreamO': ['diffusers>=0.21.0', 'transformers>=4.25.0', 'accelerate>=0.20.0']
}

# ==================== ENHANCED OPERATIONS ====================

async def _download_file(url, directory=WEBUI, filename=None):
    """Download single file with improved error handling."""
    try:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / (filename or Path(url).name)

        if file_path.exists():
            file_path.unlink()

        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    with open(file_path, 'wb') as f:
                        f.write(content)
                    print(f"✅ Downloaded: {file_path.name}")
                else:
                    print(f"⚠️ Failed to download {url}: HTTP {response.status}")
    except Exception as e:
        print(f"⚠️ Download error for {url}: {e}")

async def get_extensions_list():
    """Fetch list of extensions from config file with enhanced error handling."""
    config_file = CONFIG_URL + f"/{UI}/_extensions.txt"

    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(config_file) as response:
                if response.status == 200:
                    text = await response.text()
                    urls = []
                    for line in text.splitlines():
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Handle lines with custom names or additional info
                            if ' ' in line:
                                url = line.split()[0]
                            else:
                                url = line
                            if url.startswith('http'):
                                urls.append(url)
                    return urls
                else:
                    print(f"⚠️ Extensions config not found: HTTP {response.status}")
    except Exception as e:
        print(f"⚠️ Could not fetch extensions list: {e}")
    
    return []

async def download_configuration():
    """Download WebUI configuration files with comprehensive error handling."""
    if UI in ['FaceFusion', 'RoopUnleashed', 'DreamO']:
        print(f"📄 Skipping standard configs for {UI} (uses specialized configuration)")
        return
    
    try:
        config_files = ["config.json", "ui-config.json"]
        
        for config_file in config_files:
            config_url = f"{CONFIG_URL}/{UI}/{config_file}"
            await _download_file(config_url, WEBUI, config_file)
            
    except Exception as e:
        print(f"⚠️ Configuration download issue: {e}")

async def install_extensions():
    """Install WebUI extensions with comprehensive error handling."""
    # Skip extensions for WebUIs that don't support them
    if UI in ['FaceFusion', 'RoopUnleashed', 'DreamO']:
        print(f"📦 Skipping extensions for {UI} (uses specialized modules)")
        return
    
    extensions = await get_extensions_list()
    
    if not extensions:
        print("📦 No extensions to install")
        return
        
    print(f"📦 Installing {len(extensions)} extensions...")
    
    EXTS.mkdir(parents=True, exist_ok=True)
    CD(EXTS)

    # Install extensions one by one with proper error handling
    successful = 0
    failed = 0
    
    for ext_url in extensions:
        try:
            ext_name = Path(ext_url).name
            print(f"  📥 Installing: {ext_name}")
            
            process = await asyncio.create_subprocess_shell(
                f"git clone --depth 1 --quiet {ext_url}",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                successful += 1
                print(f"    ✅ {ext_name}")
            else:
                failed += 1
                error_msg = stderr.decode().strip()
                print(f"    ⚠️ Failed: {ext_name} - {error_msg}")
                
        except Exception as e:
            failed += 1
            print(f"    ❌ Error installing {ext_url}: {e}")
    
    print(f"✅ Extensions complete: {successful} successful, {failed} failed")

# =================== ENHANCED WEBUI INSTALLATION ===================

def install_git_webui(ui_name, repo_url):
    """Install WebUI from git repository with comprehensive setup."""
    print(f"🔧 Installing {ui_name} from git repository...")
    
    try:
        # Clone the repository
        print(f"📥 Cloning {repo_url}...")
        result = subprocess.run([
            'git', 'clone', '--depth', '1', repo_url, str(WEBUI)
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"❌ Git clone failed: {result.stderr}")
            return False
        
        CD(WEBUI)
        
        # Install WebUI-specific requirements
        if ui_name in WEBUI_REQUIREMENTS:
            requirements = WEBUI_REQUIREMENTS[ui_name]
            print(f"📦 Installing {ui_name}-specific requirements...")
            for req in requirements:
                print(f"  📦 Installing {req}...")
                result = subprocess.run([
                    'pip', 'install', req
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"⚠️ Failed to install {req}: {result.stderr}")
        
        # Install from requirements.txt if available
        req_file = WEBUI / 'requirements.txt'
        if req_file.exists():
            print(f"📦 Installing from requirements.txt...")
            result = subprocess.run([
                'pip', 'install', '-r', 'requirements.txt'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"⚠️ Requirements install issues: {result.stderr}")
        
        # Setup WebUI-specific environment
        setup_webui_environment(ui_name)
        
        print(f"✅ {ui_name} installation complete")
        return True
        
    except subprocess.TimeoutExpired:
        print(f"❌ Installation timeout for {ui_name}")
        return False
    except Exception as e:
        print(f"❌ Installation error for {ui_name}: {e}")
        return False

def setup_webui_environment(ui_name):
    """Setup WebUI-specific environment and directories."""
    webui_path = Path(WEBUI)
    
    if ui_name in ['FaceFusion', 'RoopUnleashed']:
        # Face swap WebUIs setup
        print(f"🎭 Setting up {ui_name} face swap environment...")
        
        # Create directories
        for folder in ['models', 'input', 'output']:
            (webui_path / folder).mkdir(exist_ok=True)
        
        if ui_name == 'FaceFusion':
            # FaceFusion-specific setup
            for folder in ['models/face_analyser', 'models/face_swapper', 'models/face_enhancer']:
                (webui_path / folder).mkdir(parents=True, exist_ok=True)
        
        elif ui_name == 'RoopUnleashed':
            # RoopUnleashed-specific setup
            for folder in ['models/inswapper', 'models/gfpgan', 'models/gpen']:
                (webui_path / folder).mkdir(parents=True, exist_ok=True)
            
            # Create config file if it doesn't exist
            config_file = webui_path / 'config.yaml'
            if not config_file.exists():
                config_content = """
# RoopUnleashed Configuration
face_swap:
  quality: high
  gpu_acceleration: true
output:
  format: mp4
  quality: best
"""
                with open(config_file, 'w') as f:
                    f.write(config_content)
                
    elif ui_name == 'DreamO':
        # DreamO-specific setup
        print(f"🎨 Setting up {ui_name} specialized environment...")
        for folder in ['models/diffusion', 'models/vae', 'assets', 'output']:
            (webui_path / folder).mkdir(parents=True, exist_ok=True)
            
    elif ui_name in ['Forge', 'ReForge', 'SD-UX']:
        # Enhanced SD WebUIs setup
        print(f"⚒️ Setting up {ui_name} enhanced SD environment...")
        for folder in ['models/Stable-diffusion', 'models/VAE', 'models/Lora', 'embeddings', 'extensions']:
            (webui_path / folder).mkdir(parents=True, exist_ok=True)

def unpack_webui():
    """Download and extract WebUI archive with enhanced error handling."""
    if not MODULES_AVAILABLE:
        print("⚠️ Manager module not available, using fallback download")
        import urllib.request
        try:
            urllib.request.urlretrieve(REPO_URL, str(HOME / f"{UI}.zip"))
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False
    else:
        try:
            zip_path = HOME / f"{UI}.zip"
            m_download(f"{REPO_URL} {HOME} {UI}.zip")
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False
    
    # Extract archive
    try:
        zip_path = HOME / f"{UI}.zip"
        if zip_path.exists():
            ipySys(f"unzip -q -o {zip_path} -d {WEBUI} && rm -rf {zip_path}")
            print(f"✅ {UI} extracted successfully")
            return True
        else:
            print(f"❌ Archive not found: {zip_path}")
            return False
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return False

def apply_classic_fixes():
    """Apply specific fixes for Classic UI."""
    if UI != 'Classic':
        return

    cmd_args_path = WEBUI / 'modules/cmd_args.py'
    if not cmd_args_path.exists():
        return

    marker = '# Arguments added by ANXETY'
    try:
        with cmd_args_path.open('r+', encoding='utf-8') as f:
            content = f.read()
            if marker in content:
                return
            f.write(f"\n\n{marker}\n")
            f.write('parser.add_argument("--hypernetwork-dir", type=normalized_filepath, '
                   'default=os.path.join(models_path, \'hypernetworks\'), help="hypernetwork directory")')
        print("✅ Classic UI fixes applied")
    except Exception as e:
        print(f"⚠️ Could not apply Classic fixes: {e}")

def run_tagcomplete_tag_parser():
    """Run tagcomplete tag parser for supported WebUIs."""
    parser_script = WEBUI / 'tagcomplete-tags-parser.py'
    if parser_script.exists():
        try:
            ipyRun('run', str(parser_script))
            print("✅ Tag parser executed")
        except Exception as e:
            print(f"⚠️ Tag parser execution failed: {e}")

# ENHANCED: WebUI detection and installation logic
def is_git_based_webui(ui_name):
    """Check if WebUI should be installed from git."""
    return ui_name in WEBUI_REPOSITORIES

def should_use_archive(ui_name):
    """Check if WebUI should use archive-based installation."""
    archive_webuis = ['A1111', 'ComfyUI', 'Classic', 'Lightning.ai']
    return ui_name in archive_webuis

def download_webui_models(ui_name):
    """Download essential models for specialized WebUIs."""
    webui_path = Path(WEBUI)
    
    if ui_name == 'FaceFusion':
        print("📦 Downloading FaceFusion models...")
        models = [
            ('https://github.com/facefusion/facefusion-assets/releases/download/models/inswapper_128.onnx', 'models/face_swapper/'),
            ('https://github.com/facefusion/facefusion-assets/releases/download/models/arcface_w600k_r50.onnx', 'models/face_analyser/')
        ]
        
        for model_url, model_dir in models:
            try:
                model_path = webui_path / model_dir
                model_path.mkdir(parents=True, exist_ok=True)
                asyncio.run(_download_file(model_url, model_path))
            except Exception as e:
                print(f"⚠️ Model download failed: {e}")
    
    elif ui_name == 'RoopUnleashed':
        print("📦 Downloading RoopUnleashed models...")
        models = [
            ('https://huggingface.co/CountFloyd/deepfake/resolve/main/inswapper_128.onnx', 'models/'),
            ('https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth', 'models/gfpgan/')
        ]
        
        for model_url, model_dir in models:
            try:
                model_path = webui_path / model_dir
                model_path.mkdir(parents=True, exist_ok=True)
                asyncio.run(_download_file(model_url, model_path))
            except Exception as e:
                print(f"⚠️ Model download failed: {e}")

# ======================== MAIN INSTALLATION LOGIC =======================

async def main():
    """Enhanced main installation logic with comprehensive WebUI detection."""
    
    print(f"🔧 Installing WebUI: {UI}")
    print(f"📍 Environment: {ENV_NAME}")
    print(f"📂 Installation path: {WEBUI}")
    
    try:
        # Check if WebUI already exists
        if WEBUI.exists() and any(WEBUI.iterdir()):
            print(f"✅ {UI} already installed at {WEBUI}")
            return True
        
        # Determine installation method
        if is_git_based_webui(UI):
            print(f"🔗 Using git installation for {UI}")
            
            if UI not in WEBUI_REPOSITORIES:
                print(f"❌ Repository URL not found for {UI}")
                return False
            
            repo_url = WEBUI_REPOSITORIES[UI]
            success = install_git_webui(UI, repo_url)
            
            if success:
                # Download specialized models if needed
                download_webui_models(UI)
            
            return success
            
        elif should_use_archive(UI):
            print(f"📦 Using archive installation for {UI}")
            success = unpack_webui()
            
            if success:
                # Apply UI-specific fixes
                apply_classic_fixes()
                
                # Download and install extensions
                await download_configuration()
                await install_extensions()
                
                # Run additional setup
                run_tagcomplete_tag_parser()
            
            return success
        
        else:
            print(f"❌ Unknown installation method for {UI}")
            return False
            
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

# Execute main installation
if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        if result:
            print(f"🎉 {UI} installation completed successfully!")
            
            # Log installation summary
            print(f"\n📋 Installation Summary:")
            print(f"  WebUI: {UI}")
            print(f"  Path: {WEBUI}")
            print(f"  Type: {'Git-based' if is_git_based_webui(UI) else 'Archive-based'}")
            
            if UI in ['FaceFusion', 'RoopUnleashed']:
                print(f"  Category: Face Swap")
                print(f"  Note: This WebUI specializes in face swapping and doesn't use standard SD models")
            elif UI in ['Forge', 'ReForge', 'SD-UX']:
                print(f"  Category: Enhanced Stable Diffusion")
                print(f"  Note: This WebUI includes performance optimizations and additional features")
            elif UI == 'DreamO':
                print(f"  Category: Specialized AI Tool")
                print(f"  Note: This WebUI provides specialized AI capabilities")
            else:
                print(f"  Category: Standard Stable Diffusion")
        else:
            print(f"❌ {UI} installation failed!")
            print("Please check the error messages above and try again.")
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Installation cancelled by user")
    except Exception as e:
        print(f"❌ Critical installation error: {e}")
        print("Please report this error if it persists.")
