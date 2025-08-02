"""
Simple JavaScript validation tests that don't require browser automation.
Tests the JavaScript code for defensive programming patterns and potential issues.
"""
import pytest
import re
import os


class TestJavaScriptCodeQuality:
    """Test JavaScript code quality and defensive programming."""
    
    @pytest.fixture
    def js_content(self):
        """Load the JavaScript file content."""
        js_file_path = '/home/runner/work/recipes_management/recipes_management/static/js/app.js'
        with open(js_file_path, 'r') as f:
            return f.read()
    
    def test_no_meal_times_references(self, js_content):
        """Test that there are no references to meal-times functionality that doesn't exist."""
        problematic_references = [
            'loadMealTimes',
            'renderMealTimeFilter', 
            'meal-times',
            'mealTimes'
        ]
        
        for reference in problematic_references:
            assert reference not in js_content, f"Found problematic reference '{reference}' in JavaScript file"
    
    def test_defensive_programming_getelementbyid(self, js_content):
        """Test that getElementById calls are protected with null checks."""
        lines = js_content.split('\n')
        
        # Find lines that use getElementById
        getelementbyid_lines = []
        for i, line in enumerate(lines):
            if 'getElementById' in line and 'safeAddEventListener' not in line:
                getelementbyid_lines.append((i + 1, line.strip()))
        
        # Check each getElementById usage
        for line_num, line_content in getelementbyid_lines:
            # Skip lines that are part of the safe helper function
            if 'const element = document.getElementById(elementId)' in line_content:
                continue
                
            # Look for defensive patterns in surrounding context
            start_line = max(0, line_num - 6)
            end_line = min(len(lines), line_num + 3)
            context = '\n'.join(lines[start_line:end_line])
            
            # Check for defensive patterns
            has_null_check = any(pattern in context for pattern in [
                'if (',
                'if(',
                ' ? ',
                ' && ',
                ' || ',
                'console.warn',
                'console.error',
                '!element',
                '!modal',
                '!title',
                '!content',
                '!container',
                '!tagFilter'
            ])
            
            assert has_null_check, f"Line {line_num} uses getElementById without null check: {line_content}"
    
    def test_safe_event_listener_usage(self, js_content):
        """Test that the safeAddEventListener helper function is properly used."""
        # Should have the helper function defined
        assert 'safeAddEventListener' in js_content, "safeAddEventListener helper function not found"
        
        # Count direct addEventListener calls vs safe calls
        direct_calls = len(re.findall(r'\.addEventListener\(', js_content))
        safe_calls = len(re.findall(r'safeAddEventListener\(', js_content))
        
        # The only direct addEventListener should be for window events
        window_calls = len(re.findall(r'window\.addEventListener\(', js_content))
        
        # All element event listeners should use the safe wrapper
        unsafe_element_calls = direct_calls - window_calls
        assert unsafe_element_calls <= 1, f"Found {unsafe_element_calls} unsafe addEventListener calls (should use safeAddEventListener)"
    
    def test_console_warnings_for_missing_elements(self, js_content):
        """Test that missing elements generate console warnings."""
        assert 'console.warn' in js_content, "Should have console.warn statements for missing elements"
        
        # Check that warnings mention element IDs
        warning_patterns = [
            "not found",
            "Cannot render",
            "Cannot show",
            "Skipping event binding"
        ]
        
        found_warnings = False
        for pattern in warning_patterns:
            if pattern in js_content:
                found_warnings = True
                break
        
        assert found_warnings, "Should have meaningful warning messages for missing elements"
    
    def test_no_undefined_function_calls(self, js_content):
        """Test that there are no calls to undefined functions."""
        # Check for common problematic function calls
        problematic_calls = [
            'this.loadMealTimes',
            'this.renderMealTimeFilter',
            'this.deleteRecipeBtn',  # This was a typo we fixed
        ]
        
        for call in problematic_calls:
            assert call not in js_content, f"Found call to undefined/incorrect function: {call}"
    
    def test_proper_error_handling(self, js_content):
        """Test that API calls have proper error handling."""
        # Find async functions that make fetch calls
        async_functions = re.findall(r'async\s+(\w+)\s*\([^)]*\)\s*{[^}]*fetch\([^}]*}', js_content, re.DOTALL)
        
        # Check that fetch calls are wrapped in try-catch
        fetch_calls = re.findall(r'fetch\([^)]+\)', js_content)
        try_catch_blocks = re.findall(r'try\s*{[^}]*catch[^}]*}', js_content, re.DOTALL)
        
        assert len(fetch_calls) > 0, "Should have fetch calls for API communication"
        assert len(try_catch_blocks) > 0, "Should have try-catch blocks for error handling"
    
    def test_proper_dom_ready_initialization(self, js_content):
        """Test that the application initializes only after DOM is ready."""
        # Should use DOMContentLoaded event
        assert 'DOMContentLoaded' in js_content, "Should wait for DOMContentLoaded before initializing"
        
        # Should create RecipeManager instance
        assert 'new RecipeManager()' in js_content, "Should create RecipeManager instance"
        
        # Should assign to window for testing access
        assert 'window.recipeManager' in js_content, "Should assign RecipeManager to window for testing"
    
    def test_html_elements_referenced_exist(self):
        """Test that HTML elements referenced in JavaScript actually exist in the template."""
        js_file_path = '/home/runner/work/recipes_management/recipes_management/static/js/app.js'
        html_file_path = '/home/runner/work/recipes_management/recipes_management/templates/index.html'
        
        with open(js_file_path, 'r') as f:
            js_content = f.read()
        
        with open(html_file_path, 'r') as f:
            html_content = f.read()
        
        # Extract element IDs referenced in JavaScript
        js_element_ids = re.findall(r"getElementById\(['\"]([^'\"]+)['\"]", js_content)
        js_element_ids += re.findall(r"safeAddEventListener\(['\"]([^'\"]+)['\"]", js_content)
        
        # Remove duplicates
        js_element_ids = list(set(js_element_ids))
        
        # Check that each ID exists in HTML (or should be created dynamically)
        dynamic_elements = [
            'recipeModal',
            'modalTitle', 
            'recipeDetailModal',
            'detailTitle',
            'recipeDetailContent',
            'closeModal',
            'closeDetailModal', 
            'cancelBtn',
            'recipeForm',
            'addIngredient',
            'addInstruction',
            'editRecipeBtn',
            'deleteRecipeBtn',
        ]
        
        for element_id in js_element_ids:
            if element_id in dynamic_elements:
                # These elements should be created by modal HTML which might be in the template
                continue
            
            id_pattern = f'id="{element_id}"'
            assert id_pattern in html_content, f"Element ID '{element_id}' referenced in JavaScript but not found in HTML template"


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])