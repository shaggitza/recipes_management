class RecipeManager {
    constructor() {
        this.recipes = [];
        this.tags = [];
        this.currentRecipe = null;
        this.editingRecipe = null;
        this.uploadedImages = []; // Track uploaded image URLs
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadRecipes();
        this.loadTags();
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

        // Dynamic form elements
        safeAddEventListener('addIngredient', 'click', () => this.addIngredientRow());
        safeAddEventListener('addInstruction', 'click', () => this.addInstructionRow());

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
            this.recipes = await response.json();
            this.renderRecipes();
        } catch (error) {
            console.error('Error loading recipes:', error);
            this.showError('Failed to load recipes');
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

    async searchRecipes() {
        try {
            this.showLoading(true);
            
            const searchElement = document.getElementById('searchInput');
            const difficultyElement = document.getElementById('difficultyFilter');
            const tagElement = document.getElementById('tagFilter');
            
            const search = searchElement ? searchElement.value : '';
            const difficulty = difficultyElement ? difficultyElement.value : '';
            const tag = tagElement ? tagElement.value : '';
            
            const params = new URLSearchParams();
            if (search) params.append('search', search);
            if (difficulty) params.append('difficulty', difficulty);
            if (tag) params.append('tags', tag);
            
            const response = await fetch(`/api/recipes/?${params}`);
            this.recipes = await response.json();
            this.renderRecipes();
        } catch (error) {
            console.error('Error searching recipes:', error);
            this.showError('Search failed');
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

    showRecipeDetail(recipe) {
        this.currentRecipe = recipe;
        const modal = document.getElementById('recipeDetailModal');
        const title = document.getElementById('detailTitle');
        const content = document.getElementById('recipeDetailContent');
        
        if (!modal || !title || !content) {
            console.warn('Recipe detail modal elements not found. Cannot show recipe detail.');
            return;
        }
        
        title.textContent = recipe.title;
        content.innerHTML = this.renderRecipeDetail(recipe);
        modal.style.display = 'block';
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

    populateForm(recipe) {
        // Basic fields
        document.getElementById('title').value = recipe.title || '';
        document.getElementById('description').value = recipe.description || '';
        document.getElementById('prepTime').value = recipe.prep_time || '';
        document.getElementById('cookTime').value = recipe.cook_time || '';
        document.getElementById('servings').value = recipe.servings || '';
        document.getElementById('difficulty').value = recipe.difficulty || '';
        document.getElementById('tags').value = (recipe.tags || []).join(', ');
        
        // Source
        document.getElementById('sourceType').value = recipe.source?.type || 'manual';
        document.getElementById('sourceUrl').value = recipe.source?.url || '';
        document.getElementById('sourceName').value = recipe.source?.name || '';
        
        // Ingredients
        this.populateIngredients(recipe.ingredients || []);
        
        // Instructions
        this.populateInstructions(recipe.instructions || []);
        
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
            <input type="text" placeholder="Ingredient name" class="ingredient-name" value="${ingredient?.name || ''}">
            <input type="text" placeholder="Amount" class="ingredient-amount" value="${ingredient?.amount || ''}">
            <input type="text" placeholder="Unit (optional)" class="ingredient-unit" value="${ingredient?.unit || ''}">
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
            <textarea placeholder="Step ${container.children.length + 1}" class="instruction-text" rows="2">${instruction || ''}</textarea>
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
        
        if (ingredientsContainer) {
            ingredientsContainer.innerHTML = '';
        }
        if (instructionsContainer) {
            instructionsContainer.innerHTML = '';
        }
        
        // Clear image previews
        this.clearImagePreviews();
        
        this.addIngredientRow();
        this.addInstructionRow();
    }

    closeModal() {
        const modal = document.getElementById('recipeModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    closeDetailModal() {
        const modal = document.getElementById('recipeDetailModal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.currentRecipe = null;
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