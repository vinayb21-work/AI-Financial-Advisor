#!/bin/bash

echo "🚀 Setting up AI Financial Advisor Agent..."

# Check for required tools
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed. Aborting." >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed. Aborting." >&2; exit 1; }
command -v psql >/dev/null 2>&1 || { echo "❌ PostgreSQL is required but not installed. Aborting." >&2; exit 1; }

echo "✅ All required tools found"

# Backend setup
echo "\n📦 Setting up backend..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
echo "✅ Backend dependencies installed"

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    cp env.example .env
    echo "⚠️  Created .env file. Please edit it with your credentials."
fi

cd ..

# Frontend setup
echo "\n📦 Setting up frontend..."
cd frontend

# Install dependencies
npm install
echo "✅ Frontend dependencies installed"

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  Created frontend .env file"
fi

cd ..

echo "\n✅ Setup complete!"
echo "\n📝 Next steps:"
echo "1. Edit backend/.env with your API credentials"
echo "2. Create PostgreSQL database: createdb ai_advisor"
echo "3. Start backend: cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo "4. Start frontend: cd frontend && npm run dev"
echo "5. Open http://localhost:3000 in your browser"
echo "\n🎉 Happy coding!"

