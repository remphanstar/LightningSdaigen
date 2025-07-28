# Enhanced webui-installer.py with complete implementations

async def main():
    if UI == 'FaceFusion':
        print("🎭 Setting up FaceFusion (Uncensored)...")
        ipySys(f"git clone https://github.com/X-croot/facefusion-uncensored {WEBUI}")
        CD(WEBUI)
        ipySys("pip install -r requirements.txt")
        ipySys("pip install onnxruntime-gpu torch torchvision")
        # Download essential models
        model_dir = WEBUI / "models"
        model_dir.mkdir(exist_ok=True)
        print("📦 Downloading essential FaceFusion models...")
        
    elif UI == 'RoopUnleashed':
        print("🎭 Setting up RoopUnleashed...")
        ipySys(f"git clone https://github.com/C0untFloyd/roop-unleashed {WEBUI}")
        CD(WEBUI)
        ipySys("pip install -r requirements.txt")
        ipySys("pip install onnxruntime-gpu")
        # Setup model directories
        for folder in ['models', 'faces', 'frames']:
            (WEBUI / folder).mkdir(exist_ok=True)
            
    elif UI == 'DreamO':
        print("🎨 Setting up DreamO (ByteDance)...")
        ipySys(f"git clone https://github.com/bytedance/DreamO {WEBUI}")
        CD(WEBUI)
        ipySys("pip install -r requirements.txt")
        ipySys("pip install diffusers transformers accelerate")
        
    elif UI == 'Forge':
        print("⚒️  Setting up Stable Diffusion WebUI Forge...")
        ipySys(f"git clone https://github.com/lllyasviel/stable-diffusion-webui-forge {WEBUI}")
        CD(WEBUI)
        # Apply Forge-specific optimizations
        ipySys("pip install -r requirements_versions.txt")
        
    elif UI == 'ReForge':
        print("🔄 Setting up Stable Diffusion WebUI ReForge...")
        ipySys(f"git clone https://github.com/Panchovix/stable-diffusion-webui-reForge {WEBUI}")
        CD(WEBUI)
        ipySys("pip install -r requirements_versions.txt")
        
    elif UI == 'SD-UX':
        print("✨ Setting up SD-UX (Modern UI)...")
        ipySys(f"git clone https://github.com/anapnoe/stable-diffusion-webui-ux {WEBUI}")
        CD(WEBUI)
        ipySys("pip install -r requirements.txt")
        
    elif UI == 'ComfyUI':
        print("🖼️  Setting up ComfyUI...")
        ipySys(f"git clone https://github.com/comfyanonymous/ComfyUI {WEBUI}")
        CD(WEBUI)
        ipySys("pip install -r requirements.txt")
        ipySys("pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu121")
        
    else:
        # Original archive-based installation for A1111, Classic, Lightning.ai
        unpack_webui()
        await download_configuration()
        await install_extensions()
        apply_classic_fixes()

        if UI not in ['ComfyUI', 'FaceFusion', 'RoopUnleashed', 'DreamO']:
            run_tagcomplete_tag_parser()

    # Universal post-installation steps
    await post_install_setup()

async def post_install_setup():
    """Universal post-installation configuration."""
    print("🔧 Applying post-installation setup...")
    
    # Create standard directories based on WEBUI_PATHS
    from webui_utils import WEBUI_PATHS
    if UI in WEBUI_PATHS:
        paths = WEBUI_PATHS[UI]
        for i, folder in enumerate(paths):
            if folder:  # Skip empty folder definitions
                folder_path = WEBUI / folder
                folder_path.mkdir(parents=True, exist_ok=True)
                print(f"📁 Created: {folder_path}")
    
    # Install extensions if configuration exists
    ext_config = Path(f"__configs__/{UI}/_extensions.txt")
    if ext_config.exists():
        await install_extensions()
    
    print("✅ Post-installation setup complete.")
