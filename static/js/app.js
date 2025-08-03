class RecipeManager {
    constructor() {
        this.recipes = [];
        this.tags = [];
        this.currentRecipe = null;
        this.editingRecipe = null;
        this.uploadedImages = []; // Track uploaded image URLs
        this.savedFilters = null; // Store filters when navigating to recipe
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadRecipes();
        this.loadTags();
        this.loadMealTimes();
        this.initMobileFeatures();
        this.initUrlHandling();
    }

    initMobileFeatures() {
        // Mobile filter toggle
        this.setupMobileFilters();
        
        // Mobile touch enhancements
        this.setupTouchEnhancements();
        
        // Check if we're on mobile and show/hide appropriate elements
        this.checkMobileView();
    }
    
    setupMobileFilters() {
        const filterToggle = document.getElementById('filterToggle');
        const filterContent = document.getElementById('filterContent');
        
        if (filterToggle && filterContent) {
            // Add click handler for mobile filter toggle
            filterToggle.addEventListener('click', () => {
                console.log('Filter toggle clicked'); // Debug log
                
                const isExpanded = filterContent.classList.contains('expanded');
                console.log('Current expanded state:', isExpanded); // Debug log
                
                filterContent.classList.toggle('expanded');
                filterToggle.classList.toggle('active');
                
                // Update button text and icon
                if (isExpanded) {
                    filterToggle.innerHTML = '<i class="fas fa-filter"></i> Filters';
                } else {
                    filterToggle.innerHTML = '<i class="fas fa-times"></i> Hide Filters';
                }
                
                console.log('New expanded state:', filterContent.classList.contains('expanded')); // Debug log
            });
        } else {
            console.warn('Filter toggle or content not found');
        }
    }
    
    setupTouchEnhancements() {
        // Add haptic feedback simulation for recipe cards (if supported)
        document.addEventListener('touchstart', (e) => {
            if (e.target.closest('.recipe-card')) {
                // Vibrate if supported (very subtle)
                if (navigator.vibrate) {
                    navigator.vibrate(10);
                }
            }
        });
        
        // Improve scroll behavior for modals on mobile
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.addEventListener('touchmove', (e) => {
                e.stopPropagation();
            });
        });
    }
    
    checkMobileView() {
        const isMobile = window.innerWidth <= 768;
        const filterToggle = document.getElementById('filterToggle');
        const filterContent = document.getElementById('filterContent');
        
        if (filterToggle && filterContent) {
            if (isMobile) {
                filterToggle.style.display = 'block';
                filterContent.classList.remove('expanded');
                filterToggle.classList.remove('active');
            } else {
                filterToggle.style.display = 'none';
                filterContent.classList.add('expanded');
                filterContent.style.display = 'grid';
            }
        }
        
        // Handle window resize
        window.addEventListener('resize', () => {
            this.checkMobileView();
        });
    }
    
    initUrlHandling() {
        // Handle browser back/forward buttons
        window.addEventListener('popstate', (event) => {
            if (event.state && event.state.recipeId) {
                // Going back to a recipe
                const recipe = this.recipes.find(r => r.id === event.state.recipeId);
                if (recipe) {
                    this.showRecipeDetail(recipe, false); // false = don't update URL again
                }
            } else {
                // Going back to main list
                this.closeDetailModal(false); // false = don't update URL again
                // Restore saved filters if they exist
                if (this.savedFilters) {
                    this.restoreFilters(this.savedFilters);
                    this.savedFilters = null;
                }
            }
        });
        
        // Check for recipe ID in URL on page load
        this.checkUrlForRecipe();
    }
    
    checkUrlForRecipe() {
        const urlParams = new URLSearchParams(window.location.search);
        const hash = window.location.hash;
        
        // Check for recipe ID in hash (e.g., #recipe-123)
        if (hash.startsWith('#recipe-')) {
            const recipeId = hash.substring(8); // Remove '#recipe-' prefix
            // Wait for recipes to load, then show the recipe
            const checkAndShow = () => {
                const recipe = this.recipes.find(r => r.id === recipeId);
                if (recipe) {
                    this.showRecipeDetail(recipe, false);
                } else if (this.recipes.length === 0) {
                    // Recipes not loaded yet, wait a bit and try again
                    setTimeout(checkAndShow, 100);
                }
            };
            checkAndShow();
        }
    }
    
    saveCurrentFilters() {
        const searchInput = document.getElementById('searchInput');
        const difficultyFilter = document.getElementById('difficultyFilter');
        const tagFilter = document.getElementById('tagFilter');
        const mealTimeFilter = document.getElementById('mealTimeFilter');
        
        return {
            search: searchInput ? searchInput.value : '',
            difficulty: difficultyFilter ? difficultyFilter.value : '',
            tag: tagFilter ? tagFilter.value : '',
            mealTimes: mealTimeFilter ? Array.from(mealTimeFilter.selectedOptions).map(option => option.value) : []
        };
    }
    
    restoreFilters(filters) {
        const searchInput = document.getElementById('searchInput');
        const difficultyFilter = document.getElementById('difficultyFilter');
        const tagFilter = document.getElementById('tagFilter');
        const mealTimeFilter = document.getElementById('mealTimeFilter');
        
        if (searchInput) searchInput.value = filters.search || '';
        if (difficultyFilter) difficultyFilter.value = filters.difficulty || '';
        if (tagFilter) tagFilter.value = filters.tag || '';
        if (mealTimeFilter && filters.mealTimes) {
            Array.from(mealTimeFilter.options).forEach(option => {
                option.selected = filters.mealTimes.includes(option.value);
            });
        }
        
        // Reload recipes with restored filters
        this.searchRecipes();
    }

    bindEvents() {
        // Helper function to safely add event listeners
        const safeAddEventListener = (elementId, event, handler) => {
            const element = document.getElementById(elementId);
            if (element) {
                element.addEventListener(event, handler);
            } else {
                console.warn(`Element with ID '${elementId}' not found. Skipping event binding.`);
            }
        };

        // Modal controls
        safeAddEventListener('addRecipeBtn', 'click', () => this.showAddModal());
        safeAddEventListener('importRecipeBtn', 'click', () => this.showImportModal());
        safeAddEventListener('closeModal', 'click', () => this.closeModal());
        safeAddEventListener('closeDetailModal', 'click', () => this.closeDetailModal());
        safeAddEventListener('closeImportModal', 'click', () => this.closeImportModal());
        safeAddEventListener('cancelBtn', 'click', () => this.closeModal());
        safeAddEventListener('cancelImportBtn', 'click', () => this.closeImportModal());

        // Form submission
        safeAddEventListener('recipeForm', 'submit', (e) => this.handleSubmit(e));
        safeAddEventListener('importForm', 'submit', (e) => this.handleImportSubmit(e));

        // Search and filters
        safeAddEventListener('searchBtn', 'click', () => this.searchRecipes());
        safeAddEventListener('searchInput', 'keypress', (e) => {
            if (e.key === 'Enter') this.searchRecipes();
        });
        safeAddEventListener('difficultyFilter', 'change', () => this.searchRecipes());
        safeAddEventListener('tagFilter', 'change', () => this.searchRecipes());
        safeAddEventListener('mealTimeFilter', 'change', () => this.searchRecipes());
        safeAddEventListener('clearFiltersBtn', 'click', () => this.clearFilters());


        // Dynamic form elements
        safeAddEventListener('addIngredient', 'click', () => this.addIngredientRow());
        safeAddEventListener('addInstruction', 'click', () => this.addInstructionRow());
        safeAddEventListener('addApplianceSetting', 'click', () => this.addApplianceSettingRow());

        // Recipe detail actions
        safeAddEventListener('editRecipeBtn', 'click', () => this.editCurrentRecipe());
        safeAddEventListener('deleteRecipeBtn', 'click', () => this.deleteCurrentRecipe());

        // Image upload
        safeAddEventListener('imageUpload', 'change', (e) => this.handleImageUpload(e));

        // Close modals on outside click
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal();
                this.closeDetailModal();
                this.closeImportModal();
            }
        });
    }

    async loadRecipes() {
        try {
            this.showLoading(true);
            const response = await fetch('/api/recipes/');
            
            // Check if response is ok (status 200-299)
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Server error: ${response.status}`);
            }
            
            this.recipes = await response.json();
            
            // Ensure recipes is an array
            if (!Array.isArray(this.recipes)) {
                throw new Error('Invalid response format: expected array of recipes');
            }
            
            this.renderRecipes();
        } catch (error) {
            console.error('Error loading recipes:', error);
            this.showError(`Failed to load recipes: ${error.message}`);
            // Set recipes to empty array to prevent further errors
            this.recipes = [];
            this.renderRecipes();
        } finally {
            this.showLoading(false);
        }
    }

    async loadTags() {
        try {
            const response = await fetch('/api/recipes/tags/all');
            this.tags = await response.json();
            this.renderTagFilter();
        } catch (error) {
            console.error('Error loading tags:', error);
        }
    }

    async loadMealTimes() {
        try {
            const response = await fetch('/api/recipes/meal-times/all');
            this.mealTimes = await response.json();
            this.renderMealTimeFilter();
        } catch (error) {
            console.error('Error loading meal times:', error);
        }
    }

    async searchRecipes() {
        try {
            this.showLoading(true);
            
            const searchElement = document.getElementById('searchInput');
            const difficultyElement = document.getElementById('difficultyFilter');
            const tagElement = document.getElementById('tagFilter');
            const mealTimeElement = document.getElementById('mealTimeFilter');

            
            const search = searchElement ? searchElement.value : '';
            const difficulty = difficultyElement ? difficultyElement.value : '';
            const tag = tagElement ? tagElement.value : '';
            const mealTimes = mealTimeElement ? Array.from(mealTimeElement.selectedOptions).map(option => option.value).filter(v => v) : [];

            
            const params = new URLSearchParams();
            if (search) params.append('search', search);
            if (difficulty) params.append('difficulty', difficulty);
            if (tag) params.append('tags', tag);
            if (mealTimes.length > 0) params.append('meal_times', mealTimes.join(','));
            
            const response = await fetch(`/api/recipes/?${params}`);
            
            // Check if response is ok (status 200-299)
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Server error: ${response.status}`);
            }
            
            this.recipes = await response.json();
            
            // Ensure recipes is an array
            if (!Array.isArray(this.recipes)) {
                throw new Error('Invalid response format: expected array of recipes');
            }
            
            this.renderRecipes();
        } catch (error) {
            console.error('Error searching recipes:', error);
            this.showError(`Search failed: ${error.message}`);
            // Set recipes to empty array to prevent further errors
            this.recipes = [];
            this.renderRecipes();
        } finally {
            this.showLoading(false);
        }
    }

    renderRecipes() {
        const container = document.getElementById('recipesContainer');
        const noResults = document.getElementById('noResults');
        
        if (!container) {
            console.warn('recipesContainer element not found. Cannot render recipes.');
            return;
        }
        
        if (this.recipes.length === 0) {
            container.innerHTML = '';
            if (noResults) {
                noResults.style.display = 'block';
            }
            return;
        }
        
        if (noResults) {
            noResults.style.display = 'none';
        }
        container.innerHTML = this.recipes.map(recipe => this.renderRecipeCard(recipe)).join('');
        
        // Bind click events to recipe cards
        container.querySelectorAll('.recipe-card').forEach((card, index) => {
            card.addEventListener('click', () => this.showRecipeDetail(this.recipes[index]));
        });
    }

    renderRecipeCard(recipe) {
        const totalTime = (recipe.prep_time || 0) + (recipe.cook_time || 0);
        const timeDisplay = totalTime > 0 ? `${totalTime} min` : '';
        const hasImage = recipe.images && recipe.images.length > 0;
        
        return `
            <div class="recipe-card ${hasImage ? 'with-image' : ''}">
                ${hasImage ? `<img src="${recipe.images[0]}" alt="${this.escapeHtml(recipe.title)}" class="recipe-card-image" />` : ''}
                <div class="recipe-card-content">
                    <div class="recipe-card-header">
                        <h3 class="recipe-card-title">${this.escapeHtml(recipe.title)}</h3>
                        ${recipe.description ? `<p class="recipe-card-description">${this.escapeHtml(recipe.description)}</p>` : ''}
                    </div>
                    <div class="recipe-card-body">
                        <div class="recipe-meta">
                            ${timeDisplay ? `<div class="recipe-meta-item"><i class="fas fa-clock"></i> ${timeDisplay}</div>` : ''}
                            ${recipe.servings ? `<div class="recipe-meta-item"><i class="fas fa-users"></i> ${recipe.servings} servings</div>` : ''}
                            ${recipe.difficulty ? `<div class="recipe-meta-item"><i class="fas fa-signal"></i> ${this.capitalize(recipe.difficulty)}</div>` : ''}
                        </div>
                        ${recipe.tags && recipe.tags.length > 0 ? `
                            <div class="recipe-tags">
                                ${recipe.tags.map(tag => `<span class="tag">${this.escapeHtml(tag)}</span>`).join('')}
                            </div>
                        ` : ''}
                        ${recipe.meal_times && recipe.meal_times.length > 0 ? `
                            <div class="recipe-meal-times">
                                ${recipe.meal_times.map(mealTime => `<span class="tag meal-time-tag">${this.escapeHtml(this.capitalize(mealTime))}</span>`).join('')}
                            </div>
                        ` : ''}

                        ${recipe.source && recipe.source.url ? `
                            <div class="recipe-source">
                                <i class="fas fa-link"></i> 
                                <a href="${recipe.source.url}" target="_blank" class="source-link" onclick="event.stopPropagation()">
                                    ${recipe.source.name || recipe.source.type || 'Source'}
                                </a>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    renderTagFilter() {
        const tagFilter = document.getElementById('tagFilter');
        if (tagFilter) {
            tagFilter.innerHTML = '<option value="">All Tags</option>' + 
                this.tags.map(tag => `<option value="${this.escapeHtml(tag)}">${this.escapeHtml(tag)}</option>`).join('');
        } else {
            console.warn('tagFilter element not found. Cannot render tag filter options.');
        }
    }

    renderMealTimeFilter() {
        const mealTimeFilter = document.getElementById('mealTimeFilter');
        const allMealTimes = ['breakfast', 'lunch', 'dinner', 'snack', 'brunch', 'dessert'];
        if (mealTimeFilter) {
            mealTimeFilter.innerHTML = allMealTimes.map(mealTime => 
                `<option value="${mealTime}">${mealTime.charAt(0).toUpperCase() + mealTime.slice(1)}</option>`
            ).join('');
        } else {
            console.warn('mealTimeFilter element not found. Cannot render meal time filter options.');
        }
    }

    clearFilters() {
        // Clear search input
        const searchInput = document.getElementById('searchInput');
        if (searchInput) searchInput.value = '';
        
        // Reset difficulty filter
        const difficultyFilter = document.getElementById('difficultyFilter');
        if (difficultyFilter) difficultyFilter.value = '';
        
        // Reset tag filter
        const tagFilter = document.getElementById('tagFilter');
        if (tagFilter) tagFilter.value = '';
        
        // Reset meal time filter (multiselect)
        const mealTimeFilter = document.getElementById('mealTimeFilter');
        if (mealTimeFilter) {
            Array.from(mealTimeFilter.options).forEach(option => {
                option.selected = false;
            });
        }
        
        // Reload all recipes
        this.loadRecipes();

    }

    showRecipeDetail(recipe, updateUrl = true) {
        this.currentRecipe = recipe;
        const modal = document.getElementById('recipeDetailModal');
        const title = document.getElementById('detailTitle');
        const content = document.getElementById('recipeDetailContent');
        
        if (!modal || !title || !content) {
            console.warn('Recipe detail modal elements not found. Cannot show recipe detail.');
            return;
        }
        
        // Save current filters before showing recipe
        if (updateUrl) {
            this.savedFilters = this.saveCurrentFilters();
        }
        
        title.textContent = recipe.title;
        content.innerHTML = this.renderRecipeDetail(recipe);
        modal.style.display = 'block';
        
        // Update URL to include recipe ID
        if (updateUrl && recipe.id) {
            const newUrl = `${window.location.pathname}${window.location.search}#recipe-${recipe.id}`;
            history.pushState(
                { recipeId: recipe.id }, 
                `${recipe.title} - Recipe Management`, 
                newUrl
            );
        }
    }

    renderRecipeDetail(recipe) {
        return `
            ${recipe.description ? `<p style="margin-bottom: 2rem; font-size: 1.1rem; color: #666;">${this.escapeHtml(recipe.description)}</p>` : ''}
            
            ${recipe.images && recipe.images.length > 0 ? this.displayRecipeImages(recipe.images) : ''}
            
            <div class="detail-meta">
                ${recipe.prep_time ? `
                    <div class="detail-meta-item">
                        <span class="detail-meta-value">${recipe.prep_time}</span>
                        <span class="detail-meta-label">Prep (min)</span>
                    </div>
                ` : ''}
                ${recipe.cook_time ? `
                    <div class="detail-meta-item">
                        <span class="detail-meta-value">${recipe.cook_time}</span>
                        <span class="detail-meta-label">Cook (min)</span>
                    </div>
                ` : ''}
                ${recipe.servings ? `
                    <div class="detail-meta-item">
                        <span class="detail-meta-value">${recipe.servings}</span>
                        <span class="detail-meta-label">Servings</span>
                    </div>
                ` : ''}
                ${recipe.difficulty ? `
                    <div class="detail-meta-item">
                        <span class="detail-meta-value">${this.capitalize(recipe.difficulty)}</span>
                        <span class="detail-meta-label">Difficulty</span>
                    </div>
                ` : ''}
            </div>

            ${recipe.ingredients && recipe.ingredients.length > 0 ? `
                <div class="detail-section">
                    <h3><i class="fas fa-list"></i> Ingredients</h3>
                    <ul class="ingredients-list">
                        ${recipe.ingredients.map(ing => `
                            <li>
                                <span class="ingredient-name">${this.escapeHtml(ing.name)}</span>
                                <span class="ingredient-amount">${this.escapeHtml(ing.amount)}${ing.unit ? ` ${this.escapeHtml(ing.unit)}` : ''}</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            ` : ''}

            ${recipe.instructions && recipe.instructions.length > 0 ? `
                <div class="detail-section">
                    <h3><i class="fas fa-tasks"></i> Instructions</h3>
                    <ol class="instructions-list">
                        ${recipe.instructions.map(inst => `<li>${this.escapeHtml(inst)}</li>`).join('')}
                    </ol>
                </div>
            ` : ''}

            ${recipe.tags && recipe.tags.length > 0 ? `
                <div class="detail-section">
                    <h3><i class="fas fa-tags"></i> Tags</h3>
                    <div class="detail-tags">
                        ${recipe.tags.map(tag => `<span class="tag">${this.escapeHtml(tag)}</span>`).join('')}
                    </div>
                </div>
            ` : ''}

            ${recipe.meal_times && recipe.meal_times.length > 0 ? `
                <div class="detail-section">
                    <h3><i class="fas fa-clock"></i> Meal Times</h3>
                    <div class="detail-tags">
                        ${recipe.meal_times.map(mealTime => `<span class="tag meal-time-tag">${this.escapeHtml(this.capitalize(mealTime))}</span>`).join('')}
                    </div>
                </div>
            ` : ''}

            ${recipe.appliance_settings && recipe.appliance_settings.length > 0 ? `
                <div class="detail-section">
                    <h3><i class="fas fa-tools"></i> Appliance Settings</h3>
                    <div class="appliance-settings-display">
                        ${recipe.appliance_settings.map(setting => this.renderApplianceSettingDetail(setting)).join('')}
                    </div>
                </div>
            ` : ''}

            ${recipe.source && (recipe.source.url || recipe.source.name) ? `
                <div class="detail-section">
                    <h3><i class="fas fa-link"></i> Source</h3>
                    <p>
                        ${recipe.source.name ? this.escapeHtml(recipe.source.name) : this.capitalize(recipe.source.type || 'Unknown')}
                        ${recipe.source.url ? `<br><a href="${recipe.source.url}" target="_blank" class="source-link">${recipe.source.url}</a>` : ''}
                    </p>
                </div>
            ` : ''}
        `;
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

    showAddModal() {
        this.editingRecipe = null;
        this.resetForm();
        document.getElementById('modalTitle').textContent = 'Add New Recipe';
        document.getElementById('recipeModal').style.display = 'block';
    }

    editCurrentRecipe() {
        if (!this.currentRecipe) return;
        
        this.editingRecipe = this.currentRecipe;
        this.populateForm(this.currentRecipe);
        document.getElementById('modalTitle').textContent = 'Edit Recipe';
        document.getElementById('recipeDetailModal').style.display = 'none';
        document.getElementById('recipeModal').style.display = 'block';
    }

    async deleteCurrentRecipe() {
        if (!this.currentRecipe) return;
        
        if (!confirm('Are you sure you want to delete this recipe?')) return;
        
        try {
            const response = await fetch(`/api/recipes/${this.currentRecipe.id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.closeDetailModal();
                this.loadRecipes();
                this.loadTags();
                this.showSuccess('Recipe deleted successfully!');
            } else {
                throw new Error('Failed to delete recipe');
            }
        } catch (error) {
            console.error('Error deleting recipe:', error);
            this.showError('Failed to delete recipe');
        }
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        try {
            const formData = new FormData(e.target);
            const recipeData = this.formDataToRecipe(formData);
            
            const url = this.editingRecipe ? `/api/recipes/${this.editingRecipe.id}` : '/api/recipes/';
            const method = this.editingRecipe ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(recipeData)
            });
            
            if (response.ok) {
                this.closeModal();
                this.loadRecipes();
                this.loadTags();
                this.loadMealTimes();
                this.showSuccess(this.editingRecipe ? 'Recipe updated successfully!' : 'Recipe created successfully!');
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save recipe');
            }
        } catch (error) {
            console.error('Error saving recipe:', error);
            this.showError(error.message || 'Failed to save recipe');
        }
    }

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
        recipe.images = this.uploadedImages || [];
        
        return recipe;
    }

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
        const applianceSettings = [];
        const settingItems = document.querySelectorAll('#applianceSettingsContainer .appliance-setting-item');
        
        settingItems.forEach(item => {
            const applianceType = item.dataset.applianceType;
            const setting = { appliance_type: applianceType };
            
            // Get all input/select/textarea fields
            const fields = item.querySelectorAll('.appliance-setting-fields input, .appliance-setting-fields select, .appliance-setting-fields textarea');
            
            fields.forEach(field => {
                const name = field.name;
                let value = field.value.trim();
                
                if (!value || name.startsWith('utensil_')) return; // Skip empty and utensil fields (handled separately)
                
                // Convert specific field types
                if (['temperature_celsius', 'duration_minutes', 'power_level', 'shake_interval_minutes'].includes(name)) {
                    value = parseInt(value);
                    if (isNaN(value)) return;
                } else if (['preheat_required', 'convection'].includes(name)) {
                    value = value === 'true';
                }
                
                setting[name] = value;
            });
            
            // Get utensils
            const utensils = [];
            const utensilItems = item.querySelectorAll('.utensil-item');
            
            utensilItems.forEach(utensilItem => {
                const type = utensilItem.querySelector('input[name="utensil_type"]')?.value.trim();
                const size = utensilItem.querySelector('input[name="utensil_size"]')?.value.trim();
                const material = utensilItem.querySelector('input[name="utensil_material"]')?.value.trim();
                
                if (type) {
                    const utensil = { type };
                    if (size) utensil.size = size;
                    if (material) utensil.material = material;
                    utensils.push(utensil);
                }
            });
            
            setting.utensils = utensils;
            
            // Only add if we have required fields
            if (this.validateApplianceSetting(setting)) {
                applianceSettings.push(setting);
            }
        });
        
        return applianceSettings;
    }

    validateApplianceSetting(setting) {
        const type = setting.appliance_type;
        
        // Check required fields based on appliance type
        if (type === 'gas_burner' && !setting.flame_level) return false;
        if (['electric_stove', 'stove'].includes(type) && !setting.heat_level) return false;
        if (['airfryer', 'electric_grill', 'oven'].includes(type) && !setting.temperature_celsius) return false;
        if (type === 'induction_stove' && !setting.power_level) return false;
        if (['airfryer', 'oven'].includes(type) && !setting.duration_minutes) return false;
        if (type === 'charcoal_grill' && !setting.heat_zone) return false;
        
        return true;
    }

    populateForm(recipe) {
        // Basic fields
        document.getElementById('title').value = recipe.title || '';
        document.getElementById('description').value = recipe.description || '';
        document.getElementById('prepTime').value = recipe.prep_time || '';
        document.getElementById('cookTime').value = recipe.cook_time || '';
        document.getElementById('servings').value = recipe.servings || '';
        document.getElementById('difficulty').value = recipe.difficulty || '';
        document.getElementById('tags').value = (recipe.tags || []).join(', ');
        
        // Meal times - check the appropriate checkboxes
        const mealTimeCheckboxes = document.querySelectorAll('.meal-time-checkbox');
        mealTimeCheckboxes.forEach(checkbox => {
            checkbox.checked = (recipe.meal_times || []).includes(checkbox.value);
        });
        
        // Source
        document.getElementById('sourceType').value = recipe.source?.type || 'manual';
        document.getElementById('sourceUrl').value = recipe.source?.url || '';
        document.getElementById('sourceName').value = recipe.source?.name || '';
        
        // Ingredients
        this.populateIngredients(recipe.ingredients || []);
        
        // Instructions
        this.populateInstructions(recipe.instructions || []);
        
        // Appliance Settings
        this.populateApplianceSettings(recipe.appliance_settings || []);
        
        // Images
        this.populateImages(recipe.images || []);
    }

    populateIngredients(ingredients) {
        const container = document.getElementById('ingredientsContainer');
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
        const container = document.getElementById('applianceSettingsContainer');
        container.innerHTML = '';
        
        applianceSettings.forEach(setting => {
            this.addApplianceSettingRow(setting);
        });
    }

    populateImages(images) {
        // Clear existing previews and uploaded images
        this.clearImagePreviews();
        
        // Set uploaded images array
        this.uploadedImages = [...images];
        
        // Create preview elements for existing images
        const previewContainer = document.getElementById('imagePreviewContainer');
        if (previewContainer) {
            images.forEach(imageUrl => {
                this.createExistingImagePreview(imageUrl);
            });
        }
    }

    createExistingImagePreview(imageUrl) {
        const previewContainer = document.getElementById('imagePreviewContainer');
        if (!previewContainer) {
            console.warn('imagePreviewContainer not found, cannot create image preview');
            return;
        }
        
        const previewDiv = document.createElement('div');
        previewDiv.className = 'image-preview';
        previewDiv.dataset.imageUrl = imageUrl;

        const img = document.createElement('img');
        img.src = imageUrl;
        img.alt = 'Recipe image';

        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-image';
        removeBtn.innerHTML = '×';
        removeBtn.onclick = (e) => {
            e.preventDefault();
            this.removeImagePreview(previewDiv, imageUrl);
        };

        previewDiv.appendChild(img);
        previewDiv.appendChild(removeBtn);
        previewContainer.appendChild(previewDiv);
    }

    addIngredientRow(ingredient = null) {
        const container = document.getElementById('ingredientsContainer');
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
                this.updateInstructionPlaceholders();
            }
        });
        
        container.appendChild(row);
    }

    addApplianceSettingRow(applianceSetting = null) {
        const select = document.getElementById('applianceTypeSelect');
        const applianceType = applianceSetting?.appliance_type || select.value;
        
        if (!applianceType) {
            alert('Please select an appliance type first.');
            return;
        }

        const container = document.getElementById('applianceSettingsContainer');
        const applianceDiv = document.createElement('div');
        applianceDiv.className = 'appliance-setting-item';
        applianceDiv.dataset.applianceType = applianceType;

        const applianceTypeLabel = this.getApplianceTypeLabel(applianceType);
        const fieldsHtml = this.generateApplianceFieldsHtml(applianceType, applianceSetting);

        applianceDiv.innerHTML = `
            <div class="appliance-setting-header">
                <span class="appliance-setting-type">${applianceTypeLabel}</span>
                <button type="button" class="remove-appliance-setting">
                    <i class="fas fa-trash"></i> Remove
                </button>
            </div>
            <div class="appliance-setting-fields">
                ${fieldsHtml}
            </div>
        `;

        // Add remove functionality
        applianceDiv.querySelector('.remove-appliance-setting').addEventListener('click', () => {
            applianceDiv.remove();
        });

        // Add utensil functionality
        this.bindApplianceUtensilEvents(applianceDiv);

        container.appendChild(applianceDiv);
        
        // Reset select
        if (!applianceSetting) {
            select.value = '';
        }
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

    generateApplianceFieldsHtml(applianceType, applianceSetting = null) {
        const setting = applianceSetting || {};
        let fieldsHtml = '';

        // Common fields
        if (['gas_burner', 'electric_stove', 'stove'].includes(applianceType)) {
            const heatField = applianceType === 'gas_burner' ? 'flame_level' : 'heat_level';
            const label = applianceType === 'gas_burner' ? 'Flame Level' : 'Heat Level';
            fieldsHtml += `
                <div class="appliance-field">
                    <label>${label} *</label>
                    <input type="text" name="${heatField}" value="${setting[heatField] || ''}" 
                           placeholder="e.g., medium-high" required>
                </div>
            `;
        }

        if (['airfryer', 'electric_grill', 'oven'].includes(applianceType)) {
            let tempMin, tempMax, tempPlaceholder;
            
            if (applianceType === 'airfryer') {
                tempMin = 40; tempMax = 230; tempPlaceholder = "190";
            } else if (applianceType === 'electric_grill') {
                tempMin = 95; tempMax = 260; tempPlaceholder = "200"; 
            } else if (applianceType === 'oven') {
                tempMin = 80; tempMax = 285; tempPlaceholder = "180";
            }
            
            fieldsHtml += `
                <div class="appliance-field">
                    <label>Temperature (°C) *</label>
                    <input type="number" name="temperature_celsius" value="${setting.temperature_celsius || ''}" 
                           min="${tempMin}" max="${tempMax}" placeholder="${tempPlaceholder}" required>
                </div>
            `;
        }

        if (applianceType === 'induction_stove') {
            fieldsHtml += `
                <div class="appliance-field">
                    <label>Power Level (1-10) *</label>
                    <input type="number" name="power_level" value="${setting.power_level || ''}" 
                           min="1" max="10" placeholder="5" required>
                </div>
                <div class="appliance-field">
                    <label>Temperature (°C)</label>
                    <input type="number" name="temperature_celsius" value="${setting.temperature_celsius || ''}" 
                           min="40" max="260" placeholder="175">
                </div>
            `;
        }

        // Duration field for most appliances
        if (!['charcoal_grill'].includes(applianceType) || setting.duration_minutes) {
            const required = ['airfryer', 'oven'].includes(applianceType) ? 'required' : '';
            fieldsHtml += `
                <div class="appliance-field">
                    <label>Duration (minutes)${required ? ' *' : ''}</label>
                    <input type="number" name="duration_minutes" value="${setting.duration_minutes || ''}" 
                           min="1" max="1440" placeholder="15" ${required}>
                </div>
            `;
        }

        // Special fields for specific appliances
        if (applianceType === 'airfryer') {
            fieldsHtml += `
                <div class="appliance-field">
                    <label>Preheat Required</label>
                    <select name="preheat_required">
                        <option value="true" ${setting.preheat_required !== false ? 'selected' : ''}>Yes</option>
                        <option value="false" ${setting.preheat_required === false ? 'selected' : ''}>No</option>
                    </select>
                </div>
                <div class="appliance-field">
                    <label>Shake Interval (minutes)</label>
                    <input type="number" name="shake_interval_minutes" value="${setting.shake_interval_minutes || ''}" 
                           min="1" max="30" placeholder="5">
                </div>
            `;
        }

        if (applianceType === 'electric_grill') {
            fieldsHtml += `
                <div class="appliance-field">
                    <label>Preheat Required</label>
                    <select name="preheat_required">
                        <option value="true" ${setting.preheat_required !== false ? 'selected' : ''}>Yes</option>
                        <option value="false" ${setting.preheat_required === false ? 'selected' : ''}>No</option>
                    </select>
                </div>
            `;
        }

        if (applianceType === 'oven') {
            fieldsHtml += `
                <div class="appliance-field">
                    <label>Preheat Required</label>
                    <select name="preheat_required">
                        <option value="true" ${setting.preheat_required !== false ? 'selected' : ''}>Yes</option>
                        <option value="false" ${setting.preheat_required === false ? 'selected' : ''}>No</option>
                    </select>
                </div>
                <div class="appliance-field">
                    <label>Rack Position</label>
                    <select name="rack_position">
                        <option value="">Select position...</option>
                        <option value="top" ${setting.rack_position === 'top' ? 'selected' : ''}>Top</option>
                        <option value="middle" ${setting.rack_position === 'middle' ? 'selected' : ''}>Middle</option>
                        <option value="bottom" ${setting.rack_position === 'bottom' ? 'selected' : ''}>Bottom</option>
                    </select>
                </div>
                <div class="appliance-field">
                    <label>Convection</label>
                    <select name="convection">
                        <option value="false" ${setting.convection !== true ? 'selected' : ''}>No</option>
                        <option value="true" ${setting.convection === true ? 'selected' : ''}>Yes</option>
                    </select>
                </div>
            `;
        }

        if (applianceType === 'charcoal_grill') {
            fieldsHtml += `
                <div class="appliance-field">
                    <label>Heat Zone *</label>
                    <input type="text" name="heat_zone" value="${setting.heat_zone || ''}" 
                           placeholder="e.g., direct high" required>
                </div>
                <div class="appliance-field">
                    <label>Lid Position</label>
                    <select name="lid_position">
                        <option value="">Select position...</option>
                        <option value="open" ${setting.lid_position === 'open' ? 'selected' : ''}>Open</option>
                        <option value="closed" ${setting.lid_position === 'closed' ? 'selected' : ''}>Closed</option>
                        <option value="vented" ${setting.lid_position === 'vented' ? 'selected' : ''}>Vented</option>
                    </select>
                </div>
            `;
        }

        // Notes field for all appliances
        fieldsHtml += `
            <div class="appliance-field">
                <label>Notes</label>
                <textarea name="notes" placeholder="Additional cooking notes...">${setting.notes || ''}</textarea>
            </div>
        `;

        // Utensils section
        fieldsHtml += this.generateUtensilsHtml(setting.utensils || []);

        return fieldsHtml;
    }

    generateUtensilsHtml(utensils) {
        let utensilsHtml = `
            <div class="utensils-section">
                <div class="utensils-header">
                    <h4>Utensils</h4>
                    <button type="button" class="add-utensil">
                        <i class="fas fa-plus"></i> Add Utensil
                    </button>
                </div>
                <div class="utensils-container">
        `;

        utensils.forEach(utensil => {
            utensilsHtml += this.generateUtensilItemHtml(utensil);
        });

        utensilsHtml += `
                </div>
            </div>
        `;

        return utensilsHtml;
    }

    generateUtensilItemHtml(utensil = {}) {
        return `
            <div class="utensil-item">
                <input type="text" name="utensil_type" value="${utensil.type || ''}" placeholder="Type (e.g., pan)">
                <input type="text" name="utensil_size" value="${utensil.size || ''}" placeholder="Size (e.g., 12-inch)">
                <input type="text" name="utensil_material" value="${utensil.material || ''}" placeholder="Material (e.g., non-stick)">
                <button type="button" class="remove-utensil">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
    }

    bindApplianceUtensilEvents(applianceDiv) {
        const addUtensilBtn = applianceDiv.querySelector('.add-utensil');
        const utensilsContainer = applianceDiv.querySelector('.utensils-container');

        addUtensilBtn.addEventListener('click', () => {
            const utensilDiv = document.createElement('div');
            utensilDiv.innerHTML = this.generateUtensilItemHtml();
            const utensilItem = utensilDiv.firstElementChild;
            
            utensilItem.querySelector('.remove-utensil').addEventListener('click', () => {
                utensilItem.remove();
            });

            utensilsContainer.appendChild(utensilItem);
        });

        // Bind existing remove utensil events
        utensilsContainer.querySelectorAll('.remove-utensil').forEach(btn => {
            btn.addEventListener('click', () => {
                btn.closest('.utensil-item').remove();
            });
        });
    }

    updateInstructionPlaceholders() {
        const rows = document.querySelectorAll('#instructionsContainer .instruction-row');
        rows.forEach((row, index) => {
            row.querySelector('.instruction-text').placeholder = `Step ${index + 1}`;
        });
    }

    resetForm() {
        const form = document.getElementById('recipeForm');
        if (form) {
            form.reset();
        }
        
        // Reset dynamic sections
        const ingredientsContainer = document.getElementById('ingredientsContainer');
        const instructionsContainer = document.getElementById('instructionsContainer');
        const applianceSettingsContainer = document.getElementById('applianceSettingsContainer');
        
        if (ingredientsContainer) {
            ingredientsContainer.innerHTML = '';
        }
        if (instructionsContainer) {
            instructionsContainer.innerHTML = '';
        }
        if (applianceSettingsContainer) {
            applianceSettingsContainer.innerHTML = '';
        }
        
        // Clear image previews
        this.clearImagePreviews();

        // Reset meal time checkboxes
        const mealTimeCheckboxes = document.querySelectorAll('.meal-time-checkbox');
        mealTimeCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
        });

        
        this.addIngredientRow();
        this.addInstructionRow();
    }

    closeModal() {
        const modal = document.getElementById('recipeModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    closeDetailModal(updateUrl = true) {
        const modal = document.getElementById('recipeDetailModal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.currentRecipe = null;
        
        // Update URL to remove recipe hash
        if (updateUrl) {
            const newUrl = `${window.location.pathname}${window.location.search}`;
            history.pushState(null, 'Recipe Management', newUrl);
            
            // Restore saved filters if they exist
            if (this.savedFilters) {
                this.restoreFilters(this.savedFilters);
                this.savedFilters = null;
            }
        }
    }

    showImportModal() {
        this.resetImportForm();
        document.getElementById('importModal').style.display = 'block';
    }

    closeImportModal() {
        const modal = document.getElementById('importModal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.resetImportForm();
    }

    resetImportForm() {
        const form = document.getElementById('importForm');
        if (form) {
            form.reset();
        }
        
        // Hide progress and result sections
        const progress = document.getElementById('importProgress');
        const result = document.getElementById('importResult');
        if (progress) progress.style.display = 'none';
        if (result) result.style.display = 'none';
        
        // Reset button state
        const importBtn = document.getElementById('importBtn');
        if (importBtn) {
            importBtn.disabled = false;
            importBtn.innerHTML = '<i class="fas fa-download"></i> Import Recipe';
        }
    }

    async handleImportSubmit(e) {
        e.preventDefault();
        
        const url = document.getElementById('importUrl').value.trim();
        const tags = document.getElementById('importTags').value.trim();
        
        if (!url) {
            this.showError('Please enter a recipe URL');
            return;
        }

        try {
            // Show progress
            const progress = document.getElementById('importProgress');
            const result = document.getElementById('importResult');
            const importBtn = document.getElementById('importBtn');
            
            if (progress) progress.style.display = 'block';
            if (result) result.style.display = 'none';
            if (importBtn) {
                importBtn.disabled = true;
                importBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Importing...';
            }

            // Prepare request data
            const requestData = {
                url: url
            };

            // Add tags to metadata if provided
            if (tags) {
                requestData.metadata = {
                    additional_tags: tags.split(',').map(tag => tag.trim()).filter(tag => tag)
                };
            }

            // Make import request
            const response = await fetch('/ai/import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            const data = await response.json();

            // Hide progress
            if (progress) progress.style.display = 'none';

            // Show result
            if (result) {
                result.style.display = 'block';
                this.displayImportResult(data);
            }

            // If successful, refresh the recipes list
            if (data.success) {
                await this.loadRecipes();
                
                // Auto-close modal after 3 seconds on success
                setTimeout(() => {
                    this.closeImportModal();
                }, 3000);
            }

        } catch (error) {
            console.error('Import error:', error);
            
            // Hide progress
            const progress = document.getElementById('importProgress');
            if (progress) progress.style.display = 'none';
            
            // Show error result
            const result = document.getElementById('importResult');
            if (result) {
                result.style.display = 'block';
                result.className = 'import-result error';
                result.innerHTML = `
                    <h4><i class="fas fa-exclamation-circle"></i> Import Failed</h4>
                    <p>An error occurred while importing the recipe: ${error.message || 'Unknown error'}</p>
                    <p>Please check the URL and try again.</p>
                `;
            }
        } finally {
            // Reset button state
            const importBtn = document.getElementById('importBtn');
            if (importBtn) {
                importBtn.disabled = false;
                importBtn.innerHTML = '<i class="fas fa-download"></i> Import Recipe';
            }
        }
    }

    displayImportResult(data) {
        const result = document.getElementById('importResult');
        if (!result) return;

        if (data.success) {
            result.className = 'import-result success';
            result.innerHTML = `
                <h4><i class="fas fa-check-circle"></i> Import Successful!</h4>
                <p>Recipe imported successfully from: <a href="${data.url}" target="_blank">${data.url}</a></p>
                <p>Recipe ID: ${data.recipe_id}</p>
                <p>Import completed in ${data.attempts} attempt(s)</p>
                ${data.extraction_metadata ? `
                    <div class="recipe-preview">
                        <h5>Recipe Preview:</h5>
                        ${data.extraction_metadata.extracted_title ? `<p><strong>Title:</strong> ${data.extraction_metadata.extracted_title}</p>` : ''}
                        ${data.extraction_metadata.method_used ? `<p><strong>Extraction Method:</strong> ${data.extraction_metadata.method_used}</p>` : ''}
                        ${data.extraction_metadata.language_detected ? `<p><strong>Language:</strong> ${data.extraction_metadata.language_detected}</p>` : ''}
                    </div>
                ` : ''}
                <p><small>This modal will close automatically in 3 seconds...</small></p>
            `;
        } else {
            result.className = 'import-result error';
            result.innerHTML = `
                <h4><i class="fas fa-exclamation-circle"></i> Import Failed</h4>
                <p>Failed to import recipe from: <a href="${data.url}" target="_blank">${data.url}</a></p>
                <p><strong>Error:</strong> ${data.error || 'Unknown error'}</p>
                <p>Attempts made: ${data.attempts}</p>
                <p>Please check the URL and try again. Make sure the URL contains a valid recipe.</p>
            `;
        }
    }

    showLoading(show) {
        document.getElementById('loadingSpinner').style.display = show ? 'block' : 'none';
    }

    showSuccess(message) {
        // Simple success notification - could be enhanced with a proper toast system
        alert(message);
    }

    showError(message) {
        // Simple error notification - could be enhanced with a proper toast system
        alert('Error: ' + message);
    }

    // Image handling methods
    async handleImageUpload(event) {
        const files = Array.from(event.target.files);
        if (files.length === 0) return;

        const previewContainer = document.getElementById('imagePreviewContainer');
        
        for (const file of files) {
            // Validate file
            if (!file.type.startsWith('image/')) {
                this.showError('Please select only image files');
                continue;
            }

            // Check file size (5MB max)
            if (file.size > 5 * 1024 * 1024) {
                this.showError('Image size must be less than 5MB');
                continue;
            }

            try {
                // Upload file
                const formData = new FormData();
                formData.append('file', file);

                const response = await fetch('/api/recipes/upload-image', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error('Upload failed');
                }

                const result = await response.json();
                this.uploadedImages.push(result.url);

                // Create preview element
                this.createImagePreview(result.url, file);
                
            } catch (error) {
                console.error('Error uploading image:', error);
                this.showError('Failed to upload image');
            }
        }

        // Clear the file input
        event.target.value = '';
    }

    createImagePreview(imageUrl, file) {
        const previewContainer = document.getElementById('imagePreviewContainer');
        if (!previewContainer) {
            console.warn('imagePreviewContainer not found, cannot create image preview');
            return;
        }
        
        const previewDiv = document.createElement('div');
        previewDiv.className = 'image-preview';
        previewDiv.dataset.imageUrl = imageUrl;

        const img = document.createElement('img');
        img.src = imageUrl;
        img.alt = file.name;

        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-image';
        removeBtn.innerHTML = '×';
        removeBtn.onclick = (e) => {
            e.preventDefault();
            this.removeImagePreview(previewDiv, imageUrl);
        };

        previewDiv.appendChild(img);
        previewDiv.appendChild(removeBtn);
        previewContainer.appendChild(previewDiv);
    }

    removeImagePreview(previewElement, imageUrl) {
        // Remove from uploaded images array
        this.uploadedImages = this.uploadedImages.filter(url => url !== imageUrl);
        
        // Remove preview element
        previewElement.remove();
    }

    clearImagePreviews() {
        const previewContainer = document.getElementById('imagePreviewContainer');
        previewContainer.innerHTML = '';
        this.uploadedImages = [];
    }

    displayRecipeImages(images) {
        if (!images || images.length === 0) return '';
        
        return `
            <div class="recipe-image-gallery">
                ${images.map(imageUrl => `
                    <div class="recipe-image-item" onclick="window.recipeManager.showImageLightbox('${imageUrl}')">
                        <img src="${imageUrl}" alt="Recipe image" />
                    </div>
                `).join('')}
            </div>
        `;
    }

    showImageLightbox(imageUrl) {
        // Create lightbox if it doesn't exist
        let lightbox = document.getElementById('imageLightbox');
        if (!lightbox) {
            lightbox = document.createElement('div');
            lightbox.id = 'imageLightbox';
            lightbox.className = 'image-lightbox';
            lightbox.innerHTML = `
                <div class="lightbox-content">
                    <img id="lightboxImage" src="" alt="Recipe image" />
                    <button class="lightbox-close">&times;</button>
                </div>
            `;
            document.body.appendChild(lightbox);

            // Add event listeners for closing
            const closeBtn = lightbox.querySelector('.lightbox-close');
            closeBtn.addEventListener('click', () => this.closeLightbox());

            // Close on background click
            lightbox.addEventListener('click', (e) => {
                if (e.target === lightbox) {
                    this.closeLightbox();
                }
            });

            // Prevent content click from closing
            const content = lightbox.querySelector('.lightbox-content');
            content.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }

        // Show the lightbox with the image
        const lightboxImage = document.getElementById('lightboxImage');
        if (lightboxImage) {
            lightboxImage.src = imageUrl;
        }
        lightbox.style.display = 'block';

        // Add ESC key listener
        this.addLightboxKeyListener();
    }

    closeLightbox() {
        const lightbox = document.getElementById('imageLightbox');
        if (lightbox) {
            lightbox.style.display = 'none';
        }
        this.removeLightboxKeyListener();
    }

    addLightboxKeyListener() {
        this.lightboxKeyHandler = (e) => {
            if (e.key === 'Escape') {
                this.closeLightbox();
            }
        };
        document.addEventListener('keydown', this.lightboxKeyHandler);
    }

    removeLightboxKeyListener() {
        if (this.lightboxKeyHandler) {
            document.removeEventListener('keydown', this.lightboxKeyHandler);
            this.lightboxKeyHandler = null;
        }
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
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.recipeManager = new RecipeManager();
});