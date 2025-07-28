# ~ setup.py | by ANXETY - PLATFORM AGNOSTIC FIXED VERSION ~

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
CIVITAI_API_TOKEN = "65b66176dcf284b266579de57fbdc024"

nest_asyncio.apply()  # Async support for Jupyter


# ======================== CONSTANTS =======================

def detect_platform_home():
    """Detect the appropriate home directory based on platform."""
    if 'COLAB_GPU' in os.environ or '/content' in os.getcwd():
        return Path('/content')
    elif 'KAGGLE_URL_BASE' in os.environ or '/kaggle' in os.getcwd():
        return Path('/kaggle/working')
    elif '/teamspace/' in os.getcwd() or any('LIGHTNING' in k for k in os.environ):
        return Path('/teamspace/studios/this_studio')
    elif '/workspace/' in os.getcwd():
        return Path('/workspace')
    else:
        # Default fallback - try to detect from current working directory
        cwd = Path.cwd()
        if cwd.name == 'content':
            return cwd
        elif 'content' in cwd.parts:
            return Path('/content')
        else:
            return cwd.parent if cwd.name == 'ANXETY' else cwd

# FIXED: Platform-agnostic path detection
HOME = detect_platform_home()
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'
VENV_PATH = HOME / 'venv'
MODULES_FOLDER = SCR_PATH / "modules"

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

# Environment detection
SUPPORTED_ENVS = {
    'COLAB_GPU': 'Google Colab',
    'KAGGLE_URL_BASE': 'Kaggle',
    'LIGHTNING_AI': 'Lightning.ai'
}

# FIXED: File structure - scripts are now directly in scripts folder
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
        'enhanced_model_selector.py', 'requirements.txt'
    ],
    '__configs__': {
        'A1111': ['config.json', 'ui-config.json', '_extensions.txt'],
        'Classic': ['config.json', 'ui-config.json', '_extensions.txt'],
        'ComfyUI': {
            'Comfy-Manager': ['config.ini'],
            'workflows': ['anxety-workflow.json'],
            '': ['install-deps.py', '_extensions.txt', 'comfy.settings.json']
        },
        'Forge': ['config.json', 'ui-config.json', '_extensions.txt'],
        'ReForge': ['config.json', 'ui-config.json', '_extensions.txt'],
        'SD-UX': ['config.json', 'ui-config.json', '_extensions.txt'],
        '': [
            'card-no-preview.png', 'gradio-tunneling.py', 'notification.mp3',
            'styles.csv', 'tagcomplete-tags-parser.py', 'user.css'
        ]
    }
}


# =================== UTILITY FUNCTIONS ====================
def reinitialize_paths(base_path):
    """Re-initializes global path variables based on a new home directory."""
    global HOME, SCR_PATH, SETTINGS_PATH, VENV_PATH, MODULES_FOLDER
    HOME = base_path
    SCR_PATH = HOME / 'ANXETY'
    SETTINGS_PATH = SCR_PATH / 'settings.json'
    VENV_PATH = HOME / 'venv'
    MODULES_FOLDER = SCR_PATH / "modules"

    os.environ.update({
        'home_path': str(HOME),
        'scr_path': str(SCR_PATH),
        'venv_path': str(VENV_PATH),
        'settings_path': str(SETTINGS_PATH)
    })

def _install_deps() -> bool:
    """Check if all required dependencies are installed (aria2 and gdown)."""
    try:
        from shutil import which
        required_tools = ['aria2c', 'gdown']
        return all(which(tool) is not None for tool in required_tools)
    except ImportError:
        return False

def _get_start_timer() -> int:
    """Get start timer from settings or return current time minus 5 seconds."""
    try:
        if SETTINGS_PATH.exists():
            settings = json.loads(SETTINGS_PATH.read_text())
            return settings.get("ENVIRONMENT", {}).get("start_timer", int(time.time() - 5))
    except (json.JSONDecodeError, OSError):
        pass
    return int(time.time() - 5)

def save_env_to_json(data: dict, filepath: Path) -> None:
    """Save environment data to JSON file, merging with existing content."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    existing_data = {}
    if filepath.exists():
        try:
            existing_data = json.loads(filepath.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    merged_data = {**existing_data, **data}
    filepath.write_text(json.dumps(merged_data, indent=4))


# =================== MODULE MANAGEMENT ====================

def _clear_module_cache(modules_folder = None):
    """Clear module cache for modules in specified folder or default modules folder."""
    target_folder = Path(modules_folder) if modules_folder else MODULES_FOLDER
    target_folder = target_folder.resolve()
    modules_to_remove = []
    for module_name, module in sys.modules.items():
        if hasattr(module, "__file__") and module.__file__:
            try:
                module_path = Path(module.__file__).resolve()
                if target_folder in module_path.parents:
                    modules_to_remove.append(module_name)
            except (ValueError, RuntimeError, OSError):
                continue
    for module_name in modules_to_remove:
        try:
            del sys.modules[module_name]
        except KeyError:
            pass
    importlib.invalidate_caches()

def setup_module_folder(modules_folder = None):
    """Set up module folder by clearing cache and adding to sys.path."""
    target_folder = Path(modules_folder) if modules_folder else MODULES_FOLDER
    target_folder.mkdir(parents=True, exist_ok=True)
    _clear_module_cache(target_folder)
    folder_str = str(target_folder)
    if folder_str not in sys.path:
        sys.path.insert(0, folder_str)


# =================== ENVIRONMENT SETUP ====================

def detect_environment():
    """FIXED: Improved environment detection."""
    if 'COLAB_GPU' in os.environ or '/content' in os.getcwd():
        return 'Google Colab'
    elif 'KAGGLE_URL_BASE' in os.environ or '/kaggle' in os.getcwd():
        return 'Kaggle'
    elif '/teamspace/' in os.getcwd() or any('LIGHTNING' in k for k in os.environ):
        return 'Lightning.ai'
    elif '/workspace/' in os.getcwd():
        return 'Vast.ai'
    else:
        print("Warning: Unknown environment, assuming Colab compatibility")
        return 'Google Colab'

def parse_fork_arg(fork_arg):
    """Parse fork argument into user/repo."""
    if not fork_arg:
        return DEFAULT_USER, DEFAULT_REPO
    parts = fork_arg.split("/", 1)
    return parts[0], (parts[1] if len(parts) > 1 else DEFAULT_REPO)

def create_environment_data(env, lang, fork_user, fork_repo, branch):
    """Create environment data dictionary."""
    install_deps = _install_deps()
    start_timer = _get_start_timer()
    return {
        "ENVIRONMENT": {
            "env_name": env,
            "install_deps": install_deps,
            "fork": f"{fork_user}/{fork_repo}",
            "branch": branch,
            "lang": lang,
            "home_path": os.environ['home_path'],
            "scr_path": os.environ['scr_path'],
            "venv_path": os.environ['venv_path'],
            "settings_path": os.environ['settings_path'],
            "start_timer": start_timer,
            "public_ip": "",
            "civitai_api_token": CIVITAI_API_TOKEN
        }
    }


# ===================== DOWNLOAD LOGIC =====================

def generate_file_list(structure: Dict, base_url: str, lang: str) -> List[Tuple[str, Path]]:
    """FIXED: Generate flat list of (url, path) from nested structure - no lang folders."""
    def walk(struct: Dict, path_parts: List[str]) -> List[Tuple[str, Path]]:
        items = []
        for key, value in struct.items():
            current_path = [*path_parts, key] if key else path_parts
            if isinstance(value, dict):
                items.extend(walk(value, current_path))
            else:
                url_path = "/".join(current_path)
                for file in value:
                    url = f"{base_url}/{url_path}/{file}" if url_path else f"{base_url}/{file}"
                    file_path = SCR_PATH / "/".join(current_path) / file
                    items.append((url, file_path))
        return items
    return walk(structure, [])

async def download_file(session: aiohttp.ClientSession, url: str, path: Path, max_retries: int = 3) -> Tuple[bool, str, Path, Optional[str]]:
    """Download and save single file with error handling and retry logic."""
    for attempt in range(max_retries):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                resp.raise_for_status()
                path.parent.mkdir(parents=True, exist_ok=True)
                temp_path = path.with_suffix(path.suffix + '.tmp')
                content = await resp.read()
                temp_path.write_bytes(content)
                temp_path.rename(path)
                return (True, url, path, None)
        except asyncio.TimeoutError:
            error_msg = f"Timeout error (attempt {attempt + 1}/{max_retries})"
            if attempt == max_retries - 1:
                return (False, url, path, error_msg)
            await asyncio.sleep(2 ** attempt)
        except aiohttp.ClientResponseError as e:
            error_msg = f"HTTP error {e.status}: {e.message}"
            if e.status >= 500 and attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            return (False, url, path, error_msg)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            if attempt == max_retries - 1:
                return (False, url, path, error_msg)
            await asyncio.sleep(2 ** attempt)
    return (False, url, path, "Max retries exceeded")

async def download_files_async(lang, fork_user, fork_repo, branch, log_errors):
    """Main download executor with error logging and improved reliability."""
    base_url = f"{BASE_GITHUB_URL}/{fork_user}/{fork_repo}/{branch}"
    file_list = generate_file_list(FILE_STRUCTURE, base_url, lang)
    connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
    timeout = aiohttp.ClientTimeout(total=60, connect=10)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [download_file(session, url, path) for url, path in file_list]
        errors = []
        successful = 0
        for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Downloading files", unit="file"):
            success, url, path, error = await future
            if success:
                successful += 1
            else:
                errors.append((url, path, error))
        clear_output()
        print(f"Downloaded {successful}/{len(file_list)} files successfully")
        if errors:
            print(f"\n{len(errors)} files failed to download")
            if log_errors:
                print("\nErrors occurred during download:")
                for url, path, error in errors[:10]:
                    print(f"URL: {url}\nPath: {path}\nError: {error}\n")
                if len(errors) > 10:
                    print(f"... and {len(errors) - 10} more errors")
            critical_files = ['json_utils.py', '_season.py']
            critical_errors = [e for e in errors if any(cf in str(e[1]) for cf in critical_files)]
            if critical_errors:
                raise RuntimeError(f"Critical files failed to download: {[str(e[1]) for e in critical_errors]}")

# ===================== MAIN EXECUTION =====================

async def main_async(args=None):
    """Entry point with improved error handling."""
    parser = argparse.ArgumentParser(description='ANXETY Download Manager')
    parser.add_argument('--lang', default=DEFAULT_LANG, help=f"Language to be used (default: {DEFAULT_LANG})")
    parser.add_argument('--branch', default=DEFAULT_BRANCH, help=f"Branch to download files from (default: {DEFAULT_BRANCH})")
    parser.add_argument('--fork', default=None, help="Specify project fork (user or user/repo)")
    parser.add_argument('-s', '--skip-download', action="store_true", help="Skip downloading files")
    parser.add_argument('-l', "--log", action="store_true", help="Enable logging of download errors")
    args, _ = parser.parse_known_args(args)
    try:
        env = detect_environment()
        print(f"🌍 Detected environment: {env}")
        print(f"📁 Using home directory: {HOME}")
        
        user, repo = parse_fork_arg(args.fork)
        if not args.skip_download:
            await download_files_async(args.lang, user, repo, args.branch, args.log)
        setup_module_folder()
        env_data = create_environment_data(env, args.lang, user, repo, args.branch)
        save_env_to_json(env_data, SETTINGS_PATH)
        if CIVITAI_API_TOKEN:
            os.environ['CIVITAI_API_TOKEN'] = CIVITAI_API_TOKEN
        try:
            from _season import display_info
            display_info(
                env=env,
                scr_folder=os.environ['scr_path'],
                branch=args.branch,
                lang=args.lang,
                fork=args.fork
            )
        except ImportError as e:
            print(f"Warning: Could not load season display: {e}")
            print("Setup completed successfully!")
    except Exception as e:
        print(f"Setup failed: {str(e)}")
        print("Please check your internet connection and try again.")
        raise

if __name__ == "__main__":
    asyncio.run(main_async())
