# 🚀 Local Setup & Testing Guide

## Step 1: Install PostgreSQL (if not installed)

### On macOS (using Homebrew):
```bash
# Install PostgreSQL with pgvector
brew install postgresql@15 pgvector

# Start PostgreSQL
brew services start postgresql@15
```

### On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install postgresql-15 postgresql-15-pgvector
sudo systemctl start postgresql
```

### Using Docker (easiest):
```bash
docker run -d \
  --name postgres \
  -e POSTGRES_USER=ai_advisor \
  -e POSTGRES_PASSWORD=password123 \
  -e POSTGRES_DB=ai_advisor \
  -p 5432:5432 \
  pgvector/pgvector:pg15
```

## Step 2: Create Database

If using local PostgreSQL:
```bash
createdb ai_advisor
```

If using Docker, the database is already created!

## Step 3: Set Up Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp env.example .env
```

Now edit `backend/.env` with your credentials:

```env
# Database (use this if running Docker)
DATABASE_URL=postgresql+asyncpg://ai_advisor:password123@localhost:5432/ai_advisor

# OpenAI API Key (get from https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-your-key-here

# Google OAuth (set up in next section)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Hubspot OAuth (set up in next section)
HUBSPOT_CLIENT_ID=your-client-id
HUBSPOT_CLIENT_SECRET=your-client-secret
HUBSPOT_REDIRECT_URI=http://localhost:8000/auth/hubspot/callback

# App Config
SECRET_KEY=$(openssl rand -hex 32)
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

# Redis (optional for now)
REDIS_URL=redis://localhost:6379/0
```

## Step 4: Set Up Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env
```

## Step 5: Set Up OAuth Credentials

### Google OAuth Setup (15 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable APIs:
   - Gmail API
   - Google Calendar API
4. Go to "Credentials" → "Create Credentials" → "OAuth client ID"
5. Select "Web application"
6. Add authorized redirect URI:
   ```
   http://localhost:8000/auth/google/callback
   ```
7. Add test user under "OAuth consent screen":
   ```
   webshookeng@gmail.com
   ```
8. Copy **Client ID** and **Client Secret** to `backend/.env`

### Hubspot OAuth Setup (10 minutes)

1. Go to [Hubspot Developers](https://developers.hubspot.com/)
2. Create a developer account (free)
3. Create a new app
4. Under "Auth" tab:
   - Add redirect URL:
     ```
     http://localhost:8000/auth/hubspot/callback
     ```
   - Add scopes:
     - `crm.objects.contacts.read`
     - `crm.objects.contacts.write`
     - `crm.schemas.contacts.read`
     - `timeline`
5. Copy **Client ID** and **Client Secret** to `backend/.env`

## Step 6: Start the Application

### Terminal 1 - Start Backend

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Terminal 2 - Start Frontend

```bash
cd frontend
npm run dev
```

You should see:
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:3000/
```

## Step 7: Test the Application

### 1. Open Your Browser

Go to: **http://localhost:3000**

### 2. Login with Google

- Click "Continue with Google"
- Select your Google account
- Grant permissions for Gmail and Calendar
- You'll be redirected back to the app

### 3. Connect Hubspot

- Click "Connect Hubspot"
- Login to Hubspot
- Authorize the app
- You'll be redirected back

### 4. Sync Data

The setup wizard will guide you:
1. ✅ Connect Hubspot (done)
2. Click "Sync Gmail" - imports last 100 emails
3. Click "Sync Calendar" - imports events
4. Click "Sync Hubspot Data" - imports contacts

Wait a few seconds for each sync to complete.

### 5. Start Chatting!

Try these example queries:

**Basic Questions:**
```
"What emails did I receive today?"
"Who are my recent contacts?"
"What meetings do I have this week?"
"Show me emails from john@example.com"
```

**Search Questions (RAG):**
```
"Who mentioned baseball?"
"Did anyone talk about selling stock?"
"What did Sara say about the project?"
```

**Task Execution:**
```
"Schedule a meeting with John next week"
"Send an email to jane@example.com saying hello"
"Create a Hubspot contact for bob@company.com with phone 555-1234"
"What times am I available tomorrow?"
```

**Ongoing Instructions:**
```
"When someone emails me who isn't in Hubspot, create a contact for them"
"When I create a contact, send them a welcome email"
"Remember to always check the calendar before scheduling"
```

## Troubleshooting

### Backend won't start

**Error: "connection refused" or "database error"**
```bash
# Check if PostgreSQL is running
# For Homebrew:
brew services list

# For Docker:
docker ps

# Start PostgreSQL
brew services start postgresql@15
# Or for Docker:
docker start postgres
```

**Error: "module not found"**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend won't start

**Error: "Cannot find module"**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### OAuth Errors

**Error: "redirect_uri_mismatch"**
- Check that redirect URIs in Google/Hubspot console match EXACTLY:
  - Google: `http://localhost:8000/auth/google/callback`
  - Hubspot: `http://localhost:8000/auth/hubspot/callback`

**Error: "invalid_client"**
- Double-check your Client ID and Client Secret in `backend/.env`
- Make sure there are no extra spaces

### Database Errors

**Error: "relation does not exist"**
```bash
# The app should auto-create tables on startup
# If not, restart the backend:
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

**Error: "extension 'vector' does not exist"**
```bash
# Connect to database and enable pgvector
psql ai_advisor
CREATE EXTENSION vector;
\q
```

### API Errors

**Error: "OpenAI API key invalid"**
- Check your OPENAI_API_KEY in `backend/.env`
- Get a valid key from https://platform.openai.com/api-keys

**Error: "Gmail API not enabled"**
- Go to Google Cloud Console
- APIs & Services → Library
- Search for "Gmail API" and enable it
- Do the same for "Google Calendar API"

## Quick Reset

If something goes wrong and you want to start fresh:

```bash
# Stop all services
# Ctrl+C in both terminals

# Reset database
dropdb ai_advisor
createdb ai_advisor

# Or with Docker
docker rm -f postgres
docker run -d \
  --name postgres \
  -e POSTGRES_USER=ai_advisor \
  -e POSTGRES_PASSWORD=password123 \
  -e POSTGRES_DB=ai_advisor \
  -p 5432:5432 \
  pgvector/pgvector:pg15

# Clear browser data
# Go to browser settings → Clear cookies and site data for localhost

# Restart both backend and frontend
```

## Viewing Logs

### Backend Logs
The backend prints logs directly to the terminal. Look for:
- `INFO` - Normal operations
- `ERROR` - Problems that need attention

### Frontend Logs
Open browser DevTools (F12) and check the Console tab.

### Database Data

To view data in the database:
```bash
psql ai_advisor

# View users
SELECT id, email, gmail_synced, hubspot_connected FROM users;

# View messages
SELECT id, role, content FROM messages ORDER BY created_at DESC LIMIT 10;

# View documents (RAG)
SELECT id, source, title FROM documents ORDER BY created_at DESC LIMIT 10;

\q
```

## API Documentation

While the backend is running, view the API docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Performance Tips

### Speed up RAG queries
The first query might be slow (5-10 seconds) because it needs to:
1. Create embeddings
2. Search vectors
3. Call OpenAI

Subsequent queries are faster (2-3 seconds).

### Reduce sync time
By default, Gmail sync fetches 100 emails. To change:
```python
# In backend/app/services/gmail_service.py
# Line 30, change maxResults:
maxResults=50  # or any number
```

## Development Tips

### Backend Auto-Reload
The `--reload` flag makes the backend restart on code changes.
Edit any `.py` file and it will automatically reload!

### Frontend Hot Module Replacement
Vite provides instant HMR. Edit any React component and see changes immediately!

### Adding Debug Logging
Add this to any Python file:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Debug message here")
```

## Next Steps

Once everything works locally:
1. ✅ Test all features
2. ✅ Verify OAuth flows
3. ✅ Test RAG search
4. ✅ Test AI agent tools
5. 🚀 Deploy to production (see DEPLOYMENT.md)

## Common Test Scenarios

### Test 1: Basic Chat
```
You: "Hello"
Agent: Should respond with a greeting
```

### Test 2: Email Search
```
You: "What emails did I get today?"
Agent: Should list recent emails
```

### Test 3: Calendar
```
You: "What's on my calendar tomorrow?"
Agent: Should list tomorrow's events
```

### Test 4: Hubspot
```
You: "Who are my contacts?"
Agent: Should list Hubspot contacts
```

### Test 5: Complex Task
```
You: "Schedule a 30-minute meeting with John Smith next Tuesday at 2pm"
Agent: Should:
1. Look up John Smith in Hubspot
2. Check calendar availability
3. Send email to John
4. (After John replies) Add to calendar
```

### Test 6: Ongoing Instruction
```
You: "When someone emails me, add them to Hubspot"
Agent: Should save this instruction
Then test by having someone email you
```

## Support

Need help? Check:
- Main README: `README.md`
- Deployment guide: `DEPLOYMENT.md`
- Quick start: `QUICKSTART.md`

## Success Checklist

- [ ] PostgreSQL running
- [ ] Database created
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Environment variables set
- [ ] Google OAuth configured
- [ ] Hubspot OAuth configured
- [ ] Backend started successfully
- [ ] Frontend started successfully
- [ ] Can login with Google
- [ ] Can connect Hubspot
- [ ] Data synced successfully
- [ ] Chat works
- [ ] AI responds to questions
- [ ] Tools execute successfully

When all checked, you're ready to deploy! 🚀

