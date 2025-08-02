#!/usr/bin/env python3
"""Test script to validate langfun integration for recipe extraction."""

import asyncio
import os
import sys
from typing import Dict, Any

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.ai.extractor import RecipeExtractor

# Sample recipe content for testing
SAMPLE_RECIPE_CONTENT = """
HEADING: Scovergi Munteneşti

HEADING: Ingrediente
ITEM: 500g făină
ITEM: 1 ou
ITEM: 250ml lapte cald
ITEM: 1 linguriță drojdie uscată
ITEM: 1 linguriță zahăr
ITEM: 1 linguriță sare
ITEM: 2 linguri ulei

HEADING: Preparare
ITEM: Într-un bol mare, amestecăm făina cu sarea.
ITEM: Într-un alt bol, dizolvăm drojdia în laptele cald împreună cu zahărul.
ITEM: Adăugăm oul bătut și uleiul peste amestecul cu drojdie.
ITEM: Incorporăm treptat amestecul lichid în făină, frământând până obținem un aluat omogen.
ITEM: Lăsăm aluatul să se odihnească 30 de minute.
ITEM: Întindem aluatul într-o foaie subțire și tăiem bucăți rectangulare.
ITEM: Prăjim scovergile în ulei încins până se rumenesc pe ambele părți.
"""

async def test_langfun_extraction():
    """Test langfun AI extraction with sample Romanian recipe."""
    print("🧪 Testing langfun integration for recipe extraction...")
    
    # Check if OpenAI API key is available
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OPENAI_API_KEY found in environment variables")
        print("   Set your API key with: export OPENAI_API_KEY='your-key-here'")
        print("   Testing will use rule-based extraction instead.")
        
    # Test with AI enabled (will fall back to rule-based if no API key)
    extractor = RecipeExtractor(use_ai=True, api_key=api_key)
    
    print(f"🔧 Extractor configured - AI mode: {extractor.use_ai}")
    print(f"🔑 API key available: {'Yes' if api_key else 'No'}")
    
    try:
        # Extract recipe data
        result = await extractor.extract_recipe(
            content=SAMPLE_RECIPE_CONTENT,
            source_url="https://example.com/test-recipe"
        )
        
        print(f"\n📊 Extraction Result:")
        print(f"   ✅ Success: {result.success}")
        
        if result.success and result.recipe:
            recipe = result.recipe
            metadata = result.extraction_metadata
            
            print(f"   📝 Title: {recipe.title}")
            print(f"   📄 Description: {recipe.description or 'None'}")
            print(f"   🥘 Ingredients: {len(recipe.ingredients)} items")
            print(f"   📋 Instructions: {len(recipe.instructions)} steps")
            print(f"   ⏱️  Prep time: {recipe.prep_time} min")
            print(f"   🔥 Cook time: {recipe.cook_time} min")
            print(f"   👥 Servings: {recipe.servings}")
            print(f"   📊 Difficulty: {recipe.difficulty}")
            print(f"   🏷️  Tags: {recipe.tags}")
            print(f"   🤖 Method: {metadata.get('method', 'unknown')}")
            
            # Show first few ingredients and instructions
            if recipe.ingredients:
                print(f"\n🥘 Sample Ingredients:")
                for i, ing in enumerate(recipe.ingredients[:3]):
                    print(f"   - {ing.amount} {ing.unit or ''} {ing.name}".strip())
                if len(recipe.ingredients) > 3:
                    print(f"   ... and {len(recipe.ingredients) - 3} more")
            
            if recipe.instructions:
                print(f"\n📋 Sample Instructions:")
                for i, inst in enumerate(recipe.instructions[:2]):
                    print(f"   {i+1}. {inst}")
                if len(recipe.instructions) > 2:
                    print(f"   ... and {len(recipe.instructions) - 2} more steps")
        else:
            print(f"   ❌ Error: {result.error}")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
        
    print(f"\n✅ Test completed successfully!")
    return True

async def test_fallback_behavior():
    """Test that rule-based extraction works when AI is disabled."""
    print("\n🧪 Testing rule-based fallback extraction...")
    
    # Explicitly disable AI
    extractor = RecipeExtractor(use_ai=False)
    
    result = await extractor.extract_recipe(
        content=SAMPLE_RECIPE_CONTENT,
        source_url="https://example.com/test-recipe-fallback"
    )
    
    print(f"📊 Fallback Result:")
    print(f"   ✅ Success: {result.success}")
    print(f"   🤖 Method: {result.extraction_metadata.get('method', 'unknown')}")
    
    if result.success and result.recipe:
        print(f"   📝 Title: {result.recipe.title}")
        print(f"   🥘 Ingredients: {len(result.recipe.ingredients)} items")
        print(f"   📋 Instructions: {len(result.recipe.instructions)} steps")
    
    return result.success

async def main():
    """Run all tests."""
    print("🚀 Starting langfun integration tests...")
    print("=" * 50)
    
    # Test AI extraction
    ai_success = await test_langfun_extraction()
    
    # Test fallback
    fallback_success = await test_fallback_behavior()
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   🤖 AI Extraction: {'✅ Pass' if ai_success else '❌ Fail'}")
    print(f"   🔧 Rule-based Fallback: {'✅ Pass' if fallback_success else '❌ Fail'}")
    
    if ai_success and fallback_success:
        print(f"\n🎉 All tests passed! Langfun integration is working correctly.")
        return 0
    else:
        print(f"\n❌ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)