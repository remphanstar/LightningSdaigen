""" CivitAi API Module (V2) | by ANXETY (FIXED VERSION) """

from urllib.parse import urlparse, parse_qs, urlencode
from typing import Optional, Union, Tuple, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
from PIL import Image
import requests
import json
import os
import re
import io


# === Logger Utility ===
class APILogger:
    """Colored logger for API events"""
    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def log(self, msg: str, level: str = "info"):
        if not self.verbose and level != "error":
            return
        colors = {"error": 31, "success": 32, "warning": 33, "info": 34}
        print(f"\033[{colors[level]}m[API {level.title()}]:\033[0m {msg}")


# === Model Data ===
@dataclass
class ModelData:
    download_url: str
    clean_url: str
    model_name: str
    model_type: str
    version_id: str
    model_id: str
    image_url: Optional[str] = None
    image_name: Optional[str] = None
    early_access: bool = False
    base_model: Optional[str] = None
    trained_words: Optional[List[str]] = None
    sha256: Optional[str] = None


# === Main API ===
class CivitAiAPI:
    """
    Usage Example:
        api = CivitAiAPI(token=token)
        result = api.validate_download(
            url='https://civitai.com/models/...',
            file_name='model.safetensors'
        )

        full_data = api.get_model_data(url='https://civitai.com/models/...')
    """

    BASE_URL = 'https://civitai.com/api/v1'
    SUPPORTED_TYPES = {'Checkpoint', 'TextualInversion', 'LORA'}    # For Save Preview
    IS_KAGGLE = os.getenv('KAGGLE_URL_BASE')

    def __init__(self, token: Optional[str] = None, log: bool = True):
        # FIXED: Remove hardcoded fake token, validate token format
        self.token = self._validate_token(token)
        self.logger = APILogger(verbose=log)
        
        if not self.token:
            self.logger.log("No valid CivitAI token provided. Some features may be limited.", "warning")

    def _validate_token(self, token: Optional[str]) -> Optional[str]:
        """Validate CivitAI token format."""
        if not token:
            return None
        
        # FIXED: Basic token validation (CivitAI tokens are typically 32 char hex)
        if len(token) < 20:
            self.logger.log("Token appears too short to be valid", "warning")
            return None
        
        # Remove whitespace and validate basic format
        clean_token = token.strip()
        if not re.match(r'^[a-fA-F0-9]{20,}$', clean_token):
            self.logger.log("Token format appears invalid (should be hexadecimal)", "warning")
            return None
        
        return clean_token

    # === Core Helpers ===
    def _build_url(self, endpoint: str) -> str:
        """Construct full API URL for given endpoint"""
        return f"{self.BASE_URL}/{endpoint}"

    def _get(self, url: str) -> Optional[Dict]:
        """Perform GET request and return JSON or None"""
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            # FIXED: Add timeout and better error handling
            res = requests.get(url, headers=headers, timeout=30)
            
            # FIXED: Handle rate limiting specifically
            if res.status_code == 429:
                self.logger.log("Rate limited by CivitAI API. Please wait before retrying.", "warning")
                return None
            elif res.status_code == 401:
                self.logger.log("Invalid or expired CivitAI token", "error")
                return None
            elif res.status_code == 404:
                self.logger.log(f"Model not found: {url}", "warning")
                return None
                
            res.raise_for_status()
            return res.json()
            
        except requests.exceptions.Timeout:
            self.logger.log(f"Request timeout for {url}", "error")
            return None
        except requests.exceptions.ConnectionError:
            self.logger.log(f"Connection error for {url}", "error")
            return None
        except requests.RequestException as e:
            self.logger.log(f"Request failed for {url}: {e}", "error")
            return None
        except json.JSONDecodeError:
            self.logger.log(f"Invalid JSON response from {url}", "error")
            return None

    def _extract_version_id(self, url: str) -> Optional[str]:
        """Extract version ID from various CivitAI URL formats"""
        if not url or not isinstance(url, str):
            self.logger.log("Invalid URL provided", "error")
            return None
            
        if not url.startswith(('http://', 'https://')):
            self.logger.log("Invalid URL format - must start with http:// or https://", "error")
            return None

        try:
            if 'modelVersionId=' in url:
                version_id = url.split('modelVersionId=')[1].split('&')[0]
                if version_id.isdigit():
                    return version_id

            if 'civitai.com/models/' in url:
                model_id = url.split('/models/')[1].split('/')[0].split('?')[0]
                if model_id.isdigit():
                    model_data = self._get(self._build_url(f"models/{model_id}"))
                    if model_data and 'modelVersions' in model_data and model_data['modelVersions']:
                        return str(model_data['modelVersions'][0].get('id'))

            if '/api/download/models/' in url:
                version_id = url.split('/api/download/models/')[1].split('?')[0]
                if version_id.isdigit():
                    return version_id

        except (IndexError, ValueError) as e:
            self.logger.log(f"Error parsing URL {url}: {e}", "error")
            return None

        self.logger.log(f"Could not extract version ID from URL: {url}", "error")
        return None

    def _process_url(self, download_url: str) -> Tuple[str, str]:
        """Sanitize and sign download URL"""
        try:
            parsed = urlparse(download_url)
            query = parse_qs(parsed.query)
            query.pop('token', None)  # Remove existing token
            clean_url = parsed._replace(query=urlencode(query, doseq=True)).geturl()
            
            # Only add token if we have a valid one
            if self.token:
                final_url = f"{clean_url}{'&' if '?' in clean_url else '?'}token={self.token}"
            else:
                final_url = clean_url
                self.logger.log("No token available - download may fail for private models", "warning")
            
            return clean_url, final_url
        except Exception as e:
            self.logger.log(f"Error processing URL {download_url}: {e}", "error")
            return download_url, download_url

    def _get_preview(self, images: List[Dict], name: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract a valid preview image URL and filename"""
        if not images:
            return None, None
            
        for img in images:
            if not isinstance(img, dict):
                continue
                
            url = img.get('url', '')
            if not url:
                continue
                
            # FIXED: Better NSFW filtering for Kaggle
            if self.IS_KAGGLE and img.get('nsfwLevel', 0) >= 4:
                continue
                
            # Skip animated/video content
            if any(url.lower().endswith(ext) for ext in ['.gif', '.mp4', '.webm']):
                continue
                
            try:
                ext = url.split('.')[-1].split('?')[0]
                if ext.lower() in ['jpg', 'jpeg', 'png', 'webp']:
                    preview_name = f"{Path(name).stem}.preview.{ext}"
                    return url, preview_name
            except (IndexError, AttributeError):
                continue
                
        return None, None

    def _parse_model_name(self, data: Dict, filename: Optional[str]) -> Tuple[str, str]:
        """Generate final model filename from metadata"""
        if not data.get('files') or not isinstance(data['files'], list) or not data['files']:
            raise ValueError("No files found in model data")
            
        original_name = data['files'][0].get('name', 'unknown.safetensors')
        model_type = data.get('model', {}).get('type', 'Unknown')
        
        if not filename:
            return model_type, original_name
            
        # Add extension if not present
        if '.' not in filename:
            ext = original_name.split('.')[-1] if '.' in original_name else 'safetensors'
            filename = f"{filename}.{ext}"
            
        return model_type, filename

    def _early_access_check(self, data: Dict) -> bool:
        """Check if model is gated behind Early Access"""
        ea = data.get('availability') == 'EarlyAccess' or data.get('earlyAccessEndsAt')
        if ea:
            model_id = data.get('modelId', 'unknown')
            version_id = data.get('id', 'unknown')
            self.logger.log(f"Model requires Early Access: https://civitai.com/models/{model_id}?modelVersionId={version_id}", "warning")
        return ea

    # === sdAIgen ===
    def validate_download(self, url: str, file_name: Optional[str] = None) -> Optional[ModelData]:
        """Validate and prepare download data for a CivitAI model."""
        if not url:
            self.logger.log("Empty URL provided", "error")
            return None
            
        version_id = self._extract_version_id(url)
        if not version_id:
            return None

        data = self._get(self._build_url(f"model-versions/{version_id}"))
        if not data:
            return None

        if self._early_access_check(data):
            return None

        try:
            model_type, name = self._parse_model_name(data, file_name)
            
            # Check if download URL exists
            download_url = data.get('downloadUrl')
            if not download_url:
                self.logger.log("No download URL found in model data", "error")
                return None
                
            clean_url, full_url = self._process_url(download_url)

            preview_url, preview_name = (None, None)
            if model_type in self.SUPPORTED_TYPES:
                preview_url, preview_name = self._get_preview(data.get('images', []), name)

            return ModelData(
                download_url=full_url,
                clean_url=clean_url,
                model_name=name,
                model_type=model_type,
                version_id=str(data.get('id', version_id)),
                model_id=str(data.get('modelId', 'unknown')),
                early_access=False,
                image_url=preview_url,
                image_name=preview_name,
                base_model=data.get("baseModel"),
                trained_words=data.get("trainedWords", []),
                sha256=data.get("files", [{}])[0].get("hashes", {}).get("SHA256")
            )
        except Exception as e:
            self.logger.log(f"Error processing model data: {e}", "error")
            return None

    # === General ===
    def get_model_data(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch full model version metadata from CivitAI by URL"""
        version_id = self._extract_version_id(url)
        if not version_id:
            self.logger.log(f"Cannot get model data — failed to extract version ID from URL: {url}", "error")
            return None

        data = self._get(self._build_url(f"model-versions/{version_id}"))
        if not data:
            self.logger.log(f"Failed to retrieve model version data for ID: {version_id}", "error")

        return data

    def get_model_versions(self, model_id: str) -> Optional[List[Dict]]:
        """Get all available versions of a model by ID"""
        if not model_id or not model_id.isdigit():
            self.logger.log("Invalid model ID provided", "error")
            return None
            
        data = self._get(self._build_url(f"models/{model_id}"))
        return data.get("modelVersions", []) if data else None

    def find_by_sha256(self, sha256: str) -> Optional[Dict]:
        """Find model version data by SHA256 hash"""
        if not sha256 or len(sha256) != 64:
            self.logger.log("Invalid SHA256 hash format", "error")
            return None
            
        return self._get(self._build_url(f"model-versions/by-hash/{sha256}"))

    def download_preview_image(self, model_data: ModelData, save_path: Optional[Union[str, Path]] = None, resize: bool = False):
        """
        Download and save model preview image.

        Args:
            model_data: ModelData object with preview metadata
            save_path: Directory path (str or Path) where image will be saved. Defaults to current directory.
            resize: If True, resize image to 512px max (default: False)
        """
        if model_data is None:
            self.logger.log("ModelData is None — skipping download_preview_image", "warning")
            return

        if not model_data.image_url:
            self.logger.log("No preview image URL available", "warning")
            return

        try:
            save_dir = Path(save_path) if save_path else Path.cwd()
            save_dir.mkdir(parents=True, exist_ok=True)
            file_path = save_dir / model_data.image_name

            if file_path.exists():
                self.logger.log(f"Preview already exists: {file_path}", "info")
                return

            # FIXED: Add timeout and better error handling
            res = requests.get(model_data.image_url, timeout=30)
            res.raise_for_status()
            
            img_data = self._resize_image(res.content) if resize else io.BytesIO(res.content)
            file_path.write_bytes(img_data.read())
            self.logger.log(f"Saved preview: {file_path}", "success")
            
        except requests.exceptions.Timeout:
            self.logger.log("Timeout downloading preview image", "error")
        except requests.RequestException as e:
            self.logger.log(f"Failed to download preview: {e}", "error")
        except OSError as e:
            self.logger.log(f"Failed to save preview: {e}", "error")
        except Exception as e:
            self.logger.log(f"Unexpected error downloading preview: {e}", "error")

    def _resize_image(self, raw: bytes, size: int = 512) -> io.BytesIO:
        """Resize image to target size while preserving aspect ratio"""
        try:
            img = Image.open(io.BytesIO(raw))
            w, h = img.size
            
            # Only resize if image is larger than target size
            if w <= size and h <= size:
                return io.BytesIO(raw)
                
            new_size = (size, int(h * size / w)) if w > h else (int(w * size / h), size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            img.save(output, format='PNG', optimize=True)
            output.seek(0)
            return output
        except Exception as e:
            self.logger.log(f"Resize failed: {e}", "warning")
            return io.BytesIO(raw)

    def save_model_info(self, model_data: ModelData, save_path: Optional[Union[str, Path]] = None):
        """
        Save model metadata to a JSON file.

        Args:
            model_data: ModelData object
            save_path: Directory path (str or Path) to save metadata. Defaults to current directory.
        """
        if model_data is None:
            self.logger.log("ModelData is None — skipping save_model_info", "warning")
            return

        try:
            save_dir = Path(save_path) if save_path else Path.cwd()
            save_dir.mkdir(parents=True, exist_ok=True)
            info_file = save_dir / f"{Path(model_data.model_name).stem}.json"

            if info_file.exists():
                self.logger.log(f"Model info already exists: {info_file}", "info")
                return

            base_mapping = {
                'SD 1': 'SD1', 'SD 1.5': 'SD1', 'SD 2': 'SD2', 'SD 3': 'SD3',
                'SDXL': 'SDXL', 'Pony': 'SDXL', 'Illustrious': 'SDXL',
            }
            
            info = {
                "model_type": model_data.model_type,
                "sd_version": next((v for k, v in base_mapping.items() if k in (model_data.base_model or '')), ''),
                "modelId": model_data.model_id,
                "modelVersionId": model_data.version_id,
                "activation_text": ', '.join(model_data.trained_words or []),
                "sha256": model_data.sha256,
                "downloaded_at": str(Path().cwd())  # Add download timestamp
            }
            
            info_file.write_text(json.dumps(info, indent=4))
            self.logger.log(f"Saved model info: {info_file}", "success")
            
        except OSError as e:
            self.logger.log(f"Failed to save model info: {e}", "error")
        except Exception as e:
            self.logger.log(f"Unexpected error saving model info: {e}", "error")
