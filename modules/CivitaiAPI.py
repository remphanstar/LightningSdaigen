# ~ CivitaiAPI Module (V3) - Enhanced for 10WebUI System | by ANXETY ~

import json_utils as js
import requests
import time
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict, List, Tuple, Any
import hashlib
import os

# Environment and settings
osENV = os.environ
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}

try:
    SETTINGS_PATH = PATHS['settings_path']
except KeyError:
    SETTINGS_PATH = Path.cwd() / 'ANXETY' / 'settings.json'

class CivitAiAPI:
    """Enhanced CivitAI API client with comprehensive model support."""
    
    BASE_URL = "https://civitai.com/api/v1"
    DOWNLOAD_URL = "https://civitai.com/api/download"
    
    def __init__(self, token: str = None, timeout: int = 30):
        """Initialize CivitAI API client with enhanced configuration."""
        
        # Get token from multiple sources
        self.token = token or self._get_token()
        self.timeout = timeout
        self.session = requests.Session()
        
        # Configure session
        self.session.headers.update({
            'User-Agent': 'LightningSdaigen/3.0 (Enhanced WebUI Manager)',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        if self.token:
            self.session.headers['Authorization'] = f'Bearer {self.token}'
            self._log("CivitAI API initialized with authentication")
        else:
            self._log("CivitAI API initialized without authentication (limited access)", 'warning')
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests
        
        # Cache for API responses
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
    
    def _get_token(self) -> Optional[str]:
        """Get CivitAI token from multiple sources."""
        
        # Priority: Settings file -> Environment variable -> None
        try:
            token = js.read(SETTINGS_PATH, 'WIDGETS.civitai_token')
            if token:
                return token
                
            token = js.read(SETTINGS_PATH, 'ENVIRONMENT.civitai_api_token')
            if token:
                return token
        except Exception:
            pass
        
        # Fallback to environment variable
        return os.getenv('CIVITAI_API_TOKEN')
    
    def _log(self, message: str, level: str = 'info'):
        """Enhanced logging with timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        colors = {
            'info': '\033[34m',     # Blue
            'warning': '\033[33m',  # Yellow
            'error': '\033[31m',    # Red
            'success': '\033[32m',  # Green
            'debug': '\033[36m'     # Cyan
        }
        color = colors.get(level, '')
        reset = '\033[0m'
        print(f"{color}[{timestamp}] CIVITAI {level.upper()}: {message}{reset}")
    
    def _rate_limit(self):
        """Implement rate limiting to respect API limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key for API responses."""
        import json
        key_data = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid."""
        return time.time() - cache_entry['timestamp'] < self.cache_duration
    
    def _
