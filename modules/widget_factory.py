# ~ widget_factory.py | Enhanced Widget Factory for 10WebUI System | by ANXETY ~

import ipywidgets as widgets
from IPython.display import display, HTML, Javascript
import json_utils as js
from pathlib import Path
import os
import re
from typing import List, Dict, Any, Optional, Union, Callable

# Safe imports with fallbacks
try:
    from webui_utils import (get_webui_features, is_webui_supported, get_webui_category,
                           get_available_webuis, get_webuis_by_category)
    WEBUI_UTILS_AVAILABLE = True
except ImportError:
    WEBUI_UTILS_AVAILABLE = False
    # Fallback functions
    def get_webui_features(ui): return {'supports_models': True, 'supports_extensions': True}
    def is_webui_supported(ui, feature): return True
    def get_webui_category(ui): return 'standard_sd'
    def get_available_webuis(): return ['A1111', 'ComfyUI', 'Classic', 'Lightning.ai']
    def get_webuis_by_category(): return {'standard_sd': ['A1111', 'ComfyUI', 'Classic', 'Lightning.ai']}

# Environment paths
osENV = os.environ
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}

try:
    HOME = PATHS['home_path']
    SCR_PATH = PATHS['scr_path']
    SETTINGS_PATH = PATHS['settings_path']
except KeyError:
    # Fallback paths
    HOME = Path.cwd()
    SCR_PATH = HOME / 'ANXETY'
    SETTINGS_PATH = SCR_PATH / 'settings.json'

class WidgetFactory:
    """Enhanced widget factory with WebUI-aware capabilities and modern styling."""
    
    def __init__(self):
        """Initialize the widget factory with enhanced capabilities."""
        
        self.current_webui = self._get_current_webui()
        self.widget_cache = {}
        self.event_handlers = {}
        self.custom_styles = self._load_custom_styles()
        
        # Enhanced widget styling
        self.default_layout = widgets.Layout(width='auto', margin='2px')
        self.full_width_layout = widgets.Layout(width='100%', margin='2px')
        self.compact_layout = widgets.Layout(width='150px', margin='2px')
        
        # Widget themes
        self.themes = {
            'default': {
                'primary_color': '#007bff',
                'success_color': '#28a745',
                'warning_color': '#ffc107',
                'danger_color': '#dc3545',
                'dark_color': '#343a40'
            },
            'dark': {
                'primary_color': '#0d6efd',
                'success_color': '#198754',
                'warning_color': '#fd7e14',
                'danger_color': '#dc3545',
                'dark_color': '#212529'
            }
        }
        
        self.current_theme = 'default'
        
        print("✅ Enhanced Widget Factory initialized")
    
    def _get_current_webui(self) -> str:
        """Get current WebUI selection."""
        try:
            return js.read(SETTINGS_PATH, 'WEBUI.current') or 'A1111'
        except:
            return 'A1111'
    
    def _load_custom_styles(self) -> str:
        """Load custom CSS styles from file."""
        try:
            css_path = SCR_PATH / 'CSS' / 'main-widgets.css'
            if css_path.exists():
                with open(css_path, 'r') as f:
                    return f.read()
        except Exception as e:
            print(f"⚠️ Could not load custom styles: {e}")
        
        # Fallback default styles
        return """
        .widget-container { margin: 5px 0; }
        .category-header { 
            font-weight: bold; 
            color: #4CAF50; 
            margin: 15px 0 5px 0; 
            font-size: 16px;
        }
        .webui-info { 
            background: #f8f9fa; 
            padding: 10px; 
            border-radius: 6px; 
            margin: 8px 0;
            border-left: 4px solid #007bff;
        }
        .feature-disabled {
            opacity: 0.6;
            background: #f5f5f5;
        }
        .warning-box {
            background: #fff3cd;
            color: #856404;
            padding: 8px;
            border-radius: 4px;
            border: 1px solid #ffeaa7;
        }
        """
    
    def apply_custom_styles(self):
        """Apply custom CSS styles to the notebook."""
        display(HTML(f'<style>{self.custom_styles}</style>'))
    
    def create_header(self, text: str, level: int = 3, 
                     style: str = None, icon: str = None) -> widgets.HTML:
        """Create enhanced header widget with icons and styling."""
        
        icon_html = f'<span style="margin-right: 8px;">{icon}</span>' if icon else ''
        
        if style:
            style_attr = f'style="{style}"'
        else:
            style_attr = 'class="category-header"'
        
        html_content = f'<h{level} {style_attr}>{icon_html}{text}</h{level}>'
        
        return widgets.HTML(
            value=html_content,
            layout=self.full_width_layout
        )
    
    def create_info_box(self, content: str, box_type: str = 'info', 
                       dismissible: bool = False) -> widgets.HTML
