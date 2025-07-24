# ~ setup.py | by ANXETY ~ (FIXED VERSION)

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


nest_asyncio.apply()  # Async support for Jupyter


# ======================== CONSTANTS =======================

HOME = Path.home()
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'
VENV_PATH = HOME / 'venv'
MODULES_FOLDER = SCR_PATH / "modules"

# Add paths to the environment
os.environ.update({
    'home_path': str(HOME),
    'scr_path': str(SCR_PATH),
    'venv_path': str(VENV_PATH),
    'settings_path': str(SETTINGS_PATH)
})

# GitHub configuration - FIXED: Updated to correct repository
DEFAULT_USER = 'anxety-solo'
DEFAULT_REPO = 'sdAIgen'
DEFAULT_BRANCH = 'main'
DEFAULT_LANG = 'en'
BASE_GITHUB_URL = "https://raw.githubusercontent.com"

# Environment detection
SUPPORTED_ENVS = {
    'COLAB_GPU': 'Google Colab',
    'KAGGLE_URL_BASE': 'Kaggle',
    'LIGHTNING_AI': 'Lightning.ai'
}

# File structure configuration
FILE_STRUCTURE = {
    'CSS': ['main-widgets.css', 'download-result.css', 'auto-cleaner.css'],
    'JS': ['main-widgets.js'],
    'modules': [
        'json_utils.py', 'webui_utils.py', 'widget_factory.py',
        'CivitaiAPI.py', 'Manager.py', 'TunnelHub.py', '_season.py'
    ],
    'scripts': {
        '{lang}': ['widgets-{lang}.py', 'downloading-{lang}.py'],
        '': [
            'webui-installer.py', 'launch.py', 'download-result.py', 'auto-cleaner.py',
            '_models-data.py', '_xl-models-data.py'
        ]
    }
}

# FIXED: Add retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2


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
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Load existing data if file exists
        existing_data = {}
        if filepath.exists():
            try:
                existing_data = json.loads(filepath.read_text())
            except (json.JSONDecodeError, OSError):
                print("Warning: Could not read existing settings, creating new file")

        # Merge new data with existing
        merged_data = {**existing_data, **data}
        filepath.write_text(json.dumps(merged_data, indent=4))
    except Exception as e:
        print(f"Error saving settings: {e}")
        raise


# =================== MODULE MANAGEMENT ====================

def _clear_module_cache(modules_folder = None):
    """Clear module cache for modules in specified folder or default modules folder."""
    target_folder = Path(modules_folder) if modules_folder else MODULES_FOLDER
    target_folder = target_folder.resolve()   # Full absolute path

    # FIXED: More careful module cleanup to avoid breaking other code
    modules_to_remove = []
    for module_name, module in sys.modules.items():
        if hasattr(module, "__file__") and module.__file__:
            try:
                module_path = Path(module.__file__).resolve()
                if target_folder in module_path.parents:
                    modules_to_remove.append(module_name)
            except (ValueError, RuntimeError, OSError):
                continue

    # Remove modules safely
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
    """Detect runtime environment."""
    for var, name in SUPPORTED_ENVS.items():
        if var in os.environ:
            return name
    
    # FIXED: Better error message and fallback
    print("Warning: Unknown environment detected. Supported environments:")
    for var, name in SUPPORTED_ENVS.items():
        print(f"  - {name} (env var: {var})")
    
    # Try to detect common paths as fallback
    if '/content' in str(Path.cwd()):
        print("Detected Google Colab based on path")
        return 'Google Colab'
    elif '/kaggle' in str(Path.cwd()):
        print("Detected Kaggle based on path")
        return 'Kaggle'
    elif '/teamspace' in str(Path.cwd()):
        print("Detected Lightning.ai based on path")
        return 'Lightning.ai'
    
    raise EnvironmentError(f"Unsupported environment. Please run in one of: {', '.join(SUPPORTED_ENVS.values())}")

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
            "public_ip": ""
        }
    }


# ===================== DOWNLOAD LOGIC =====================

def _format_lang_path(path: str, lang: str) -> str:
    """Format path with language placeholder."""
    return path.format(lang=lang) if '{lang}' in path else path

def generate_file_list(structure: Dict, base_url: str, lang: str) -> List[Tuple[str, Path]]:
    """Generate flat list of (url, path) from nested structure."""
    def walk(struct: Dict, path_parts: List[str]) -> List[Tuple[str, Path]]:
        items = []
        for key, value in struct.items():
            # Handle language-specific paths
            current_key = _format_lang_path(key, lang)
            current_path = [*path_parts, current_key] if current_key else path_parts

            if isinstance(value, dict):
                items.extend(walk(value, current_path))
            else:
                url_path = "/".join(current_path)
                for file in value:
                    # Handle language-specific files
                    formatted_file = _format_lang_path(file, lang)
                    url = f"{base_url}/{url_path}/{formatted_file}" if url_path else f"{base_url}/{formatted_file}"
                    file_path = SCR_PATH / "/".join(current_path) / formatted_file
                    items.append((url, file_path))
        return items

    return walk(structure, [])

async def download_file_with_retry(session: aiohttp.ClientSession, url: str, path: Path) -> Tuple[bool, str, Path, Optional[str]]:
    """Download and save single file with retry logic and error handling."""
    for attempt in range(MAX_RETRIES):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 404:
                    return (False, url, path, f"File not found (404): {url}")
                resp.raise_for_status()
                
                # FIXED: Ensure parent directory exists and handle write errors
                path.parent.mkdir(parents=True, exist_ok=True)
                content = await resp.read()
                
                # Write to temporary file first, then rename for atomic operation
                temp_path = path.with_suffix(path.suffix + '.tmp')
                try:
                    temp_path.write_bytes(content)
                    temp_path.rename(path)
                    return (True, url, path, None)
                except OSError as e:
                    if temp_path.exists():
                        temp_path.unlink()
                    raise e
                    
        except asyncio.TimeoutError:
            error_msg = f"Timeout (attempt {attempt + 1}/{MAX_RETRIES})"
        except aiohttp.ClientResponseError as e:
            error_msg = f"HTTP error {e.status}: {e.message} (attempt {attempt + 1}/{MAX_RETRIES})"
        except Exception as e:
            error_msg = f"Error: {str(e)} (attempt {attempt + 1}/{MAX_RETRIES})"
        
        # Wait before retry (except on last attempt)
        if attempt < MAX_RETRIES - 1:
            await asyncio.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
    
    return (False, url, path, error_msg)

async def download_files_async(lang, fork_user, fork_repo, branch, log_errors):
    """Main download executor with error logging and retry logic."""
    base_url = f"{BASE_GITHUB_URL}/{fork_user}/{fork_repo}/{branch}"
    file_list = generate_file_list(FILE_STRUCTURE, base_url, lang)

    # FIXED: Better session configuration and connection limits
    connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
    timeout = aiohttp.ClientTimeout(total=60, connect=10)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [download_file_with_retry(session, url, path) for url, path in file_list]
        errors = []
        success_count = 0

        for future in tqdm(asyncio.as_completed(tasks), total=len(tasks),
                          desc="Downloading files", unit="file"):
            success, url, path, error = await future
            if success:
                success_count += 1
            else:
                errors.append((url, path, error))

        clear_output()
        
        # FIXED: Better error reporting and success feedback
        print(f"✅ Downloaded {success_count}/{len(file_list)} files successfully")

        if errors:
            print(f"❌ {len(errors)} files failed to download")
            if log_errors:
                print("\nDetailed error log:")
                for url, path, error in errors:
                    print(f"URL: {url}")
                    print(f"Path: {path}")
                    print(f"Error: {error}\n")
            else:
                print("Use --log flag to see detailed error information")
            
            # Don't fail completely if only some files failed
            if len(errors) < len(file_list) / 2:  # Less than 50% failed
                print("⚠️  Continuing with partial download (more than 50% succeeded)")
            else:
                raise RuntimeError(f"Too many download failures: {len(errors)}/{len(file_list)}")

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
        user, repo = parse_fork_arg(args.fork)   # GitHub: user/repo

        # FIXED: More robust path detection for different environments
        if env == 'Lightning.ai':
            # Try common Lightning.ai paths
            possible_paths = [
                Path('/teamspace/studios/this_studio'),
                Path('/teamspace/repositories'),
                Path.home()
            ]
            for path in possible_paths:
                if path.exists() and os.access(path, os.W_OK):
                    reinitialize_paths(path)
                    break
            else:
                print("Warning: Using default home path, Lightning.ai path detection failed")
        elif env == 'Google Colab':
            reinitialize_paths(Path('/content'))
        elif env == 'Kaggle':
            reinitialize_paths(Path('/kaggle/working'))

        # download scripts files
        if not args.skip_download:
            print(f"📥 Downloading from {user}/{repo} (branch: {args.branch})")
            await download_files_async(args.lang, user, repo, args.branch, args.log)

        setup_module_folder()
        env_data = create_environment_data(env, args.lang, user, repo, args.branch)
        save_env_to_json(env_data, SETTINGS_PATH)

        # Display info after setup
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
            print(f"⚠️  Could not load seasonal display: {e}")
            print(f"✅ Setup complete! Environment: {env}, Language: {args.lang}")

    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        if args.log:
            import traceback
            traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(main_async())
