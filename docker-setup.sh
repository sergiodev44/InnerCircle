#!/bin/bash
# Local development setup with Docker

set -e

echo "=========================================="
echo "InnerCircle Docker Setup"
echo "=========================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo "⚠️  Don't forget to update .env with your credentials!"
fi

# Build and start containers
echo "🐳 Building Docker image..."
docker compose build

echo "🚀 Starting containers..."
docker compose up -d

echo "⏳ Waiting for database to be ready..."
sleep 10

echo "📦 Running migrations..."
docker compose exec -T web python proyecto_final/manage.py migrate

echo "🔐 Creating superuser..."
docker compose exec -T web python proyecto_final/manage.py createsuperuser

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Access your application:"
echo "- Web: http://localhost"
echo "- Admin: http://localhost/admin"
echo ""
echo "Useful commands:"
echo "  docker compose logs -f          # View logs"
echo "  docker compose exec web bash    # Access container shell"
echo "  docker compose down             # Stop containers"
echo ""
