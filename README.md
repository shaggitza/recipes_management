# Recipe Management Application

A simple and extensible recipe management application built with FastAPI, MongoDB, and vanilla JavaScript.

## Features

- 📝 Easy recipe creation and management
- 🔗 TikTok link support for future bot integration
- 🏷️ Tagging and categorization
- ⏱️ Prep and cook time tracking
- 📱 Responsive web interface
- 🐳 Docker containerization

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd recipes_management
```

2. Start the application:
```bash
docker-compose up --build
```

3. Open your browser and navigate to `http://localhost:8000`

### Manual Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start MongoDB (locally or using Docker):
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

3. Start the application:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once the application is running, you can access:
- API Documentation: `http://localhost:8000/docs`
- ReDoc Documentation: `http://localhost:8000/redoc`

## Testing

Run tests using pytest:
```bash
pytest
```

## Recipe Data Structure

Recipes are stored with an extensible format that supports:
- Basic recipe information (title, description, ingredients, instructions)
- Timing information (prep time, cook time, servings)
- Source tracking (TikTok links, websites, etc.)
- Tags and categorization
- Metadata field for future extensions

## Future Enhancements

- TikTok bot integration for automatic recipe extraction
- Image upload and management
- Recipe sharing and export
- Nutritional information
- Meal planning features