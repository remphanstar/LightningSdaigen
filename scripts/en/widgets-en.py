# ~ widgets.py | by ANXETY - FIXED VERSION ~

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
SETTINGS_PATH = PATHS['settings_path']
ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')

SCRIPTS = SCR_PATH / 'scripts'

CSS = SCR_PATH / 'CSS'
JS = SCR_PATH / 'JS'
widgets_css = CSS / 'main-widgets.css'
widgets_js = JS / 'main-widgets.js'


# ========================= UTILITIES =========================

class WidgetManager:
    """FIXED: Encapsulate widget management to avoid global pollution"""
    
    def __init__(self):
        self.factory = WidgetFactory()
        self.widgets = {}
        self.settings_keys = [
            'XL_models', 'model', 'model_num', 'inpainting_model', 'vae', 'vae_num',
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
            'cnet': ('controlnet_list', ['none', 'ALL'])
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

    # FIXED: Input validation functions
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

# ========================= WIDGETS ========================

# Initialize the WidgetManager
wm = WidgetManager()
factory = wm.factory
HR = widgets.HTML('<hr>')

WEBUI_SELECTION = {
    'A1111':   "--xformers --no-half-vae",
    'ComfyUI': "--dont-print-server",
    'Forge':   "--xformers --cuda-stream --pin-shared-memory",
    'Classic': "--persistent-patches --cuda-stream --pin-shared-memory",
    'ReForge': "--xformers --cuda-stream --pin-shared-memory",
    'SD-UX':   "--xformers --no-half-vae"
}

# --- MODEL ---
"""Create model selection widgets."""
model_header = factory.create_header('Model Selection')
model_options = wm.read_model_data(f"{SCRIPTS}/_models-data.py", 'model')

# FIXED: Use safe default selection for models
model_preferred_defaults = [
    'D5K6.0',  # First model in your custom list
    'Merged amateurs - Mixed Amateurs',  # Second option
]
model_default = wm.get_safe_default(model_options, model_preferred_defaults)
model_widget = factory.create_dropdown(model_options, 'Model:', model_default)

model_num_widget = factory.create_text('Model Number:', '', 'Enter model numbers for download.')
inpainting_model_widget = factory.create_checkbox('Inpainting Models', False, class_names=['inpaint'], layout={'width': '250px'})
XL_models_widget = factory.create_checkbox('SDXL', False, class_names=['sdxl'])

switch_model_widget = factory.create_hbox([inpainting_model_widget, XL_models_widget])

# Store widgets in manager
wm.widgets.update({
    'model': model_widget,
    'model_num': model_num_widget,
    'inpainting_model': inpainting_model_widget,
    'XL_models': XL_models_widget
})

# --- VAE ---
"""Create VAE selection widgets."""
vae_header = factory.create_header('VAE Selection')
vae_options = wm.read_model_data(f"{SCRIPTS}/_models-data.py", 'vae')

# FIXED: Use safe default selection for VAE
vae_preferred_defaults = [
    'vae-ft-mse-840000-ema-pruned | 840000 | 840k SD1.5 VAE - vae-ft-mse-840k',  # First VAE in your list
    'ClearVAE(SD1.5) - v2.3',  # Second option
    'none'
]
vae_default = wm.get_safe_default(vae_options, vae_preferred_defaults)
vae_widget = factory.create_dropdown(vae_options, 'Vae:', vae_default)

vae_num_widget = factory.create_text('Vae Number:', '', 'Enter vae numbers for download.')

wm.widgets.update({
    'vae': vae_widget,
    'vae_num': vae_num_widget
})

# --- ADDITIONAL ---
"""Create additional configuration widgets."""
additional_header = factory.create_header('Additional')
latest_webui_widget = factory.create_checkbox('Update WebUI', True)
latest_extensions_widget = factory.create_checkbox('Update Extensions', True)
check_custom_nodes_deps_widget = factory.create_checkbox('Check Custom-Nodes Dependencies', True)
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
controlnet_widget = factory.create_dropdown(controlnet_options, 'ControlNet:', 'none')
controlnet_num_widget = factory.create_text('ControlNet Number:', '', 'Enter ControlNet model numbers for download.')
commit_hash_widget = factory.create_text('Commit Hash:', '', 'Switch between branches or commits.')

# FIXED: Add validation for tokens
civitai_token_widget = factory.create_text('CivitAI Token:', '', 'Enter your CivitAi API token.')
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
'', '', """Use special tags. Portable analogue of "File (txt)"
Tags: model (ckpt), vae, lora, embed (emb), extension (ext), adetailer (ad), control (cnet), upscale (ups), clip, unet, vision (vis), encoder (enc), diffusion (diff), config (cfg)
Short-tags: start with '$' without space -> $ckpt
------ Example ------

# Lora
https://civitai.com/api/download/models/229782

$ext
https://github.com/hako-mikan/sd-webui-cd-tuner[CD-Tuner]
""")

Model_url_widget = factory.create_text('Model:')
Vae_url_widget = factory.create_text('Vae:')
LoRA_url_widget = factory.create_text('LoRa:')
Embedding_url_widget = factory.create_text('Embedding:')
Extensions_url_widget = factory.create_text('Extensions:')
ADetailer_url_widget = factory.create_text('ADetailer:')
custom_file_urls_widget = factory.create_text('File (txt):')

# Store custom download widgets
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

# --- Save Button ---
"""Create button widgets."""
save_button = factory.create_button('Save', class_names=['button', 'button_save'])

# =================== GDrive Toggle Button =================
"""Create Google Drive toggle button - FIXED: Only for Colab."""
BTN_STYLE = {'width': '48px', 'height': '48px'}
TOOLTIPS = ("Disconnect Google Drive", "Connect Google Drive")

GD_status = js.read(SETTINGS_PATH, 'mountGDrive', False)
GDrive_button = factory.create_button('', layout=BTN_STYLE, class_names=['sideContainer-btn', 'gdrive-btn'])
GDrive_button.tooltip = TOOLTIPS[not GD_status]
GDrive_button.toggle = GD_status

# FIXED: Properly handle non-Colab environments
if not IN_COLAB:
    GDrive_button.layout.display = 'none'
else:
    if GD_status:
        GDrive_button.add_class('active')

    def handle_toggle(btn):
        """Toggle Google Drive button state"""
        btn.toggle = not btn.toggle
        btn.tooltip = TOOLTIPS[not btn.toggle]
        btn.toggle and btn.add_class('active') or btn.remove_class('active')

    GDrive_button.on_click(handle_toggle)

# ========= Export/Import Widget Settings Buttons ==========
"""Create buttons to export/import widget settings - FIXED: Only for Colab."""
export_button = factory.create_button('', layout=BTN_STYLE, class_names=['sideContainer-btn', 'export-btn'])
export_button.tooltip = "Export settings to JSON"

import_button = factory.create_button('', layout=BTN_STYLE, class_names=['sideContainer-btn', 'import-btn'])
import_button.tooltip = "Import settings from JSON"

if not IN_COLAB:
    export_button.layout.display = 'none'
    import_button.layout.display = 'none'

# EXPORT
def export_settings(button=None, filter_empty=False):
    """FIXED: Better error handling for export"""
    if not IN_COLAB:
        show_notification("Export only available in Google Colab", "warning")
        return
        
    try:
        widgets_data = {}
        for key in wm.settings_keys:
            if key in wm.widgets:
                value = wm.widgets[key].value
                if not filter_empty or (value not in [None, '', False]):
                    widgets_data[key] = value

        settings_data = {
            'widgets': widgets_data,
            'mountGDrive': GDrive_button.toggle
        }

        display(Javascript(f'downloadJson({json.dumps(settings_data)});'))
        show_notification("Settings exported successfully!", "success")
    except Exception as e:
        show_notification(f"Export failed: {str(e)}", "error")

# IMPORT
def import_settings(button=None):
    """FIXED: Better error handling for import"""
    if not IN_COLAB:
        show_notification("Import only available in Google Colab", "warning")
        return
    display(Javascript('openFilePicker();'))

# APPLY SETTINGS
def apply_imported_settings(data):
    """FIXED: Better validation and error handling"""
    try:
        success_count = 0
        total_count = 0
        failed_items = []

        if 'widgets' in data:
            for key, value in data['widgets'].items():
                total_count += 1
                if key in wm.settings_keys and key in wm.widgets:
                    try:
                        # FIXED: Validate input before setting
                        if key.endswith('_token') and not wm.validate_token(value, key.replace('_token', '')):
                            failed_items.append(f"{key}: invalid format")
                            continue
                        if key.endswith('_url') and not wm.validate_url(value):
                            failed_items.append(f"{key}: invalid URL")
                            continue
                            
                        wm.widgets[key].value = value
                        success_count += 1
                    except Exception as e:
                        failed_items.append(f"{key}: {str(e)}")

        if 'mountGDrive' in data and IN_COLAB:
            GDrive_button.toggle = data['mountGDrive']
            if GDrive_button.toggle:
                GDrive_button.add_class('active')
            else:
                GDrive_button.remove_class('active')

        if failed_items:
            show_notification(f"Import completed with warnings: {', '.join(failed_items[:3])}", "warning")
        elif success_count == total_count:
            show_notification("Settings imported successfully!", "success")
        else:
            show_notification(f"Imported {success_count}/{total_count} settings", "warning")

    except Exception as e:
        show_notification(f"Import failed: {str(e)}", "error")

# ============= NOTIFICATION for Export/Import =============
"""Create widget-popup displaying status of Export/Import settings."""
notification_popup = factory.create_html('', class_names=['notification-popup', 'hidden'])

def show_notification(message, message_type='info'):
    """FIXED: Better notification handling"""
    icon_map = {
        'success':  '✅',
        'error':    '❌',
        'info':     'ℹ️',
        'warning':  '⚠️'
    }
    icon = icon_map.get(message_type, 'ℹ️')

    notification_popup.value = f'''
    <div class="notification {message_type}">
        <span class="notification-icon">{icon}</span>
        <span class="notification-text">{message}</span>
    </div>
    '''

    notification_popup.remove_class('visible')
    notification_popup.remove_class('hidden')
    notification_popup.add_class('visible')

    # Auto-hide PopUp After 2.5s - only if JS is available
    if IN_COLAB:
        display(Javascript("hideNotification(delay = 2500);"))

# REGISTER CALLBACK
"""Register callbacks only if in Colab"""
if IN_COLAB:
    output.register_callback('importSettingsFromJS', apply_imported_settings)
    output.register_callback('showNotificationFromJS', show_notification)

export_button.on_click(export_settings)
import_button.on_click(import_settings)

# =================== DISPLAY / SETTINGS ===================

factory.load_css(widgets_css)   # load CSS (widgets)
if IN_COLAB:
    factory.load_js(widgets_js)     # load JS (widgets) - only in Colab

# Display sections
model_widgets = [model_header, model_widget, model_num_widget, switch_model_widget]
vae_widgets = [vae_header, vae_widget, vae_num_widget]
additional_widgets = additional_widget_list
custom_download_widgets = [
    custom_download_header_popup,
    empowerment_widget,
    empowerment_output_widget,
    Model_url_widget,
    Vae_url_widget,
    LoRA_url_widget,
    Embedding_url_widget,
    Extensions_url_widget,
    ADetailer_url_widget,
    custom_file_urls_widget
]

# Create Boxes
model_box = factory.create_vbox(model_widgets, class_names=['container'])
vae_box = factory.create_vbox(vae_widgets, class_names=['container'])
additional_box = factory.create_vbox(additional_widgets, class_names=['container'])
custom_download_box = factory.create_vbox(custom_download_widgets, class_names=['container', 'container_cdl'])

# Create Containers
CONTAINERS_WIDTH = '1080px'
model_vae_box = factory.create_hbox(
    [model_box, vae_box],
    class_names=['widgetContainer', 'model-vae'],
)

widgetContainer = factory.create_vbox(
    [model_vae_box, additional_box, custom_download_box, save_button],
    class_names=['widgetContainer'],
    layout={'min_width': CONTAINERS_WIDTH, 'max_width': CONTAINERS_WIDTH}
)
sideContainer = factory.create_vbox(
    [GDrive_button, export_button, import_button, notification_popup],
    class_names=['sideContainer']
)

# CRITICAL FIX: CSS flexbox properties must use hyphenated values, not underscore notation
# The ipywidgets Layout trait system enforces strict CSS specification compliance
# 'flex_start' is invalid - must be 'flex-start' per CSS flexbox specification
mainContainer = factory.create_hbox(
    [widgetContainer, sideContainer],
    class_names=['mainContainer'],
    layout={'align_items': 'flex-start'}  # FIXED: hyphenated CSS property value
)

factory.display(mainContainer)

# ==================== CALLBACK FUNCTION ===================

# Initialize visibility
check_custom_nodes_deps_widget.layout.display = 'none'
empowerment_output_widget.add_class('empowerment-output')
empowerment_output_widget.add_class('hidden')

# FIXED: Improved callback functions with error handling
def update_XL_options(change, widget):
    """FIXED: Better error handling and state management"""
    try:
        is_xl = change['new']
        
        data_file = '_xl-models-data.py' if is_xl else '_models-data.py'
        
        # Update options with error handling
        try:
            model_widget.options = wm.read_model_data(f"{SCRIPTS}/{data_file}", 'model')
            vae_widget.options = wm.read_model_data(f"{SCRIPTS}/{data_file}", 'vae')
            controlnet_widget.options = wm.read_model_data(f"{SCRIPTS}/{data_file}", 'cnet')
        except Exception as e:
            print(f"Warning: Could not update model options: {e}")
            return

        # FIXED: Use safe defaults for XL vs regular models
        if is_xl:
            # XL model defaults - use first available XL model
            xl_model_defaults = list(model_widget.options)[1:4]  # Skip 'none', get first few
            xl_vae_defaults = ['none', 'ALL']
            xl_controlnet_defaults = ['none']
            
            model_widget.value = wm.get_safe_default(model_widget.options, xl_model_defaults)
            vae_widget.value = wm.get_safe_default(vae_widget.options, xl_vae_defaults)
            controlnet_widget.value = wm.get_safe_default(controlnet_widget.options, xl_controlnet_defaults)
            
            # Handle inpainting checkbox for XL
            inpainting_model_widget.add_class('_disable')
            inpainting_model_widget.value = False
        else:
            # Regular model defaults - use your custom models
            regular_model_defaults = [
                'D5K6.0',
                'Merged amateurs - Mixed Amateurs'
            ]
            regular_vae_defaults = [
                'vae-ft-mse-840000-ema-pruned | 840000 | 840k SD1.5 VAE - vae-ft-mse-840k',
                'ClearVAE(SD1.5) - v2.3',
                'none'
            ]
            regular_controlnet_defaults = ['none']
            
            model_widget.value = wm.get_safe_default(model_widget.options, regular_model_defaults)
            vae_widget.value = wm.get_safe_default(vae_widget.options, regular_vae_defaults)
            controlnet_widget.value = wm.get_safe_default(controlnet_widget.options, regular_controlnet_defaults)
            
            # Enable inpainting checkbox for regular models
            inpainting_model_widget.remove_class('_disable')
            
    except Exception as e:
        print(f"Error in update_XL_options: {e}")

def update_change_webui(change, widget):
    """FIXED: Better WebUI change handling"""
    try:
        webui = change['new']
        commandline_arguments_widget.value = WEBUI_SELECTION.get(webui, '')

        is_comfy = webui == 'ComfyUI'

        latest_extensions_widget.layout.display = 'none' if is_comfy else ''
        latest_extensions_widget.value = not is_comfy
        check_custom_nodes_deps_widget.layout.display = '' if is_comfy else 'none'
        theme_accent_widget.layout.display = 'none' if is_comfy else ''
        Extensions_url_widget.description = 'Custom Nodes:' if is_comfy else 'Extensions:'
    except Exception as e:
        print(f"Error in update_change_webui: {e}")

def update_empowerment(change, widget):
    """FIXED: Better empowerment toggle handling"""
    try:
        selected_emp = change['new']

        customDL_widgets = [
            Model_url_widget, Vae_url_widget, LoRA_url_widget,
            Embedding_url_widget, Extensions_url_widget, ADetailer_url_widget
        ]
        
        for widget in customDL_widgets:
            widget.add_class('empowerment-text-field')

        if selected_emp:
            for wg in customDL_widgets:
                wg.add_class('hidden')
            empowerment_output_widget.remove_class('hidden')
        else:
            for wg in customDL_widgets:
                wg.remove_class('hidden')
            empowerment_output_widget.add_class('hidden')

    except Exception as e:
        print(f"Error in update_empowerment: {e}")


# Connecting widgets
factory.connect_widgets([(change_webui_widget, 'value')], update_change_webui)
factory.connect_widgets([(XL_models_widget, 'value')], update_XL_options)
factory.connect_widgets([(empowerment_widget, 'value')], update_empowerment)


# ================ Load / Save - Settings V4 ===============

def save_settings():
    """Save widget values to settings."""
    widgets_values = {key: wm.widgets[key].value for key in wm.settings_keys if key in wm.widgets}
    js.save(SETTINGS_PATH, 'WIDGETS', widgets_values)
    if IN_COLAB:
        js.save(SETTINGS_PATH, 'mountGDrive', True if GDrive_button.toggle else False)  # Save Status GDrive-btn

    update_current_webui(change_webui_widget.value)  # Update Selected WebUI in settings.json

def load_settings():
    """Load widget values from settings."""
    if js.key_exists(SETTINGS_PATH, 'WIDGETS'):
        widget_data = js.read(SETTINGS_PATH, 'WIDGETS')
        for key in wm.settings_keys:
            if key in widget_data and key in wm.widgets:
                try:
                    wm.widgets[key].value = widget_data.get(key, '')
                except Exception as e:
                    print(f"Warning: could not load setting for {key}: {e}")

    # Load Status GDrive-btn
    if IN_COLAB:
        GD_status = js.read(SETTINGS_PATH, 'mountGDrive', False)
        GDrive_button.toggle = (GD_status == True)
        if GDrive_button.toggle:
            GDrive_button.add_class('active')
        else:
            GDrive_button.remove_class('active')

def save_data(button):
    """Handle save button click."""
    save_settings()
    all_widgets = [
        model_box, vae_box, additional_box, custom_download_box, save_button,   # mainContainer
        GDrive_button, export_button, import_button, notification_popup         # sideContainer
    ]
    factory.close(all_widgets, class_names=['hide'], delay=0.8)

load_settings()
save_button.on_click(save_data)
