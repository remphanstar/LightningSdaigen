# ~ widgets.py | by ANXETY - Enhanced with Multiple WebUI Support ~

from widget_factory import WidgetFactory        # WIDGETS
from webui_utils import update_current_webui    # WEBUI
import json_utils as js                         # JSON

from IPython.display import display, Javascript
import ipywidgets as widgets
from pathlib import Path
import json
import os

# FIXED: Conditional imports for platform-specific features
try:
    from google.colab import output, drive
    IN_COLAB = True
except ImportError:
    IN_COLAB = False
    # Create dummy objects for non-Colab environments
    class DummyOutput:
        @staticmethod
        def register_callback(name, func):
            pass
    output = DummyOutput()

osENV = os.environ

# Constants (auto-convert env vars to Path)
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}   # k -> key; v -> value

HOME = PATHS['home_path']
SCR_PATH = PATHS['scr_path']
SETTINGS_PATH = SCR_PATH / 'settings.json'
ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')

SCRIPTS = SCR_PATH / 'scripts'

CSS = SCR_PATH / 'CSS'
JS = SCR_PATH / 'JS'
widgets_css = CSS / 'main-widgets.css'
widgets_js = JS / 'main-widgets.js'


# ========================= UTILITIES =========================

class WidgetManager:
    """Enhanced widget management with WebUI awareness"""
    
    def __init__(self):
        self.factory = WidgetFactory()
        self.widgets = {}
        self.settings_keys = [
            'XL_models', 'model', 'model_num', 'inpainting_model', 'vae', 'vae_num', 'lora',
            'latest_webui', 'latest_extensions', 'check_custom_nodes_deps', 'change_webui', 'detailed_download',
            'controlnet', 'controlnet_num', 'commit_hash',
            'civitai_token', 'huggingface_token', 'zrok_token', 'ngrok_token', 'commandline_arguments', 'theme_accent',
            # CustomDL
            'empowerment', 'empowerment_output',
            'Model_url', 'Vae_url', 'LoRA_url', 'Embedding_url', 'Extensions_url', 'ADetailer_url',
            'custom_file_urls'
        ]
        
    def create_expandable_button(self, text, url):
        return self.factory.create_html(f'''
        <a href="{url}" target="_blank" class="button button_api">
            <span class="icon"><</span>
            <span class="text">{text}</span>
        </a>
        ''')

    def read_model_data(self, file_path, data_type):
        """Reads model, VAE, or ControlNet data from the specified file."""
        type_map = {
            'model': ('model_list', ['none']),
            'vae': ('vae_list', ['none', 'ALL']),
            'cnet': ('controlnet_list', ['none', 'ALL']),
            'lora': ('lora_list', ['none', 'ALL'])
        }
        key, prefixes = type_map[data_type]
        local_vars = {}

        try:
            with open(file_path) as f:
                exec(f.read(), {}, local_vars)
            names = list(local_vars[key].keys())
            return prefixes + names
        except Exception as e:
            print(f"Warning: Could not load {data_type} data: {e}")
            return prefixes  # Return at least the prefixes

    def get_safe_default(self, options, preferred_defaults):
        """Get the first available option from preferred defaults, or first option if none match"""
        for default in preferred_defaults:
            if default in options:
                return default
        # If no preferred defaults exist, return the first non-'none' option, or 'none' if that's all we have
        return next((opt for opt in options if opt != 'none'), options[0] if options else 'none')

    # ENHANCED: Input validation functions
    def validate_token(self, token, token_type=""):
        """Validate API token format"""
        if not token:
            return True  # Empty is okay
        
        # Basic token validation
        if token_type.lower() == 'civitai':
            # CivitAI tokens are typically 32-character hex strings
            if len(token) == 32 and all(c in '0123456789abcdef' for c in token.lower()):
                return True
            return False
        elif token_type.lower() == 'huggingface':
            # HF tokens start with 'hf_'
            return token.startswith('hf_') and len(token) > 10
        elif token_type.lower() in ['ngrok', 'zrok']:
            # Basic length check for tunnel tokens
            return len(token) > 10
        
        return True  # Default to valid for unknown types

    def validate_url(self, url):
        """Basic URL validation"""
        if not url:
            return True
        return url.startswith(('http://', 'https://'))

# ========================= ENHANCED WEBUI SELECTION =========================

# ENHANCED: Complete WebUI selection with all implementations
WEBUI_SELECTION = {
    # Standard Stable Diffusion WebUIs
    'A1111': "--xformers --no-half-vae",
    'ComfyUI': "--dont-print-server",
    'Classic': "--persistent-patches --cuda-stream --pin-shared-memory",
    'Lightning.ai': "--xformers --no-half-vae",
    
    # ENHANCED: Forge Variants
    'Forge': "--xformers --cuda-stream --pin-shared-memory",
    'ReForge': "--xformers --cuda-stream --pin-shared-memory",
    'SD-UX': "--xformers --no-half-vae --theme dark",
    
    # ENHANCED: Face Manipulation WebUIs
    'FaceFusion': "--execution-provider cuda --face-analyser buffalo_l --face-swapper inswapper_128",
    'RoopUnleashed': "--execution-provider cuda --frame-processor face_swapper --ui-layout horizontal",
    
    # ENHANCED: Specialized WebUIs
    'DreamO': "--device cuda --precision fp16 --max-batch-size 4"
}

# ENHANCED: WebUI Categories for better organization
WEBUI_CATEGORIES = {
    'Standard SD': ['A1111', 'Classic', 'Lightning.ai'],
    'Enhanced SD': ['Forge', 'ReForge', 'SD-UX'],
    'Node-Based': ['ComfyUI'],
    'Face Swap': ['FaceFusion', 'RoopUnleashed'],
    'Specialized': ['DreamO']
}

# ========================= ENHANCED WEBUI HANDLING =========================

def enhanced_update_change_webui(change, widget_manager):
    """Enhanced WebUI change handling with feature detection."""
    try:
        webui = change['new']
        wm = widget_manager
        
        # Update command line arguments
        wm.widgets['commandline_arguments'].value = WEBUI_SELECTION.get(webui, '')
        
        # ENHANCED: Get WebUI features
        from webui_utils import get_webui_features, is_webui_supported, get_webui_category
        features = get_webui_features(webui)
        category = get_webui_category(webui)
        
        # Handle extension/custom nodes visibility
        supports_extensions = is_webui_supported(webui, 'extensions')
        is_comfy = webui == 'ComfyUI'
        is_face_swap = category == 'face_swap'
        
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
        
        # ENHANCED: Handle model selection visibility based on WebUI capabilities
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
        
        # ENHANCED: Display WebUI-specific information
        display_webui_info(webui, category, features)
        
    except Exception as e:
        print(f"Error in enhanced_update_change_webui: {e}")

def display_webui_info(webui, category, features):
    """Display information about the selected WebUI."""
    info_messages = {
        'face_swap': f"🎭 {webui}: Face swapping and manipulation. Traditional SD features disabled.",
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

def update_XL_options(change, widget):
    """ENHANCED: Better XL options handling with WebUI awareness"""
    try:
        from webui_utils import is_webui_supported
        current_webui = widget.widgets.get('change_webui')
        
        # Only apply XL logic for WebUIs that support models
        if current_webui and not is_webui_supported(current_webui.value, 'models'):
            return
            
        is_xl = change['new']
        
        if 'model' in widget.widgets:
            model_widget = widget.widgets['model']
            vae_widget = widget.widgets.get('vae')
            lora_widget = widget.widgets.get('lora')
            controlnet_widget = widget.widgets.get('controlnet')
            
            if is_xl:
                # SDXL defaults
                xl_model_defaults = ['none']
                xl_vae_defaults = ['sdxl_vae | SDXL VAE', 'sdxl_vae', 'none']
                xl_lora_defaults = ['none']
                xl_controlnet_defaults = ['none']
                
                model_widget.value = (widget.get_safe_default(model_widget.options, xl_model_defaults),)
                if vae_widget:
                    vae_widget.value = widget.get_safe_default(vae_widget.options, xl_vae_defaults)
                if lora_widget:
                    lora_widget.value = (widget.get_safe_default(lora_widget.options, xl_lora_defaults),)
                if controlnet_widget:
                    controlnet_widget.value = (widget.get_safe_default(controlnet_widget.options, xl_controlnet_defaults),)
            else:
                # Regular SD 1.5 defaults
                regular_model_defaults = ['none']
                regular_vae_defaults = ['vae-ft-mse-840000-ema-pruned | 840000 | 840k SD1.5 VAE - vae-ft-mse-840k', 'ClearVAE(SD1.5) - v2.3', 'none']
                regular_lora_defaults = ['none']
                regular_controlnet_defaults = ['none']
                
                model_widget.value = (widget.get_safe_default(model_widget.options, regular_model_defaults),)
                if vae_widget:
                    vae_widget.value = widget.get_safe_default(vae_widget.options, regular_vae_defaults)
                if lora_widget:
                    lora_widget.value = (widget.get_safe_default(lora_widget.options, regular_lora_defaults),)
                if controlnet_widget:
                    controlnet_widget.value = (widget.get_safe_default(controlnet_widget.options, regular_controlnet_defaults),)
                    
    except Exception as e:
        print(f"Error in update_XL_options: {e}")

def update_empowerment(change, widget):
    """Enhanced empowerment toggle handling"""
    try:
        selected_emp = change['new']

        customDL_widgets = [
            'Model_url', 'Vae_url', 'LoRA_url', 'Embedding_url', 'Extensions_url', 'ADetailer_url',
            'custom_file_urls', 'empowerment_output'
        ]

        display_value = '' if selected_emp else 'none'
        for widget_name in customDL_widgets:
            if widget_name in widget.widgets:
                widget.widgets[widget_name].layout.display = display_value

    except Exception as e:
        print(f"Error in update_empowerment: {e}")

# ========================= WIDGETS ========================

# Initialize the WidgetManager
wm = WidgetManager()
factory = wm.factory
HR = widgets.HTML('<hr>')

# --- MODEL ---
"""Create model selection widgets with WebUI awareness."""
model_header = factory.create_header('Model Selection')
model_options = wm.read_model_data(f"{SCRIPTS}/_models-data.py", 'model')
model_widget = factory.create_select_multiple(model_options, 'Model:', ('none',))
model_num_widget = factory.create_text('Model Number:', '', 'Enter model numbers for batch download.')

# XL and Inpainting options (will be hidden for non-SD WebUIs)
xl_models_widget = factory.create_checkbox('SDXL Models', False)
inpainting_model_widget = factory.create_checkbox('Inpainting Models', False)

wm.widgets.update({
    'model': model_widget,
    'model_num': model_num_widget,
    'XL_models': xl_models_widget,
    'inpainting_model': inpainting_model_widget
})

# --- VAE ---
"""Create VAE selection widgets."""
vae_header = factory.create_header('VAE Selection')
vae_options = wm.read_model_data(f"{SCRIPTS}/_models-data.py", 'vae')
vae_widget = factory.create_dropdown(vae_options, 'VAE:', 'none')
vae_num_widget = factory.create_text('VAE Number:', '', 'Enter VAE numbers for download.')

wm.widgets.update({
    'vae': vae_widget,
    'vae_num': vae_num_widget
})

# --- LORA ---
"""Create LoRA selection widgets."""
lora_header = factory.create_header('LoRA Selection')
lora_options = wm.read_model_data(f"{SCRIPTS}/_models-data.py", 'lora')
lora_widget = factory.create_select_multiple(lora_options, 'LoRA:', ('none',))

wm.widgets.update({
    'lora': lora_widget
})

# --- ADDITIONAL ---
"""Create additional configuration widgets with enhanced WebUI support."""
additional_header = factory.create_header('Additional')
latest_webui_widget = factory.create_checkbox('Update WebUI', True)
latest_extensions_widget = factory.create_checkbox('Update Extensions', True)
check_custom_nodes_deps_widget = factory.create_checkbox('Check Custom-Nodes Dependencies', True)

# ENHANCED: WebUI selector with all options
change_webui_widget = factory.create_dropdown(list(WEBUI_SELECTION.keys()), 'WebUI:', 'A1111', layout={'width': 'auto'})
detailed_download_widget = factory.create_dropdown(['off', 'on'], 'Detailed Download:', 'off', layout={'width': 'auto'})

choose_changes_box = factory.create_hbox(
    [
        latest_webui_widget,
        latest_extensions_widget,
        check_custom_nodes_deps_widget,
        change_webui_widget,
        detailed_download_widget
    ],
    layout={'justify_content': 'space-between'}
)

controlnet_options = wm.read_model_data(f"{SCRIPTS}/_models-data.py", 'cnet')
controlnet_widget = factory.create_select_multiple(controlnet_options, 'ControlNet:', ('none',))
controlnet_num_widget = factory.create_text('ControlNet Number:', '', 'Enter ControlNet model numbers for download.')
commit_hash_widget = factory.create_text('Commit Hash:', '', 'Switch between branches or commits.')

# Token widgets with validation
civitai_token_from_env = os.getenv('CIVITAI_API_TOKEN')
civitai_token_widget = factory.create_text('CivitAI Token:', '', 'Enter your CivitAi API token.')
if civitai_token_from_env:
    civitai_token_widget.value = "Set in setup.py"
    civitai_token_widget.disabled = True

civitai_button = wm.create_expandable_button('Get CivitAI Token', 'https://civitai.com/user/account')
civitai_box = factory.create_hbox([civitai_token_widget, civitai_button])

huggingface_token_widget = factory.create_text('HuggingFace Token:')
huggingface_button = wm.create_expandable_button('Get HuggingFace Token', 'https://huggingface.co/settings/tokens')
huggingface_box = factory.create_hbox([huggingface_token_widget, huggingface_button])

ngrok_token_widget = factory.create_text('Ngrok Token:')
ngrok_button = wm.create_expandable_button('Get Ngrok Token', 'https://dashboard.ngrok.com/get-started/your-authtoken')
ngrok_box = factory.create_hbox([ngrok_token_widget, ngrok_button])

zrok_token_widget = factory.create_text('Zrok Token:')
zrok_button = wm.create_expandable_button('Get Zrok Token', 'https://colab.research.google.com/drive/1d2sjWDJi_GYBUavrHSuQyHTDuLy36WpU')
zrok_box = factory.create_hbox([zrok_token_widget, zrok_button])

commandline_arguments_widget = factory.create_text('Arguments:', WEBUI_SELECTION['A1111'])

accent_colors_options = ['anxety', 'blue', 'green', 'peach', 'pink', 'red', 'yellow']
theme_accent_widget = factory.create_dropdown(accent_colors_options, 'Theme Accent:', 'anxety',
                                              layout={'width': 'auto', 'margin': '0 0 0 8px'})

additional_footer_box = factory.create_hbox([commandline_arguments_widget, theme_accent_widget])

# Store additional widgets
wm.widgets.update({
    'latest_webui': latest_webui_widget,
    'latest_extensions': latest_extensions_widget,
    'check_custom_nodes_deps': check_custom_nodes_deps_widget,
    'change_webui': change_webui_widget,
    'detailed_download': detailed_download_widget,
    'controlnet': controlnet_widget,
    'controlnet_num': controlnet_num_widget,
    'commit_hash': commit_hash_widget,
    'civitai_token': civitai_token_widget,
    'huggingface_token': huggingface_token_widget,
    'ngrok_token': ngrok_token_widget,
    'zrok_token': zrok_token_widget,
    'commandline_arguments': commandline_arguments_widget,
    'theme_accent': theme_accent_widget
})

additional_widget_list = [
    additional_header,
    choose_changes_box,
    HR,
    controlnet_widget, controlnet_num_widget,
    commit_hash_widget,
    civitai_box, huggingface_box, zrok_box, ngrok_box,
    HR,
    additional_footer_box
]

# --- CUSTOM DOWNLOAD ---
"""Create Custom-Download Selection widgets."""
custom_download_header_popup = factory.create_html('''
<div class="header" style="cursor: pointer;" onclick="toggleContainer()">Custom Download</div>
<div class="info">INFO</div>
<div class="popup">
    Separate multiple URLs with comma/space.
    For <span class="file_name">custom filename</span> specify it through <span class="braces">[ ]</span> after URL without spaces.
    <span class="required">File extension is required</span> for files - <span class="extension">File Extension.</span>
    <div class="sample">
        <span class="sample_label">File Example:</span>
        https://civitai.com/api/download/models/229782<span class="braces">[</span><span class="file_name">Detailer</span><span class="extension">.safetensors</span><span class="braces">]</span>
        <br>
        <span class="sample_label">Extension Example:</span>
        https://github.com/hako-mikan/sd-webui-regional-prompter<span class="braces">[</span><span class="file_name">Regional-Prompter</span><span class="braces">]</span>
    </div>
</div>
''')

empowerment_widget = factory.create_checkbox('Empowerment Mode', False, class_names=['empowerment'])
empowerment_output_widget = factory.create_textarea(
'', '', """Use special tags.
$model - model (example: "{model}")
$vae - vae (example: "{vae}")
$lora - lora (example: "{lora}")
etc...""", layout={'width': '100%', 'height': '120px'})

# Custom download widgets
Model_url_widget = factory.create_textarea('Model:', '', 'model.safetensors')
Vae_url_widget = factory.create_textarea('VAE:', '', 'vae.pt')
LoRA_url_widget = factory.create_textarea('LoRA:', '', 'lora.safetensors')
Embedding_url_widget = factory.create_textarea('Embedding:', '', 'embedding.pt')
Extensions_url_widget = factory.create_textarea('Extensions:', '', 'https://github.com')
ADetailer_url_widget = factory.create_textarea('ADetailer:', '', 'adetailer.pt')
custom_file_urls_widget = factory.create_textarea('Custom File:', '', 'filename.extension')

wm.widgets.update({
    'empowerment': empowerment_widget,
    'empowerment_output': empowerment_output_widget,
    'Model_url': Model_url_widget,
    'Vae_url': Vae_url_widget,
    'LoRA_url': LoRA_url_widget,
    'Embedding_url': Embedding_url_widget,
    'Extensions_url': Extensions_url_widget,
    'ADetailer_url': ADetailer_url_widget,
    'custom_file_urls': custom_file_urls_widget
})

custom_download_widget_list = [
    custom_download_header_popup, HR,
    empowerment_widget, empowerment_output_widget, HR,
    Model_url_widget, Vae_url_widget, LoRA_url_widget,
    Embedding_url_widget, Extensions_url_widget, ADetailer_url_widget,
    custom_file_urls_widget
]

# ENHANCED: Connect WebUI change callback
factory.connect_widgets([(change_webui_widget, 'value')], 
                       lambda change, widget: enhanced_update_change_webui(change, wm))

# Connect other callbacks
factory.connect_widgets([(xl_models_widget, 'value')], lambda change, widget: update_XL_options(change, wm))
factory.connect_widgets([(empowerment_widget, 'value')], lambda change, widget: update_empowerment(change, wm))

# Save settings function
def save_settings():
    """Save all widget settings to JSON."""
    settings = {key: wm.widgets[key].value for key in wm.settings_keys if key in wm.widgets}
    js.save(SETTINGS_PATH, 'WIDGETS', settings)
    update_current_webui(settings['change_webui'])

# ========================= LAYOUT & DISPLAY =========================

# Load and apply CSS/JS
try:
    with open(widgets_css, 'r', encoding='utf-8') as f:
        css_content = f.read()
    with open(widgets_js, 'r', encoding='utf-8') as f:
        js_content = f.read()
    
    display(widgets.HTML(f"<style>{css_content}</style>"))
    display(widgets.HTML(f"<script>{js_content}</script>"))
except FileNotFoundError as e:
    print(f"CSS/JS file not found: {e}")

# Create main widget containers
model_widgets_container = factory.create_vbox([
    model_header, 
    model_widget, model_num_widget, 
    xl_models_widget, inpainting_model_widget
])

vae_widgets_container = factory.create_vbox([
    vae_header,
    vae_widget, vae_num_widget
])

lora_widgets_container = factory.create_vbox([
    lora_header,
    lora_widget
])

additional_widgets_container = factory.create_vbox(additional_widget_list)
custom_download_widgets_container = factory.create_vbox(custom_download_widget_list)

# Display all widgets
display(model_widgets_container, vae_widgets_container, lora_widgets_container, 
        additional_widgets_container, custom_download_widgets_container)

# Save settings button
save_button = factory.create_button('Save Settings', save_settings, class_names=['save_button'])
display(save_button)

print("🎛️ Enhanced WebUI widget system loaded!")
print("🔧 Select your desired WebUI from the dropdown to see adapted options")
