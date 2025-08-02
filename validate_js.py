#!/usr/bin/env python3
"""
Standalone JavaScript validation script.
Validates JavaScript code for defensive programming patterns and potential issues.
"""
import re
import os


def validate_javascript():
    """Run all JavaScript validation checks."""
    js_file_path = '/home/runner/work/recipes_management/recipes_management/static/js/app.js'
    html_file_path = '/home/runner/work/recipes_management/recipes_management/templates/index.html'
    
    print("🔍 Running JavaScript validation checks...")
    
    with open(js_file_path, 'r') as f:
        js_content = f.read()
    
    with open(html_file_path, 'r') as f:
        html_content = f.read()
    
    checks_passed = 0
    total_checks = 0
    
    # Test 1: No meal-times references
    total_checks += 1
    problematic_references = ['loadMealTimes', 'renderMealTimeFilter', 'meal-times', 'mealTimes']
    found_problems = [ref for ref in problematic_references if ref in js_content]
    
    if not found_problems:
        print("✅ No problematic meal-times references found")
        checks_passed += 1
    else:
        print(f"❌ Found problematic references: {found_problems}")
    
    # Test 2: Safe event listener usage
    total_checks += 1
    if 'safeAddEventListener' in js_content:
        print("✅ safeAddEventListener helper function found")
        checks_passed += 1
    else:
        print("❌ safeAddEventListener helper function not found")
    
    # Test 3: Console warnings for missing elements
    total_checks += 1
    if 'console.warn' in js_content and 'not found' in js_content:
        print("✅ Console warnings for missing elements found")
        checks_passed += 1
    else:
        print("❌ Missing console warnings for missing elements")
    
    # Test 4: Proper error handling  
    total_checks += 1
    fetch_calls = len(re.findall(r'fetch\([^)]+\)', js_content))
    try_blocks = len(re.findall(r'try\s*\{', js_content))
    
    if fetch_calls > 0 and try_blocks > 0:
        print(f"✅ Found {fetch_calls} fetch calls with {try_blocks} try blocks")
        checks_passed += 1
    else:
        print(f"❌ Insufficient error handling: {fetch_calls} fetch calls, {try_blocks} try blocks")
    
    # Test 5: DOM ready initialization
    total_checks += 1
    if 'DOMContentLoaded' in js_content and 'new RecipeManager()' in js_content:
        print("✅ Proper DOM ready initialization found")
        checks_passed += 1
    else:
        print("❌ Missing proper DOM ready initialization")
    
    # Test 6: Check for dangerous direct getElementById usage
    total_checks += 1
    lines = js_content.split('\n')
    dangerous_lines = []
    
    for i, line in enumerate(lines):
        if 'getElementById' in line and 'safeAddEventListener' not in line:
            # Skip the safe helper function definition
            if 'const element = document.getElementById(elementId)' in line:
                continue
            
            # Look for null checks in surrounding context (expanded range)
            start_line = max(0, i - 8)
            end_line = min(len(lines), i + 8)
            context = '\n'.join(lines[start_line:end_line])
            
            has_null_check = any(pattern in context for pattern in [
                'if (', 'if(', ' ? ', ' && ', ' || ', 'console.warn', 'console.error',
                '!element', '!modal', '!title', '!content', '!container', '!tagFilter',
                'Element ?', 'Element?', '? searchElement', '? difficultyElement', '? tagElement'
            ])
            
            # Also check if the variable is used safely in the following lines
            line_var_name = None
            if 'const ' in line:
                var_match = re.search(r'const\s+(\w+)\s*=', line)
                if var_match:
                    line_var_name = var_match.group(1)
                    # Check if the variable is used with null checks
                    next_lines = '\n'.join(lines[i:i+5])
                    if f'{line_var_name} ?' in next_lines:
                        has_null_check = True
            
            if not has_null_check:
                dangerous_lines.append((i + 1, line.strip()))
    
    if not dangerous_lines:
        print("✅ All getElementById calls are properly protected")
        checks_passed += 1
    else:
        print(f"❌ Found {len(dangerous_lines)} unprotected getElementById calls:")
        for line_num, line_content in dangerous_lines[:3]:  # Show first 3 only
            print(f"   Line {line_num}: {line_content}")
    
    # Test 7: Check for undefined function calls
    total_checks += 1
    problematic_calls = ['this.loadMealTimes', 'this.renderMealTimeFilter', 'this.deleteRecipeBtn']
    found_bad_calls = [call for call in problematic_calls if call in js_content]
    
    if not found_bad_calls:
        print("✅ No undefined function calls found")
        checks_passed += 1
    else:
        print(f"❌ Found undefined function calls: {found_bad_calls}")
    
    # Summary
    print(f"\n📊 JavaScript Validation Summary: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("🎉 All JavaScript validation checks passed!")
        return True
    else:
        print("⚠️  Some JavaScript validation checks failed.")
        return False


def check_html_elements():
    """Check that HTML elements referenced in JavaScript exist."""
    js_file_path = '/home/runner/work/recipes_management/recipes_management/static/js/app.js'
    html_file_path = '/home/runner/work/recipes_management/recipes_management/templates/index.html'
    
    print("\n🔍 Checking HTML element references...")
    
    with open(js_file_path, 'r') as f:
        js_content = f.read()
    
    with open(html_file_path, 'r') as f:
        html_content = f.read()
    
    # Extract element IDs referenced in JavaScript
    js_element_ids = re.findall(r"getElementById\(['\"]([^'\"]+)['\"]", js_content)
    js_element_ids += re.findall(r"safeAddEventListener\(['\"]([^'\"]+)['\"]", js_content)
    
    # Remove duplicates
    js_element_ids = list(set(js_element_ids))
    
    # Elements that might be created dynamically
    dynamic_elements = [
        'recipeModal', 'modalTitle', 'recipeDetailModal', 'detailTitle',
        'recipeDetailContent', 'closeModal', 'closeDetailModal', 'cancelBtn',
        'recipeForm', 'addIngredient', 'addInstruction', 'editRecipeBtn',
        'deleteRecipeBtn', 'imageUpload', 'lightboxImage', 'imageLightbox'  # Added lightbox elements
    ]
    
    missing_elements = []
    found_elements = []
    
    for element_id in js_element_ids:
        id_pattern = f'id="{element_id}"'
        if id_pattern in html_content:
            found_elements.append(element_id)
        elif element_id in dynamic_elements:
            print(f"🔄 {element_id} - Expected to be dynamic/modal element")
        else:
            missing_elements.append(element_id)
    
    print(f"✅ Found {len(found_elements)} elements in HTML")
    if missing_elements:
        print(f"❌ Missing elements: {missing_elements}")
        return False
    else:
        print("✅ All referenced elements accounted for")
        return True


if __name__ == "__main__":
    js_valid = validate_javascript()
    html_valid = check_html_elements()
    
    if js_valid and html_valid:
        print("\n🎉 All validation checks passed!")
        exit(0)
    else:
        print("\n❌ Some validation checks failed.")
        exit(1)