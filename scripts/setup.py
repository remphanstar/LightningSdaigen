# ~ setup.py | by ANXETY - Enhanced Platform Agnostic Setup ~

from IPython.display import display, HTML, clear_output
from typing import Dict, List, Tuple, Optional, Union
from pathlib import Path
from tqdm import tqdm
import nest_asyncio
import importlib
import argparse
import aiohttp
import asyncio
import time
import json
import sys
import os

# --- Civitai API Token ---
# Add your Civitai API token here to permanently store it in the notebook.
# This will override the token set in the widgets.
# Get your token here: https://civitai.com/user/account
CIVITAI_API_TOKEN = "9d333451a6148a1682349e326967efc2"

nest_asyncio.apply()  # Async support for Jupyter

# ======================== ENHANCED CONSTANTS =======================

def detect_platform_home():
    """Enhanced platform detection with comprehensive fallbacks."""
    
    # Check environment variables for platform detection
    if 'COLAB_GPU' in os.environ or '/content' in os.getcwd():
        print("🔍 Detected: Google Colab")
        return Path('/content')
    elif 'KAGGLE_URL_BASE' in os.environ or '/kaggle' in os.getcwd():
        print("🔍 Detected: Kaggle")
        return Path('/kaggle/working')
    elif '/teamspace/' in os.getcwd() or any('LIGHTNING' in k for k in os.environ):
        print("🔍 Detected: Lightning.ai")
        return Path('/teamspace/studios/this_studio')
    elif '/workspace/' in os.getcwd():
        print("🔍 Detected: Generic workspace")
        return Path('/workspace')
    elif 'VAST_CONTAINERLABEL' in os.environ:
        print("🔍 Detected: Vast.ai")
        return Path('/workspace')
    else:
        # Enhanced fallback detection
        cwd = Path.cwd()
        print(f"🔍 Platform detection fallback - Current dir: {cwd}")
        
        if cwd.name == 'content':
            return cwd
        elif 'content' in cwd.parts:
            return Path('/content')
        elif cwd.name == 'working':
            return cwd.parent / 'working'
        else:
            # Use current directory as home
            return cwd.parent if cwd.name == 'ANXETY' else cwd

# FIXED: Enhanced platform-agnostic path detection
HOME = detect_platform_home()
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'
VENV_PATH = HOME / 'venv'
MODULES_FOLDER = SCR_PATH / "modules"

print(f"🏠 Home directory: {HOME}")
print(f"📁 Scripts directory: {SCR_PATH}")

# Add corrected paths to the environment
os.environ.update({
    'home_path': str(HOME),
    'scr_path': str(SCR_PATH),
    'venv_path': str(VENV_PATH),
    'settings_path': str(SETTINGS_PATH)
})

# GitHub configuration
DEFAULT_USER = 'remphanstar'
DEFAULT_REPO = 'LightningSdaigen'
DEFAULT_BRANCH = 'main'
DEFAULT_LANG = 'en'
BASE_GITHUB_URL = "https://raw.githubusercontent.com"

# Enhanced environment detection
SUPPORTED_ENVS = {
    'COLAB_GPU': 'Google Colab',
    'KAGGLE_URL_BASE': 'Kaggle', 
    'LIGHTNING_AI': 'Lightning.ai',
    'VAST_CONTAINERLABEL': 'Vast.ai'
}

# ENHANCED: Complete file structure for 10WebUI system
FILE_STRUCTURE = {
    'CSS': ['main-widgets.css', 'download-result.css', 'auto-cleaner.css'],
    'JS': ['main-widgets.js'],
    'modules': [
        'json_utils.py', 'webui_utils.py', 'widget_factory.py',
        'CivitaiAPI.py', 'Manager.py', 'TunnelHub.py', '_season.py'
    ],
    'scripts': [
        'widgets-en.py', 'downloading-en.py', 'webui-installer.py',
        'launch.py', 'download-result.py', 'auto-cleaner.py',
        '_models-data.py', '_xl-models-data.py', 'setup.py',
        'requirements.txt'
    ],
    '__configs__': {
        'A1111': ['_extensions.txt', 'config.json', 'ui-config.json'],
        'ComfyUI': ['_extensions.txt', 'extra_model_paths.yaml'],
        'Classic': ['_extensions.txt', 'config.json', 'ui-config.json'], 
        'Lightning.ai': ['_extensions.txt', 'config.json', 'ui-config.json'],
        'Forge': ['_extensions.txt', 'config.json', 'ui-config.json'],
        'ReForge': ['_extensions.txt', 'config.json', 'ui-config.json'],
        'SD-UX': ['_extensions.txt', 'config.json', 'ui-config.json'],
        'FaceFusion': ['facefusion.ini'],
        'RoopUnleashed': ['_extensions.txt', 'config.yaml'],
        'DreamO': ['config.yaml']
    }
}

# ======================== UTILITY FUNCTIONS =======================

def _get_start_timer():
    """Get high-precision start timer."""
    return time.time()

def _install_deps():
    """Determine if dependencies should be installed."""
    # Always install deps in cloud environments
    return any(env in os.environ for env in SUPPORTED_ENVS.keys())

def _get_env():
    """Enhanced environment detection."""
    for env_var, env_name in SUPPORTED_ENVS.items():
        if env_var in os.environ:
            return env_name
    return "Unknown Environment"

def parse_args():
    """Parse command line arguments with enhanced defaults."""
    parser = argparse.ArgumentParser(description='LightningSdaigen Enhanced Setup')
    parser.add_argument('--branch', type=str, default=DEFAULT_BRANCH, 
                       help=f'Repository branch (default: {DEFAULT_BRANCH})')
    parser.add_argument('--fork', type=str, default=f"{DEFAULT_USER}/{DEFAULT_REPO}",
                       help=f'Repository fork (default: {DEFAULT_USER}/{DEFAULT_REPO})')
    parser.add_argument('--lang', type=str, default=DEFAULT_LANG,
                       help=f'Language (default: {DEFAULT_LANG})')
    
    # Parse args, handling both notebook and script contexts
    try:
        return parser.parse_args()
    except SystemExit:
        # In notebook context, create default args
        args = argparse.Namespace()
        args.branch = DEFAULT_BRANCH
        args.fork = f"{DEFAULT_USER}/{DEFAULT_REPO}"
        args.lang = DEFAULT_LANG
        return args

def parse_fork_arg(fork_arg: str) -> Tuple[str, str]:
    """Parse fork argument into user and repo with validation."""
    if not fork_arg:
        return DEFAULT_USER, DEFAULT_REPO
    
    parts = fork_arg.split("/", 1)
    if len(parts) == 1:
        return parts[0], DEFAULT_REPO
    elif len(parts) == 2:
        return parts[0], parts[1]
    else:
        return DEFAULT_USER, DEFAULT_REPO

def create_environment_data(env, lang, fork_user, fork_repo, branch):
    """Create comprehensive environment data dictionary."""
    install_deps = _install_deps()
    start_timer = _get_start_timer()
    
    return {
        "ENVIRONMENT": {
            "env_name": env,
            "install_deps": install_deps,
            "fork": f"{fork_user}/{fork_repo}",
            "branch": branch,
            "lang": lang,
            "home_path": str(HOME),
            "scr_path": str(SCR_PATH),
            "venv_path": str(VENV_PATH),
            "settings_path": str(SETTINGS_PATH),
            "start_timer": start_timer,
            "public_ip": "",
            "civitai_api_token": CIVITAI_API_TOKEN
        },
        "WEBUI": {
            "current": "A1111",
            "latest": None,
            "webui_path": str(HOME / "A1111"),
            "model_dir": "",
            "vae_dir": "",
            "lora_dir": "", 
            "embed_dir": "",
            "extension_dir": "",
            "upscale_dir": "",
            "output_dir": ""
        },
        "WIDGETS": {}
    }

# ===================== ENHANCED DOWNLOAD LOGIC =====================

def generate_file_list(structure: Dict, base_url: str, lang: str) -> List[Tuple[str, Path]]:
    """Generate flat list of (url, path) from nested structure."""
    
    def walk(struct: Dict, path_parts: List[str]) -> List[Tuple[str, Path]]:
        items = []
        for key, value in struct.items():
            current_path = [*path_parts, key] if key else path_parts
            
            if isinstance(value, dict):
                items.extend(walk(value, current_path))
            else:
                # Handle list of files
                url_path = "/".join(current_path)
                for file in value:
                    url = f"{base_url}/{url_path}/{file}" if url_path else f"{base_url}/{file}"
                    file_path = SCR_PATH / "/".join(current_path) / file
                    items.append((url, file_path))
        return items
    
    return walk(structure, [])

async def download_file(session: aiohttp.ClientSession, url: str, path: Path, 
                       max_retries: int = 3) -> Tuple[bool, str, Path, Optional[str]]:
    """Download and save single file with enhanced error handling and retry logic."""
    
    for attempt in range(max_retries):
        try:
            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    # Write file atomically
                    temp_path = path.with_suffix(path.suffix + '.tmp')
                    with open(temp_path, 'wb') as f:
                        f.write(content)
                    
                    # Atomic rename
                    temp_path.rename(path)
                    
                    return True, "Success", path, None
                elif response.status == 404:
                    return False, f"Not found (404)", path, f"URL: {url}"
                else:
                    return False, f"HTTP {response.status}", path, f"URL: {url}"
                    
        except asyncio.TimeoutError:
            if attempt < max_retries - 1:
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                continue
            return False, "Timeout", path, f"URL: {url}"
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(1 * (attempt + 1))
                continue
            return False, f"Error: {str(e)}", path, f"URL: {url}"
    
    return False, "Max retries exceeded", path, f"URL: {url}"

async def download_files_batch(session: aiohttp.ClientSession, 
                              file_list: List[Tuple[str, Path]], 
                              batch_size: int = 10) -> Dict[str, int]:
    """Download files in batches with progress tracking."""
    
    results = {"success": 0, "failed": 0, "errors": []}
    
    # Process files in batches to avoid overwhelming the server
    for i in range(0, len(file_list), batch_size):
        batch = file_list[i:i + batch_size]
        
        # Create download tasks for current batch
        tasks = [download_file(session, url, path) for url, path in batch]
        
        # Execute batch
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for j, result in enumerate(batch_results):
            if isinstance(result, Exception):
                results["failed"] += 1
                results["errors"].append(f"Exception: {result}")
            else:
                success, message, path, error_info = result
                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    if error_info:
                        results["errors"].append(f"{path.name}: {message} - {error_info}")
        
        # Small delay between batches
        if i + batch_size < len(file_list):
            await asyncio.sleep(0.1)
    
    return results

async def download_repository_files(fork_user: str, fork_repo: str, branch: str, lang: str):
    """Download repository files with comprehensive error handling and progress tracking."""
    
    base_url = f"{BASE_GITHUB_URL}/{fork_user}/{fork_repo}/{branch}"
    file_list = generate_file_list(FILE_STRUCTURE, base_url, lang)
    
    print(f"📥 Downloading {len(file_list)} files from repository...")
    print(f"📍 Repository: {fork_user}/{fork_repo} (branch: {branch})")
    
    # Configure session with proper timeouts
    timeout = aiohttp.ClientTimeout(total=30, connect=10)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Download files with progress tracking
        with tqdm(total=len(file_list), desc="Downloading", unit="file") as pbar:
            results = {"success": 0, "failed": 0, "errors": []}
            
            # Process in smaller batches for better progress updates
            batch_size = 5
            for i in range(0, len(file_list), batch_size):
                batch = file_list[i:i + batch_size]
                batch_results = await download_files_batch(session, batch, batch_size)
                
                # Update results
                results["success"] += batch_results["success"]
                results["failed"] += batch_results["failed"]
                results["errors"].extend(batch_results["errors"])
                
                # Update progress bar
                pbar.update(len(batch))
    
    # Report results
    total_files = results["success"] + results["failed"]
    success_rate = (results["success"] / total_files * 100) if total_files > 0 else 0
    
    print(f"\n📊 Download Summary:")
    print(f"  ✅ Successful: {results['success']}")
    print(f"  ❌ Failed: {results['failed']}")
    print(f"  📈 Success Rate: {success_rate:.1f}%")
    
    if results["errors"] and len(results["errors"]) <= 10:
        print(f"\n⚠️ Errors encountered:")
        for error in results["errors"][:10]:
            print(f"    • {error}")
        if len(results["errors"]) > 10:
            print(f"    ... and {len(results['errors']) - 10} more errors")
    
    return results["success"] > 0  # Return True if at least some files downloaded

def save_environment_data(data: Dict, settings_path: Path):
    """Save environment data to settings file with error handling."""
    
    try:
        # Ensure directory exists
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write settings atomically
        temp_path = settings_path.with_suffix('.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        # Atomic rename
        temp_path.rename(settings_path)
        
        print(f"✅ Settings saved to: {settings_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save settings: {e}")
        return False

def setup_module_paths():
    """Add modules directory to Python path for imports."""
    
    modules_path = str(MODULES_FOLDER)
    if modules_path not in sys.path:
        sys.path.insert(0, modules_path)
        print(f"✅ Added modules path: {modules_path}")
    
    # Verify critical modules can be imported
    try:
        import json_utils
        print("✅ json_utils module verified")
    except ImportError as e:
        print(f"⚠️ Could not import json_utils: {e}")

# ======================== MAIN SETUP LOGIC =======================

async def main():
    """Enhanced main setup function with comprehensive error handling."""
    
    print("🚀 LightningSdaigen Enhanced Setup Starting...")
    print("=" * 60)
    
    try:
        # Parse arguments
        args = parse_args()
        fork_user, fork_repo = parse_fork_arg(args.fork)
        
        # Detect environment
        env = _get_env()
        print(f"🌍 Environment: {env}")
        
        # Create environment data
        env_data = create_environment_data(env, args.lang, fork_user, fork_repo, args.branch)
        
        # Save initial settings
        if not save_environment_data(env_data, SETTINGS_PATH):
            print("⚠️ Could not save initial settings, continuing anyway...")
        
        # Download repository files
        print(f"\n📥 Downloading repository files...")
        download_success = await download_repository_files(fork_user, fork_repo, args.branch, args.lang)
        
        if not download_success:
            print("❌ Critical files could not be downloaded!")
            print("🔧 Attempting to create minimal structure...")
            
            # Create minimal directory structure
            for dir_name in ['modules', 'scripts', '__configs__', 'CSS', 'JS']:
                dir_path = SCR_PATH / dir_name
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"📁 Created: {dir_path}")
        
        # Setup module paths
        setup_module_paths()
        
        # Final validation
        critical_files = [
            SCR_PATH / 'modules' / 'json_utils.py',
            SCR_PATH / 'scripts' / 'widgets-en.py',
            SCR_PATH / 'scripts' / 'downloading-en.py',
            SCR_PATH / 'scripts' / 'launch.py'
        ]
        
        missing_files = []
        for file_path in critical_files:
            if not file_path.exists():
                missing_files.append(file_path.name)
        
        if missing_files:
            print(f"\n⚠️ Missing critical files: {', '.join(missing_files)}")
            print("🔧 You may need to manually download these files or check your internet connection.")
        else:
            print(f"\n✅ All critical files verified!")
        
        # Display setup completion
        print(f"\n🎉 Setup completed!")
        print(f"📁 Installation directory: {SCR_PATH}")
        print(f"⚙️ Settings file: {SETTINGS_PATH}")
        print(f"🌍 Environment: {env}")
        print(f"📦 Repository: {fork_user}/{fork_repo} (branch: {args.branch})")
        
        # Show next steps
        print(f"\n📋 Next Steps:")
        print(f"1. Run the widgets cell to configure your setup")
        print(f"2. Run the downloading cell to install WebUI and models")
        print(f"3. Run the launch cell to start your WebUI")
        
        if missing_files:
            print(f"\n🔧 If you encounter issues:")
            print(f"1. Check your internet connection")
            print(f"2. Try running the setup cell again")
            print(f"3. Manually download missing files if needed")
        
        return True
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Setup cancelled by user")
        return False
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        print(f"🔧 Try running the setup again or check your internet connection")
        return False

def create_requirements_file():
    """Create enhanced requirements.txt file for the system."""
    
    requirements_content = """# LightningSdaigen Enhanced Requirements
# Core dependencies for all WebUI types

# Web and networking
requests>=2.25.0
aiohttp>=3.8.0
urllib3>=1.26.0

# Data processing
numpy>=1.21.0
Pillow>=9.0.0
opencv-python>=4.6.0

# Progress and UI
tqdm>=4.64.0
ipywidgets>=7.7.0

# Async support
nest-asyncio>=1.5.0

# JSON and data handling
jsonschema>=4.0.0

# File handling
pathlib2>=2.3.0

# System utilities
psutil>=5.8.0

# WebUI-specific dependencies (installed as needed)
# torch>=2.0.0  # For SD WebUIs
# onnxruntime-gpu>=1.15.0  # For face swap WebUIs
# diffusers>=0.21.0  # For specialized WebUIs
# transformers>=4.25.0  # For AI models
# accelerate>=0.20.0  # For performance
# xformers>=0.0.20  # For memory optimization
# gradio>=3.50.0  # For web interfaces
# insightface>=0.7.3  # For face analysis
# gfpgan>=1.3.8  # For face enhancement
"""
    
    requirements_path = SCR_PATH / 'scripts' / 'requirements.txt'
    
    try:
        requirements_path.parent.mkdir(parents=True, exist_ok=True)
        with open(requirements_path, 'w', encoding='utf-8') as f:
            f.write(requirements_content)
        print(f"✅ Requirements file created: {requirements_path}")
        return True
    except Exception as e:
        print(f"⚠️ Could not create requirements file: {e}")
        return False

def display_banner():
    """Display enhanced setup banner with system information."""
    
    banner = f"""
    {chr(9608)*2}{chr(9604)*2}{chr(9608)*2}  LightningSdaigen Enhanced Setup  {chr(9608)*2}{chr(9604)*2}{chr(9608)*2}
    
    🚀 Multi-Platform WebUI Deployment System
    ⚡ Supporting 10+ WebUI Types
    🎭 Face Swap • 🎨 Image Generation • 🔗 Node-Based Workflows
    
    Platform: {_get_env()}
    Home: {HOME}
    Python: {sys.version.split()[0]}
    """
    
    display(HTML(f'<pre style="background:#1a1a1a;color:#00ff00;padding:15px;border-radius:8px;font-family:monospace;">{banner}</pre>'))

def check_system_requirements():
    """Check system requirements and display warnings if needed."""
    
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("⚠️ Warning: Python 3.8+ recommended, you have", sys.version.split()[0])
    else:
        print(f"✅ Python version: {sys.version.split()[0]}")
    
    # Check available disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage(HOME)
        free_gb = free // (1024**3)
        
        if free_gb < 10:
            print(f"⚠️ Warning: Low disk space ({free_gb}GB free). Consider freeing up space.")
        else:
            print(f"✅ Disk space: {free_gb}GB available")
            
    except Exception as e:
        print(f"⚠️ Could not check disk space: {e}")
    
    # Check for GPU
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ NVIDIA GPU detected")
        else:
            print("⚠️ No NVIDIA GPU detected - some WebUIs may run slowly")
    except FileNotFoundError:
        print("⚠️ nvidia-smi not found - GPU status unknown")
    except Exception:
        print("⚠️ Could not detect GPU")

# ======================== EXECUTION =======================

if __name__ == "__main__":
    try:
        # Display banner
        display_banner()
        
        # Check system requirements
        check_system_requirements()
        
        # Create requirements file
        create_requirements_file()
        
        # Run main setup
        print(f"\n🔧 Starting enhanced setup process...")
        success = asyncio.run(main())
        
        if success:
            print(f"\n{chr(9989)} Setup completed successfully!")
            print(f"🎛️ You can now proceed to the widgets cell to configure your WebUI selection.")
        else:
            print(f"\n❌ Setup encountered issues.")
            print(f"🔧 Please check the error messages above and try again.")
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Critical setup error: {e}")
        print(f"🔧 Please report this error if it persists.")

        
