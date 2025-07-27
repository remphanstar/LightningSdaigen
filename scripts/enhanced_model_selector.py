# enhanced_model_selector.py
# This file should be saved in the scripts directory

# Copy the complete EnhancedModelSelector class and all functions from the previous artifacts
# This is the complete standalone file

import json
from IPython.display import HTML, Javascript

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
        
        <style>
        .enhanced-model-selector {{
            margin: 20px 0;
            padding: 20px;
            background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
            border-radius: 16px;
            border: 2px solid rgba(255, 151, 239, 0.3);
        }}
        
        .model-selection-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .model-selection-header h3 {{
            margin: 0;
            color: var(--aw-accent-color);
            font-family: var(--aw-font-family-primary);
        }}
        
        .model-selection-stats {{
            color: rgba(255, 255, 255, 0.7);
            font-size: 14px;
        }}
        </style>
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
                modelSelector = initializeModelSelector(modelData, '{self.container_id}');
                
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
            background: var(--aw-accent-color);
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


# Integration functions
def create_enhanced_model_selector(widget_manager, model_data_path):
    """Create enhanced model selector and integrate with existing system"""
    
    # Create enhanced selector
    enhanced_selector = EnhancedModelSelector(widget_manager, model_data_path)
    selector_widget = enhanced_selector.create_enhanced_selector()
    integration_widget = enhanced_selector.create_integration_callbacks()
    
    # Store reference in widget manager
    widget_manager.enhanced_model_selector = enhanced_selector
    widget_manager.widgets['enhanced_model_selector'] = enhanced_selector.hidden_model_widget
    
    return selector_widget, integration_widget


def create_enhanced_model_section(widget_manager, scripts_path):
    """Replace the existing model section with enhanced version"""
    
    model_header = widget_manager.factory.create_header('Enhanced Model Selection')
    
    # Load model data
    model_files = '_xl-models-data.py' if widget_manager.widgets.get('XL_models', {}).value else '_models-data.py'
    model_data_path = scripts_path / model_files
    
    # Create enhanced selector
    enhanced_selector_widget, integration_widget = create_enhanced_model_selector(
        widget_manager, 
        model_data_path
    )
    
    # Keep existing widgets for compatibility
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
        'model_num': model_num_widget,
        'inpainting_model': inpainting_model_widget,
        'XL_models': XL_models_widget
    })
    
    # Create callback for XL toggle to reload enhanced selector
    def update_enhanced_XL_options(change, widget):
        """Update enhanced selector when XL toggle changes"""
        is_xl = change['new']
        
        # Reload model data
        model_files = '_xl-models-data.py' if is_xl else '_models-data.py'
        model_data_path = scripts_path / model_files
        
        if hasattr(widget_manager, 'enhanced_model_selector'):
            # Reload model data in enhanced selector
            widget_manager.enhanced_model_selector.model_data = widget_manager.enhanced_model_selector.load_model_data(model_data_path)
            
            # Update JavaScript with new data
            from IPython.display import display, Javascript
            display(Javascript(f'''
                if (window.modelSelector) {{
                    const newModelData = {json.dumps(widget_manager.enhanced_model_selector.model_data)};
                    window.modelSelector.loadModels(newModelData);
                }}
            '''))
    
    # Connect XL toggle callback
    widget_manager.factory.connect_widgets(
        [(XL_models_widget, 'value')], 
        update_enhanced_XL_options
    )
    
    return [
        model_header,
        enhanced_selector_widget,
        integration_widget,
        model_num_widget,
        options_panel
    ]


# Additional CSS for enhanced integration
ENHANCED_MODEL_CSS = '''
<style>
/* Enhanced Model Selector Integration */
.backup-selector {
    transition: all 0.3s ease;
}

.backup-selector select {
    min-height: 120px;
}

/* Smooth transitions between modes */
.enhanced-model-selector {
    transition: all 0.3s ease;
}

/* Model Selection Container */
.model-selection-container {
    display: flex;
    flex-direction: column;
    gap: 15px;
    padding: 20px;
    background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

/* Search and Filter Bar */
.model-filter-bar {
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 15px;
}

.model-search-input {
    flex: 1;
    min-width: 200px;
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.1);
    border: 2px solid rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    color: white;
    font-size: 14px;
    transition: all 0.3s ease;
}

.model-search-input:focus {
    border-color: var(--aw-accent-color);
    background: rgba(255, 255, 255, 0.15);
    outline: none;
}

.model-search-input::placeholder {
    color: rgba(255, 255, 255, 0.6);
}

/* Filter Chips */
.model-filter-chips {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.filter-chip {
    padding: 6px 12px;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 20px;
    color: white;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
    user-select: none;
}

.filter-chip:hover {
    background: rgba(255, 255, 255, 0.2);
}

.filter-chip.active {
    background: var(--aw-accent-color);
    border-color: var(--aw-accent-color);
    color: black;
}

/* Model Grid Layout */
.model-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px;
    max-height: 500px;
    overflow-y: auto;
    padding: 10px;
}

/* Model Card */
.model-card {
    position: relative;
    background: linear-gradient(145deg, #2d2d2d 0%, #1a1a1a 100%);
    border: 2px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 16px;
    cursor: pointer;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    overflow: hidden;
}

.model-card:hover {
    transform: translateY(-4px) scale(1.02);
    border-color: var(--aw-accent-color);
    box-shadow: 0 12px 40px rgba(255, 151, 239, 0.3);
}

.model-card.selected {
    border-color: var(--aw-accent-color);
    background: linear-gradient(145deg, #3a2d3a 0%, #2a1a2a 100%);
    box-shadow: 0 8px 32px rgba(255, 151, 239, 0.4);
}

.model-card.selected::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--aw-accent-color), #ff6b9d, var(--aw-accent-color));
    animation: shimmer 2s infinite;
}

@keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

/* Model Preview Image */
.model-preview {
    width: 100%;
    height: 120px;
    background: linear-gradient(45deg, #333, #555);
    border-radius: 12px;
    margin-bottom: 12px;
    overflow: hidden;
    position: relative;
}

.model-preview img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s ease;
}

.model-card:hover .model-preview img {
    transform: scale(1.1);
}

.model-preview-placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    color: rgba(255, 255, 255, 0.6);
    font-size: 24px;
}

/* Model Info */
.model-info {
    color: white;
}

.model-name {
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 8px;
    line-height: 1.3;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.model-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: 8px;
}

.model-tag {
    padding: 2px 6px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    font-size: 10px;
    color: rgba(255, 255, 255, 0.9);
}

.model-tag.inpainting {
    background: rgba(187, 202, 83, 0.8);
    color: black;
}

.model-tag.sdxl {
    background: rgba(234, 134, 26, 0.8);
    color: white;
}

.model-tag.nsfw {
    background: rgba(255, 107, 71, 0.8);
    color: white;
}

.model-stats {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: rgba(255, 255, 255, 0.7);
    margin-top: 8px;
}

/* Selection Counter */
.model-selection-counter {
    position: sticky;
    top: 0;
    background: rgba(0, 0, 0, 0.9);
    backdrop-filter: blur(10px);
    padding: 12px 16px;
    border-radius: 12px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 10;
}

.selection-count {
    color: var(--aw-accent-color);
    font-weight: 600;
}

.clear-selection-btn {
    padding: 6px 12px;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    color: white;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.clear-selection-btn:hover {
    background: rgba(255, 107, 71, 0.8);
}

/* Quick Select Buttons */
.quick-select-bar {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
    flex-wrap: wrap;
}

.quick-select-btn {
    padding: 8px 16px;
    background: linear-gradient(45deg, #4a4a4a, #363636);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    color: white;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
    user-select: none;
}

.quick-select-btn:hover {
    background: linear-gradient(45deg, var(--aw-accent-color), #ff6b9d);
    transform: translateY(-2px);
}

/* Notification integration */
.model-notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: linear-gradient(135deg, var(--aw-accent-color), #ff6b9d);
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    z-index: 1000;
    opacity: 0;
    transform: translateX(100%);
    transition: all 0.3s ease;
}

.model-notification.show {
    opacity: 1;
    transform: translateX(0);
}

/* Responsive design improvements */
@media (max-width: 768px) {
    .selector-mode-toggle {
        flex-direction: column;
        gap: 10px;
        align-items: flex-start;
    }
    
    .model-grid {
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 12px;
    }
    
    .model-filter-bar {
        flex-direction: column;
        align-items: stretch;
    }
    
    .model-search-input {
        min-width: unset;
    }
}

/* Loading Animation */
.model-grid.loading {
    position: relative;
}

.model-grid.loading::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 40px;
    height: 40px;
    border: 3px solid rgba(255, 255, 255, 0.3);
    border-top: 3px solid var(--aw-accent-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    transform: translate(-50%, -50%);
}

@keyframes spin {
    0% { transform: translate(-50%, -50%) rotate(0deg); }
    100% { transform: translate(-50%, -50%) rotate(360deg); }
}
</style>
'''