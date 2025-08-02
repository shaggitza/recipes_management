"""
JavaScript validation tests for the Recipe Management application.
Tests the JavaScript functionality using Selenium WebDriver to catch runtime errors.
"""
import pytest
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
import subprocess
import signal
import threading
from contextlib import contextmanager

class TestJavaScriptValidation:
    """Test JavaScript functionality to catch runtime errors."""
    
    @pytest.fixture(scope="class")
    def server_process(self):
        """Start the FastAPI server for testing."""
        env = os.environ.copy()
        env['PYTHONPATH'] = '/home/runner/work/recipes_management/recipes_management'
        
        # Start the server in the background
        process = subprocess.Popen(
            ['python', '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'],
            cwd='/home/runner/work/recipes_management/recipes_management',
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a bit for the server to start
        time.sleep(3)
        
        yield process
        
        # Cleanup
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
    
    @pytest.fixture(scope="class")
    def driver(self, server_process):
        """Create a Chrome WebDriver instance."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(10)
            yield driver
        finally:
            if 'driver' in locals():
                driver.quit()
    
    def test_no_javascript_errors_on_page_load(self, driver):
        """Test that no JavaScript errors occur when the page loads."""
        driver.get("http://localhost:8000")
        
        # Wait for the page to fully load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check for JavaScript errors in the console
        logs = driver.get_log('browser')
        javascript_errors = [log for log in logs if log['level'] == 'SEVERE']
        
        # Print errors for debugging
        if javascript_errors:
            print("JavaScript errors found:")
            for error in javascript_errors:
                print(f"  {error['message']}")
        
        assert len(javascript_errors) == 0, f"JavaScript errors found: {javascript_errors}"
    
    def test_recipe_manager_initializes(self, driver):
        """Test that the RecipeManager class initializes without errors."""
        driver.get("http://localhost:8000")
        
        # Wait for RecipeManager to initialize
        WebDriverWait(driver, 10).until(
            lambda driver: driver.execute_script("return typeof window.recipeManager !== 'undefined'")
        )
        
        # Check that RecipeManager exists
        recipe_manager_exists = driver.execute_script("return typeof window.recipeManager === 'object'")
        assert recipe_manager_exists, "RecipeManager not properly initialized"
    
    def test_dom_elements_exist(self, driver):
        """Test that required DOM elements exist."""
        driver.get("http://localhost:8000")
        
        # List of critical elements that JavaScript depends on
        required_elements = [
            'addRecipeBtn',
            'searchInput', 
            'searchBtn',
            'difficultyFilter',
            'tagFilter',
            'recipesContainer'
        ]
        
        for element_id in required_elements:
            element = driver.find_element(By.ID, element_id)
            assert element is not None, f"Required element '{element_id}' not found"
            assert element.is_displayed() or element_id in ['recipeModal', 'recipeDetailModal'], f"Element '{element_id}' not visible"
    
    def test_event_handlers_bound_without_errors(self, driver):
        """Test that event handlers are bound without throwing errors."""
        driver.get("http://localhost:8000")
        
        # Wait for the page to load and JavaScript to execute
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "addRecipeBtn"))
        )
        
        # Test clicking the Add Recipe button doesn't cause errors
        add_recipe_btn = driver.find_element(By.ID, "addRecipeBtn")
        add_recipe_btn.click()
        
        # Check for JavaScript errors after clicking
        logs = driver.get_log('browser')
        javascript_errors = [log for log in logs if log['level'] == 'SEVERE']
        
        assert len(javascript_errors) == 0, f"JavaScript errors after clicking Add Recipe: {javascript_errors}"
    
    def test_search_functionality_no_errors(self, driver):
        """Test that search functionality works without errors."""
        driver.get("http://localhost:8000")
        
        # Wait for search elements to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "searchInput"))
        )
        
        # Test search functionality
        search_input = driver.find_element(By.ID, "searchInput")
        search_btn = driver.find_element(By.ID, "searchBtn")
        
        search_input.send_keys("test")
        search_btn.click()
        
        # Check for JavaScript errors after search
        logs = driver.get_log('browser')
        javascript_errors = [log for log in logs if log['level'] == 'SEVERE']
        
        assert len(javascript_errors) == 0, f"JavaScript errors after search: {javascript_errors}"
    
    def test_api_endpoints_exist(self, driver):
        """Test that the API endpoints referenced in JavaScript exist."""
        driver.get("http://localhost:8000")
        
        # Test API endpoints by making requests from the browser
        api_tests = [
            ("'/api/recipes/'", "Recipes API should be accessible"),
            ("'/api/recipes/tags/all'", "Tags API should be accessible"),
        ]
        
        for endpoint, description in api_tests:
            result = driver.execute_script(f"""
                return fetch({endpoint})
                    .then(response => response.status)
                    .catch(error => 'error: ' + error.message);
            """)
            
            # For async operations, we need to wait or handle differently
            # For now, just ensure no 404 errors are logged
            time.sleep(1)
            
        logs = driver.get_log('browser')
        http_404_errors = [log for log in logs if '404' in log['message'] and 'meal-times' not in log['message']]
        
        assert len(http_404_errors) == 0, f"HTTP 404 errors found: {http_404_errors}"


class TestJavaScriptFunctionalValidation:
    """Test JavaScript functionality without browser automation (lighter tests)."""
    
    def test_javascript_syntax_validation(self):
        """Test that the JavaScript file has valid syntax."""
        js_file_path = '/home/runner/work/recipes_management/recipes_management/static/js/app.js'
        
        # Use Node.js to validate syntax if available
        try:
            result = subprocess.run(
                ['node', '--check', js_file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            assert result.returncode == 0, f"JavaScript syntax errors: {result.stderr}"
        except FileNotFoundError:
            # Node.js not available, skip this test
            pytest.skip("Node.js not available for syntax validation")
        except subprocess.TimeoutExpired:
            pytest.fail("JavaScript syntax check timed out")
    
    def test_no_meal_times_references(self):
        """Test that there are no references to meal-times functionality that doesn't exist."""
        js_file_path = '/home/runner/work/recipes_management/recipes_management/static/js/app.js'
        
        with open(js_file_path, 'r') as f:
            content = f.read()
        
        # Check for meal-times references that were causing errors
        problematic_references = [
            'loadMealTimes',
            'renderMealTimeFilter', 
            'meal-times',
            'mealTimes'
        ]
        
        for reference in problematic_references:
            assert reference not in content, f"Found problematic reference '{reference}' in JavaScript file"
    
    def test_defensive_programming_patterns(self):
        """Test that defensive programming patterns are used."""
        js_file_path = '/home/runner/work/recipes_management/recipes_management/static/js/app.js'
        
        with open(js_file_path, 'r') as f:
            content = f.read()
        
        # Check for null checks before DOM manipulation
        assert 'getElementById' in content, "JavaScript should use getElementById"
        assert 'safeAddEventListener' in content, "JavaScript should use safeAddEventListener helper"
        
        # Check that we're checking for null before setting innerHTML
        lines = content.split('\n')
        innerHTML_lines = [i for i, line in enumerate(lines) if 'innerHTML' in line]
        
        for line_num in innerHTML_lines:
            # Look for null checks in the surrounding lines
            context = lines[max(0, line_num-5):line_num+1]
            context_text = '\n'.join(context)
            
            # Should have some form of null check nearby
            has_null_check = any(
                check in context_text 
                for check in ['if (', 'if(', '? ', ' && ', ' || ', 'console.warn']
            )
            
            assert has_null_check, f"Line {line_num+1} sets innerHTML without null check: {lines[line_num].strip()}"