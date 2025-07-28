# Enhanced widgets-en.py with complete WebUI support

# Enhanced WEBUI_SELECTION with all implementations
WEBUI_SELECTION = {
    # Standard Stable Diffusion WebUIs
    'A1111': "--xformers --no-half-vae",
    'ComfyUI': "--dont-print-server",
    'Classic': "--persistent-patches --cuda-stream --pin-shared-memory",
    'Lightning.ai': "--xformers --no-half-vae",
    
    # Enhanced Forge Variants
    'Forge': "--xformers --cuda-stream --pin-shared-memory",
    'ReForge': "--xformers --cuda-stream --pin-shared-memory",
    'SD-UX': "--xformers --no-half-vae --theme dark",
    
    # Face Manipulation WebUIs
    'FaceFusion': "--execution-provider cuda --face-analyser buffalo_l --face-swapper inswapper_128",
    'RoopUnleashed': "--execution-provider cuda --frame-processor face_swapper --ui-layout horizontal",
    
    # Specialized WebUIs
    'DreamO': "--device cuda --precision fp16 --max-batch-size 4"
}

# WebUI Categories for better organization
WEBUI_CATEGORIES = {
    'Standard SD': ['A1111', 'Classic', 'Lightning.ai'],
    'Enhanced SD': ['Forge', 'ReForge', 'SD-UX'],
    'Node-Based': ['ComfyUI'],
    'Face Swap': ['FaceFusion', 'RoopUnleashed'],
    'Specialized': ['DreamO']
}

def create_webui_selector_widget(wm):
    """Create enhanced WebUI selector with categories."""
    from webui_utils import get_webui_features, is_webui_supported
    
    # Create categorized options
    all_options = []
    for category, webuis in WEBUI_CATEGORIES.items():
        all_options.extend(webuis)
    
    change_webui_widget = wm.factory.create_dropdown(
        all_options, 
        'WebUI:', 
        'A1111', 
        layout={'width': 'auto'}
    )
    
    return change_webui_widget

def enhanced_update_change_webui(change, widget_manager):
    """Enhanced WebUI change handling with feature detection."""
    try:
        webui = change['new']
        wm = widget_manager
        
        # Update command line arguments
        wm.widgets['commandline_arguments'].value = WEBUI_SELECTION.get(webui, '')
        
        # Get WebUI features
        from webui_utils import get_webui_features, is_webui_supported
        features = get_webui_features(webui)
        
        # Handle extension/custom nodes visibility
        supports_extensions = is_webui_supported(webui, 'extensions')
        is_comfy = webui == 'ComfyUI'
        is_face_swap = webui in ['FaceFusion', 'RoopUnleashed']
        
        # Update extension-related widgets
        if 'latest_extensions' in wm.widgets:
            wm.widgets['latest_extensions'].layout.display = 'none' if not supports_extensions else ''
            wm.widgets['latest_extensions'].value = supports_extensions
            
        if 'check_custom_nodes_deps' in wm.widgets:
            wm.widgets['check_custom_nodes_deps'].layout.display = '' if is_comfy else 'none'
            
        if 'theme_accent' in wm.widgets:
            wm.widgets['theme_accent'].layout.display = 'none' if is_face_swap else ''
            
        # Update Extensions URL description
        if 'Extensions_url' in wm.widgets:
            if is_comfy:
                wm.widgets['Extensions_url'].description = 'Custom Nodes:'
            elif supports_extensions:
                wm.widgets['Extensions_url'].description = 'Extensions:'
            else:
                wm.widgets['Extensions_url'].description = 'Add-ons:'
        
        # Handle model selection visibility based on WebUI capabilities
        supports_models = is_webui_supported(webui, 'models')
        supports_lora = is_webui_supported(webui, 'lora')
        supports_vae = is_webui_supported(webui, 'vae')
        supports_controlnet = is_webui_supported(webui, 'controlnet')
        
        # Show/hide model widgets based on support
        model_widgets = ['model', 'model_num', 'XL_models', 'inpainting_model']
        for widget_name in model_widgets:
            if widget_name in wm.widgets:
                wm.widgets[widget_name].layout.display = '' if supports_models else 'none'
        
        # Show/hide VAE widgets
        vae_widgets = ['vae', 'vae_num']
        for widget_name in vae_widgets:
            if widget_name in wm.widgets:
                wm.widgets[widget_name].layout.display = '' if supports_vae else 'none'
        
        # Show/hide LoRA widgets
        lora_widgets = ['lora']
        for widget_name in lora_widgets:
            if widget_name in wm.widgets:
                wm.widgets[widget_name].layout.display = '' if supports_lora else 'none'
        
        # Show/hide ControlNet widgets
        controlnet_widgets = ['controlnet', 'controlnet_num']
        for widget_name in controlnet_widgets:
            if widget_name in wm.widgets:
                wm.widgets[widget_name].layout.display = '' if supports_controlnet else 'none'
        
        # Display WebUI-specific information
        display_webui_info(webui, features)
        
    except Exception as e:
        print(f"Error in enhanced_update_change_webui: {e}")

def display_webui_info(webui, features):
    """Display information about the selected WebUI."""
    from webui_utils import get_webui_category
    
    category = get_webui_category(webui)
    
    info_messages = {
        'face_swap': f"🎭 {webui}: Face swapping and manipulation. Models and traditional SD features disabled.",
        'node_based': f"🖼️ {webui}: Node-based interface. Uses custom nodes instead of extensions.",
        'enhanced_sd': f"⚒️ {webui}: Enhanced Stable Diffusion with performance optimizations.",
        'specialized': f"🎨 {webui}: Specialized AI tool with unique capabilities.",
        'standard_sd': f"🖼️ {webui}: Standard Stable Diffusion interface."
    }
    
    if category in info_messages:
        print(f"\n{info_messages[category]}")
        
    # Display supported features
    supported_features = []
    for feature in ['models', 'lora', 'vae', 'controlnet', 'extensions']:
        if features.get(f'supports_{feature}', False):
            supported_features.append(feature.upper())
    
    if supported_features:
        print(f"✅ Supported: {', '.join(supported_features)}")

# Enhanced widget creation with WebUI-aware features
def create_enhanced_widgets(wm, SCRIPTS):
    """Create widgets with WebUI-specific feature detection."""
    
    # Create WebUI selector
    change_webui_widget = create_webui_selector_widget(wm)
    
    # Create model widgets (will be hidden for non-SD WebUIs)
    model_header = wm.factory.create_header('Model Selection')
    
    # Enhanced model selection with WebUI awareness
    try:
        enhanced_model_widgets = create_complete_enhanced_widgets(wm, SCRIPTS)
        model_bridge_widget = wm.factory.create_html(create_model_selection_bridge())
        model_widgets = enhanced_model_widgets + [model_bridge_widget]
    except:
        # Fallback to traditional model selection
        model_options = wm.read_model_data(f"{SCRIPTS}/_models-data.py", 'model')
        model_widget = wm.factory.create_select_multiple(model_options, 'Model:', ('none',))
        model_num_widget = wm.factory.create_text('Model Number:', '', 'Enter model numbers for batch download.')
        
        xl_models_widget = wm.factory.create_checkbox('SDXL Models', False)
        inpainting_model_widget = wm.factory.create_checkbox('Inpainting Models', False)
        
        wm.widgets.update({
            'model': model_widget,
            'model_num': model_num_widget,
            'XL_models': xl_models_widget,
            'inpainting_model': inpainting_model_widget
        })
        
        model_widgets = [model_widget, model_num_widget, xl_models_widget, inpainting_model_widget]
    
    # Store WebUI selector
    wm.widgets['change_webui'] = change_webui_widget
    
    # Connect WebUI change callback
    wm.factory.connect_widgets([(change_webui_widget, 'value')], 
                               lambda change, widget: enhanced_update_change_webui(change, wm))
    
    return {
        'webui_selector': change_webui_widget,
        'model_widgets': model_widgets
    }

# Integration instructions for the main widgets file
INTEGRATION_NOTES = """
To integrate this enhanced WebUI support:

1. Replace the WEBUI_SELECTION dictionary in your main widgets file
2. Replace the update_change_webui function with enhanced_update_change_webui
3. Add the create_enhanced_widgets function call
4. Update webui_utils.py with the enhanced version
5. Update webui-installer.py with the enhanced version

This provides:
- Complete support for 10 different WebUIs
- Automatic feature detection and UI adaptation
- Categorized WebUI selection
- WebUI-specific path configuration
- Enhanced face swapping capabilities through RoopUnleashed
- Better integration of existing partial implementations
"""
