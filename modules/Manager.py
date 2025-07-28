# ~ Manager Module (V3) - Enhanced for 10WebUI System | by ANXETY ~

import json_utils as js              # JSON utilities
from urllib.parse import urlparse, unquote
from pathlib import Path
import subprocess
import tempfile
import zipfile
import shlex
import sys
import re
import os
import time
import hashlib
import requests
from typing import Optional, Tuple, Dict, List

# Safe import of CivitaiAPI with fallback
try:
    from CivitaiAPI import CivitAiAPI
    CIVITAI_AVAILABLE = True
except ImportError:
    print("⚠️ CivitaiAPI not available, using fallback")
    CIVITAI_AVAILABLE = False
    class CivitAiAPI:
        def __init__(self, token): self.token = token
        def validate_download(self, url, filename=None): return None

osENV = os.environ
CD = os.chdir

# Constants with enhanced path handling
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}

try:
    HOME = PATHS['home_path']
    SCR_PATH = PATHS['scr_path']
    SETTINGS_PATH = PATHS['settings_path']
    VENV_PATH = PATHS.get('venv_path', HOME / 'venv')
except KeyError as e:
    print(f"⚠️ Missing environment path: {e}")
    # Fallback to current directory structure
    HOME = Path.cwd()
    SCR_PATH = HOME / 'ANXETY'
    SETTINGS_PATH = SCR_PATH / 'settings.json'
    VENV_PATH = HOME / 'venv'

# Enhanced token handling with multiple sources
def get_tokens():
    """Get API tokens from multiple sources with priority."""
    tokens = {
        'civitai': None,
        'huggingface': None
    }
    
    # Priority: Environment variables -> Settings file -> Default
    try:
        # Try settings file first
        tokens['civitai'] = js.read(SETTINGS_PATH, 'WIDGETS.civitai_token') or js.read(SETTINGS_PATH, 'ENVIRONMENT.civitai_api_token')
        tokens['huggingface'] = js.read(SETTINGS_PATH, 'WIDGETS.huggingface_token')
    except:
        pass
    
    # Fallback to environment variables
    tokens['civitai'] = tokens['civitai'] or os.getenv('CIVITAI_API_TOKEN', '')
    tokens['huggingface'] = tokens['huggingface'] or os.getenv('HUGGINGFACE_TOKEN', '')
    
    return tokens

TOKENS = get_tokens()
CAI_TOKEN = TOKENS['civitai']
HF_TOKEN = TOKENS['huggingface']

# ========================= Enhanced Logging ========================

class Logger:
    """Enhanced logging with color support and levels."""
    
    COLORS = {
        'error': '\033[31m',    # Red
        'warning': '\033[33m',  # Yellow
        'success': '\033[32m',  # Green
        'info': '\033[34m',     # Blue
        'debug': '\033[36m',    # Cyan
        'reset': '\033[0m'      # Reset
    }
    
    @classmethod
    def log(cls, message: str, level: str = 'info', show: bool = True, prefix: str = "MANAGER"):
        """Enhanced logging with color and timestamp."""
        if not show:
            return
            
        color = cls.COLORS.get(level.lower(), '')
        reset = cls.COLORS['reset']
        timestamp = time.strftime("%H:%M:%S")
        
        level_text = f"[{level.upper()}]"
        formatted_message = f"{color}[{timestamp}] {prefix} {level_text}: {message}{reset}"
        
        print(formatted_message)
    
    @classmethod
    def error(cls, message: str, show: bool = True):
        cls.log(message, 'error', show)
    
    @classmethod
    def warning(cls, message: str, show: bool = True):
        cls.log(message, 'warning', show)
    
    @classmethod
    def success(cls, message: str, show: bool = True):
        cls.log(message, 'success', show)
    
    @classmethod
    def info(cls, message: str, show: bool = True):
        cls.log(message, 'info', show)
    
    @classmethod
    def debug(cls, message: str, show: bool = True):
        cls.log(message, 'debug', show)

# Enhanced error handling decorator
def handle_errors(func):
    """Enhanced error handling with detailed logging."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            Logger.warning("Operation cancelled by user")
            return None
        except Exception as e:
            Logger.error(f"{func.__name__} failed: {str(e)}")
            if hasattr(e, '__traceback__'):
                import traceback
                Logger.debug(f"Traceback: {traceback.format_exc()}")
            return None
    return wrapper

# ===================== Enhanced Core Utilities =====================

def get_file_hash(file_path: Path, algorithm: str = 'sha256') -> Optional[str]:
    """Calculate file hash for verification."""
    try:
        hash_func = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        Logger.error(f"Hash calculation failed: {e}")
        return None

def validate_url(url: str) -> bool:
    """Enhanced URL validation."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def get_file_size(url: str) -> Optional[int]:
    """Get file size from URL headers."""
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            return int(response.headers.get('content-length', 0))
    except Exception as e:
        Logger.debug(f"Could not get file size: {e}")
    return None

def format_bytes(bytes_size: int) -> str:
    """Format bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f}PB"

def _get_file_name(url: str, is_git: bool = False) -> Optional[str]:
    """Enhanced filename extraction with better handling."""
    
    # Special handling for known platforms
    if 'civitai.com' in url:
        # CivitAI URLs need special handling
        if CIVITAI_AVAILABLE and CAI_TOKEN:
            try:
                api = CivitAiAPI(CAI_TOKEN)
                result = api.validate_download(url)
                if result and 'filename' in result:
                    return result['filename']
            except Exception:
                pass
        return None
    
    if 'drive.google.com' in url:
        # Google Drive files need special handling
        return None
    
    if 'huggingface.co' in url:
        # HuggingFace files
        try:
            # Extract filename from HF URL pattern
            if '/resolve/' in url:
                filename = url.split('/')[-1]
                return unquote(filename) if filename else None
        except Exception:
            pass
    
    # Standard URL filename extraction
    try:
        parsed = urlparse(url)
        filename = Path(parsed.path).name
        
        if not filename:
            return None
        
        # For git repos, don't add extensions
        if is_git:
            return filename
        
        # Ensure file has extension
        if not Path(filename).suffix:
            # Try to detect from URL or content-type
            suffix = Path(parsed.path).suffix
            if suffix:
                filename += suffix
            else:
                return None
                
        return unquote(filename)
    except Exception:
        return None

def handle_path_and_filename(parts: List[str], url: str, is_git: bool = False) -> Tuple[Optional[Path], Optional[str]]:
    """Enhanced path and filename handling with validation."""
    
    if len(parts) < 2:
        Logger.error("Invalid command format. Expected: <url> <path> [filename]")
        return None, None
    
    url = parts[0]
    path_str = parts[1]
    
    # Validate URL
    if not validate_url(url):
        Logger.error(f"Invalid URL: {url}")
        return None, None
    
    # Handle path
    try:
        path = Path(path_str).expanduser().resolve()
        
        # Ensure directory exists
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            Logger.info(f"Created directory: {path}")
        
        if not path.is_dir():
            Logger.error(f"Path is not a directory: {path}")
            return None, None
            
    except Exception as e:
        Logger.error(f"Invalid path: {path_str} - {e}")
        return None, None
    
    # Handle filename
    filename = None
    if len(parts) >= 3:
        # Explicit filename provided
        filename = parts[2]
    else:
        # Try to extract from URL
        filename = _get_file_name(url, is_git)
    
    return path, filename

# ===================== Enhanced Download Functions =====================

def get_download_command(url: str, output_path: Path, filename: str = None, 
                        show_progress: bool = True, resume: bool = True) -> List[str]:
    """Generate optimized download command based on available tools."""
    
    output_file = output_path / filename if filename else output_path / "download"
    
    # Try aria2c first (fastest for large files)
    if subprocess.run(['which', 'aria2c'], capture_output=True).returncode == 0:
        cmd = [
            'aria2c',
            '--console-log-level=warn' if not show_progress else '--console-log-level=info',
            '--summary-interval=1',
            '--download-result=hide',
            f'--dir={output_path}',
            '--max-tries=3',
            '--retry-wait=3',
            '--timeout=30',
            '--max-connection-per-server=8',
            '--split=8'
        ]
        
        if filename:
            cmd.append(f'--out={filename}')
        if resume:
            cmd.append('--continue=true')
        if HF_TOKEN and 'huggingface.co' in url:
            cmd.extend(['--header', f'Authorization: Bearer {HF_TOKEN}'])
        
        cmd.append(url)
        return cmd
    
    # Fallback to curl
    elif subprocess.run(['which', 'curl'], capture_output=True).returncode == 0:
        cmd = ['curl', '-L', '--fail', '--retry', '3', '--retry-delay', '3']
        
        if show_progress:
            cmd.append('--progress-bar')
        else:
            cmd.append('--silent')
            
        if resume:
            cmd.append('--continue-at')
            cmd.append('-')
            
        if HF_TOKEN and 'huggingface.co' in url:
            cmd.extend(['-H', f'Authorization: Bearer {HF_TOKEN}'])
        
        cmd.extend(['-o', str(output_file), url])
        return cmd
    
    # Final fallback to wget
    elif subprocess.run(['which', 'wget'], capture_output=True).returncode == 0:
        cmd = ['wget', '--tries=3', '--timeout=30']
        
        if not show_progress:
            cmd.append('--quiet')
        if resume:
            cmd.append('--continue')
        if HF_TOKEN and 'huggingface.co' in url:
            cmd.extend(['--header', f'Authorization: Bearer {HF_TOKEN}'])
        
        cmd.extend(['-O', str(output_file), url])
        return cmd
    
    else:
        Logger.error("No suitable download tool found (aria2c, curl, or wget required)")
        return None

@handle_errors
def m_download(command: str, show_progress: bool = True, **kwargs) -> bool:
    """Enhanced download function with comprehensive error handling and progress."""
    
    if not command or not command.strip():
        Logger.error("Empty download command")
        return False
    
    # Parse command
    parts = shlex.split(command.strip())
    path, filename = handle_path_and_filename(parts, parts[0])
    
    if not path:
        return False
    
    url = parts[0]
    
    # Get file info
    file_size = get_file_size(url)
    if file_size:
        Logger.info(f"File size: {format_bytes(file_size)}")
    
    # Generate download command
    download_cmd = get_download_command(url, path, filename, show_progress)
    if not download_cmd:
        return False
    
    Logger.info(f"Downloading: {url}")
    if filename:
        Logger.info(f"Output: {path / filename}")
    
    try:
        # Execute download
        start_time = time.time()
        result = subprocess.run(download_cmd, cwd=str(path), timeout=3600)  # 1 hour timeout
        duration = time.time() - start_time
        
        if result.returncode == 0:
            output_file = path / filename if filename else path / "download"
            if output_file.exists():
                actual_size = output_file.stat().st_size
                speed = actual_size / duration if duration > 0 else 0
                Logger.success(f"Download completed in {duration:.1f}s ({format_bytes(int(speed))}/s)")
                
                # Verify file integrity if possible
                if file_size and actual_size != file_size:
                    Logger.warning(f"Size mismatch: expected {format_bytes(file_size)}, got {format_bytes(actual_size)}")
                
                return True
            else:
                Logger.error("Download completed but file not found")
                return False
        else:
            Logger.error(f"Download failed with exit code: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        Logger.error("Download timeout (1 hour limit)")
        return False
    except Exception as e:
        Logger.error(f"Download error: {e}")
        return False

@handle_errors
def m_clone(command: str, show_progress: bool = True, **kwargs) -> bool:
    """Enhanced git clone function with comprehensive error handling."""
    
    if not command or not command.strip():
        Logger.error("Empty clone command")
        return False
    
    # Parse command
    parts = shlex.split(command.strip())
    if len(parts) < 2:
        Logger.error("Invalid clone command format. Expected: <git_url> <destination>")
        return False
    
    git_url = parts[0]
    destination = Path(parts[1]).expanduser().resolve()
    
    # Validate git URL
    if not any(domain in git_url for domain in ['github.com', 'gitlab.com', 'bitbucket.org', 'huggingface.co']):
        Logger.warning(f"Unusual git URL: {git_url}")
    
    # Prepare destination
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove existing directory if it exists and is not empty
        if destination.exists():
            if any(destination.iterdir()):
                Logger.warning(f"Destination exists and is not empty: {destination}")
                import shutil
                shutil.rmtree(destination)
                Logger.info(f"Removed existing directory: {destination}")
    except Exception as e:
        Logger.error(f"Could not prepare destination: {e}")
        return False
    
    # Build git command
    git_cmd = ['git', 'clone']
    
    # Add options for better performance and reliability
    git_cmd.extend([
        '--depth', '1',  # Shallow clone for speed
        '--single-branch',  # Only clone default branch
        '--recurse-submodules',  # Include submodules
        '--jobs', '4'  # Parallel submodule fetching
    ])
    
    if not show_progress:
        git_cmd.append('--quiet')
    
    # Add authentication for private repos
    if HF_TOKEN and 'huggingface.co' in git_url:
        # Insert token into HuggingFace URL
        if git_url.startswith('https://huggingface.co/'):
            git_url = git_url.replace('https://huggingface.co/', f'https://oauth2:{HF_TOKEN}@huggingface.co/')
    
    git_cmd.extend([git_url, str(destination)])
    
    Logger.info(f"Cloning: {parts[0]}")  # Log original URL for security
    Logger.info(f"Destination: {destination}")
    
    try:
        start_time = time.time()
        result = subprocess.run(git_cmd, timeout=1800, capture_output=not show_progress, text=True)  # 30 min timeout
        duration = time.time() - start_time
        
        if result.returncode == 0:
            Logger.success(f"Clone completed in {duration:.1f}s")
            
            # Verify clone success
            if destination.exists() and any(destination.iterdir()):
                # Get repo info
                try:
                    info_result = subprocess.run(
                        ['git', 'log', '--oneline', '-1'], 
                        cwd=str(destination), 
                        capture_output=True, 
                        text=True, 
                        timeout=10
                    )
                    if info_result.returncode == 0:
                        Logger.info(f"Latest commit: {info_result.stdout.strip()}")
                except Exception:
                    pass
                
                return True
            else:
                Logger.error("Clone completed but destination is empty")
                return False
        else:
            error_msg = result.stderr if result.stderr else "Unknown git error"
            Logger.error(f"Clone failed: {error_msg}")
            return False
            
    except subprocess.TimeoutExpired:
        Logger.error("Clone timeout (30 minutes limit)")
        return False
    except Exception as e:
        Logger.error(f"Clone error: {e}")
        return False

# ===================== Enhanced Utility Functions =====================

@handle_errors
def extract_archive(archive_path: Path, destination: Path, remove_archive: bool = True) -> bool:
    """Enhanced archive extraction with support for multiple formats."""
    
    if not archive_path.exists():
        Logger.error(f"Archive not found: {archive_path}")
        return False
    
    Logger.info(f"Extracting: {archive_path.name}")
    destination.mkdir(parents=True, exist_ok=True)
    
    try:
        if archive_path.suffix.lower() in ['.zip']:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(destination)
                
        elif archive_path.suffix.lower() in ['.tar', '.gz', '.bz2', '.xz']:
            import tarfile
            with tarfile.open(archive_path, 'r:*') as tar_ref:
                tar_ref.extractall(destination)
        else:
            Logger.error(f"Unsupported archive format: {archive_path.suffix}")
            return False
        
        Logger.success(f"Extraction completed: {destination}")
        
        if remove_archive:
            archive_path.unlink()
            Logger.info(f"Removed archive: {archive_path.name}")
        
        return True
        
    except Exception as e:
        Logger.error(f"Extraction failed: {e}")
        return False

@handle_errors
def verify_installation() -> Dict[str, bool]:
    """Verify system requirements and available tools."""
    
    tools = {
        'git': False,
        'aria2c': False,
        'curl': False,
        'wget': False,
        'python': False,
        'pip': False
    }
    
    for tool in tools.keys():
        try:
            result = subprocess.run(['which', tool], capture_output=True, timeout=5)
            tools[tool] = result.returncode == 0
        except Exception:
            tools[tool] = False
    
    # Special check for Python and pip
    try:
        tools['python'] = sys.version_info >= (3, 8)
        import pip
        tools['pip'] = True
    except ImportError:
        tools['pip'] = False
    
    return tools

# ===================== Enhanced Manager Class =====================

class DownloadManager:
    """Enhanced download manager with queue support and progress tracking."""
    
    def __init__(self):
        self.queue = []
        self.completed = []
        self.failed = []
        self.stats = {
            'total_downloaded': 0,
            'total_failed': 0,
            'total_bytes': 0,
            'start_time': None
        }
    
    def add_download(self, url: str, destination: Path, filename: str = None):
        """Add download to queue."""
        self.queue.append({
            'url': url,
            'destination': destination,
            'filename': filename,
            'added_at': time.time()
        })
    
    def add_clone(self, git_url: str, destination: Path):
        """Add git clone to queue."""
        self.queue.append({
            'git_url': git_url,
            'destination': destination,
            'is_git': True,
            'added_at': time.time()
        })
    
    def process_queue(self, show_progress: bool = True) -> Dict[str, int]:
        """Process all items in queue."""
        if not self.queue:
            Logger.info("Download queue is empty")
            return {'completed': 0, 'failed': 0}
        
        self.stats['start_time'] = time.time()
        Logger.info(f"Processing {len(self.queue)} items in download queue")
        
        for i, item in enumerate(self.queue, 1):
            Logger.info(f"Processing item {i}/{len(self.queue)}")
            
            try:
                if item.get('is_git'):
                    # Git clone
                    command = f"{item['git_url']} {item['destination']}"
                    success = m_clone(command, show_progress)
                else:
                    # Regular download
                    filename = item.get('filename', '')
                    command = f"{item['url']} {item['destination']}"
                    if filename:
                        command += f" {filename}"
                    success = m_download(command, show_progress)
                
                if success:
                    self.completed.append(item)
                    self.stats['total_downloaded'] += 1
                else:
                    self.failed.append(item)
                    self.stats['total_failed'] += 1
                    
            except Exception as e:
                Logger.error(f"Queue processing error: {e}")
                self.failed.append(item)
                self.stats['total_failed'] += 1
        
        # Clear queue after processing
        original_count = len(self.queue)
        self.queue.clear()
        
        # Report results
        duration = time.time() - self.stats['start_time']
        Logger.success(f"Queue processing completed in {duration:.1f}s")
        Logger.info(f"Results: {self.stats['total_downloaded']} completed, {self.stats['total_failed']} failed")
        
        return {
            'completed': self.stats['total_downloaded'],
            'failed': self.stats['total_failed'],
            'duration': duration
        }

# ===================== Module Initialization =====================

def initialize_manager():
    """Initialize the Manager module with system verification."""
    Logger.info("Initializing Enhanced Download Manager")
    
    # Verify system requirements
    tools = verify_installation()
    missing_tools = [tool for tool, available in tools.items() if not available]
    
    if missing_tools:
        Logger.warning(f"Missing tools: {', '.join(missing_tools)}")
        Logger.info("Some functionality may be limited")
    else:
        Logger.success("All required tools are available")
    
    # Log token status
    if CAI_TOKEN:
        Logger.success("CivitAI token configured")
    else:
        Logger.info("CivitAI token not set (some downloads may fail)")
    
    if HF_TOKEN:
        Logger.success("HuggingFace token configured")
    
    Logger.success("Enhanced Download Manager initialized")

# Initialize on import
initialize_manager()

# Export main functions for backward compatibility
__all__ = ['m_download', 'm_clone', 'DownloadManager', 'Logger', 'extract_archive', 'verify_installation']
