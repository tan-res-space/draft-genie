#!/bin/bash

# DraftGenie Setup Script
# This script automates the initial setup process

set -e

echo "🚀 DraftGenie Setup Script"
echo "=========================="
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 20+ from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    echo "❌ Node.js version must be 20 or higher. Current version: $(node -v)"
    exit 1
fi
echo "✅ Node.js $(node -v)"

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed"
    exit 1
fi
echo "✅ npm $(npm -v)"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker from https://www.docker.com/"
    exit 1
fi
echo "✅ Docker $(docker -v | cut -d' ' -f3 | cut -d',' -f1)"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    exit 1
fi
echo "✅ Docker Compose $(docker-compose -v | cut -d' ' -f4 | cut -d',' -f1)"

echo ""
echo "📦 Installing dependencies..."
npm install

echo ""
echo "⚙️  Setting up environment..."
if [ ! -f docker/.env ]; then
    cp docker/.env.example docker/.env
    echo "✅ Created docker/.env file"
    echo "⚠️  Please edit docker/.env and add your GEMINI_API_KEY"
    echo ""
    read -p "Press Enter to continue after adding your API key..."
else
    echo "✅ docker/.env already exists"
fi

echo ""
echo "🐳 Starting Docker services..."
npm run docker:up

echo ""
echo "⏳ Waiting for services to be healthy (30 seconds)..."
sleep 30

echo ""
echo "🗄️  Running database migrations..."
npm run db:migrate

echo ""
read -p "Do you want to seed the database with mock data? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    npm run db:seed
    echo "✅ Database seeded with mock data"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎉 You can now start the services:"
echo "   npm run dev:all"
echo ""
echo "📚 Documentation:"
echo "   - Setup Guide: docs/SETUP.md"
echo "   - API Docs: http://localhost:3000/api/docs (after starting services)"
echo ""
echo "🔗 Service URLs (after starting):"
echo "   - API Gateway: http://localhost:3000"
echo "   - Speaker Service: http://localhost:3001"
echo "   - Draft Service: http://localhost:3002"
echo "   - RAG Service: http://localhost:3003"
echo ""

