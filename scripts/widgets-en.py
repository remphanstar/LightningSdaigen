# ~ widgets-en.py | by ANXETY - Enhanced with Complete 10WebUI Support ~

import json_utils as js
from pathlib import Path
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
import os

# Safe import with fallbacks
try:
    from webui_utils import (get_webui_features, is_webui_supported, get_webui_category, 
                           validate_webui_selection, get_available_webuis, 
                           get_webuis_by_category, update_current_webui)
    WEBUI_UTILS_AVAILABLE = True
    print("✅ Enhanced WebUI utilities loaded")
except ImportError as e:
    print(f"⚠️ Enhanced utilities not available: {e}")
    WEBUI_UTILS_AVAILABLE = False
    # Create fallback functions
    def get_webui_features(ui): return {'supports_models': True, 'supports_extensions': True}
    def is_webui_supported(ui, feature): return True
    def get_webui_category(ui): return 'standard_sd'
    def validate_webui_selection(ui): return ui in ['A1111', 'ComfyUI', 'Classic', 'Lightning.ai']
    def get_available_webuis(): return ['A1111', 'ComfyUI', 'Classic', 'Lightning.ai']
    def get_webuis_by_category(): return {'standard_sd': ['A1111', 'ComfyUI', 'Classic', 'Lightning.ai']}
    def update_current_webui(ui): js.save(SETTINGS_PATH, 'WEBUI.current', ui)

# Environment paths
osENV = os.environ
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME = PATHS['home_path']
SETTINGS_PATH = PATHS['settings_path']

# ==================== ENHANCED WEBUI SELECTION ====================

# ENHANCED: Complete WebUI selection with all 10 WebUIs
WEBUI_SELECTION = {
    'A1111': '--listen --enable-insecure-extension-access --theme dark --no-half-vae --no-hashing',
    'ComfyUI': '--listen --port 7860',  
    'Classic': '--listen --enable-insecure-extension-access --theme dark --no-half-vae --no-hashing --gradio-queue',
    'Lightning.ai': '--listen --enable-insecure-extension-access --theme dark --no-half-vae --no-hashing',
    'Forge': '--listen --enable-insecure-extension-access --theme dark --cuda-malloc --pin-shared-memory',
    'ReForge': '--listen --enable-insecure-extension-access --theme dark --cuda-malloc --attention-pytorch',
    'SD-UX': '--listen --enable-insecure-extension-access --theme dark --gradio-img2img-tool color-sketch',
    'FaceFusion': '--ui-layouts 1 --execution-providers cuda',
    'RoopUnleashed': '--execution-provider cuda --max-memory 8',
    'DreamO': '--host 0.0.0.0 --port 7860'
}

# ENHANCED: WebUI Categories for organized display
WEBUI_CATEGORIES = {
    'Standard SD': ['A1111', 'Classic', 'Lightning.ai'],
    'Enhanced SD': ['Forge', 'ReForge', 'SD-UX'],
    'Node-Based': ['ComfyUI'],
    'Face Swap': ['FaceFusion', 'RoopUnleashed'],
    'Specialized': ['DreamO']
}

# Load CSS styles
try:
    css_path = PATHS['scr_path'] / 'CSS' / 'main-widgets.css'
    if css_path.exists():
        with open(css_path, 'r') as f:
            css_content = f.read()
        display(HTML(f'<style>{css_content}</style>'))
    else:
        # Fallback basic styles
        display(HTML('''
        <style>
        .widget-container { margin: 10px 0; }
        .category-header { font-weight: bold; color: #4CAF50; margin-top: 15px; }
        .webui-info { background: #f0f0f0; padding: 8px; border-radius: 4px; margin: 5px 0; }
        </style>
        '''))
except Exception as e:
    print(f"⚠️ Could not load CSS: {e}")

# ==================== ENHANCED WIDGET FUNCTIONS ====================

def enhanced_update_change_webui(webui_widget, **other_widgets):
    """Enhanced WebUI change handler with dynamic UI adaptation."""
    
    def on_change(change):
        if change['type'] == 'change' and change['name'] == 'value':
            new_webui = change['new']
            
            # Validate WebUI selection
            if WEBUI_UTILS_AVAILABLE and not validate_webui_selection(new_webui):
                print(f"⚠️ Unknown WebUI: {new_webui}")
                return
            
            print(f"🔄 Switching to {new_webui}...")
            
            # Update WebUI in settings
            update_current_webui(new_webui)
            
            # Get WebUI features for dynamic adaptation
            if WEBUI_UTILS_AVAILABLE:
                features = get_webui_features(new_webui)
                category = get_webui_category(new_webui)
                
                print(f"✅ Selected {new_webui} ({category})")
                
                # Show/hide widgets based on WebUI capabilities
                adapt_widgets_to_webui(new_webui, features, other_widgets)
            else:
                print(f"✅ Selected {new_webui}")
                
            # Update commandline arguments
            if new_webui in WEBUI_SELECTION:
                js.save(SETTINGS_PATH, 'WIDGETS.commandline_arguments', WEBUI_SELECTION[new_webui])
    
    return on_change

def adapt_widgets_to_webui(webui, features, widgets_dict):
    """Dynamically adapt widget visibility based on WebUI features."""
    
    try:
        # Model widgets adaptation
        if 'model_widget' in widgets_dict:
            if features.get('supports_models', True):
                widgets_dict['model_widget'].layout.display = 'block'
            else:
                widgets_dict['model_widget'].layout.display = 'none'
                print(f"🎭 Model selection hidden for {webui} (face swap WebUI)")
        
        # VAE widgets adaptation  
        if 'vae_widget' in widgets_dict:
            if features.get('supports_vae', True):
                widgets_dict['vae_widget'].layout.display = 'block'
            else:
                widgets_dict['vae_widget'].layout.display = 'none'
        
        # LoRA widgets adaptation
        if 'lora_widget' in widgets_dict:
            if features.get('supports_lora', True):
                widgets_dict['lora_widget'].layout.display = 'block'
            else:
                widgets_dict['lora_widget'].layout.display = 'none'
        
        # Extension widgets adaptation
        if 'extension_widget' in widgets_dict:
            if features.get('supports_extensions', True):
                widgets_dict['extension_widget'].layout.display = 'block'
                # Update extension widget label based on WebUI type
                if webui == 'ComfyUI':
                    if hasattr(widgets_dict['extension_widget'], 'description'):
                        widgets_dict['extension_widget'].description = 'Custom Nodes:'
            else:
                widgets_dict['extension_widget'].layout.display = 'none'
                print(f"🔧 Extensions hidden for {webui} (uses specialized modules)")
        
        # ControlNet widgets adaptation
        if 'control_widget' in widgets_dict:
            if features.get('supports_controlnet', True):
                widgets_dict['control_widget'].layout.display = 'block'
            else:
                widgets_dict['control_widget'].layout.display = 'none'
        
        # Show category-specific information
        category = features.get('category', 'standard_sd')
        if category == 'face_swap':
            display(HTML('''
            <div class="webui-info">
            🎭 <strong>Face Swap WebUI Selected</strong><br>
            This WebUI specializes in face swapping and doesn't use standard Stable Diffusion models.
            Specialized face swap models will be configured automatically.
            </div>
            '''))
        elif category == 'node_based':
            display(HTML('''
            <div class="webui-info">
            🔗 <strong>Node-Based WebUI Selected</strong><br>
            This WebUI uses a node-based workflow. Extensions are called "Custom Nodes".
            </div>
            '''))
        elif category == 'enhanced_sd':
            display(HTML('''
            <div class="webui-info">
            ⚒️ <strong>Enhanced WebUI Selected</strong><br>
            This WebUI includes performance optimizations and additional features for Stable Diffusion.
            </div>
            '''))
        
    except Exception as e:
        print(f"⚠️ Widget adaptation error: {e}")

def create_webui_dropdown():
    """Create enhanced WebUI dropdown with categories."""
    
    if WEBUI_UTILS_AVAILABLE:
        available_webuis = get_available_webuis()
        categories = get_webuis_by_category()
    else:
        available_webuis = ['A1111', 'ComfyUI', 'Classic', 'Lightning.ai']
        categories = WEBUI_CATEGORIES
    
    # Create organized options list
    options = []
    for category, webuis in categories.items():
        # Add category separator
        options.append((f"--- {category} ---", f"separator_{category.lower().replace(' ', '_')}"))
        # Add WebUIs in this category
        for webui in webuis:
            if webui in available_webuis:
                options.append((f"  {webui}", webui))
    
    # Get current selection
    try:
        current_webui = js.read(SETTINGS_PATH, 'WEBUI.current') or 'A1111'
    except:
        current_webui = 'A1111'
    
    # Create dropdown widget
    webui_dropdown = widgets.Dropdown(
        options=options,
        value=current_webui if current_webui in available_webuis else available_webuis[0],
        description='WebUI:',
        style={'description_width': 'initial'},
        layout=widgets.Layout(width='300px')
    )
    
    return webui_dropdown

def create_model_selector():
    """Create model selector widget with WebUI awareness."""
    
    # Load model data based on current WebUI
    try:
        current_webui = js.read(SETTINGS_PATH, 'WEBUI.current') or 'A1111'
        if WEBUI_UTILS_AVAILABLE and get_webui_category(current_webui) == 'face_swap':
            # Hide model selector for face swap WebUIs
            return widgets.HTML(value="<div style='display:none;'></div>")
    except:
        current_webui = 'A1111'
    
    try:
        # Try to load model data
        exec(open(PATHS['scr_path'] / 'scripts' / '_models-data.py').read(), globals())
        if 'model_list' in globals():
            model_options = ['none'] + model_list
        else:
            model_options = ['none', 'Custom Model URL']
    except Exception as e:
        print(f"⚠️ Could not load model data: {e}")
        model_options = ['none', 'Custom Model URL']
    
    model_widget = widgets.SelectMultiple(
        options=model_options,
        value=['none'],
        description='Models:',
        style={'description_width': 'initial'},
        layout=widgets.Layout(width='400px', height='120px')
    )
    
    return model_widget

def create_component_selector(component_type, description):
    """Create a generic component selector widget."""
    
    try:
        # Try to load component-specific data
        if component_type == 'vae':
            exec(open(PATHS['scr_path'] / 'scripts' / '_models-data.py').read(), globals())
            if 'vae_list' in globals():
                options = ['none'] + vae_list
            else:
                options = ['none', 'Custom VAE URL']
                
            return widgets.Dropdown(
                options=options,
                value='none',
                description=description,
                style={'description_width': 'initial'},
                layout=widgets.Layout(width='400px')
            )
        else:
            # For other components, provide basic selection
            options = ['none', f'Custom {component_type.title()} URL']
            
            return widgets.SelectMultiple(
                options=options,
                value=['none'],
                description=description,
                style={'description_width': 'initial'},
                layout=widgets.Layout(width='400px', height='100px')
            )
            
    except Exception as e:
        print(f"⚠️ Could not create {component_type} selector: {e}")
        return widgets.HTML(value=f"<div>{description} selector not available</div>")

# ==================== WIDGET CREATION ====================

def create_all_widgets():
    """Create all widgets with enhanced WebUI support."""
    
    print("🎛️ Creating enhanced widget interface...")
    
    # Create main widgets
    webui_widget = create_webui_dropdown()
    model_widget = create_model_selector()
    vae_widget = create_component_selector('vae', 'VAE:')
    lora_widget = create_component_selector('lora', 'LoRA:')
    embed_widget = create_component_selector('embed', 'Embeddings:')
    extension_widget = create_component_selector('extension', 'Extensions:')
    control_widget = create_component_selector('control', 'ControlNet:')
    
    # Additional widgets
    inpainting_widget = widgets.Checkbox(
        value=False,
        description='Download Inpainting models',
        style={'description_width': 'initial'}
    )
    
    detailed_widget = widgets.Checkbox(
        value=False,
        description='Detailed download output',
        style={'description_width': 'initial'}
    )
    
    commandline_widget = widgets.Text(
        value=WEBUI_SELECTION.get('A1111', ''),
        description='Launch arguments:',
        style={'description_width': 'initial'},
        layout=widgets.Layout(width='600px')
    )
    
    # Create widget dictionary for adaptation
    widget_dict = {
        'model_widget': model_widget,
        'vae_widget': vae_widget, 
        'lora_widget': lora_widget,
        'embed_widget': embed_widget,
        'extension_widget': extension_widget,
        'control_widget': control_widget
    }
    
    # Set up WebUI change handler
    webui_widget.observe(
        enhanced_update_change_webui(webui_widget, **widget_dict), 
        names='value'
    )
    
    # Set up other change handlers
    def save_widget_value(widget_name, path_key):
        def handler(change):
            if change['type'] == 'change' and change['name'] == 'value':
                js.save(SETTINGS_PATH, path_key, change['new'])
        return handler
    
    model_widget.observe(save_widget_value('model', 'WIDGETS.model'), names='value')
    vae_widget.observe(save_widget_value('vae', 'WIDGETS.vae'), names='value')
    lora_widget.observe(save_widget_value('lora', 'WIDGETS.lora'), names='value')
    embed_widget.observe(save_widget_value('embed', 'WIDGETS.embed'), names='value')
    extension_widget.observe(save_widget_value('extension', 'WIDGETS.extension'), names='value')
    control_widget.observe(save_widget_value('control', 'WIDGETS.control'), names='value')
    inpainting_widget.observe(save_widget_value('inpainting', 'WIDGETS.inpainting'), names='value')
    detailed_widget.observe(save_widget_value('detailed', 'WIDGETS.detailed_download'), names='value')
    commandline_widget.observe(save_widget_value('commandline', 'WIDGETS.commandline_arguments'), names='value')
    
    # Display all widgets
    display(HTML('<h3>🎛️ LightningSdaigen Enhanced Configuration</h3>'))
    
    display(HTML('<div class="category-header">WebUI Selection</div>'))
    display(webui_widget)
    
    display(HTML('<div class="category-header">Model Configuration</div>'))
    display(model_widget)
    display(vae_widget)
    
    display(HTML('<div class="category-header">Additional Components</div>'))
    display(lora_widget)
    display(embed_widget)
    display(extension_widget)
    display(control_widget)
    
    display(HTML('<div class="category-header">Options</div>'))
    display(inpainting_widget)
    display(detailed_widget)
    
    display(HTML('<div class="category-header">Launch Configuration</div>'))
    display(commandline_widget)
    
    # Trigger initial WebUI adaptation
    try:
        current_webui = js.read(SETTINGS_PATH, 'WEBUI.current') or 'A1111'
        if WEBUI_UTILS_AVAILABLE:
            features = get_webui_features(current_webui)
            adapt_widgets_to_webui(current_webui, features, widget_dict)
    except Exception as e:
        print(f"⚠️ Initial adaptation error: {e}")
    
    print("✅ Widget interface created successfully!")
    
    # Show helpful information
    display(HTML('''
    <div style="margin-top: 20px; padding: 10px; background: #e8f5e8; border-radius: 5px;">
    <strong>💡 Tips:</strong><br>
    • WebUIs are organized by category for easier selection<br>
    • Widget visibility adapts automatically based on WebUI capabilities<br>
    • Face swap WebUIs automatically hide incompatible options<br>
    • Launch arguments are pre-configured for optimal performance
    </div>
    '''))

# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    try:
        create_all_widgets()
    except Exception as e:
        print(f"❌ Widget creation failed: {e}")
        print("Please ensure all required modules are installed and try again.")
