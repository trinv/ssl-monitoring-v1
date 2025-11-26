#!/bin/bash
# Domain Monitor - Quick Start Script

echo "=========================================="
echo " Domain Monitor - Starting..."
echo " Server: 74.48.129.112"
echo " Backend Port: 8080"
echo "=========================================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install it first."
    exit 1
fi

# Create .env if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
fi

# Start services
echo "🚀 Starting services..."
docker-compose up -d --build

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 10

# Show status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "=========================================="
echo "✅ Domain Monitor is ready!"
echo "=========================================="
echo ""
echo "🌐 Access:"
echo "   Frontend: http://74.48.129.112"
echo "   Backend API: http://74.48.129.112:8080"
echo ""
echo "🔑 Login:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📝 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop: docker-compose stop"
echo "   Restart: docker-compose restart"
echo "=========================================="
