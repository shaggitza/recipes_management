#!/usr/bin/env python3
"""Basic validation script to test appliance settings functionality without external dependencies."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test imports
try:
    from app.models.recipe import (
        ApplianceSettings, GasBurnerSettings, AirfryerSettings, 
        OvenSettings, ElectricStoveSettings
    )
    from app.ai.models import (
        RecipeExtraction, ApplianceSettings as AIApplianceSettings,
        GasBurnerSettings as AIGasBurnerSettings, Ingredient as AIIngredient
    )
    from app.ai.bridge import recipe_extraction_to_dict
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Test 1: Bridge conversion includes appliance_settings
def test_bridge_conversion():
    print("\nTest 1: Bridge conversion includes appliance_settings")
    
    # Create AI appliance setting
    ai_gas_setting = AIGasBurnerSettings(
        flame_level="high",
        burner_size="large",
        utensils=["cast iron pan"],
        notes="Test notes"
    )
    
    ai_appliance_setting = AIApplianceSettings(
        appliance_type="gas_burner",
        gas_burner=ai_gas_setting
    )
    
    # Create AI recipe
    ai_recipe = RecipeExtraction(
        title="Test Recipe",
        description="Test description",
        ingredients=[AIIngredient(name="flour", amount="1 cup")],
        instructions=["Mix ingredients"],
        appliance_settings=[ai_appliance_setting]
    )
    
    # Test bridge conversion
    recipe_dict = recipe_extraction_to_dict(ai_recipe, "https://test.com")
    
    assert "appliance_settings" in recipe_dict, "appliance_settings missing from bridge conversion"
    assert len(recipe_dict["appliance_settings"]) == 1, "Incorrect number of appliance settings"
    
    print("✓ Bridge conversion includes appliance_settings correctly")

# Test 2: Pydantic model creation
def test_pydantic_models():
    print("\nTest 2: Pydantic model creation")
    
    # Test gas burner settings
    gas_settings = GasBurnerSettings(
        flame_level="high",
        burner_size="large", 
        utensils=["pan", "spatula"],
        notes="High heat cooking"
    )
    
    appliance_setting = ApplianceSettings(
        appliance_type="gas_burner",
        settings=gas_settings
    )
    
    print("✓ Pydantic models created successfully")
    
    # Test airfryer settings
    airfryer_settings = AirfryerSettings(
        temperature=375,
        time_minutes=15,
        preheat=True,
        shake_interval=5,
        utensils=["air fryer basket"],
        notes="Shake every 5 minutes"
    )
    
    airfryer_appliance = ApplianceSettings(
        appliance_type="airfryer",
        settings=airfryer_settings
    )
    
    print("✓ Multiple appliance types work correctly")

# Test 3: Model serialization
def test_serialization():
    print("\nTest 3: Model serialization")
    
    oven_settings = OvenSettings(
        temperature=425,
        cooking_mode="convection",
        rack_position="middle",
        preheat=True,
        utensils=["baking sheet"],
        notes="Rotate halfway"
    )
    
    appliance_setting = ApplianceSettings(
        appliance_type="oven",
        settings=oven_settings
    )
    
    # Test serialization
    serialized = appliance_setting.model_dump()
    assert "appliance_type" in serialized
    assert "settings" in serialized
    assert serialized["appliance_type"] == "oven"
    
    print("✓ Model serialization works correctly")

if __name__ == "__main__":
    print("Running appliance settings validation tests...")
    
    test_bridge_conversion()
    test_pydantic_models()
    test_serialization()
    
    print("\n✓ All validation tests passed!")
    print("✓ Appliance settings functionality is working correctly")