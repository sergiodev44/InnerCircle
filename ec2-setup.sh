#!/bin/bash
# InnerCircle EC2 Deployment Setup Script (Debian 13)
# This script prepares a Debian EC2 instance for deployment

set -e

echo "=========================================="
echo "InnerCircle EC2 Setup Script"
echo "=========================================="

# Update system packages
echo "🔄 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages (Docker install handled via user data script)
echo "📦 Installing dependencies..."
sudo apt-get install -y \
    curl \
    git \
    postgresql-client

# Docker is installed via EC2 user data script
# Add admin user to docker group
echo "👤 Configuring Docker permissions..."
sudo usermod -aG docker admin
newgrp docker

# Create app directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/innercircle
sudo chown admin:admin /opt/innercircle

echo ""
echo "=========================================="
echo "✅ EC2 Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Clone your repository:"
echo "   cd /opt/innercircle"
echo "   git clone -b feature/deploy_0 <your-repo-url> ."
echo ""
echo "2. Create .env file with production values:"
echo "   cp .env.example .env"
echo "   nano .env"
echo ""
echo "3. Start the application:"
echo "   docker compose up -d"
echo ""
echo "4. Run migrations:"
echo "   docker compose exec web python manage.py migrate"
echo ""
echo "5. Check logs:"
echo "   docker compose logs -f"
echo ""
