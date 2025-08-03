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

            ${recipe.appliance_settings && recipe.appliance_settings.length > 0 ? `
                <div class="detail-section">
                    <h3><i class="fas fa-fire"></i> Appliance Settings</h3>
                    <div class="appliance-settings-display">
                        ${recipe.appliance_settings.map(setting => this.renderApplianceSettingDetail(setting)).join('')}
                    </div>
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
        const applianceNames = {
            'gas_burner': 'Gas Burner',
            'electric_stove': 'Electric Stove',
            'induction_stove': 'Induction Stove', 
            'airfryer': 'Air Fryer',
            'electric_grill': 'Electric Grill',
            'oven': 'Oven',
            'charcoal_grill': 'Charcoal Grill',
            'electric_basic': 'Electric Basic'
        };
        
        const applianceName = applianceNames[setting.appliance_type] || setting.appliance_type;
        const settings = setting.settings || {};
        
        let settingsHtml = '';
        
        switch (setting.appliance_type) {
            case 'gas_burner':
                settingsHtml += settings.flame_level ? `<div class="setting-item"><strong>Flame Level:</strong> ${this.capitalize(settings.flame_level)}</div>` : '';
                settingsHtml += settings.burner_size ? `<div class="setting-item"><strong>Burner Size:</strong> ${this.capitalize(settings.burner_size)}</div>` : '';
                break;
            case 'electric_stove':
                settingsHtml += settings.heat_level ? `<div class="setting-item"><strong>Heat Level:</strong> ${settings.heat_level}/10</div>` : '';
                break;
            case 'induction_stove':
                settingsHtml += settings.temperature ? `<div class="setting-item"><strong>Temperature:</strong> ${settings.temperature}°F</div>` : '';
                settingsHtml += settings.power_level ? `<div class="setting-item"><strong>Power Level:</strong> ${settings.power_level}/10</div>` : '';
                break;
            case 'airfryer':
                settingsHtml += settings.temperature ? `<div class="setting-item"><strong>Temperature:</strong> ${settings.temperature}°F</div>` : '';
                settingsHtml += settings.time_minutes ? `<div class="setting-item"><strong>Time:</strong> ${settings.time_minutes} min</div>` : '';
                settingsHtml += settings.preheat !== undefined ? `<div class="setting-item"><strong>Preheat:</strong> ${settings.preheat ? 'Yes' : 'No'}</div>` : '';
                settingsHtml += settings.shake_interval ? `<div class="setting-item"><strong>Shake Every:</strong> ${settings.shake_interval} min</div>` : '';
                break;
            case 'electric_grill':
                settingsHtml += settings.temperature ? `<div class="setting-item"><strong>Temperature:</strong> ${settings.temperature}°F</div>` : '';
                settingsHtml += settings.preheat_time ? `<div class="setting-item"><strong>Preheat Time:</strong> ${settings.preheat_time} min</div>` : '';
                break;
            case 'oven':
                settingsHtml += settings.temperature ? `<div class="setting-item"><strong>Temperature:</strong> ${settings.temperature}°F</div>` : '';
                settingsHtml += settings.cooking_mode ? `<div class="setting-item"><strong>Mode:</strong> ${this.capitalize(settings.cooking_mode)}</div>` : '';
                settingsHtml += settings.rack_position ? `<div class="setting-item"><strong>Rack:</strong> ${this.capitalize(settings.rack_position)}</div>` : '';
                settingsHtml += settings.preheat !== undefined ? `<div class="setting-item"><strong>Preheat:</strong> ${settings.preheat ? 'Yes' : 'No'}</div>` : '';
                break;
            case 'charcoal_grill':
                settingsHtml += settings.charcoal_amount ? `<div class="setting-item"><strong>Charcoal:</strong> ${this.capitalize(settings.charcoal_amount)}</div>` : '';
                settingsHtml += settings.heat_zone ? `<div class="setting-item"><strong>Heat Zone:</strong> ${this.capitalize(settings.heat_zone)}</div>` : '';
                settingsHtml += settings.cooking_time ? `<div class="setting-item"><strong>Cooking Time:</strong> ${settings.cooking_time} min</div>` : '';
                break;
            case 'electric_basic':
                settingsHtml += settings.power_setting ? `<div class="setting-item"><strong>Power:</strong> ${this.capitalize(settings.power_setting)}</div>` : '';
                break;
        }
        
        if (settings.utensils && settings.utensils.length > 0) {
            settingsHtml += `<div class="setting-item"><strong>Utensils:</strong> ${settings.utensils.join(', ')}</div>`;
        }
        
        if (settings.notes) {
            settingsHtml += `<div class="setting-item"><strong>Notes:</strong> ${this.escapeHtml(settings.notes)}</div>`;
        }
        
        return `
            <div class="appliance-setting">
                <h4 class="appliance-name"><i class="fas fa-fire"></i> ${applianceName}</h4>
                <div class="appliance-details">
                    ${settingsHtml}
                </div>
            </div>
        `;
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
        
        // Appliance settings
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
        const rows = document.querySelectorAll('#applianceSettingsContainer .appliance-setting-row');
        
        rows.forEach(row => {
            const applianceType = row.querySelector('.appliance-type-select').value;
            if (!applianceType) return;
            
            const detailsDiv = row.querySelector('.appliance-settings-details');
            const settings = this.collectApplianceSettings(applianceType, detailsDiv);
            
            applianceSettings.push({
                appliance_type: applianceType,
                settings: settings
            });
        });
        
        return applianceSettings;
    }

    collectApplianceSettings(applianceType, detailsDiv) {
        const settings = {};
        
        // Collect utensils and notes (common to all)
        const utensilsInput = detailsDiv.querySelector('.setting-utensils');
        if (utensilsInput && utensilsInput.value.trim()) {
            settings.utensils = utensilsInput.value.split(',').map(u => u.trim()).filter(u => u);
        } else {
            settings.utensils = [];
        }
        
        const notesInput = detailsDiv.querySelector('.setting-notes');
        if (notesInput && notesInput.value.trim()) {
            settings.notes = notesInput.value.trim();
        }
        
        // Collect appliance-specific settings
        switch (applianceType) {
            case 'gas_burner':
                const flameLevel = detailsDiv.querySelector('.setting-flame-level');
                const burnerSize = detailsDiv.querySelector('.setting-burner-size');
                if (flameLevel) settings.flame_level = flameLevel.value;
                if (burnerSize && burnerSize.value) settings.burner_size = burnerSize.value;
                break;
                
            case 'electric_stove':
                const heatLevel = detailsDiv.querySelector('.setting-heat-level');
                if (heatLevel) settings.heat_level = parseInt(heatLevel.value);
                break;
                
            case 'induction_stove':
                const temp = detailsDiv.querySelector('.setting-temperature');
                const powerLevel = detailsDiv.querySelector('.setting-power-level');
                if (temp && temp.value) settings.temperature = parseInt(temp.value);
                if (powerLevel && powerLevel.value) settings.power_level = parseInt(powerLevel.value);
                break;
                
            case 'airfryer':
                const airTemp = detailsDiv.querySelector('.setting-temperature');
                const timeMinutes = detailsDiv.querySelector('.setting-time-minutes');
                const preheat = detailsDiv.querySelector('.setting-preheat');
                const shakeInterval = detailsDiv.querySelector('.setting-shake-interval');
                if (airTemp) settings.temperature = parseInt(airTemp.value);
                if (timeMinutes && timeMinutes.value) settings.time_minutes = parseInt(timeMinutes.value);
                if (preheat) settings.preheat = preheat.checked;
                if (shakeInterval && shakeInterval.value) settings.shake_interval = parseInt(shakeInterval.value);
                break;
                
            case 'electric_grill':
                const grillTemp = detailsDiv.querySelector('.setting-temperature');
                const preheatTime = detailsDiv.querySelector('.setting-preheat-time');
                if (grillTemp) settings.temperature = parseInt(grillTemp.value);
                if (preheatTime && preheatTime.value) settings.preheat_time = parseInt(preheatTime.value);
                break;
                
            case 'oven':
                const ovenTemp = detailsDiv.querySelector('.setting-temperature');
                const cookingMode = detailsDiv.querySelector('.setting-cooking-mode');
                const rackPosition = detailsDiv.querySelector('.setting-rack-position');
                const ovenPreheat = detailsDiv.querySelector('.setting-preheat');
                if (ovenTemp) settings.temperature = parseInt(ovenTemp.value);
                if (cookingMode) settings.cooking_mode = cookingMode.value;
                if (rackPosition) settings.rack_position = rackPosition.value;
                if (ovenPreheat) settings.preheat = ovenPreheat.checked;
                break;
                
            case 'charcoal_grill':
                const charcoalAmount = detailsDiv.querySelector('.setting-charcoal-amount');
                const heatZone = detailsDiv.querySelector('.setting-heat-zone');
                const cookingTime = detailsDiv.querySelector('.setting-cooking-time');
                if (charcoalAmount) settings.charcoal_amount = charcoalAmount.value;
                if (heatZone) settings.heat_zone = heatZone.value;
                if (cookingTime && cookingTime.value) settings.cooking_time = parseInt(cookingTime.value);
                break;
                
            case 'electric_basic':
                const powerSetting = detailsDiv.querySelector('.setting-power-setting');
                if (powerSetting) settings.power_setting = powerSetting.value;
                break;
        }
        
        return settings;
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
        
        // Appliance settings
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
        if (!container) return;
        
        container.innerHTML = '';
        
        if (applianceSettings.length > 0) {
            applianceSettings.forEach(setting => {
                this.addApplianceSettingRow(setting);
            });
        }
        // Don't add a default row - let user add as needed
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
        const container = document.getElementById('applianceSettingsContainer');
        const row = document.createElement('div');
        row.className = 'appliance-setting-row';
        
        const applianceType = applianceSetting?.appliance_type || '';
        const settings = applianceSetting?.settings || {};
        
        row.innerHTML = `
            <div class="appliance-setting-header">
                <select class="appliance-type-select">
                    <option value="">Select Appliance</option>
                    <option value="gas_burner" ${applianceType === 'gas_burner' ? 'selected' : ''}>Gas Burner</option>
                    <option value="electric_stove" ${applianceType === 'electric_stove' ? 'selected' : ''}>Electric Stove</option>
                    <option value="induction_stove" ${applianceType === 'induction_stove' ? 'selected' : ''}>Induction Stove</option>
                    <option value="airfryer" ${applianceType === 'airfryer' ? 'selected' : ''}>Air Fryer</option>
                    <option value="electric_grill" ${applianceType === 'electric_grill' ? 'selected' : ''}>Electric Grill</option>
                    <option value="oven" ${applianceType === 'oven' ? 'selected' : ''}>Oven</option>
                    <option value="charcoal_grill" ${applianceType === 'charcoal_grill' ? 'selected' : ''}>Charcoal Grill</option>
                    <option value="electric_basic" ${applianceType === 'electric_basic' ? 'selected' : ''}>Electric Basic</option>
                </select>
                <button type="button" class="btn btn-danger remove-appliance-setting">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            <div class="appliance-settings-details" style="display: ${applianceType ? 'block' : 'none'};">
                <!-- Settings will be populated based on appliance type -->
            </div>
        `;
        
        const typeSelect = row.querySelector('.appliance-type-select');
        const detailsDiv = row.querySelector('.appliance-settings-details');
        
        typeSelect.addEventListener('change', () => {
            this.updateApplianceSettingsDetails(typeSelect.value, detailsDiv, settings);
        });
        
        row.querySelector('.remove-appliance-setting').addEventListener('click', () => {
            row.remove();
        });
        
        container.appendChild(row);
        
        // Initialize with current settings if provided
        if (applianceType) {
            this.updateApplianceSettingsDetails(applianceType, detailsDiv, settings);
        }
    }

    updateApplianceSettingsDetails(applianceType, detailsDiv, existingSettings = {}) {
        if (!applianceType) {
            detailsDiv.style.display = 'none';
            return;
        }
        
        detailsDiv.style.display = 'block';
        let html = '';
        
        // Common utensils field for all appliances
        const utensils = existingSettings.utensils || [];
        const utensilsValue = Array.isArray(utensils) ? utensils.join(', ') : utensils;
        
        switch (applianceType) {
            case 'gas_burner':
                html = `
                    <div class="settings-row">
                        <label>Flame Level:</label>
                        <select class="setting-flame-level">
                            <option value="low" ${existingSettings.flame_level === 'low' ? 'selected' : ''}>Low</option>
                            <option value="medium" ${existingSettings.flame_level === 'medium' ? 'selected' : ''}>Medium</option>
                            <option value="high" ${existingSettings.flame_level === 'high' ? 'selected' : ''}>High</option>
                            <option value="simmer" ${existingSettings.flame_level === 'simmer' ? 'selected' : ''}>Simmer</option>
                        </select>
                    </div>
                    <div class="settings-row">
                        <label>Burner Size:</label>
                        <select class="setting-burner-size">
                            <option value="">Any Size</option>
                            <option value="small" ${existingSettings.burner_size === 'small' ? 'selected' : ''}>Small</option>
                            <option value="medium" ${existingSettings.burner_size === 'medium' ? 'selected' : ''}>Medium</option>
                            <option value="large" ${existingSettings.burner_size === 'large' ? 'selected' : ''}>Large</option>
                        </select>
                    </div>
                `;
                break;
            case 'electric_stove':
                html = `
                    <div class="settings-row">
                        <label>Heat Level (1-10):</label>
                        <input type="number" class="setting-heat-level" min="1" max="10" value="${existingSettings.heat_level || 5}">
                    </div>
                `;
                break;
            case 'induction_stove':
                html = `
                    <div class="settings-row">
                        <label>Temperature (°F):</label>
                        <input type="number" class="setting-temperature" min="100" max="500" value="${existingSettings.temperature || ''}">
                    </div>
                    <div class="settings-row">
                        <label>Power Level (1-10):</label>
                        <input type="number" class="setting-power-level" min="1" max="10" value="${existingSettings.power_level || ''}">
                    </div>
                `;
                break;
            case 'airfryer':
                html = `
                    <div class="settings-row">
                        <label>Temperature (°F):</label>
                        <input type="number" class="setting-temperature" min="100" max="500" value="${existingSettings.temperature || 350}">
                    </div>
                    <div class="settings-row">
                        <label>Time (minutes):</label>
                        <input type="number" class="setting-time-minutes" min="1" max="120" value="${existingSettings.time_minutes || ''}">
                    </div>
                    <div class="settings-row">
                        <label>
                            <input type="checkbox" class="setting-preheat" ${existingSettings.preheat !== false ? 'checked' : ''}> Preheat
                        </label>
                    </div>
                    <div class="settings-row">
                        <label>Shake Interval (minutes):</label>
                        <input type="number" class="setting-shake-interval" min="1" max="30" value="${existingSettings.shake_interval || ''}">
                    </div>
                `;
                break;
            case 'electric_grill':
                html = `
                    <div class="settings-row">
                        <label>Temperature (°F):</label>
                        <input type="number" class="setting-temperature" min="200" max="600" value="${existingSettings.temperature || 400}">
                    </div>
                    <div class="settings-row">
                        <label>Preheat Time (minutes):</label>
                        <input type="number" class="setting-preheat-time" min="1" max="30" value="${existingSettings.preheat_time || ''}">
                    </div>
                `;
                break;
            case 'oven':
                html = `
                    <div class="settings-row">
                        <label>Temperature (°F):</label>
                        <input type="number" class="setting-temperature" min="200" max="550" value="${existingSettings.temperature || 350}">
                    </div>
                    <div class="settings-row">
                        <label>Cooking Mode:</label>
                        <select class="setting-cooking-mode">
                            <option value="bake" ${existingSettings.cooking_mode === 'bake' ? 'selected' : ''}>Bake</option>
                            <option value="broil" ${existingSettings.cooking_mode === 'broil' ? 'selected' : ''}>Broil</option>
                            <option value="convection" ${existingSettings.cooking_mode === 'convection' ? 'selected' : ''}>Convection</option>
                            <option value="roast" ${existingSettings.cooking_mode === 'roast' ? 'selected' : ''}>Roast</option>
                        </select>
                    </div>
                    <div class="settings-row">
                        <label>Rack Position:</label>
                        <select class="setting-rack-position">
                            <option value="top" ${existingSettings.rack_position === 'top' ? 'selected' : ''}>Top</option>
                            <option value="middle" ${existingSettings.rack_position === 'middle' ? 'selected' : ''}>Middle</option>
                            <option value="bottom" ${existingSettings.rack_position === 'bottom' ? 'selected' : ''}>Bottom</option>
                        </select>
                    </div>
                    <div class="settings-row">
                        <label>
                            <input type="checkbox" class="setting-preheat" ${existingSettings.preheat !== false ? 'checked' : ''}> Preheat
                        </label>
                    </div>
                `;
                break;
            case 'charcoal_grill':
                html = `
                    <div class="settings-row">
                        <label>Charcoal Amount:</label>
                        <select class="setting-charcoal-amount">
                            <option value="light" ${existingSettings.charcoal_amount === 'light' ? 'selected' : ''}>Light</option>
                            <option value="medium" ${existingSettings.charcoal_amount === 'medium' ? 'selected' : ''}>Medium</option>
                            <option value="heavy" ${existingSettings.charcoal_amount === 'heavy' ? 'selected' : ''}>Heavy</option>
                        </select>
                    </div>
                    <div class="settings-row">
                        <label>Heat Zone:</label>
                        <select class="setting-heat-zone">
                            <option value="direct" ${existingSettings.heat_zone === 'direct' ? 'selected' : ''}>Direct</option>
                            <option value="indirect" ${existingSettings.heat_zone === 'indirect' ? 'selected' : ''}>Indirect</option>
                            <option value="mixed" ${existingSettings.heat_zone === 'mixed' ? 'selected' : ''}>Mixed</option>
                        </select>
                    </div>
                    <div class="settings-row">
                        <label>Cooking Time (minutes):</label>
                        <input type="number" class="setting-cooking-time" min="1" max="480" value="${existingSettings.cooking_time || ''}">
                    </div>
                `;
                break;
            case 'electric_basic':
                html = `
                    <div class="settings-row">
                        <label>Power Setting:</label>
                        <select class="setting-power-setting">
                            <option value="low" ${existingSettings.power_setting === 'low' ? 'selected' : ''}>Low</option>
                            <option value="medium" ${existingSettings.power_setting === 'medium' ? 'selected' : ''}>Medium</option>
                            <option value="high" ${existingSettings.power_setting === 'high' ? 'selected' : ''}>High</option>
                        </select>
                    </div>
                `;
                break;
        }
        
        // Add common fields
        html += `
            <div class="settings-row">
                <label>Required Utensils (comma-separated):</label>
                <input type="text" class="setting-utensils" placeholder="e.g., pan, spatula" value="${utensilsValue}">
            </div>
            <div class="settings-row">
                <label>Notes:</label>
                <textarea class="setting-notes" rows="2" placeholder="Additional cooking notes">${existingSettings.notes || ''}</textarea>
            </div>
        `;
        
        detailsDiv.innerHTML = html;
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
        // Don't add a default appliance setting row - let user add as needed
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