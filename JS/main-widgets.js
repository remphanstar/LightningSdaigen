// Enhanced Widget Manager for UI interactions
class EnhancedWidgetManager {
    constructor() {
        this.selectedModels = new Set();
        this.selectedVAE = null;
        this.selectedLoras = new Set();
        this.isSDXL = false;
        this.isInpainting = false;
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadSavedSettings();
        this.updateUI();
    }
    
    setupEventListeners() {
        // Model selection handlers
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('model-checkbox')) {
                this.handleModelSelection(e.target);
            }
        });
        
        // SDXL/Inpainting toggle handlers
        document.addEventListener('change', (e) => {
            if (e.target.id === 'sdxl-toggle') {
                this.toggleSDXL(e.target.checked);
            } else if (e.target.id === 'inpainting-toggle') {
                this.toggleInpainting(e.target.checked);
            }
        });
        
        // Auto-save settings
        document.addEventListener('change', () => {
            this.saveSettings();
        });
    }
    
    handleModelSelection(checkbox) {
        const modelId = checkbox.dataset.modelId;
        const modelType = checkbox.dataset.modelType;
        
        if (checkbox.checked) {
            this.selectedModels.add(modelId);
            
            // Auto-detect SDXL/Inpainting from model name
            if (modelType === 'sdxl' || checkbox.dataset.modelName.toLowerCase().includes('xl')) {
                this.setSDXL(true);
            }
            if (modelType === 'inpaint' || checkbox.dataset.modelName.toLowerCase().includes('inpaint')) {
                this.setInpainting(true);
            }
        } else {
            this.selectedModels.delete(modelId);
        }
        
        this.updateModelCounter();
        this.showNotification(`Model ${checkbox.checked ? 'selected' : 'deselected'}: ${checkbox.dataset.modelName}`, 'success');
    }
    
    toggleSDXL(enabled) {
        this.isSDXL = enabled;
        this.updateCompatibleModels();
        this.showNotification(`SDXL mode ${enabled ? 'enabled' : 'disabled'}`, enabled ? 'success' : 'warning');
    }
    
    toggleInpainting(enabled) {
        this.isInpainting = enabled;
        this.updateCompatibleModels();
        this.showNotification(`Inpainting mode ${enabled ? 'enabled' : 'disabled'}`, enabled ? 'success' : 'warning');
    }
    
    updateCompatibleModels() {
        const modelCheckboxes = document.querySelectorAll('.model-checkbox');
        
        modelCheckboxes.forEach(checkbox => {
            const modelType = checkbox.dataset.modelType;
            const modelName = checkbox.dataset.modelName.toLowerCase();
            
            let isCompatible = true;
            
            if (this.isSDXL && !modelName.includes('xl') && modelType !== 'sdxl') {
                isCompatible = false;
            }
            
            if (this.isInpainting && !modelName.includes('inpaint') && modelType !== 'inpaint') {
                isCompatible = false;
            }
            
            const option = checkbox.closest('.multiselect-option');
            option.style.opacity = isCompatible ? '1' : '0.4';
            checkbox.disabled = !isCompatible;
        });
    }
    
    updateModelCounter() {
        const counter = document.querySelector('.model-counter');
        if (counter) {
            counter.textContent = `${this.selectedModels.size} selected`;
        }
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="width: 6px; height: 6px; border-radius: 50%; background: currentColor;"></div>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Trigger animation
        setTimeout(() => notification.classList.add('show'), 100);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    saveSettings() {
        const settings = {
            selectedModels: Array.from(this.selectedModels),
            selectedVAE: this.selectedVAE,
            selectedLoras: Array.from(this.selectedLoras),
            isSDXL: this.isSDXL,
            isInpainting: this.isInpainting,
            timestamp: Date.now()
        };
        
        localStorage.setItem('widgetSettings', JSON.stringify(settings));
    }
    
    loadSavedSettings() {
        try {
            const saved = localStorage.getItem('widgetSettings');
            if (saved) {
                const settings = JSON.parse(saved);
                this.selectedModels = new Set(settings.selectedModels || []);
                this.selectedVAE = settings.selectedVAE;
                this.selectedLoras = new Set(settings.selectedLoras || []);
                this.isSDXL = settings.isSDXL || false;
                this.isInpainting = settings.isInpainting || false;
            }
        } catch (e) {
            console.warn('Failed to load saved settings:', e);
        }
    }
    
    exportSettings() {
        const settings = {
            selectedModels: Array.from(this.selectedModels),
            selectedVAE: this.selectedVAE,
            selectedLoras: Array.from(this.selectedLoras),
            isSDXL: this.isSDXL,
            isInpainting: this.isInpainting,
            exportDate: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(settings, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `widget-settings-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
        this.showNotification('Settings exported successfully!', 'success');
    }
    
    importSettings(fileInput) {
        const file = fileInput.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const settings = JSON.parse(e.target.result);
                this.selectedModels = new Set(settings.selectedModels || []);
                this.selectedVAE = settings.selectedVAE;
                this.selectedLoras = new Set(settings.selectedLoras || []);
                this.isSDXL = settings.isSDXL || false;
                this.isInpainting = settings.isInpainting || false;
                
                this.updateUI();
                this.saveSettings();
                this.showNotification('Settings imported successfully!', 'success');
            } catch (err) {
                this.showNotification('Failed to import settings. Invalid file format.', 'error');
            }
        };
        reader.readAsText(file);
    }
    
    updateUI() {
        // Update checkboxes based on selected items
        document.querySelectorAll('.model-checkbox').forEach(checkbox => {
            checkbox.checked = this.selectedModels.has(checkbox.dataset.modelId);
        });
        
        // Update toggle switches
        const sdxlToggle = document.querySelector('#sdxl-toggle');
        const inpaintToggle = document.querySelector('#inpainting-toggle');
        if (sdxlToggle) sdxlToggle.checked = this.isSDXL;
        if (inpaintToggle) inpaintToggle.checked = this.isInpainting;
        
        this.updateModelCounter();
        this.updateCompatibleModels();
    }
    
    selectAllModels(type = 'all') {
        const checkboxes = document.querySelectorAll('.model-checkbox');
        
        checkboxes.forEach(checkbox => {
            if (type === 'all' || checkbox.dataset.modelType === type) {
                checkbox.checked = true;
                this.selectedModels.add(checkbox.dataset.modelId);
            }
        });
        
        this.updateModelCounter();
        this.showNotification(`Selected all ${type} models`, 'success');
    }
    
    clearAllSelections() {
        this.selectedModels.clear();
        this.selectedLoras.clear();
        
        document.querySelectorAll('.model-checkbox, .lora-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        this.updateModelCounter();
        this.showNotification('All selections cleared', 'warning');
    }
}

// Initialize the enhanced widget manager
const widgetManager = new EnhancedWidgetManager();

// Global functions for widget interaction
function exportSettings() {
    widgetManager.exportSettings();
}

function importSettings() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e) => widgetManager.importSettings(e.target);
    input.click();
}

function selectAllModels(type) {
    widgetManager.selectAllModels(type);
}

function clearAllSelections() {
    widgetManager.clearAllSelections();
}

// Enhanced search functionality
function setupSearch() {
    const searchInputs = document.querySelectorAll('.search-input');
    
    searchInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const container = e.target.closest('.widget-card');
            const options = container.querySelectorAll('.multiselect-option');
            
            options.forEach(option => {
                const text = option.textContent.toLowerCase();
                const matches = text.includes(query);
                option.style.display = matches ? 'flex' : 'none';
            });
        });
    });
}

// Initialize search when DOM is ready
document.addEventListener('DOMContentLoaded', setupSearch);
