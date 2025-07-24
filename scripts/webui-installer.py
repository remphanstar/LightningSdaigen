# ~ webui-installer.py | by ANXETY ~

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


# ==================== WEBUI OPERATIONS ====================

async def _download_file(url, directory=WEBUI, filename=None):
    # ... (rest of the function is the same)

async def get_extensions_list():
    # ... (rest of the function is the same)


# ================= CONFIGURATION HANDLING =================

# ... (CONFIG_MAP remains the same)

async def download_configuration():
    # ... (rest of the function is the same)

# ================= EXTENSIONS INSTALLATION ================

async def install_extensions():
    # ... (rest of the function is the same)


# =================== WEBUI SETUP & FIXES ==================

def unpack_webui():
    """Download and extract WebUI archive."""
    zip_path = HOME / f"{UI}.zip"
    m_download(f"{REPO_URL} {HOME} {UI}.zip")
    ipySys(f"unzip -q -o {zip_path} -d {WEBUI} && rm -rf {zip_path}")

def apply_classic_fixes():
    # ... (rest of the function is the same)

def run_tagcomplete_tag_parser():
    ipyRun('run', f"{WEBUI}/tagcomplete-tags-parser.py")

# ======================== MAIN CODE =======================

async def main():
    if UI == 'FaceFusion':
        ipySys(f"git clone https://github.com/X-croot/facefusion-uncensored {WEBUI}")
        CD(WEBUI)
        ipySys("pip install -r requirements.txt")
    elif UI == 'DreamO':
        ipySys(f"git clone https://github.com/bytedance/DreamO {WEBUI}")
        CD(WEBUI)
        ipySys("pip install -r requirements.txt")
    else:
        unpack_webui()
        await download_configuration()
        await install_extensions()
        apply_classic_fixes()

        if UI != 'ComfyUI':
            run_tagcomplete_tag_parser()

if __name__ == '__main__':
    with capture.capture_output():
        asyncio.run(main())
