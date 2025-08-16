# AI Recipe Import Module

This module provides AI-powered recipe extraction from web pages using ScrapeGraphAI, implementing intelligent recipe parsing with better Pydantic model integration and modern AI capabilities.

## Features

- **Web Scraping**: Uses requests/BeautifulSoup (with Playwright ready for future enhancement)
- **AI Extraction**: ScrapeGraphAI integration with OpenAI GPT models for intelligent recipe parsing
- **Data Transformation**: Converts extracted data to application Recipe models
- **Retry Logic**: Robust error handling with configurable retry policies
- **Modular Design**: Clean separation of concerns across multiple modules
- **Pydantic Models**: Pure Pydantic models for better type safety and validation

## Architecture

```
app/ai/
├── __init__.py          # Module initialization
├── models.py           # Pydantic models for extracted data
├── scraper.py          # Web scraping with requests/BeautifulSoup
├── extractor.py        # AI extraction with ScrapeGraphAI integration
├── simple_extractor.py # Core ScrapeGraphAI extraction logic
├── bridge.py           # Compatibility layer for existing code
├── transformer.py      # Data transformation to Recipe models
└── importer.py         # Import service with retry logic

app/routers/
└── ai_import.py        # API endpoints for AI import functionality
```

## API Endpoints

### POST `/ai/import`
Import a single recipe from a URL.

**Request:**
```json
{
    "url": "https://raftulbunicii.ro/retete-romanesti/retete-din-muntenia/scovergi-muntenesti/",
    "metadata": {
        "imported_by": "user123",
        "category": "traditional"
    }
}
```

**Response:**
```json
{
    "success": true,
    "recipe_id": "60f8d2b8c8a4e1b2c8d4e5f6",
    "url": "https://raftulbunicii.ro/...",
    "attempts": 1,
    "timestamp": "2024-08-02T07:08:00Z"
}
```

### POST `/ai/import/batch`
Import multiple recipes concurrently.

**Request:**
```json
{
    "urls": [
        "https://example1.com/recipe1",
        "https://example2.com/recipe2"
    ],
    "max_concurrent": 3,
    "metadata": {
        "batch_id": "batch_001"
    }
}
```

### GET `/ai/import/test`
Test the AI extraction system status.

### GET `/ai/import/sources`
Get information about supported recipe sources.

## Usage Examples

### Basic Import with AI
```python
import os
from app.ai.importer import RecipeImporter
from app.repositories.recipe_repository import RecipeRepository

# Set your OpenAI API key
os.environ['OPENAI_API_KEY'] = 'your-api-key-here'

# Initialize with AI extraction
repository = RecipeRepository()
importer = RecipeImporter(repository, openai_api_key=os.environ.get('OPENAI_API_KEY'))

# Import a recipe with AI extraction
result = await importer.import_recipe_from_url(
    "https://raftulbunicii.ro/retete-romanesti/retete-din-muntenia/scovergi-muntenesti/"
)

if result.success:
    print(f"Recipe imported with ID: {result.recipe_id}")
    print(f"Extraction method: {result.extraction_result.extraction_metadata.get('method')}")
else:
    print(f"Import failed: {result.error}")
```

### Batch Import
```python
urls = [
    "https://example1.com/recipe1",
    "https://example2.com/recipe2",
    "https://example3.com/recipe3"
]

results = await importer.batch_import(urls, max_concurrent=2)

successful = sum(1 for r in results.values() if r.success)
print(f"Imported {successful}/{len(urls)} recipes successfully")
```

### Using the API with AI
```bash
# Set your OpenAI API key in environment
export OPENAI_API_KEY="your-openai-api-key-here"

# Import a recipe with AI extraction
curl -X POST "http://localhost:8000/ai/import" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://raftulbunicii.ro/retete-romanesti/retete-din-muntenia/scovergi-muntenesti/"
  }'

# Test the AI system
curl -X GET "http://localhost:8000/ai/import/test"

# Get supported sources
curl -X GET "http://localhost:8000/ai/import/sources"
```

## Configuration

The importer requires an OpenAI API key for AI extraction:

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

Additional configuration options:

- **max_retries**: Number of retry attempts (default: 3)
- **retry_delay**: Delay between retries in seconds (default: 1.0)
- **timeout**: Request timeout in seconds (default: 30)
- **max_concurrent**: Maximum concurrent imports for batch operations (default: 3)

## AI Integration

The system now uses ScrapeGraphAI with OpenAI GPT models for intelligent recipe extraction:

### Automatic Translation
- Recipes in Romanian, Spanish, French, or other languages are automatically translated to English
- Preserves original cooking techniques and cultural context

### Structured Extraction  
- Uses ScrapeGraphAI's JSON output formatting for consistent data structure
- Intelligent parsing of ingredients with amounts, units, and names
- Smart estimation of missing cooking times and servings

### Fallback System
- If AI extraction fails, automatically falls back to rule-based parsing
- Graceful degradation ensures recipes are still imported even without API access

## Error Handling

The system includes comprehensive error handling:

1. **Network Errors**: Automatic retry with exponential backoff
2. **Parsing Errors**: Fallback to simpler extraction methods
3. **Validation Errors**: Clear error messages for invalid data
4. **Database Errors**: Transaction rollback and error reporting

## Future Enhancements

### Advanced ScrapeGraphAI Features
The current implementation provides a foundation for advanced ScrapeGraphAI capabilities:

```python
# In simple_extractor.py - ready for advanced ScrapeGraphAI features
async def _extract_with_advanced_ai(self, content: str, source_url: str):
    """Advanced AI extraction with multi-model support."""
    
    # Support for different model backends
    graph_config = {
        "llm": {
            "model": "gpt-4",  # or "claude-3", "gemini-pro"
            "api_key": self.api_key,
        },
    }
    
    # Chain of thought reasoning for complex recipes
    prompt = "Analyze this recipe step by step and extract detailed information..."
    
    return await self._extract_with_scrapegraphai(content, prompt, graph_config)
    
    return refined_result
```

### Playwright Integration
For JavaScript-heavy sites:

```python
# Enhanced scraper with Playwright
async def scrape_with_playwright(self, url: str) -> Optional[str]:
    """Scrape using Playwright for dynamic content."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        content = await page.content()
        await browser.close()
        return content
```

## Testing

Run the test suite:

```bash
# Basic tests
python test_ai_basic.py

# Complete workflow test
python test_complete_workflow.py

# API tests (requires running server)
pytest tests/test_ai_import.py
```

## Supported Websites

Currently optimized for:
- **raftulbunicii.ro**: Romanian recipes (translated to English)
- General recipe websites with standard HTML structure
- Sites with JSON-LD structured data

The system uses fallback parsing for other recipe websites.

## Dependencies

- `requests`: HTTP client for web scraping
- `beautifulsoup4`: HTML parsing
- `playwright`: Ready for JavaScript-heavy sites
- `pydantic`: Data validation and models
- `fastapi`: API framework
- `scrapegraphai`: AI-powered web scraping with language models ✅ **IMPLEMENTED**
- `openai`: OpenAI API client for GPT models ✅ **IMPLEMENTED**

## Troubleshooting

### Common Issues

1. **AI Extraction Fails**: OpenAI API key not set or invalid
   - Solution: Set `OPENAI_API_KEY` environment variable with valid key
   - Fallback: System automatically uses rule-based extraction

2. **ScrapeGraphAI Import Error**: Package not installed
   - Solution: `pip install scrapegraphai openai`
   - Fallback: System disables AI extraction and uses mock implementation

3. **Scraping Fails**: Website may block automated requests
   - Solution: Add delays, rotate user agents, or use Playwright

4. **Extraction Returns No Data**: Content structure not recognized
   - Solution: AI extraction is more flexible than rule-based patterns

5. **Import Fails**: Database connection issues
   - Solution: Verify MongoDB connection and credentials

### Debugging

Enable debug logging:

```python
import logging
logging.getLogger('app.ai').setLevel(logging.DEBUG)
```

## License

This module is part of the recipes_management application and follows the same license terms.