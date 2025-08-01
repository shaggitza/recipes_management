#!/bin/bash

echo "🚀 Recipe Management Application Deployment"
echo "=========================================="

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build and start services
echo "🏗️  Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "🌐 Application URLs:"
    echo "   • Main Application: http://localhost:8000"
    echo "   • API Documentation: http://localhost:8000/docs"
    echo "   • Health Check: http://localhost:8000/health"
    echo ""
    echo "📱 Features:"
    echo "   • Add, edit, delete recipes"
    echo "   • Search and filter recipes"
    echo "   • TikTok URL support"
    echo "   • Responsive design"
    echo "   • RESTful API"
    echo ""
    echo "🛑 To stop the application: docker-compose down"
    echo "📊 To view logs: docker-compose logs -f"
else
    echo "❌ Services failed to start. Check logs with: docker-compose logs"
    exit 1
fi