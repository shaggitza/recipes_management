"""Tests for appliance settings functionality."""

import pytest
from typing import List
from app.models.recipe import (
    Recipe, RecipeCreate, RecipeUpdate, RecipeResponse,
    GasBurnerSettings, AirfryerSettings, ElectricGrillSettings,
    ElectricStoveSettings, InductionStoveSettings, OvenSettings,
    CharcoalGrillSettings, GeneralStoveSettings, Utensil, ApplianceSettings
)
from app.ai.models import (
    RecipeExtraction, GasBurnerSettings as AIGasBurnerSettings,
    AirfryerSettings as AIAirfryerSettings, Utensil as AIUtensil,
    create_appliance_settings_choice
)


class TestUtensilModel:
    """Test Utensil model functionality."""

    def test_utensil_creation_pydantic(self):
        """Test creating a utensil with Pydantic model."""
        utensil = Utensil(
            type="pan",
            size="12-inch",
            material="non-stick",
            notes="Good for eggs"
        )
        assert utensil.type == "pan"
        assert utensil.size == "12-inch"
        assert utensil.material == "non-stick"
        assert utensil.notes == "Good for eggs"

    def test_utensil_creation_pyglove(self):
        """Test creating a utensil with PyGlove model."""
        utensil = AIUtensil(
            type="tray",
            size="large",
            material="stainless steel"
        )
        assert utensil.type == "tray"
        assert utensil.size == "large"
        assert utensil.material == "stainless steel"
        assert utensil.notes is None

    def test_utensil_minimal(self):
        """Test creating a utensil with minimal fields."""
        utensil = Utensil(type="pot")
        assert utensil.type == "pot"
        assert utensil.size is None
        assert utensil.material is None
        assert utensil.notes is None


class TestApplianceSettingsModels:
    """Test all appliance settings models."""

    def test_gas_burner_settings(self):
        """Test gas burner settings model."""
        settings = GasBurnerSettings(
            flame_level="medium-high",
            duration_minutes=15,
            utensils=[Utensil(type="pan", size="10-inch")],
            notes="Watch for burning"
        )
        assert settings.appliance_type == "gas_burner"
        assert settings.flame_level == "medium-high"
        assert settings.duration_minutes == 15
        assert len(settings.utensils) == 1
        assert settings.utensils[0].type == "pan"
        assert settings.notes == "Watch for burning"

    def test_airfryer_settings(self):
        """Test airfryer settings model."""
        settings = AirfryerSettings(
            temperature_fahrenheit=400,
            duration_minutes=12,
            preheat_required=True,
            shake_interval_minutes=6
        )
        assert settings.appliance_type == "airfryer"
        assert settings.temperature_fahrenheit == 400
        assert settings.duration_minutes == 12
        assert settings.preheat_required is True
        assert settings.shake_interval_minutes == 6

    def test_electric_grill_settings(self):
        """Test electric grill settings model."""
        settings = ElectricGrillSettings(
            temperature_fahrenheit=450,
            duration_minutes=8,
            preheat_required=True,
            utensils=[Utensil(type="grill mat")]
        )
        assert settings.appliance_type == "electric_grill"
        assert settings.temperature_fahrenheit == 450
        assert settings.duration_minutes == 8
        assert settings.preheat_required is True
        assert len(settings.utensils) == 1

    def test_electric_stove_settings(self):
        """Test electric stove settings model."""
        settings = ElectricStoveSettings(
            heat_level="medium",
            duration_minutes=20,
            utensils=[Utensil(type="saucepan")]
        )
        assert settings.appliance_type == "electric_stove"
        assert settings.heat_level == "medium"
        assert settings.duration_minutes == 20
        assert len(settings.utensils) == 1

    def test_induction_stove_settings(self):
        """Test induction stove settings model."""
        settings = InductionStoveSettings(
            power_level=7,
            temperature_fahrenheit=350,
            duration_minutes=10,
            utensils=[Utensil(type="cast iron pan")]
        )
        assert settings.appliance_type == "induction_stove"
        assert settings.power_level == 7
        assert settings.temperature_fahrenheit == 350
        assert settings.duration_minutes == 10

    def test_oven_settings(self):
        """Test oven settings model."""
        settings = OvenSettings(
            temperature_fahrenheit=375,
            duration_minutes=25,
            preheat_required=True,
            rack_position="middle",
            convection=False,
            utensils=[Utensil(type="baking sheet")]
        )
        assert settings.appliance_type == "oven"
        assert settings.temperature_fahrenheit == 375
        assert settings.duration_minutes == 25
        assert settings.rack_position == "middle"
        assert settings.convection is False

    def test_charcoal_grill_settings(self):
        """Test charcoal grill settings model."""
        settings = CharcoalGrillSettings(
            heat_zone="direct high",
            duration_minutes=15,
            lid_position="closed",
            utensils=[Utensil(type="grill grate")]
        )
        assert settings.appliance_type == "charcoal_grill"
        assert settings.heat_zone == "direct high"
        assert settings.duration_minutes == 15
        assert settings.lid_position == "closed"

    def test_general_stove_settings(self):
        """Test general stove settings model."""
        settings = GeneralStoveSettings(
            heat_level="low",
            duration_minutes=30,
            utensils=[Utensil(type="pot", size="large")]
        )
        assert settings.appliance_type == "stove"
        assert settings.heat_level == "low"
        assert settings.duration_minutes == 30


class TestRecipeWithApplianceSettings:
    """Test Recipe models with appliance settings."""

    def test_recipe_create_with_appliance_settings(self):
        """Test creating a recipe with appliance settings."""
        gas_settings = GasBurnerSettings(
            flame_level="medium",
            duration_minutes=10,
            utensils=[Utensil(type="pan")]
        )
        oven_settings = OvenSettings(
            temperature_fahrenheit=350,
            duration_minutes=20
        )
        
        recipe_data = RecipeCreate(
            title="Test Recipe",
            description="A test recipe with appliance settings",
            appliance_settings=[gas_settings, oven_settings]
        )
        
        assert recipe_data.title == "Test Recipe"
        assert len(recipe_data.appliance_settings) == 2
        assert recipe_data.appliance_settings[0].appliance_type == "gas_burner"
        assert recipe_data.appliance_settings[1].appliance_type == "oven"

    def test_recipe_update_with_appliance_settings(self):
        """Test updating a recipe with appliance settings."""
        airfryer_settings = AirfryerSettings(
            temperature_fahrenheit=380,
            duration_minutes=12
        )
        
        recipe_update = RecipeUpdate(
            title="Updated Recipe",
            appliance_settings=[airfryer_settings]
        )
        
        assert recipe_update.title == "Updated Recipe"
        assert len(recipe_update.appliance_settings) == 1
        assert recipe_update.appliance_settings[0].appliance_type == "airfryer"

    def test_empty_appliance_settings(self):
        """Test recipe with empty appliance settings."""
        recipe_data = RecipeCreate(
            title="Simple Recipe",
            appliance_settings=[]
        )
        
        assert recipe_data.title == "Simple Recipe"
        assert recipe_data.appliance_settings == []


class TestPyGloveApplianceSettings:
    """Test PyGlove appliance settings functionality."""

    def test_pyglove_gas_burner_settings(self):
        """Test PyGlove gas burner settings."""
        settings = AIGasBurnerSettings(
            flame_level="high",
            duration_minutes=5,
            utensils=[AIUtensil(type="wok")],
            notes="Stir frequently"
        )
        
        assert settings.appliance_type == "gas_burner"
        assert settings.flame_level == "high"
        assert settings.duration_minutes == 5
        assert len(settings.utensils) == 1
        assert settings.utensils[0].type == "wok"

    def test_pyglove_airfryer_settings(self):
        """Test PyGlove airfryer settings."""
        settings = AIAirfryerSettings(
            temperature_fahrenheit=400,
            duration_minutes=10,
            preheat_required=True,
            shake_interval_minutes=5
        )
        
        assert settings.appliance_type == "airfryer"
        assert settings.temperature_fahrenheit == 400
        assert settings.duration_minutes == 10
        assert settings.preheat_required is True

    def test_recipe_extraction_with_appliance_settings(self):
        """Test RecipeExtraction with appliance settings."""
        gas_settings = AIGasBurnerSettings(
            flame_level="medium",
            duration_minutes=8
        )
        
        recipe = RecipeExtraction(
            title="AI Extracted Recipe",
            description="Recipe extracted by AI",
            appliance_settings=[gas_settings]
        )
        
        assert recipe.title == "AI Extracted Recipe"
        assert len(recipe.appliance_settings) == 1
        assert recipe.appliance_settings[0].appliance_type == "gas_burner"

    def test_create_appliance_settings_choice(self):
        """Test the utility function for creating appliance settings choices."""
        choice = create_appliance_settings_choice()
        # The choice should be a PyGlove oneof object
        assert hasattr(choice, 'candidates')
        # Should have 8 different appliance types
        assert len(choice.candidates) == 8


class TestApplianceSettingsValidation:
    """Test validation of appliance settings."""

    def test_airfryer_temperature_validation(self):
        """Test airfryer temperature limits."""
        with pytest.raises(ValueError):
            AirfryerSettings(
                temperature_fahrenheit=50,  # Too low
                duration_minutes=10
            )
        
        with pytest.raises(ValueError):
            AirfryerSettings(
                temperature_fahrenheit=500,  # Too high
                duration_minutes=10
            )

    def test_induction_power_level_validation(self):
        """Test induction stove power level limits."""
        with pytest.raises(ValueError):
            InductionStoveSettings(
                power_level=0  # Too low
            )
        
        with pytest.raises(ValueError):
            InductionStoveSettings(
                power_level=11  # Too high
            )

    def test_oven_temperature_validation(self):
        """Test oven temperature limits."""
        with pytest.raises(ValueError):
            OvenSettings(
                temperature_fahrenheit=150,  # Too low
                duration_minutes=20
            )
        
        with pytest.raises(ValueError):
            OvenSettings(
                temperature_fahrenheit=600,  # Too high
                duration_minutes=20
            )

    def test_required_fields_validation(self):
        """Test that required fields are validated."""
        with pytest.raises(ValueError):
            GasBurnerSettings()  # Missing flame_level
        
        with pytest.raises(ValueError):
            AirfryerSettings(temperature_fahrenheit=400)  # Missing duration_minutes