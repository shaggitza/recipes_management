"""
Comprehensive tests for appliance settings workflow from extraction to UI display.
Tests the complete flow: AI extraction → transformation → database storage → API response.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from app.ai.models import RecipeExtraction, ApplianceSettings as AIApplianceSettings
from app.ai.models import (
    GasBurnerSettings as AIGasBurnerSettings,
    ElectricStoveSettings as AIElectricStoveSettings,
    InductionStoveSettings as AIInductionStoveSettings,
    AirfryerSettings as AIAirfryerSettings,
    ElectricGrillSettings as AIElectricGrillSettings,
    OvenSettings as AIOvenSettings,
    CharcoalGrillSettings as AICharcoalGrillSettings,
    ElectricBasicSettings as AIElectricBasicSettings,
    Ingredient as AIIngredient
)
from app.models.recipe import (
    Recipe, RecipeCreate, ApplianceSettings,
    GasBurnerSettings, ElectricStoveSettings, InductionStoveSettings,
    AirfryerSettings, ElectricGrillSettings, OvenSettings,
    CharcoalGrillSettings, ElectricBasicSettings
)
from app.ai.bridge import RecipeExtractor, recipe_extraction_to_dict
from app.ai.transformer import RecipeTransformer
from app.services.recipe_service import RecipeService
from app.repositories.recipe_repository import RecipeRepository


class TestApplianceSettingsWorkflow:
    """Test the complete appliance settings workflow from AI to UI."""

    @pytest.fixture
    def mock_langfun(self):
        """Mock langfun to avoid testing the external library."""
        with patch('app.ai.simple_extractor.lf') as mock_lf:
            mock_lf.query = AsyncMock()
            yield mock_lf

    @pytest.fixture
    def transformer(self):
        """Create a RecipeTransformer instance."""
        return RecipeTransformer()

    @pytest.fixture
    def mock_repository(self):
        """Mock repository for testing."""
        repository = AsyncMock(spec=RecipeRepository)
        return repository

    @pytest.fixture
    def recipe_service(self, mock_repository):
        """Create RecipeService with mocked repository."""
        return RecipeService(repository=mock_repository)

    @pytest.mark.parametrize("appliance_type,ai_settings,expected_settings", [
        (
            "gas_burner",
            AIGasBurnerSettings(
                flame_level="high",
                burner_size="large",
                utensils=["cast iron pan", "wooden spoon"],
                notes="Keep flame steady"
            ),
            {
                "flame_level": "high",
                "burner_size": "large",
                "utensils": ["cast iron pan", "wooden spoon"],
                "notes": "Keep flame steady"
            }
        ),
        (
            "airfryer",
            AIAirfryerSettings(
                temperature=375,
                time_minutes=15,
                preheat=True,
                shake_interval=5,
                utensils=["air fryer basket"],
                notes="Shake every 5 minutes"
            ),
            {
                "temperature": 375,
                "time_minutes": 15,
                "preheat": True,
                "shake_interval": 5,
                "utensils": ["air fryer basket"],
                "notes": "Shake every 5 minutes"
            }
        ),
        (
            "oven",
            AIOvenSettings(
                temperature=425,
                cooking_mode="convection",
                rack_position="middle",
                preheat=True,
                utensils=["baking sheet", "parchment paper"],
                notes="Rotate halfway through"
            ),
            {
                "temperature": 425,
                "cooking_mode": "convection",
                "rack_position": "middle",
                "preheat": True,
                "utensils": ["baking sheet", "parchment paper"],
                "notes": "Rotate halfway through"
            }
        ),
        (
            "electric_stove",
            AIElectricStoveSettings(
                heat_level=7,
                utensils=["non-stick pan"],
                notes="Medium-high heat"
            ),
            {
                "heat_level": 7,
                "utensils": ["non-stick pan"],
                "notes": "Medium-high heat"
            }
        ),
        (
            "induction_stove",
            AIInductionStoveSettings(
                temperature=180,
                power_level=8,
                utensils=["induction-compatible pan"],
                notes="Use induction cookware only"
            ),
            {
                "temperature": 180,
                "power_level": 8,
                "utensils": ["induction-compatible pan"],
                "notes": "Use induction cookware only"
            }
        ),
        (
            "electric_grill",
            AIElectricGrillSettings(
                temperature=450,
                preheat_time=10,
                utensils=["grill brush", "tongs"],
                notes="Preheat thoroughly"
            ),
            {
                "temperature": 450,
                "preheat_time": 10,
                "utensils": ["grill brush", "tongs"],
                "notes": "Preheat thoroughly"
            }
        ),
        (
            "charcoal_grill",
            AICharcoalGrillSettings(
                charcoal_amount="heavy",
                heat_zone="indirect",
                cooking_time=45,
                utensils=["chimney starter", "grill grates"],
                notes="Use indirect heat for slow cooking"
            ),
            {
                "charcoal_amount": "heavy",
                "heat_zone": "indirect",
                "cooking_time": 45,
                "utensils": ["chimney starter", "grill grates"],
                "notes": "Use indirect heat for slow cooking"
            }
        ),
        (
            "electric_basic",
            AIElectricBasicSettings(
                power_setting="high",
                utensils=["basic pot"],
                notes="High power setting"
            ),
            {
                "power_setting": "high",
                "utensils": ["basic pot"],
                "notes": "High power setting"
            }
        )
    ])
    async def test_complete_appliance_workflow(
        self, 
        appliance_type, 
        ai_settings, 
        expected_settings,
        mock_langfun, 
        transformer, 
        mock_repository,
        recipe_service
    ):
        """
        Test the complete workflow from AI extraction to database storage for each appliance type.
        
        This test covers:
        1. AI extraction producing appliance settings
        2. Bridge conversion to dictionary format
        3. Transformation to Pydantic models
        4. Database storage
        5. Retrieval and response formatting
        """
        
        # Step 1: Mock AI extraction with appliance settings
        ai_appliance_setting = AIApplianceSettings(
            appliance_type=appliance_type,
            **{appliance_type: ai_settings}
        )
        
        mock_ai_recipe = RecipeExtraction(
            title="Test Recipe",
            description="A test recipe with appliance settings",
            ingredients=[
                AIIngredient(name="flour", amount="2 cups", unit="cups"),
                AIIngredient(name="sugar", amount="1 cup", unit="cups")
            ],
            instructions=["Mix ingredients", "Cook according to appliance settings"],
            prep_time=15,
            cook_time=30,
            servings=4,
            difficulty="medium",
            tags=["test", "automated"],
            meal_times=["dinner"],
            appliance_settings=[ai_appliance_setting]
        )
        
        mock_langfun.query.return_value = mock_ai_recipe
        
        # Step 2: Test AI extraction through bridge
        source_url = "https://example.com/recipe"
        extractor = RecipeExtractor(use_ai=True, api_key="test-key")
        
        result = await extractor.extract_recipe("test content", source_url)
        
        assert result.success
        assert result.recipe is not None
        
        # Step 3: Test bridge conversion includes appliance settings
        recipe_dict = recipe_extraction_to_dict(mock_ai_recipe, source_url)
        assert "appliance_settings" in recipe_dict
        assert len(recipe_dict["appliance_settings"]) == 1
        
        # Step 4: Test transformation to Pydantic models
        recipe_create = transformer.transform_to_recipe_create(recipe_dict)
        
        assert len(recipe_create.appliance_settings) == 1
        appliance_setting = recipe_create.appliance_settings[0]
        assert appliance_setting.appliance_type == appliance_type
        
        # Verify the settings match expected values
        settings = appliance_setting.settings
        for key, expected_value in expected_settings.items():
            actual_value = getattr(settings, key)
            assert actual_value == expected_value, f"Mismatch in {key}: expected {expected_value}, got {actual_value}"
        
        # Step 5: Test database storage
        mock_recipe = Recipe(**recipe_create.model_dump(), id="test_id_123")
        mock_repository.create.return_value = mock_recipe
        
        created_recipe = await recipe_service.create_recipe(recipe_create)
        
        assert created_recipe.appliance_settings is not None
        assert len(created_recipe.appliance_settings) == 1
        
        # Step 6: Test retrieval and response formatting
        mock_repository.get_by_id.return_value = mock_recipe
        
        retrieved_recipe = await recipe_service.get_recipe_by_id("test_id_123")
        
        assert retrieved_recipe.appliance_settings is not None
        assert len(retrieved_recipe.appliance_settings) == 1
        assert retrieved_recipe.appliance_settings[0].appliance_type == appliance_type

    async def test_multiple_appliance_settings_workflow(self, mock_langfun, transformer, mock_repository, recipe_service):
        """Test workflow with multiple appliance settings."""
        
        # Create recipe with multiple appliance settings
        gas_burner_setting = AIApplianceSettings(
            appliance_type="gas_burner",
            gas_burner=AIGasBurnerSettings(flame_level="medium", utensils=["pan"])
        )
        
        oven_setting = AIApplianceSettings(
            appliance_type="oven",
            oven=AIOvenSettings(temperature=350, cooking_mode="bake", utensils=["baking dish"])
        )
        
        mock_ai_recipe = RecipeExtraction(
            title="Multi-Appliance Recipe",
            description="Uses both gas burner and oven",
            ingredients=[AIIngredient(name="chicken", amount="1 lb")],
            instructions=["Sear on gas burner", "Finish in oven"],
            appliance_settings=[gas_burner_setting, oven_setting]
        )
        
        mock_langfun.query.return_value = mock_ai_recipe
        
        # Test transformation
        recipe_dict = recipe_extraction_to_dict(mock_ai_recipe, "https://example.com")
        recipe_create = transformer.transform_to_recipe_create(recipe_dict)
        
        assert len(recipe_create.appliance_settings) == 2
        appliance_types = [setting.appliance_type for setting in recipe_create.appliance_settings]
        assert "gas_burner" in appliance_types
        assert "oven" in appliance_types
        
        # Test database storage
        mock_recipe = Recipe(**recipe_create.model_dump(), id="multi_appliance_123")
        mock_repository.create.return_value = mock_recipe
        
        created_recipe = await recipe_service.create_recipe(recipe_create)
        assert len(created_recipe.appliance_settings) == 2

    async def test_appliance_settings_validation_errors(self, transformer):
        """Test handling of invalid appliance settings data."""
        
        # Test with invalid appliance type
        invalid_recipe_dict = {
            "title": "Test Recipe",
            "ingredients": [{"name": "flour", "amount": "1 cup"}],
            "instructions": ["Mix"],
            "appliance_settings": [
                {"appliance_type": "invalid_type", "temperature": 350}
            ]
        }
        
        recipe_create = transformer.transform_to_recipe_create(invalid_recipe_dict)
        
        # Should skip invalid appliance settings
        assert len(recipe_create.appliance_settings) == 0

    async def test_appliance_settings_missing_data(self, transformer):
        """Test handling of missing appliance settings data."""
        
        # Test recipe without appliance settings
        basic_recipe_dict = {
            "title": "Basic Recipe",
            "ingredients": [{"name": "flour", "amount": "1 cup"}],
            "instructions": ["Mix"]
        }
        
        recipe_create = transformer.transform_to_recipe_create(basic_recipe_dict)
        
        # Should handle missing appliance settings gracefully
        assert recipe_create.appliance_settings == []

    @pytest.mark.parametrize("appliance_type", [
        "gas_burner", "electric_stove", "induction_stove", "airfryer",
        "electric_grill", "oven", "charcoal_grill", "electric_basic"
    ])
    async def test_appliance_settings_field_defaults(self, appliance_type, transformer):
        """Test that appliance settings use proper defaults when fields are missing."""
        
        # Create minimal appliance setting with just type
        recipe_dict = {
            "title": "Test Recipe",
            "ingredients": [{"name": "flour", "amount": "1 cup"}],
            "instructions": ["Mix"],
            "appliance_settings": [{"appliance_type": appliance_type}]
        }
        
        recipe_create = transformer.transform_to_recipe_create(recipe_dict)
        
        assert len(recipe_create.appliance_settings) == 1
        appliance_setting = recipe_create.appliance_settings[0]
        assert appliance_setting.appliance_type == appliance_type
        
        # Verify that defaults are properly set based on appliance type
        settings = appliance_setting.settings
        if appliance_type == "gas_burner":
            assert settings.flame_level == "medium"
        elif appliance_type == "electric_stove":
            assert settings.heat_level == 5
        elif appliance_type == "airfryer":
            assert settings.temperature == 350
            assert settings.preheat == True
        elif appliance_type == "oven":
            assert settings.temperature == 350
            assert settings.cooking_mode == "bake"
            assert settings.preheat == True

    async def test_empty_appliance_settings_list(self, transformer):
        """Test handling of empty appliance settings list."""
        
        recipe_dict = {
            "title": "Test Recipe",
            "ingredients": [{"name": "flour", "amount": "1 cup"}],
            "instructions": ["Mix"],
            "appliance_settings": []
        }
        
        recipe_create = transformer.transform_to_recipe_create(recipe_dict)
        assert recipe_create.appliance_settings == []


class TestApplianceSettingsEdgeCases:
    """Test edge cases and error handling for appliance settings."""

    @pytest.fixture
    def transformer(self):
        return RecipeTransformer()

    def test_appliance_settings_with_string_utensils(self, transformer):
        """Test appliance settings with utensils as comma-separated string."""
        
        recipe_dict = {
            "title": "Test Recipe",
            "ingredients": [{"name": "flour", "amount": "1 cup"}],
            "instructions": ["Mix"],
            "appliance_settings": [{
                "appliance_type": "oven",
                "temperature": 350,
                "utensils": "baking sheet, parchment paper, oven mitts"
            }]
        }
        
        recipe_create = transformer.transform_to_recipe_create(recipe_dict)
        
        assert len(recipe_create.appliance_settings) == 1
        settings = recipe_create.appliance_settings[0].settings
        expected_utensils = ["baking sheet", "parchment paper", "oven mitts"]
        assert settings.utensils == expected_utensils

    def test_appliance_settings_with_empty_notes(self, transformer):
        """Test appliance settings with empty or whitespace-only notes."""
        
        recipe_dict = {
            "title": "Test Recipe",
            "ingredients": [{"name": "flour", "amount": "1 cup"}],
            "instructions": ["Mix"],
            "appliance_settings": [{
                "appliance_type": "gas_burner",
                "notes": "   "  # whitespace only
            }]
        }
        
        recipe_create = transformer.transform_to_recipe_create(recipe_dict)
        
        assert len(recipe_create.appliance_settings) == 1
        settings = recipe_create.appliance_settings[0].settings
        assert settings.notes is None  # Should be None, not empty string

    def test_appliance_settings_with_pyglove_object_format(self, transformer):
        """Test appliance settings from PyGlove object format."""
        
        # Simulate PyGlove object format
        class MockApplianceSettings:
            def __init__(self):
                self.appliance_type = "airfryer"
                self.airfryer = MockAirfryerSettings()
        
        class MockAirfryerSettings:
            def __init__(self):
                self.temperature = 375
                self.time_minutes = 20
                self.preheat = True
                self.shake_interval = 5
                self.utensils = ["air fryer basket"]
                self.notes = "Test notes"
        
        recipe_dict = {
            "title": "Test Recipe",
            "ingredients": [{"name": "flour", "amount": "1 cup"}],
            "instructions": ["Mix"],
            "appliance_settings": [MockApplianceSettings()]
        }
        
        recipe_create = transformer.transform_to_recipe_create(recipe_dict)
        
        assert len(recipe_create.appliance_settings) == 1
        appliance_setting = recipe_create.appliance_settings[0]
        assert appliance_setting.appliance_type == "airfryer"
        
        settings = appliance_setting.settings
        assert settings.temperature == 375
        assert settings.time_minutes == 20
        assert settings.preheat == True
        assert settings.shake_interval == 5
        assert settings.utensils == ["air fryer basket"]
        assert settings.notes == "Test notes"


class TestApplianceSettingsAPIIntegration:
    """Test API integration for appliance settings."""

    @pytest.fixture
    def mock_db_recipe(self):
        """Create a mock database recipe with appliance settings."""
        from bson import ObjectId
        from datetime import datetime, timezone
        
        appliance_settings = [
            ApplianceSettings(
                appliance_type="airfryer",
                settings=AirfryerSettings(
                    temperature=375,
                    time_minutes=15,
                    preheat=True,
                    shake_interval=5,
                    utensils=["air fryer basket"],
                    notes="Shake every 5 minutes"
                )
            )
        ]
        
        recipe = Recipe(
            id=ObjectId(),
            title="Air Fryer Chicken Wings",
            description="Crispy chicken wings made in air fryer",
            ingredients=[],
            instructions=[],
            appliance_settings=appliance_settings,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        return recipe

    async def test_recipe_response_includes_appliance_settings(self, mock_db_recipe):
        """Test that RecipeResponse properly includes appliance settings."""
        from app.models.recipe import RecipeResponse
        
        response = RecipeResponse.from_recipe(mock_db_recipe)
        
        assert response.appliance_settings is not None
        assert len(response.appliance_settings) == 1
        
        appliance_setting = response.appliance_settings[0]
        assert appliance_setting.appliance_type == "airfryer"
        
        settings = appliance_setting.settings
        assert settings.temperature == 375
        assert settings.time_minutes == 15
        assert settings.utensils == ["air fryer basket"]