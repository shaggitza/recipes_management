#!/usr/bin/env python3
"""
Demonstration script showing that AI appliance settings integration is now working.

This script shows how the AI model can now generate appliance settings and they properly
flow through to the API response format.
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.ai.models import RecipeExtraction, GasBurnerSettings, OvenSettings, Utensil
from app.ai.bridge import recipe_extraction_to_dict

def main():
    print("🧪 Demonstrating AI Appliance Settings Integration")
    print("=" * 55)
    
    # Simulate what the AI would generate for a bread recipe
    print("\n1. AI Model generates appliance settings:")
    
    # Gas burner for warming milk
    gas_setting = GasBurnerSettings(
        flame_level="low",
        duration_minutes=5,
        utensils=[Utensil(type="small saucepan")],
        notes="Warm milk gently, don't boil"
    )
    print(f"   🔥 Gas Burner: {gas_setting.flame_level} flame for {gas_setting.duration_minutes} min")
    
    # Oven for baking
    oven_setting = OvenSettings(
        temperature_celsius=200,  # 200°C
        duration_minutes=35,
        preheat_required=True,
        convection=False,
        rack_position="middle",
        utensils=[Utensil(type="baking tray", material="metal")]
    )
    print(f"   🏠 Oven: {oven_setting.temperature_celsius}°C for {oven_setting.duration_minutes} min")
    
    # Create AI-extracted recipe
    ai_recipe = RecipeExtraction(
        title="Pâine de Casă cu Drojdie",
        description="Traditional Romanian homemade bread with yeast",
        ingredients=[],  # Required field, provide empty list
        instructions=[],  # Required field, provide empty list
        prep_time=20,
        cook_time=35,
        servings=8,
        difficulty="medium",
        tags=[],  # Required field, provide empty list
        meal_times=[],  # Required field, provide empty list
        images=[],  # Required field, provide empty list
        appliance_settings=[gas_setting, oven_setting]
    )
    
    print(f"\n2. AI Recipe Object:")
    print(f"   📝 Title: {ai_recipe.title}")
    print(f"   🏠 Appliance Settings: {len(ai_recipe.appliance_settings)} generated")
    
    # Convert through bridge (what happens in the API)
    print(f"\n3. Bridge Conversion (AI → API):")
    api_dict = recipe_extraction_to_dict(ai_recipe, "https://example.com/bread")
    
    print(f"   ✅ API Format: {type(api_dict)} with {len(api_dict)} fields")
    print(f"   ✅ Appliance Settings: {len(api_dict.get('appliance_settings', []))} in API response")
    
    # Show the appliance settings in API format
    print(f"\n4. API Response Appliance Settings:")
    for i, setting in enumerate(api_dict['appliance_settings']):
        print(f"   {i+1}. {setting['appliance_type']}:")
        for key, value in setting.items():
            if key != 'appliance_type' and value is not None:
                if key == 'utensils' and value:
                    utensil_types = [u.get('type', 'unknown') for u in value]
                    print(f"      {key}: {utensil_types}")
                else:
                    print(f"      {key}: {value}")
    
    # Verify this would work with the Recipe models
    print(f"\n5. Verification:")
    print(f"   ✅ Title extracted: '{api_dict['title']}'")
    print(f"   ✅ Cooking times: prep {api_dict['prep_time']}min, cook {api_dict['cook_time']}min")
    print(f"   ✅ Appliance settings: {len(api_dict['appliance_settings'])} ready for Recipe API")
    print(f"   ✅ Gas burner flame: {api_dict['appliance_settings'][0]['flame_level']}")
    print(f"   ✅ Oven temperature: {api_dict['appliance_settings'][1]['temperature_celsius']}°C")
    
    print(f"\n🎉 SUCCESS: AI appliance settings now flow correctly to API!")
    print(f"   The issue has been fixed - AI can populate appliance_settings field.")

if __name__ == "__main__":
    main()