# Quick Start Guide

Get the AI Financial Advisor Agent running in minutes!

## Prerequisites

Make sure you have:
- ✅ Python 3.11+
- ✅ Node.js 18+
- ✅ PostgreSQL 15+ with pgvector
- ✅ OpenAI API key
- ✅ Google OAuth credentials
- ✅ Hubspot Developer account

## Quick Setup (5 minutes)

### 1. Run Setup Script

```bash
./setup.sh
```

This will:
- Create Python virtual environment
- Install backend dependencies
- Install frontend dependencies  
- Create .env files

### 2. Configure Environment Variables

Edit `backend/.env`:

```env
# Get from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-...

# Get from Google Cloud Console
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# Get from Hubspot Developer Portal
HUBSPOT_CLIENT_ID=...
HUBSPOT_CLIENT_SECRET=...

# Generate a random string
SECRET_KEY=$(openssl rand -hex 32)
```

### 3. Create Database

```bash
# Create PostgreSQL database
createdb ai_advisor

# Or use Docker
docker run -d \
  --name postgres \
  -e POSTGRES_DB=ai_advisor \
  -e POSTGRES_PASSWORD=password123 \
  -p 5432:5432 \
  pgvector/pgvector:pg15
```

### 4. Start Backend

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main:app --reload
```

Backend will run on http://localhost:8000

### 5. Start Frontend

In a new terminal:

```bash
cd frontend
npm run dev
```

Frontend will run on http://localhost:3000

### 6. Configure OAuth Apps

#### Google OAuth

1. Go to https://console.cloud.google.com/
2. Create project → Enable Gmail API & Calendar API
3. Create OAuth credentials → Web application
4. Add redirect URI: `http://localhost:8000/auth/google/callback`
5. Add test user: `webshookeng@gmail.com`

#### Hubspot OAuth

1. Go to https://developers.hubspot.com/
2. Create app
3. Add redirect URI: `http://localhost:8000/auth/hubspot/callback`
4. Add scopes: `crm.objects.contacts.read`, `crm.objects.contacts.write`, `crm.schemas.contacts.read`, `timeline`

### 7. Open App

1. Go to http://localhost:3000
2. Click "Continue with Google"
3. Grant permissions
4. Connect Hubspot
5. Sync data
6. Start chatting!

## Quick Test

Try these commands in the chat:

```
"What emails have I received today?"
"Schedule a meeting with John next week"
"Who are my recent contacts?"
"When is my next meeting?"
```

## Docker Quick Start

Prefer Docker? Run everything with one command:

```bash
# Copy environment variables
cp backend/env.example backend/.env
# Edit backend/.env with your credentials
nano backend/.env

# Start everything
docker-compose up
```

This starts:
- PostgreSQL with pgvector (port 5432)
- Redis (port 6379)
- Backend API (port 8000)
- Frontend (port 3000)

## Troubleshooting

### "Module not found" errors

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### "Database connection failed"

```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT version();"

# Check DATABASE_URL in .env
# Should be: postgresql+asyncpg://user:pass@localhost:5432/ai_advisor
```

### "OAuth redirect URI mismatch"

Make sure redirect URIs in Google/Hubspot console match exactly:
- Google: `http://localhost:8000/auth/google/callback`
- Hubspot: `http://localhost:8000/auth/hubspot/callback`

### "pgvector extension not found"

```bash
# Install pgvector
# macOS: brew install pgvector
# Ubuntu: apt-get install postgresql-15-pgvector

# Enable in database
psql ai_advisor -c "CREATE EXTENSION vector;"
```

## Next Steps

- 📖 Read the full [README.md](README.md)
- 🚀 Deploy to production: [DEPLOYMENT.md](DEPLOYMENT.md)
- 🎨 Customize the UI in `frontend/src/components/`
- 🤖 Add more tools in `backend/app/services/tools.py`
- 📊 View API docs: http://localhost:8000/docs

## Architecture Overview

```
┌─────────────┐
│   Browser   │
│             │
│  localhost  │
│   :3000     │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│   React     │────▶│   FastAPI    │
│   Vite      │     │   Python     │
│  Frontend   │     │   Backend    │
└─────────────┘     └──────┬───────┘
                           │
                ┌──────────┼──────────┐
                │          │          │
                ▼          ▼          ▼
         ┌──────────┐ ┌──────┐ ┌─────────┐
         │PostgreSQL│ │OpenAI│ │  Gmail  │
         │+pgvector │ │ API  │ │Calendar │
         │          │ └──────┘ │Hubspot  │
         └──────────┘           └─────────┘
```

## Key Files

- `backend/main.py` - API entry point
- `backend/app/services/ai_agent.py` - AI agent logic
- `backend/app/services/rag_service.py` - Vector search
- `frontend/src/pages/Chat.tsx` - Chat interface
- `frontend/src/components/ChatMessages.tsx` - Message display

## Development Tips

### Backend Auto-reload

The backend auto-reloads on code changes when running with `--reload` flag.

### Frontend Hot Module Replacement

Vite provides instant HMR. Just save files and see changes immediately.

### View API Documentation

OpenAPI docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Database GUI

Use a PostgreSQL client to view data:
- TablePlus (macOS)
- pgAdmin
- DBeaver

## Support

Need help? Check:
- Full README: [README.md](README.md)
- Deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- Create an issue on GitHub

Happy coding! 🚀

