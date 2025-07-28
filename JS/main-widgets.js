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

// ===== ENHANCED MODEL SELECTOR JAVASCRIPT =====

class ModelSelector {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.models = [];
        this.selectedModels = new Set();
        this.filteredModels = [];
        this.filters = {
            search: '',
            category: 'all',
            type: 'all',
            version: 'all'
        };
        
        this.options = {
            maxSelection: options.maxSelection || 5,
            showPreviews: options.showPreviews !== false,
            allowMultiple: options.allowMultiple !== false,
            ...options
        };
        
        this.init();
    }
    
    init() {
        this.createInterface();
        this.bindEvents();
    }
    
    createInterface() {
        this.container.innerHTML = `
            <div class="model-selection-container">
                <div class="model-selection-counter">
                    <span class="selection-count">0 models selected</span>
                    <button class="clear-selection-btn" onclick="window.modelSelector.clearSelection()">
                        Clear All
                    </button>
                </div>
                
                <div class="quick-select-bar">
                    <button class="quick-select-btn" onclick="window.modelSelector.quickSelect('popular')">
                        ðŸ”¥ Popular
                    </button>
                    <button class="quick-select-btn" onclick="window.modelSelector.quickSelect('anime')">
                        ðŸŽ¨ Anime
                    </button>
                    <button class="quick-select-btn" onclick="window.modelSelector.quickSelect('realistic')">
                        ðŸ“¸ Realistic
                    </button>
                    <button class="quick-select-btn" onclick="window.modelSelector.quickSelect('inpainting')">
                        ðŸŽ­ Inpainting
                    </button>
                    <button class="quick-select-btn" onclick="window.modelSelector.quickSelect('sdxl')">
                        âš¡ SDXL
                    </button>
                </div>
                
                <div class="model-filter-bar">
                    <input 
                        type="text" 
                        class="model-search-input" 
                        placeholder="ðŸ” Search models..."
                        id="modelSearchInput"
                    >
                    <div class="model-filter-chips">
                        <div class="filter-chip active" data-filter="category" data-value="all">All</div>
                        <div class="filter-chip" data-filter="category" data-value="anime">Anime</div>
                        <div class="filter-chip" data-filter="category" data-value="realistic">Realistic</div>
                        <div class="filter-chip" data-filter="category" data-value="artistic">Artistic</div>
                        <div class="filter-chip" data-filter="type" data-value="inpainting">Inpainting</div>
                        <div class="filter-chip" data-filter="version" data-value="sdxl">SDXL</div>
                    </div>
                </div>
                
                <div class="model-grid" id="modelGrid">
                    <!-- Models will be populated here -->
                </div>
            </div>
        `;
    }
    
    bindEvents() {
        // Search input
        const searchInput = document.getElementById('modelSearchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filters.search = e.target.value.toLowerCase();
                this.filterModels();
            });
        }
        
        // Filter chips
        document.querySelectorAll('.filter-chip').forEach(chip => {
            chip.addEventListener('click', (e) => {
                const filterType = e.target.dataset.filter;
                const filterValue = e.target.dataset.value;
                
                // Update active state
                if (filterType) {
                    document.querySelectorAll(`[data-filter="${filterType}"]`).forEach(c => c.classList.remove('active'));
                    e.target.classList.add('active');
                    this.filters[filterType] = filterValue;
                } else {
                    // Toggle filter
                    e.target.classList.toggle('active');
                }
                
                this.filterModels();
            });
        });
    }
    
    loadModels(modelData) {
        this.models = this.parseModelData(modelData);
        this.filteredModels = [...this.models];
        this.renderModels();
    }
    
    parseModelData(modelData) {
        return Object.entries(modelData).map(([key, data], index) => {
            const name = key;
            const isInpainting = name.toLowerCase().includes('inpainting') || (data && data.inpainting);
            const isSDXL = name.toLowerCase().includes('xl') || name.toLowerCase().includes('sdxl');
            const isNSFW = name.toLowerCase().includes('nsfw') || name.toLowerCase().includes('porn');
            
            // Determine category
            let category = 'realistic';
            if (name.toLowerCase().includes('anime') || name.toLowerCase().includes('counterfeit')) {
                category = 'anime';
            } else if (name.toLowerCase().includes('artistic') || name.toLowerCase().includes('art')) {
                category = 'artistic';
            }
            
            return {
                id: `model_${index}`,
                name: name,
                url: data ? data.url : '',
                filename: (data && data.name) ? data.name : '',
                category: category,
                tags: [
                    ...(isInpainting ? ['inpainting'] : []),
                    ...(isSDXL ? ['sdxl'] : ['sd1.5']),
                    ...(isNSFW ? ['nsfw'] : []),
                    category
                ],
                isInpainting,
                isSDXL,
                isNSFW,
                preview: this.getModelPreview(name, category),
                stats: {
                    size: this.estimateSize(data),
                    type: isSDXL ? 'SDXL' : 'SD 1.5'
                }
            };
        });
    }
    
    getModelPreview(name, category) {
        // Generate preview URLs based on model name/category
        const previewMap = {
            'anime': 'https://via.placeholder.com/280x120/ff97ef/ffffff?text=Anime+Style',
            'realistic': 'https://via.placeholder.com/280x120/4a90e2/ffffff?text=Realistic',
            'artistic': 'https://via.placeholder.com/280x120/f5a623/ffffff?text=Artistic'
        };
        
        return previewMap[category] || previewMap['realistic'];
    }
    
    estimateSize(data) {
        // Estimate file size based on model type
        if (data && data.name && data.name.includes('xl')) return '6.5GB';
        if (data && data.name && data.name.includes('inpainting')) return '4.2GB';
        return '2.1GB';
    }
    
    filterModels() {
        this.filteredModels = this.models.filter(model => {
            // Search filter
            if (this.filters.search && !model.name.toLowerCase().includes(this.filters.search)) {
                return false;
            }
            
            // Category filter
            if (this.filters.category !== 'all' && model.category !== this.filters.category) {
                return false;
            }
            
            // Type filter
            if (this.filters.type === 'inpainting' && !model.isInpainting) {
                return false;
            }
            
            // Version filter
            if (this.filters.version === 'sdxl' && !model.isSDXL) {
                return false;
            }
            
            return true;
        });
        
        this.renderModels();
    }
    
    renderModels() {
        const grid = document.getElementById('modelGrid');
        if (!grid) return;
        
        if (this.filteredModels.length === 0) {
            grid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; color: rgba(255,255,255,0.6); padding: 40px;">
                    <div style="font-size: 48px; margin-bottom: 16px;">ðŸ”</div>
                    <div>No models found matching your criteria</div>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = this.filteredModels.map(model => `
            <div class="model-card ${this.selectedModels.has(model.id) ? 'selected' : ''}" 
                 data-model-id="${model.id}"
                 onclick="window.modelSelector.toggleModel('${model.id}')">
                
                <div class="model-preview">
                    ${this.options.showPreviews ? 
                        `<img src="${model.preview}" alt="${model.name}" onerror="this.style.display='none'">` :
                        `<div class="model-preview-placeholder">ðŸŽ¨</div>`
                    }
                </div>
                
                <div class="model-info">
                    <div class="model-name">${this.truncateText(model.name, 60)}</div>
                    
                    <div class="model-tags">
                        ${model.tags.map(tag => 
                            `<span class="model-tag ${tag}">${this.formatTag(tag)}</span>`
                        ).join('')}
                    </div>
                    
                    <div class="model-stats">
                        <span>${model.stats.type}</span>
                        <span>${model.stats.size}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    toggleModel(modelId) {
        if (this.selectedModels.has(modelId)) {
            this.selectedModels.delete(modelId);
        } else {
            if (!this.options.allowMultiple) {
                this.selectedModels.clear();
            } else if (this.selectedModels.size >= this.options.maxSelection) {
                this.showNotification(`Maximum ${this.options.maxSelection} models can be selected`, 'warning');
                return;
            }
            this.selectedModels.add(modelId);
        }
        
        this.updateSelection();
        this.updatePythonWidget();
    }
    
    updateSelection() {
        // Update visual selection
        document.querySelectorAll('.model-card').forEach(card => {
            const modelId = card.dataset.modelId;
            card.classList.toggle('selected', this.selectedModels.has(modelId));
        });
        
        // Update counter
        const counter = document.querySelector('.selection-count');
        if (counter) {
            const count = this.selectedModels.size;
            counter.textContent = `${count} model${count !== 1 ? 's' : ''} selected`;
        }
        
        // Update clear button visibility
        const clearBtn = document.querySelector('.clear-selection-btn');
        if (clearBtn) {
            clearBtn.style.opacity = this.selectedModels.size > 0 ? '1' : '0.5';
        }
    }
    
    updatePythonWidget() {
        // Get selected model names
        const selectedNames = Array.from(this.selectedModels).map(id => {
            const model = this.models.find(m => m.id === id);
            return model ? model.name : null;
        }).filter(Boolean);
        
        // Update the Python widget (if available)
        if (window.updatePythonModelWidget) {
            window.updatePythonModelWidget(selectedNames);
        }
        
        // Trigger custom event
        window.dispatchEvent(new CustomEvent('modelSelectionChanged', {
            detail: { selectedModels: selectedNames }
        }));
    }
    
    quickSelect(type) {
        this.clearSelection();
        
        let modelsToSelect = [];
        
        switch(type) {
            case 'popular':
                modelsToSelect = this.models.filter(m => 
                    m.name.toLowerCase().includes('counterfeit') ||
                    m.name.toLowerCase().includes('merged') ||
                    m.name.toLowerCase().includes('d5k')
                ).slice(0, 3);
                break;
                
            case 'anime':
                modelsToSelect = this.models.filter(m => m.category === 'anime').slice(0, 3);
                break;
                
            case 'realistic':
                modelsToSelect = this.models.filter(m => m.category === 'realistic').slice(0, 3);
                break;
                
            case 'inpainting':
                modelsToSelect = this.models.filter(m => m.isInpainting).slice(0, 3);
                break;
                
            case 'sdxl':
                modelsToSelect = this.models.filter(m => m.isSDXL).slice(0, 3);
                break;
        }
        
        modelsToSelect.forEach(model => this.selectedModels.add(model.id));
        this.updateSelection();
        this.updatePythonWidget();
    }
    
    clearSelection() {
        this.selectedModels.clear();
        this.updateSelection();
        this.updatePythonWidget();
    }
    
    getSelectedModels() {
        return Array.from(this.selectedModels).map(id => {
            return this.models.find(m => m.id === id);
        }).filter(Boolean);
    }
    
    // Utility functions
    truncateText(text, maxLength) {
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }
    
    formatTag(tag) {
        const tagMap = {
            'inpainting': 'ðŸŽ­',
            'sdxl': 'âš¡',
            'sd1.5': 'ðŸ”¹',
            'nsfw': 'ðŸ”ž',
            'anime': 'ðŸŽ¨',
            'realistic': 'ðŸ“¸',
            'artistic': 'ðŸŽª'
        };
        
        return tagMap[tag] || tag;
    }
    
    showNotification(message, type = 'info') {
        // Integration with existing notification system
        if (window.showNotificationFromJS) {
            window.showNotificationFromJS(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }
}

// Initialize when DOM is ready
let modelSelector;

function initializeModelSelector(modelData, containerId = 'enhanced-model-selector') {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with ID "${containerId}" not found`);
        return null;
    }
    
    modelSelector = new ModelSelector(containerId, {
        maxSelection: 5,
        showPreviews: true,
        allowMultiple: true
    });
    
    modelSelector.loadModels(modelData);
    return modelSelector;
}

// Python integration function
function updateModelSelection(selectedModels) {
    // This function can be called from Python to update the selection
    if (window.updatePythonModelWidget) {
        window.updatePythonModelWidget(selectedModels);
    }
}

// Make functions globally available
window.initializeModelSelector = initializeModelSelector;
window.updateModelSelection = updateModelSelection;
