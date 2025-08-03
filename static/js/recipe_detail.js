class RecipeDetailManager {
    constructor() {
        this.recipe = null;
        this.uploadedImages = [];
        this.editingMode = false;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadRecipe();
    }

    bindEvents() {
        // Edit and delete buttons
        const editBtn = document.getElementById('editRecipeBtn');
        const deleteBtn = document.getElementById('deleteRecipeBtn');
        
        if (editBtn) {
            editBtn.addEventListener('click', () => this.startEditing());
        }
        
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => this.deleteRecipe());
        }

        // Modal controls
        const closeModal = document.getElementById('closeModal');
        const cancelBtn = document.getElementById('cancelBtn');
        
        if (closeModal) {
            closeModal.addEventListener('click', () => this.closeModal());
        }
        
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.closeModal());
        }

        // Form submission
        const recipeForm = document.getElementById('recipeForm');
        if (recipeForm) {
            recipeForm.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // Dynamic form elements
        const addIngredient = document.getElementById('addIngredient');
        const addInstruction = document.getElementById('addInstruction');
        const addApplianceSetting = document.getElementById('addApplianceSetting');
        
        if (addIngredient) {
            addIngredient.addEventListener('click', () => this.addIngredientRow());
        }
        
        if (addInstruction) {
            addInstruction.addEventListener('click', () => this.addInstructionRow());
        }
        
        if (addApplianceSetting) {
            addApplianceSetting.addEventListener('click', () => this.addApplianceSettingRow());
        }

        // Image upload
        const imageUpload = document.getElementById('imageUpload');
        if (imageUpload) {
            imageUpload.addEventListener('change', (e) => this.handleImageUpload(e));
        }

        // Close modal on outside click
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal();
            }
        });

        // Lightbox events
        const lightboxClose = document.querySelector('.lightbox-close');
        if (lightboxClose) {
            lightboxClose.addEventListener('click', () => this.closeLightbox());
        }
        
        // Close lightbox on background click
        const lightbox = document.getElementById('imageLightbox');
        if (lightbox) {
            lightbox.addEventListener('click', (e) => {
                if (e.target === lightbox) {
                    this.closeLightbox();
                }
            });
        }

        // ESC key handlers
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeLightbox();
                this.closeModal();
            }
        });
    }

    async loadRecipe() {
        try {
            this.showLoading(true);
            
            const response = await fetch(`/api/recipes/${window.RECIPE_ID}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.recipe = await response.json();
            this.renderRecipe();
            
        } catch (error) {
            console.error('Error loading recipe:', error);
            this.showError();
        } finally {
            this.showLoading(false);
        }
    }

    renderRecipe() {
        if (!this.recipe) return;

        // Update page title
        document.title = `${this.recipe.title} - Recipe Management`;
        
        // Update recipe title and description
        const titleEl = document.getElementById('recipeTitle');
        const descEl = document.getElementById('recipeDescription');
        
        if (titleEl) titleEl.textContent = this.recipe.title;
        if (descEl && this.recipe.description) {
            descEl.textContent = this.recipe.description;
            descEl.style.display = 'block';
        }

        // Render images
        this.renderImages();
        
        // Render meta information
        this.renderMeta();
        
        // Render sections
        this.renderIngredients();
        this.renderInstructions();
        this.renderApplianceSettings();
        this.renderTags();
        this.renderMealTimes();
        this.renderSource();

        // Show the content
        const content = document.getElementById('recipeContent');
        if (content) content.style.display = 'block';
    }

    renderImages() {
        const imagesContainer = document.getElementById('recipeImages');
        if (!imagesContainer) return;

        if (this.recipe.images && this.recipe.images.length > 0) {
            imagesContainer.innerHTML = `
                <div class="recipe-image-gallery">
                    ${this.recipe.images.map(imageUrl => `
                        <div class="recipe-image-item" onclick="window.recipeDetailManager.showImageLightbox('${imageUrl}')">
                            <img src="${imageUrl}" alt="${this.escapeHtml(this.recipe.title)}" />
                        </div>
                    `).join('')}
                </div>
            `;
            imagesContainer.style.display = 'block';
        } else {
            imagesContainer.style.display = 'none';
        }
    }

    renderMeta() {
        const metaContainer = document.getElementById('recipeMeta');
        if (!metaContainer) return;

        const metaItems = [];
        
        if (this.recipe.prep_time) {
            metaItems.push({
                icon: 'fas fa-clock',
                label: 'Prep Time',
                value: `${this.recipe.prep_time} min`
            });
        }
        
        if (this.recipe.cook_time) {
            metaItems.push({
                icon: 'fas fa-fire',
                label: 'Cook Time',
                value: `${this.recipe.cook_time} min`
            });
        }
        
        if (this.recipe.prep_time && this.recipe.cook_time) {
            metaItems.push({
                icon: 'fas fa-hourglass-half',
                label: 'Total Time',
                value: `${this.recipe.prep_time + this.recipe.cook_time} min`
            });
        }
        
        if (this.recipe.servings) {
            metaItems.push({
                icon: 'fas fa-users',
                label: 'Servings',
                value: this.recipe.servings
            });
        }
        
        if (this.recipe.difficulty) {
            metaItems.push({
                icon: 'fas fa-signal',
                label: 'Difficulty',
                value: this.capitalize(this.recipe.difficulty)
            });
        }

        if (metaItems.length > 0) {
            metaContainer.innerHTML = metaItems.map(item => `
                <div class="meta-item">
                    <i class="${item.icon}"></i>
                    <div class="meta-content">
                        <div class="meta-value">${item.value}</div>
                        <div class="meta-label">${item.label}</div>
                    </div>
                </div>
            `).join('');
            metaContainer.style.display = 'grid';
        } else {
            metaContainer.style.display = 'none';
        }
    }

    renderIngredients() {
        const section = document.getElementById('ingredientsSection');
        const list = document.getElementById('ingredientsList');
        
        if (!section || !list) return;

        if (this.recipe.ingredients && this.recipe.ingredients.length > 0) {
            list.innerHTML = `
                <ul class="ingredients-list">
                    ${this.recipe.ingredients.map(ing => `
                        <li class="ingredient-item">
                            <span class="ingredient-name">${this.escapeHtml(ing.name)}</span>
                            <span class="ingredient-amount">${this.escapeHtml(ing.amount)}${ing.unit ? ` ${this.escapeHtml(ing.unit)}` : ''}</span>
                        </li>
                    `).join('')}
                </ul>
            `;
            section.style.display = 'block';
        } else {
            section.style.display = 'none';
        }
    }

    renderInstructions() {
        const section = document.getElementById('instructionsSection');
        const list = document.getElementById('instructionsList');
        
        if (!section || !list) return;

        if (this.recipe.instructions && this.recipe.instructions.length > 0) {
            list.innerHTML = `
                <ol class="instructions-list">
                    ${this.recipe.instructions.map(inst => `
                        <li class="instruction-item">${this.escapeHtml(inst)}</li>
                    `).join('')}
                </ol>
            `;
            section.style.display = 'block';
        } else {
            section.style.display = 'none';
        }
    }

    renderApplianceSettings() {
        const section = document.getElementById('applianceSection');
        const container = document.getElementById('applianceSettings');
        
        if (!section || !container) return;

        if (this.recipe.appliance_settings && this.recipe.appliance_settings.length > 0) {
            container.innerHTML = this.recipe.appliance_settings.map(setting => 
                this.renderApplianceSettingDetail(setting)
            ).join('');
            section.style.display = 'block';
        } else {
            section.style.display = 'none';
        }
    }

    renderTags() {
        const section = document.getElementById('tagsSection');
        const list = document.getElementById('tagsList');
        
        if (!section || !list) return;

        if (this.recipe.tags && this.recipe.tags.length > 0) {
            list.innerHTML = this.recipe.tags.map(tag => 
                `<span class="tag">${this.escapeHtml(tag)}</span>`
            ).join('');
            section.style.display = 'block';
        } else {
            section.style.display = 'none';
        }
    }

    renderMealTimes() {
        const section = document.getElementById('mealTimesSection');
        const list = document.getElementById('mealTimesList');
        
        if (!section || !list) return;

        if (this.recipe.meal_times && this.recipe.meal_times.length > 0) {
            list.innerHTML = this.recipe.meal_times.map(mealTime => 
                `<span class="tag meal-time-tag">${this.escapeHtml(this.capitalize(mealTime))}</span>`
            ).join('');
            section.style.display = 'block';
        } else {
            section.style.display = 'none';
        }
    }

    renderSource() {
        const section = document.getElementById('sourceSection');
        const info = document.getElementById('sourceInfo');
        
        if (!section || !info) return;

        if (this.recipe.source && (this.recipe.source.url || this.recipe.source.name)) {
            info.innerHTML = `
                <p>
                    ${this.recipe.source.name ? this.escapeHtml(this.recipe.source.name) : this.capitalize(this.recipe.source.type || 'Unknown')}
                    ${this.recipe.source.url ? `<br><a href="${this.recipe.source.url}" target="_blank" class="source-link">${this.recipe.source.url}</a>` : ''}
                </p>
            `;
            section.style.display = 'block';
        } else {
            section.style.display = 'none';
        }
    }

    renderApplianceSettingDetail(setting) {
        const applianceTypeLabel = this.getApplianceTypeLabel(setting.appliance_type);
        let settingDetails = `<div class="appliance-setting-detail">
            <div class="appliance-setting-title">
                <i class="fas fa-fire"></i> ${applianceTypeLabel}
            </div>
            <div class="appliance-setting-info">`;

        // Add specific fields based on appliance type
        if (setting.flame_level) {
            settingDetails += `<span><strong>Flame Level:</strong> ${this.escapeHtml(setting.flame_level)}</span>`;
        }
        if (setting.heat_level) {
            settingDetails += `<span><strong>Heat Level:</strong> ${this.escapeHtml(setting.heat_level)}</span>`;
        }
        if (setting.temperature_celsius) {
            settingDetails += `<span><strong>Temperature:</strong> ${setting.temperature_celsius}°C</span>`;
        }
        if (setting.power_level) {
            settingDetails += `<span><strong>Power Level:</strong> ${setting.power_level}/10</span>`;
        }
        if (setting.duration_minutes) {
            settingDetails += `<span><strong>Duration:</strong> ${setting.duration_minutes} min</span>`;
        }
        if (setting.heat_zone) {
            settingDetails += `<span><strong>Heat Zone:</strong> ${this.escapeHtml(setting.heat_zone)}</span>`;
        }
        if (setting.rack_position) {
            settingDetails += `<span><strong>Rack Position:</strong> ${this.escapeHtml(setting.rack_position)}</span>`;
        }
        if (setting.lid_position) {
            settingDetails += `<span><strong>Lid Position:</strong> ${this.escapeHtml(setting.lid_position)}</span>`;
        }
        if (setting.preheat_required !== undefined) {
            settingDetails += `<span><strong>Preheat:</strong> ${setting.preheat_required ? 'Yes' : 'No'}</span>`;
        }
        if (setting.convection !== undefined) {
            settingDetails += `<span><strong>Convection:</strong> ${setting.convection ? 'Yes' : 'No'}</span>`;
        }
        if (setting.shake_interval_minutes) {
            settingDetails += `<span><strong>Shake Every:</strong> ${setting.shake_interval_minutes} min</span>`;
        }

        settingDetails += `</div>`;

        // Add utensils if any
        if (setting.utensils && setting.utensils.length > 0) {
            settingDetails += `<div class="appliance-utensils">
                <strong>Utensils:</strong>
                <ul>
                    ${setting.utensils.map(utensil => {
                        let utensilText = this.escapeHtml(utensil.type);
                        if (utensil.size) utensilText += ` (${this.escapeHtml(utensil.size)})`;
                        if (utensil.material) utensilText += ` - ${this.escapeHtml(utensil.material)}`;
                        return `<li>${utensilText}</li>`;
                    }).join('')}
                </ul>
            </div>`;
        }

        // Add notes if any
        if (setting.notes) {
            settingDetails += `<div class="appliance-notes">
                <strong>Notes:</strong> ${this.escapeHtml(setting.notes)}
            </div>`;
        }

        settingDetails += `</div>`;
        return settingDetails;
    }

    startEditing() {
        this.editingMode = true;
        this.populateForm(this.recipe);
        this.showModal();
    }

    async deleteRecipe() {
        if (!confirm('Are you sure you want to delete this recipe? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/recipes/${window.RECIPE_ID}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.showSuccess('Recipe deleted successfully!');
                // Redirect to home page after deletion
                setTimeout(() => {
                    window.location.href = '/';
                }, 1500);
            } else {
                throw new Error('Failed to delete recipe');
            }
        } catch (error) {
            console.error('Error deleting recipe:', error);
            this.showError('Failed to delete recipe');
        }
    }

    showModal() {
        const modal = document.getElementById('recipeModal');
        if (modal) {
            modal.style.display = 'block';
        }
    }

    closeModal() {
        const modal = document.getElementById('recipeModal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.editingMode = false;
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        try {
            const formData = new FormData(e.target);
            const recipeData = this.formDataToRecipe(formData);
            
            const response = await fetch(`/api/recipes/${window.RECIPE_ID}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(recipeData)
            });
            
            if (response.ok) {
                this.recipe = await response.json();
                this.renderRecipe();
                this.closeModal();
                this.showSuccess('Recipe updated successfully!');
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to update recipe');
            }
        } catch (error) {
            console.error('Error saving recipe:', error);
            this.showError(error.message || 'Failed to save recipe');
        }
    }

    // Lightbox functionality
    showImageLightbox(imageUrl) {
        const lightbox = document.getElementById('imageLightbox');
        const lightboxImage = document.getElementById('lightboxImage');
        
        if (lightbox && lightboxImage) {
            lightboxImage.src = imageUrl;
            lightbox.style.display = 'block';
        }
    }

    closeLightbox() {
        const lightbox = document.getElementById('imageLightbox');
        if (lightbox) {
            lightbox.style.display = 'none';
        }
    }

    // Form helpers (reusing methods from main app.js)
    formDataToRecipe(formData) {
        const recipe = {};
        
        // Basic fields
        recipe.title = formData.get('title');
        recipe.description = formData.get('description') || null;
        recipe.prep_time = formData.get('prep_time') ? parseInt(formData.get('prep_time')) : null;
        recipe.cook_time = formData.get('cook_time') ? parseInt(formData.get('cook_time')) : null;
        recipe.servings = formData.get('servings') ? parseInt(formData.get('servings')) : null;
        recipe.difficulty = formData.get('difficulty') || null;
        
        // Tags
        const tagsStr = formData.get('tags');
        recipe.tags = tagsStr ? tagsStr.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
        
        // Meal times
        const mealTimeCheckboxes = document.querySelectorAll('.meal-time-checkbox:checked');
        recipe.meal_times = Array.from(mealTimeCheckboxes).map(checkbox => checkbox.value);
        
        // Source
        recipe.source = {
            type: formData.get('source_type') || 'manual',
            url: formData.get('source_url') || null,
            name: formData.get('source_name') || null
        };
        
        // Ingredients
        recipe.ingredients = this.getIngredientsFromForm();
        
        // Instructions
        recipe.instructions = this.getInstructionsFromForm();
        
        // Appliance Settings
        recipe.appliance_settings = this.getApplianceSettingsFromForm();
        
        // Images
        recipe.images = this.uploadedImages || this.recipe.images || [];
        
        return recipe;
    }

    populateForm(recipe) {
        // Basic fields
        const titleEl = document.getElementById('title');
        const descEl = document.getElementById('description');
        const prepTimeEl = document.getElementById('prepTime');
        const cookTimeEl = document.getElementById('cookTime');
        const servingsEl = document.getElementById('servings');
        const difficultyEl = document.getElementById('difficulty');
        const tagsEl = document.getElementById('tags');
        
        if (titleEl) titleEl.value = recipe.title || '';
        if (descEl) descEl.value = recipe.description || '';
        if (prepTimeEl) prepTimeEl.value = recipe.prep_time || '';
        if (cookTimeEl) cookTimeEl.value = recipe.cook_time || '';
        if (servingsEl) servingsEl.value = recipe.servings || '';
        if (difficultyEl) difficultyEl.value = recipe.difficulty || '';
        if (tagsEl) tagsEl.value = (recipe.tags || []).join(', ');
        
        // Meal times - check the appropriate checkboxes
        const mealTimeCheckboxes = document.querySelectorAll('.meal-time-checkbox');
        mealTimeCheckboxes.forEach(checkbox => {
            checkbox.checked = (recipe.meal_times || []).includes(checkbox.value);
        });
        
        // Source
        const sourceTypeEl = document.getElementById('sourceType');
        const sourceUrlEl = document.getElementById('sourceUrl');
        const sourceNameEl = document.getElementById('sourceName');
        
        if (sourceTypeEl) sourceTypeEl.value = recipe.source?.type || 'manual';
        if (sourceUrlEl) sourceUrlEl.value = recipe.source?.url || '';
        if (sourceNameEl) sourceNameEl.value = recipe.source?.name || '';
        
        // Ingredients
        this.populateIngredients(recipe.ingredients || []);
        
        // Instructions
        this.populateInstructions(recipe.instructions || []);
        
        // Appliance Settings
        this.populateApplianceSettings(recipe.appliance_settings || []);
        
        // Images
        this.populateImages(recipe.images || []);
    }

    // Include other necessary methods from the main app.js (simplified versions)
    // This is a simplified implementation - in a real app, you'd want to share these methods
    
    getIngredientsFromForm() {
        const ingredients = [];
        const rows = document.querySelectorAll('#ingredientsContainer .ingredient-row');
        
        rows.forEach(row => {
            const name = row.querySelector('.ingredient-name').value.trim();
            const amount = row.querySelector('.ingredient-amount').value.trim();
            const unit = row.querySelector('.ingredient-unit').value.trim();
            
            if (name && amount) {
                ingredients.push({
                    name,
                    amount,
                    unit: unit || null
                });
            }
        });
        
        return ingredients;
    }

    getInstructionsFromForm() {
        const instructions = [];
        const rows = document.querySelectorAll('#instructionsContainer .instruction-row');
        
        rows.forEach(row => {
            const text = row.querySelector('.instruction-text').value.trim();
            if (text) {
                instructions.push(text);
            }
        });
        
        return instructions;
    }

    getApplianceSettingsFromForm() {
        // Simplified implementation
        return [];
    }

    populateIngredients(ingredients) {
        const container = document.getElementById('ingredientsContainer');
        if (!container) return;
        
        container.innerHTML = '';
        
        if (ingredients.length === 0) {
            this.addIngredientRow();
        } else {
            ingredients.forEach(ing => {
                this.addIngredientRow(ing);
            });
        }
    }

    populateInstructions(instructions) {
        const container = document.getElementById('instructionsContainer');
        if (!container) return;
        
        container.innerHTML = '';
        
        if (instructions.length === 0) {
            this.addInstructionRow();
        } else {
            instructions.forEach(inst => {
                this.addInstructionRow(inst);
            });
        }
    }

    populateApplianceSettings(applianceSettings) {
        // Simplified implementation
    }

    populateImages(images) {
        this.uploadedImages = [...images];
        // Update image preview if needed
    }

    addIngredientRow(ingredient = null) {
        const container = document.getElementById('ingredientsContainer');
        if (!container) return;
        
        const row = document.createElement('div');
        row.className = 'ingredient-row';
        row.innerHTML = `
            <input type="text" placeholder="Ingredient name" class="ingredient-name" value="${ingredient?.name || ''}" 
                   autocomplete="off" autocapitalize="words" spellcheck="true">
            <input type="text" placeholder="Amount" class="ingredient-amount" value="${ingredient?.amount || ''}" 
                   autocomplete="off" spellcheck="false">
            <input type="text" placeholder="Unit (optional)" class="ingredient-unit" value="${ingredient?.unit || ''}" 
                   autocomplete="off" spellcheck="false">
            <button type="button" class="btn btn-danger remove-ingredient">
                <i class="fas fa-trash"></i>
            </button>
        `;
        
        row.querySelector('.remove-ingredient').addEventListener('click', () => {
            if (container.children.length > 1) {
                row.remove();
            }
        });
        
        container.appendChild(row);
    }

    addInstructionRow(instruction = null) {
        const container = document.getElementById('instructionsContainer');
        if (!container) return;
        
        const row = document.createElement('div');
        row.className = 'instruction-row';
        row.innerHTML = `
            <textarea placeholder="Step ${container.children.length + 1}" class="instruction-text" rows="2" 
                      autocapitalize="sentences" spellcheck="true">${instruction || ''}</textarea>
            <button type="button" class="btn btn-danger remove-instruction">
                <i class="fas fa-trash"></i>
            </button>
        `;
        
        row.querySelector('.remove-instruction').addEventListener('click', () => {
            if (container.children.length > 1) {
                row.remove();
            }
        });
        
        container.appendChild(row);
    }

    addApplianceSettingRow() {
        // Simplified implementation
    }

    async handleImageUpload(event) {
        // Simplified implementation
    }

    // Utility methods
    showLoading(show) {
        const spinner = document.getElementById('loadingSpinner');
        if (spinner) {
            spinner.style.display = show ? 'block' : 'none';
        }
    }

    showError(message = 'An error occurred') {
        const errorEl = document.getElementById('errorMessage');
        if (errorEl) {
            if (message !== 'An error occurred') {
                const errorText = errorEl.querySelector('p');
                if (errorText) {
                    errorText.textContent = message;
                }
            }
            errorEl.style.display = 'block';
        }
    }

    showSuccess(message) {
        // Simple success notification - could be enhanced with a proper toast system
        alert(message);
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    capitalize(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    getApplianceTypeLabel(type) {
        const labels = {
            'gas_burner': 'Gas Burner',
            'airfryer': 'Airfryer',
            'electric_grill': 'Electric Grill',
            'electric_stove': 'Electric Stove',
            'induction_stove': 'Induction Stove',
            'oven': 'Oven',
            'charcoal_grill': 'Charcoal Grill',
            'stove': 'General Stove'
        };
        return labels[type] || type;
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.recipeDetailManager = new RecipeDetailManager();
});