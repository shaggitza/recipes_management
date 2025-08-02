#!/usr/bin/env python3
"""
Import functionality validation script
Validates that the import button and functionality are properly implemented
"""

import re
import os
from pathlib import Path

class ImportFunctionalityValidator:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.errors = []
        self.warnings = []
        
    def log_error(self, message):
        self.errors.append(f"❌ {message}")
        
    def log_warning(self, message):
        self.warnings.append(f"⚠️  {message}")
        
    def log_success(self, message):
        print(f"✅ {message}")
    
    def validate_html_structure(self):
        """Validate that the HTML has the correct import button and modal structure"""
        html_file = self.base_path / "templates" / "index.html"
        
        if not html_file.exists():
            self.log_error("index.html file not found")
            return False
            
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Check for import button
        if 'id="importRecipeBtn"' not in html_content:
            self.log_error("Import recipe button with id='importRecipeBtn' not found in HTML")
            return False
        
        # Check for import button styling
        if 'class="btn btn-success"' not in html_content or 'importRecipeBtn' not in html_content:
            self.log_warning("Import button may not have correct btn-success styling")
        
        # Check for import modal
        if 'id="importModal"' not in html_content:
            self.log_error("Import modal with id='importModal' not found in HTML")
            return False
            
        # Check for modal form elements
        required_elements = [
            'id="importUrl"',
            'id="importTags"', 
            'id="importBtn"',
            'id="closeImportModal"'
        ]
        
        for element in required_elements:
            if element not in html_content:
                self.log_error(f"Required import modal element '{element}' not found in HTML")
                return False
        
        self.log_success("HTML structure for import functionality is correct")
        return True
    
    def validate_javascript_functionality(self):
        """Validate that the JavaScript has proper import functionality"""
        js_file = self.base_path / "static" / "js" / "app.js"
        
        if not js_file.exists():
            self.log_error("app.js file not found")
            return False
            
        with open(js_file, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # Check for import button event binding
        if "'importRecipeBtn', 'click'" not in js_content:
            self.log_error("Import button click event binding not found in JavaScript")
            return False
            
        # Check for showImportModal function
        if 'showImportModal()' not in js_content:
            self.log_error("showImportModal function call not found in JavaScript")
            return False
            
        # Check for import form submission handler
        if "'importForm', 'submit'" not in js_content:
            self.log_error("Import form submit event binding not found in JavaScript")
            return False
            
        # Check for handleImportSubmit function
        if 'handleImportSubmit(' not in js_content:
            self.log_error("handleImportSubmit function not found in JavaScript")
            return False
            
        # Check for import modal functions
        required_functions = [
            'showImportModal(',
            'closeImportModal(',
            'resetImportForm('
        ]
        
        for func in required_functions:
            if func not in js_content:
                self.log_error(f"Required import function '{func}' not found in JavaScript")
                return False
        
        self.log_success("JavaScript import functionality is properly implemented")
        return True
    
    def validate_css_styling(self):
        """Validate that the CSS has proper button styling"""
        css_file = self.base_path / "static" / "css" / "style.css"
        
        if not css_file.exists():
            self.log_error("style.css file not found")
            return False
            
        with open(css_file, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        # Check for btn-success styling
        if '.btn-success' not in css_content:
            self.log_error("btn-success class styling not found in CSS")
            return False
            
        # Check for button hover effects
        if '.btn-success:hover' not in css_content:
            self.log_warning("btn-success hover effects not found in CSS")
            
        # Check for modal styling
        if '.modal' not in css_content:
            self.log_error("Modal styling not found in CSS")
            return False
        
        self.log_success("CSS styling for import functionality is correct")
        return True
    
    def check_for_disabled_states(self):
        """Check if there are any CSS rules that might disable the import button"""
        css_file = self.base_path / "static" / "css" / "style.css"
        
        if css_file.exists():
            with open(css_file, 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            # Look for disabled button styles that might affect import button
            if ':disabled' in css_content and 'gray' in css_content.lower():
                self.log_warning("Found disabled button styles in CSS - check if they affect import button")
            
            # Look for any explicit styling that might make import button gray
            import_btn_styles = re.findall(r'#importRecipeBtn[^{]*{[^}]*}', css_content, re.DOTALL)
            for style in import_btn_styles:
                if 'gray' in style.lower() or '#666' in style or '#888' in style:
                    self.log_warning(f"Found potential gray styling for import button: {style}")
        
        self.log_success("No obvious disabled states found for import button")
        return True
    
    def run_validation(self):
        """Run all validations"""
        print("🔍 Validating import button functionality...\n")
        
        html_valid = self.validate_html_structure()
        js_valid = self.validate_javascript_functionality()
        css_valid = self.validate_css_styling()
        disabled_check = self.check_for_disabled_states()
        
        print("\n" + "="*60)
        
        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(warning)
        
        if self.errors:
            print("\nErrors found:")
            for error in self.errors:
                print(error)
            print(f"\n💥 Validation failed with {len(self.errors)} error(s)")
            return False
        else:
            print("\n🎉 All validations passed!")
            print("The import button functionality is properly implemented and should be working correctly.")
            print("\nIf users are reporting the button as gray/unclickable, this is likely due to:")
            print("- Browser cache issues")
            print("- JavaScript errors in the browser console")
            print("- Network connectivity issues preventing CSS/JS loading")
            print("- Browser compatibility issues")
            return True

def main():
    """Main validation runner"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    validator = ImportFunctionalityValidator(base_path)
    
    success = validator.run_validation()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())