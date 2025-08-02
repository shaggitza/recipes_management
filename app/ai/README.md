# AI Recipe Import Module

This module provides AI-powered recipe extraction from web pages, implementing the requested functionality to scrape recipe websites and extract structured recipe data.

## Features

- **Web Scraping**: Uses requests/BeautifulSoup (with Playwright ready for future enhancement)
- **AI Extraction**: Rule-based extraction with langfun integration ready for future implementation
- **Data Transformation**: Converts extracted data to application Recipe models
- **Retry Logic**: Robust error handling with configurable retry policies
- **Modular Design**: Clean separation of concerns across multiple modules

## Architecture

```
app/ai/
├── __init__.py          # Module initialization
├── models.py           # PyGlove-style models for extracted data
├── scraper.py          # Web scraping with requests/BeautifulSoup
├── extractor.py        # AI extraction (rule-based + langfun ready)
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

### Basic Import
```python
from app.ai.importer import RecipeImporter
from app.repositories.recipe_repository import RecipeRepository

# Initialize
repository = RecipeRepository()
importer = RecipeImporter(repository)

# Import a recipe
result = await importer.import_recipe_from_url(
    "https://raftulbunicii.ro/retete-romanesti/retete-din-muntenia/scovergi-muntenesti/"
)

if result.success:
    print(f"Recipe imported with ID: {result.recipe_id}")
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

### Using the API
```bash
# Import a single recipe
curl -X POST "http://localhost:8000/ai/import" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://raftulbunicii.ro/retete-romanesti/retete-din-muntenia/scovergi-muntenesti/"
  }'

# Test the system
curl -X GET "http://localhost:8000/ai/import/test"

# Get supported sources
curl -X GET "http://localhost:8000/ai/import/sources"
```

## Configuration

The importer can be configured with:

- **max_retries**: Number of retry attempts (default: 3)
- **retry_delay**: Delay between retries in seconds (default: 1.0)
- **timeout**: Request timeout in seconds (default: 30)
- **max_concurrent**: Maximum concurrent imports for batch operations (default: 3)

## Error Handling

The system includes comprehensive error handling:

1. **Network Errors**: Automatic retry with exponential backoff
2. **Parsing Errors**: Fallback to simpler extraction methods
3. **Validation Errors**: Clear error messages for invalid data
4. **Database Errors**: Transaction rollback and error reporting

## Future Enhancements

### Langfun Integration
The system is designed to easily integrate langfun when available:

```python
# In extractor.py
async def _extract_with_ai(self, content: str, source_url: str) -> RecipeExtractionResult:
    """Extract recipe using langfun AI."""
    import langfun as lf
    
    prompt = self._create_extraction_prompt(content)
    response = await lf.query(prompt, model="gemini-pro")
    
    # Parse AI response and return structured data
    return self._parse_ai_response(response, source_url)
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
- `langfun`: AI integration (to be added)
- `pyglove`: Structured data modeling (to be added)

## Troubleshooting

### Common Issues

1. **Scraping Fails**: Website may block automated requests
   - Solution: Add delays, rotate user agents, or use Playwright

2. **Extraction Returns No Data**: Content structure not recognized
   - Solution: Check the extraction patterns in `extractor.py`

3. **Import Fails**: Database connection issues
   - Solution: Verify MongoDB connection and credentials

### Debugging

Enable debug logging:

```python
import logging
logging.getLogger('app.ai').setLevel(logging.DEBUG)
```

## License

This module is part of the recipes_management application and follows the same license terms.