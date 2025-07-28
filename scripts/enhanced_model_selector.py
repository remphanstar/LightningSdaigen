# enhanced_model_selector.py - Complete Enhanced Model Selection System
# This file should be saved in the scripts directory

import json
from IPython.display import HTML, Javascript
from pathlib import Path

class EnhancedModelSelector:
    def __init__(self, widget_manager, model_data_path):
        self.wm = widget_manager
        self.factory = widget_manager.factory
        self.model_data = self.load_model_data(model_data_path)
        self.selected_models = []
        self.container_id = "enhanced-model-selector"
        
    def load_model_data(self, data_path):
        """Load and parse model data from the data file"""
        local_vars = {}
        try:
            with open(data_path) as f:
                exec(f.read(), {}, local_vars)
            return local_vars.get('model_list', {})
        except Exception as e:
            print(f"Warning: Could not load model data: {e}")
            return {}
    
    def create_enhanced_selector(self):
        """Create the enhanced model selector interface"""
        
        # Create container for the enhanced selector
        html_content = f'''
        <div id="{self.container_id}" class="enhanced-model-selector">
            <div class="model-selection-header">
                <h3>🎨 Enhanced Model Selection</h3>
                <div class="model-selection-stats">
                    <span id="model-count">{len(self.model_data)} models available</span>
                </div>
            </div>
            <!-- Enhanced selector will be populated by JavaScript -->
        </div>
        '''
        
        selector_widget = self.factory.create_html(html_content)
        
        # Create JavaScript initialization
        js_init = f'''
        <script>
        // Initialize enhanced model selector
        if (typeof initializeModelSelector === 'function') {{
            const modelData = {json.dumps(self.model_data)};
            
            // Wait for DOM to be ready
            setTimeout(() => {{
                window.modelSelector = initializeModelSelector(modelData, '{self.container_id}');
                
                // Set up Python integration
                window.updatePythonModelWidget = function(selectedModels) {{
                    // Update the hidden widget that Python reads
                    const event = new CustomEvent('pythonModelUpdate', {{
                        detail: {{ models: selectedModels }}
                    }});
                    document.dispatchEvent(event);
                }};
                
                // Listen for selection changes
                window.addEventListener('modelSelectionChanged', function(event) {{
                    console.log('Model selection changed:', event.detail.selectedModels);
                }});
                
            }}, 500);
        }} else {{
            console.error('Enhanced model selector JavaScript not loaded');
        }}
        </script>
        '''
        
        js_widget = self.factory.create_html(js_init)
        
        # Create hidden widget for Python integration
        self.hidden_model_widget = self.factory.create_text(
            'Selected Models (Hidden):', 
            '',
            'Internal widget for model selection'
        )
        self.hidden_model_widget.layout.display = 'none'
        
        # Create traditional backup selector
        backup_selector = self.create_backup_selector()
        
        # Create toggle between enhanced and simple mode
        mode_toggle = self.create_mode_toggle()
        
        return self.factory.create_vbox([
            mode_toggle,
            selector_widget,
            js_widget,
            backup_selector,
            self.hidden_model_widget
        ])
    
    def create_backup_selector(self):
        """Create a traditional selector as backup"""
        model_options = ['none'] + list(self.model_data.keys())
        
        backup_widget = self.factory.create_select_multiple(
            model_options, 
            'Traditional Model Selector (Backup):', 
            ('none',),
            class_names=['backup-model-selector']
        )
        
        # Initially hidden
        backup_widget.layout.display = 'none'
        backup_widget.add_class('backup-selector')
        
        return backup_widget
    
    def create_mode_toggle(self):
        """Create toggle between enhanced and simple mode"""
        toggle_html = f'''
        <div class="selector-mode-toggle">
            <label class="mode-switch">
                <input type="checkbox" id="enhancedModeToggle" checked onchange="toggleSelectorMode(this.checked)">
                <span class="mode-slider"></span>
                <span class="mode-label">Enhanced Mode</span>
            </label>
            <div class="mode-description">
                <span id="mode-desc">Visual model selection with previews and filtering</span>
            </div>
        </div>
        
        <style>
        .selector-mode-toggle {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding: 10px 15px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
        }}
        
        .mode-switch {{
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
            user-select: none;
        }}
        
        .mode-switch input[type="checkbox"] {{
            display: none;
        }}
        
        .mode-slider {{
            width: 44px;
            height: 24px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            position: relative;
            transition: all 0.3s ease;
        }}
        
        .mode-slider::before {{
            content: '';
            position: absolute;
            top: 2px;
            left: 2px;
            width: 20px;
            height: 20px;
            background: white;
            border-radius: 50%;
            transition: all 0.3s ease;
        }}
        
        .mode-switch input:checked + .mode-slider {{
            background: #ff97ef;
        }}
        
        .mode-switch input:checked + .mode-slider::before {{
            transform: translateX(20px);
        }}
        
        .mode-label {{
            color: white;
            font-weight: 500;
        }}
        
        .mode-description {{
            color: rgba(255, 255, 255, 0.7);
            font-size: 12px;
        }}
        </style>
        
        <script>
        function toggleSelectorMode(enhanced) {{
            const enhancedSelector = document.getElementById('{self.container_id}');
            const backupSelector = document.querySelector('.backup-model-selector');
            const modeDesc = document.getElementById('mode-desc');
            
            if (enhanced) {{
                enhancedSelector.style.display = 'block';
                if (backupSelector) backupSelector.style.display = 'none';
                modeDesc.textContent = 'Visual model selection with previews and filtering';
            }} else {{
                enhancedSelector.style.display = 'none';
                if (backupSelector) backupSelector.style.display = 'block';
                modeDesc.textContent = 'Traditional dropdown selection';
            }}
        }}
        </script>
        '''
        
        return self.factory.create_html(toggle_html)
    
    def get_selected_models(self):
        """Get currently selected models"""
        return self.selected_models
    
    def set_selected_models(self, models):
        """Set selected models programmatically"""
        self.selected_models = models
        if hasattr(self, 'hidden_model_widget'):
            self.hidden_model_widget.value = ','.join(models)
    
    def create_integration_callbacks(self):
        """Create callbacks to integrate with existing widget system"""
        
        # JavaScript to bridge enhanced selector with Python
        integration_js = f'''
        <script>
        // Bridge enhanced selector with Python widgets
        document.addEventListener('pythonModelUpdate', function(event) {{
            const selectedModels = event.detail.models;
            
            // Update hidden widget that Python can read
            const hiddenWidget = document.querySelector('input[title*="Internal widget for model selection"]');
            if (hiddenWidget) {{
                hiddenWidget.value = selectedModels.join(',');
                
                // Trigger change event so Python callbacks fire
                hiddenWidget.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
            
            // Update backup selector if visible
            const backupSelector = document.querySelector('.backup-model-selector select');
            if (backupSelector && backupSelector.style.display !== 'none') {{
                // Clear current selection
                Array.from(backupSelector.options).forEach(opt => opt.selected = false);
                
                // Select matching options
                selectedModels.forEach(modelName => {{
                    const option = Array.from(backupSelector.options).find(opt => opt.value === modelName);
                    if (option) option.selected = true;
                }});
                
                // Trigger change event
                backupSelector.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
        }});
        
        // Sync backup selector changes to enhanced selector
        document.addEventListener('change', function(event) {{
            if (event.target.classList.contains('backup-model-selector')) {{
                const selectedOptions = Array.from(event.target.selectedOptions);
                const selectedModels = selectedOptions.map(opt => opt.value).filter(val => val !== 'none');
                
                // Update enhanced selector if available
                if (window.modelSelector) {{
                    window.modelSelector.clearSelection();
                    selectedModels.forEach(modelName => {{
                        const model = window.modelSelector.models.find(m => m.name === modelName);
                        if (model) {{
                            window.modelSelector.selectedModels.add(model.id);
                        }}
                    }});
                    window.modelSelector.updateSelection();
                }}
            }}
        }});
        </script>
        '''
        
        return self.factory.create_html(integration_js)


# ===== HELPER FUNCTIONS =====

def create_complete_enhanced_widgets(widget_manager, scripts_path):
    """Create the complete enhanced model widget section"""
    
    # Create enhanced selector
    model_header = widget_manager.factory.create_header('Enhanced Model Selection')
    
    # Load model data based on XL setting
    xl_models = widget_manager.widgets.get('XL_models', None)
    model_files = '_xl-models-data.py' if (xl_models and xl_models.value) else '_models-data.py'
    model_data_path = scripts_path / model_files
    
    # Create enhanced selector
    enhanced_selector = EnhancedModelSelector(widget_manager, model_data_path)
    enhanced_widget = enhanced_selector.create_enhanced_selector()
    integration_widget = enhanced_selector.create_integration_callbacks()
    
    # Store reference in widget manager
    widget_manager.enhanced_model_selector = enhanced_selector
    widget_manager.widgets['enhanced_model_selector'] = enhanced_selector.hidden_model_widget
    
    # Create traditional widgets for compatibility
    model_num_widget = widget_manager.factory.create_text(
        'Model Numbers:', 
        '', 
        'Enter model numbers for download (comma-separated)'
    )
    
    inpainting_model_widget = widget_manager.factory.create_checkbox(
        'Include Inpainting Variants', 
        False, 
        class_names=['inpaint'], 
        layout={'width': '250px'}
    )
    
    XL_models_widget = widget_manager.factory.create_checkbox(
        'SDXL Models', 
        False, 
        class_names=['sdxl']
    )
    
    # Enhanced options panel
    options_panel = widget_manager.factory.create_hbox([
        inpainting_model_widget, 
        XL_models_widget
    ])
    
    # Store widgets
    widget_manager.widgets.update({
        'model': enhanced_selector.hidden_model_widget,  # This is key for compatibility
        'model_num': model_num_widget,
        'inpainting_model': inpainting_model_widget,
        'XL_models': XL_models_widget
    })
    
    return [
        model_header,
        enhanced_widget,
        integration_widget,
        model_num_widget,
        options_panel
    ]

def create_vae_widgets(widget_manager, scripts_path):
    """Create VAE widgets (unchanged)"""
    vae_header = widget_manager.factory.create_header('VAE Selection')
    vae_options = widget_manager.read_model_data(f"{scripts_path}/_models-data.py", 'vae')
    
    vae_preferred_defaults = [
        'vae-ft-mse-840000-ema-pruned | 840000 | 840k SD1.5 VAE - vae-ft-mse-840k',
        'ClearVAE(SD1.5) - v2.3',
        'none'
    ]
    vae_default = widget_manager.get_safe_default(vae_options, vae_preferred_defaults)
    vae_widget = widget_manager.factory.create_dropdown(vae_options, 'Vae:', vae_default)
    
    vae_num_widget = widget_manager.factory.create_text('Vae Number:', '', 'Enter vae numbers for download.')
    
    widget_manager.widgets.update({
        'vae': vae_widget,
        'vae_num': vae_num_widget
    })
    
    return [vae_header, vae_widget, vae_num_widget]

def create_lora_widgets(widget_manager, scripts_path):
    """Create LoRA widgets (unchanged)"""
    lora_header = widget_manager.factory.create_header('LoRA Selection')
    lora_options = widget_manager.read_model_data(f"{scripts_path}/_models-data.py", 'lora')
    lora_widget = widget_manager.factory.create_select_multiple(lora_options, 'LoRA:', ('none',))
    
    widget_manager.widgets.update({
        'lora': lora_widget
    })
    
    return [lora_header, lora_widget]

def create_additional_widgets(widget_manager):
    """Create additional configuration widgets (unchanged)"""
    additional_header = widget_manager.factory.create_header('Additional')
    
    WEBUI_SELECTION = {
        'A1111': "--xformers --no-half-vae",
        'ComfyUI': "--dont-print-server",
        'Forge': "--xformers --cuda-stream --pin-shared-memory",
        'Classic': "--persistent-patches --cuda-stream --pin-shared-memory",
        'ReForge': "--xformers --cuda-stream --pin-shared-memory",
        'SD-UX': "--xformers --no-half-vae"
    }
    
    latest_webui_widget = widget_manager.factory.create_checkbox('Update WebUI', True)
    latest_extensions_widget = widget_manager.factory.create_checkbox('Update Extensions', True)
    check_custom_nodes_deps_widget = widget_manager.factory.create_checkbox('Check Custom-Nodes Dependencies', True)
    change_webui_widget = widget_manager.factory.create_dropdown(list(WEBUI_SELECTION.keys()), 'WebUI:', 'A1111', layout={'width': 'auto'})
    detailed_download_widget = widget_manager.factory.create_dropdown(['off', 'on'], 'Detailed Download:', 'off', layout={'width': 'auto'})

    choose_changes_box = widget_manager.factory.create_hbox([
        latest_webui_widget,
        latest_extensions_widget,
        check_custom_nodes_deps_widget,
        change_webui_widget,
        detailed_download_widget
    ], layout={'justify_content': 'space-between'})

    controlnet_options = widget_manager.read_model_data(f"{widget_manager.factory.__dict__.get('scripts_path', '')}_models-data.py", 'cnet') if hasattr(widget_manager.factory, 'scripts_path') else ['none']
    controlnet_widget = widget_manager.factory.create_select_multiple(controlnet_options, 'ControlNet:', ('none',))
    controlnet_num_widget = widget_manager.factory.create_text('ControlNet Number:', '', 'Enter ControlNet model numbers for download.')
    commit_hash_widget = widget_manager.factory.create_text('Commit Hash:', '', 'Switch between branches or commits.')

    civitai_token_widget = widget_manager.factory.create_text('CivitAI Token:', '', 'Enter your CivitAi API token.')
    civitai_button = widget_manager.create_expandable_button('Get CivitAI Token', 'https://civitai.com/user/account')
    civitai_box = widget_manager.factory.create_hbox([civitai_token_widget, civitai_button])

    huggingface_token_widget = widget_manager.factory.create_text('HuggingFace Token:')
    huggingface_button = widget_manager.create_expandable_button('Get HuggingFace Token', 'https://huggingface.co/settings/tokens')
    huggingface_box = widget_manager.factory.create_hbox([huggingface_token_widget, huggingface_button])

    ngrok_token_widget = widget_manager.factory.create_text('Ngrok Token:')
    ngrok_button = widget_manager.create_expandable_button('Get Ngrok Token', 'https://dashboard.ngrok.com/get-started/your-authtoken')
    ngrok_box = widget_manager.factory.create_hbox([ngrok_token_widget, ngrok_button])

    zrok_token_widget = widget_manager.factory.create_text('Zrok Token:')
    zrok_button = widget_manager.create_expandable_button('Get Zrok Token', 'https://colab.research.google.com/drive/1d2sjWDJi_GYBUavrHSuQyHTDuLy36WpU')
    zrok_box = widget_manager.factory.create_hbox([zrok_token_widget, zrok_button])

    commandline_arguments_widget = widget_manager.factory.create_text('Arguments:', WEBUI_SELECTION['A1111'])

    accent_colors_options = ['anxety', 'blue', 'green', 'peach', 'pink', 'red', 'yellow']
    theme_accent_widget = widget_manager.factory.create_dropdown(
        accent_colors_options, 'Theme Accent:', 'anxety',
        layout={'width': 'auto', 'margin': '0 0 0 8px'}
    )

    additional_footer_box = widget_manager.factory.create_hbox([commandline_arguments_widget, theme_accent_widget])

    # Store additional widgets
    widget_manager.widgets.update({
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

    return [
        additional_header,
        choose_changes_box,
        widget_manager.factory.create_html('<hr>'),
        controlnet_widget, controlnet_num_widget,
        commit_hash_widget,
        civitai_box, huggingface_box, zrok_box, ngrok_box,
        widget_manager.factory.create_html('<hr>'),
        additional_footer_box
    ]

def create_enhanced_callbacks(widget_manager, scripts_path):
    """Create enhanced callbacks that preserve original functionality"""
    
    def enhanced_update_XL_options(change, widget):
        """Enhanced XL toggle that updates both selectors"""
        try:
            is_xl = change['new']
            
            data_file = '_xl-models-data.py' if is_xl else '_models-data.py'
            
            # Update traditional widget options
            if 'vae' in widget_manager.widgets:
                widget_manager.widgets['vae'].options = widget_manager.read_model_data(f"{scripts_path}/{data_file}", 'vae')
            if 'controlnet' in widget_manager.widgets:
                widget_manager.widgets['controlnet'].options = widget_manager.read_model_data(f"{scripts_path}/{data_file}", 'cnet')
            
            # Update enhanced selector if available
            if hasattr(widget_manager, 'enhanced_model_selector'):
                model_data_path = scripts_path / data_file
                widget_manager.enhanced_model_selector.model_data = widget_manager.enhanced_model_selector.load_model_data(model_data_path)
                
                # Update JavaScript with new data
                from IPython.display import display, Javascript
                display(Javascript(f'''
                    if (window.modelSelector) {{
                        const newModelData = {json.dumps(widget_manager.enhanced_model_selector.model_data)};
                        window.modelSelector.loadModels(newModelData);
                    }}
                '''))
            
            # Handle inpainting checkbox for XL
            if 'inpainting_model' in widget_manager.widgets:
                if is_xl:
                    widget_manager.widgets['inpainting_model'].add_class('_disable')
                    widget_manager.widgets['inpainting_model'].value = False
                else:
                    widget_manager.widgets['inpainting_model'].remove_class('_disable')
                    
        except Exception as e:
            print(f"Error in enhanced_update_XL_options: {e}")

    def enhanced_update_change_webui(change, widget):
        """Enhanced WebUI change handling"""
        try:
            webui = change['new']
            WEBUI_SELECTION = {
                'A1111': "--xformers --no-half-vae",
                'ComfyUI': "--dont-print-server",
                'Forge': "--xformers --cuda-stream --pin-shared-memory",
                'Classic': "--persistent-patches --cuda-stream --pin-shared-memory",
                'ReForge': "--xformers --cuda-stream --pin-shared-memory",
                'SD-UX': "--xformers --no-half-vae"
            }
            
            widget_manager.widgets['commandline_arguments'].value = WEBUI_SELECTION.get(webui, '')

            is_comfy = webui == 'ComfyUI'

            widget_manager.widgets['latest_extensions'].layout.display = 'none' if is_comfy else ''
            widget_manager.widgets['latest_extensions'].value = not is_comfy
            widget_manager.widgets['check_custom_nodes_deps'].layout.display = '' if is_comfy else 'none'
            widget_manager.widgets['theme_accent'].layout.display = 'none' if is_comfy else ''
            if 'Extensions_url' in widget_manager.widgets:
                widget_manager.widgets['Extensions_url'].description = 'Custom Nodes:' if is_comfy else 'Extensions:'
        except Exception as e:
            print(f"Error in enhanced_update_change_webui: {e}")

    # Connect enhanced callbacks
    widget_manager.factory.connect_widgets([(widget_manager.widgets['change_webui'], 'value')], enhanced_update_change_webui)
    widget_manager.factory.connect_widgets([(widget_manager.widgets['XL_models'], 'value')], enhanced_update_XL_options)

def create_model_selection_bridge():
    """Create JavaScript bridge for model selection"""
    return '''
    <script>
    // Enhanced Model Selection Bridge
    document.addEventListener('DOMContentLoaded', function() {
        // Sync enhanced selector with traditional widget
        function syncModelSelection() {
            const enhancedWidget = document.querySelector('input[title*="Internal widget for model selection"]');
            const traditionalWidget = document.querySelector('.backup-model-selector select');
            
            if (enhancedWidget && traditionalWidget) {
                // Sync changes from enhanced to traditional
                enhancedWidget.addEventListener('change', function() {
                    const selectedModels = this.value.split(',').filter(m => m.trim());
                    
                    // Clear traditional selection
                    Array.from(traditionalWidget.options).forEach(opt => opt.selected = false);
                    
                    // Select matching options in traditional
                    selectedModels.forEach(modelName => {
                        const option = Array.from(traditionalWidget.options).find(opt => opt.value === modelName.trim());
                        if (option) option.selected = true;
                    });
                    
                    // Trigger change event
                    traditionalWidget.dispatchEvent(new Event('change', { bubbles: true }));
                });
            }
        }
        
        // Initialize sync
        setTimeout(syncModelSelection, 1000);
    });
    </script>
    '''
