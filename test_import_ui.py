#!/usr/bin/env python3
"""
UI tests for the import functionality
"""

import asyncio
import tempfile
import os
import subprocess
import time
from playwright.async_api import async_playwright

class ImportUITest:
    def __init__(self):
        self.server_process = None
        self.base_url = "http://localhost:8080"
    
    async def start_server(self):
        """Start a simple HTTP server for testing"""
        self.server_process = subprocess.Popen(
            ["python", "-m", "http.server", "8080", "--directory", "."],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # Wait for server to start
        time.sleep(2)
    
    def stop_server(self):
        """Stop the HTTP server"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
    
    async def test_import_button_functionality(self):
        """Test that the import button is visible, clickable, and opens the modal"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                # Navigate to the application
                await page.goto(f"{self.base_url}/templates/index.html")
                
                # Dismiss any alert dialogs that might appear
                page.on("dialog", lambda dialog: dialog.accept())
                
                # Wait for page to load
                await page.wait_for_selector("#importRecipeBtn", timeout=5000)
                
                # Test 1: Check if import button exists and is visible
                import_button = page.locator("#importRecipeBtn")
                assert await import_button.is_visible(), "Import button should be visible"
                
                # Test 2: Check if import button is enabled (not disabled)
                assert await import_button.is_enabled(), "Import button should be enabled"
                
                # Test 3: Check if import button has the correct styling class
                button_classes = await import_button.get_attribute("class")
                assert "btn-success" in button_classes, "Import button should have btn-success class (green)"
                
                # Test 4: Click the import button
                await import_button.click()
                
                # Test 5: Check if import modal opens
                import_modal = page.locator("#importModal")
                assert await import_modal.is_visible(), "Import modal should be visible after clicking button"
                
                # Test 6: Check if modal has the correct title
                modal_title = page.locator("#importModalTitle")
                title_text = await modal_title.text_content()
                assert "Import Recipe from URL" in title_text, "Modal should have correct title"
                
                # Test 7: Check if required form elements are present
                url_input = page.locator("#importUrl")
                assert await url_input.is_visible(), "URL input should be visible in modal"
                
                import_btn_in_modal = page.locator("#importBtn")
                assert await import_btn_in_modal.is_visible(), "Import button should be visible in modal"
                
                # Test 8: Close modal and verify it closes
                close_button = page.locator("#closeImportModal")
                await close_button.click()
                assert not await import_modal.is_visible(), "Modal should be hidden after closing"
                
                print("✅ All import button UI tests passed!")
                return True
                
            except Exception as e:
                print(f"❌ Import button UI test failed: {str(e)}")
                return False
            finally:
                await browser.close()
    
    async def run_tests(self):
        """Run all import UI tests"""
        print("Starting import UI tests...")
        
        # Start server
        await self.start_server()
        
        try:
            # Run tests
            success = await self.test_import_button_functionality()
            return success
        finally:
            # Clean up
            self.stop_server()

async def main():
    """Main test runner"""
    test_runner = ImportUITest()
    success = await test_runner.run_tests()
    
    if success:
        print("\n🎉 All import UI tests completed successfully!")
        print("The import button is working correctly and is not gray/unclickable.")
    else:
        print("\n💥 Some import UI tests failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)