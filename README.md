# AI Financial Advisor Agent

An intelligent AI agent for financial advisors that integrates with Gmail, Google Calendar, and Hubspot CRM. The agent uses RAG (Retrieval Augmented Generation) with OpenAI's GPT-4 and function calling to answer questions and perform tasks autonomously.

## Features

- 🔐 **Google OAuth Authentication** - Secure login with Gmail and Calendar permissions
- 📧 **Gmail Integration** - Read and send emails, search through email history
- 📅 **Calendar Integration** - View availability, schedule meetings, manage events
- 🏢 **Hubspot CRM Integration** - Sync contacts, add notes, search client information
- 🤖 **AI Agent with Tool Calling** - Autonomous task execution using OpenAI's function calling
- 💾 **RAG System** - Vector database (pgvector) for semantic search across emails and CRM data
- 🧠 **Memory System** - Remembers ongoing instructions and task context
- 🎨 **Modern Chat UI** - Clean, responsive interface matching the provided design
- ⚡ **Real-time Sync** - Manual sync and polling for data from integrations
- 🔄 **Proactive Agent** - Automatic actions based on ongoing instructions and new events

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with pgvector extension
- **AI**: OpenAI GPT-4o with function calling
- **Authentication**: Google OAuth 2.0, Hubspot OAuth
- **Background Tasks**: APScheduler for Gmail polling
- **ORM**: SQLAlchemy (async)

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: TailwindCSS
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Routing**: React Router v6

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ with pgvector extension
- OpenAI API key
- Google Cloud Project with OAuth credentials
- Hubspot Developer Account

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd ai-financial-advisor
```

### 2. Set Up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API and Google Calendar API
4. Create OAuth 2.0 credentials (Web application)
5. Add authorized redirect URI: `http://localhost:8000/auth/google/callback`
6. Add test user: `webshookeng@gmail.com`
7. Copy Client ID and Client Secret

### 3. Set Up Hubspot OAuth

1. Go to [Hubspot Developers](https://developers.hubspot.com/)
2. Create a developer account (free)
3. Create a new app
4. Set redirect URI: `http://localhost:8000/auth/hubspot/callback`
5. Add required scopes:
   - `crm.objects.contacts.read`
   - `crm.objects.contacts.write`
   - `crm.schemas.contacts.read`
   - `crm.objects.companies.read`
   - `crm.objects.companies.write`
   - `crm.objects.custom.read`
   - `crm.objects.custom.write`
   - `sales-email-read`
   - `timeline`
6. Copy Client ID and Client Secret

### 4. Set Up Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required environment variables:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_advisor
OPENAI_API_KEY=your_openai_api_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
HUBSPOT_CLIENT_ID=your_hubspot_client_id
HUBSPOT_CLIENT_SECRET=your_hubspot_client_secret
HUBSPOT_REDIRECT_URI=http://localhost:8000/auth/hubspot/callback
SECRET_KEY=your_secret_key_here
FRONTEND_URL=http://localhost:3000
```

### 5. Set Up Database

```bash
# Install PostgreSQL with pgvector
# On macOS:
brew install postgresql pgvector

# On Ubuntu:
sudo apt-get install postgresql-15 postgresql-15-pgvector

# Create database
createdb ai_advisor

# The application will automatically create tables and enable pgvector on startup
```

### 6. Set Up Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Edit .env
nano .env
```

Required environment variables:
```env
VITE_API_URL=http://localhost:8000
```

### 7. Run the Application

#### Option 1: Using Docker (Recommended for Database)

```bash
# Start PostgreSQL with pgvector
docker run -d \
  --name ai-advisor-db \
  -e POSTGRES_USER=ai_advisor \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=ai_advisor \
  -p 5432:5432 \
  ankane/pgvector
```

For detailed local setup instructions, see [LOCAL_SETUP.md](./LOCAL_SETUP.md)

#### Option 2: Run Manually

Terminal 1 - Backend:
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

### 8. Access the Application

1. Open browser and go to `http://localhost:3000`
2. Click "Continue with Google"
3. Grant permissions for Gmail and Calendar
4. Complete setup:
   - Connect Hubspot CRM
   - Sync Gmail emails
   - Sync Calendar events
   - Sync Hubspot contacts
5. Start chatting with your AI agent!

## Usage Examples

### Ask Questions

```
"Who mentioned their kid plays baseball?"
"Why did Greg want to sell AAPL stock?"
"What meetings do I have this week?"
"Show me contacts from Acme Corp"
```

### Request Actions

```
"Schedule an appointment with Sara Smith"
"Send an email to john@example.com thanking them for the meeting"
"Create a Hubspot contact for jane@example.com"
"Find available time slots next week for a 1-hour meeting"
```

### Set Ongoing Instructions

```
"When someone emails me who is not in Hubspot, create a contact for them"
"When I create a contact in Hubspot, send them a welcome email"
"When I add a calendar event, send a reminder email to attendees"
```

## Deployment

This application is deployed on Render:

- **Frontend**: [https://ai-advisor-frontend-59v2.onrender.com](https://ai-advisor-frontend-59v2.onrender.com)
- **Backend**: [https://ai-advisor-backend-02ky.onrender.com](https://ai-advisor-backend-02ky.onrender.com)

### Deploy Your Own Instance to Render

1. **Push your code to GitHub**

2. **Create Environment Group** in Render Dashboard:
   - Name: `ai-advisor-secrets`
   - Add all required environment variables (see Prerequisites)

3. **Create PostgreSQL Database**:
   - Name: `ai-advisor-db`
   - PostgreSQL Version: 15

4. **Deploy from render.yaml**:
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will detect `render.yaml` and create all services

5. **Configure Frontend Static Site**:
   - After creation, go to frontend service settings
   - Navigate to "Redirects/Rewrites" tab
   - Add rule:
     - Type: `Rewrite`
     - Source: `/*`
     - Destination: `/index.html`
     - Status: `200`

6. **Update OAuth Redirect URIs**:
   - Google Cloud Console: Update redirect URI to your backend URL
   - Hubspot Developer: Update redirect URI to your backend URL

For detailed deployment instructions, see the deployment guide in the repository.

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   React     │─────▶│   FastAPI    │─────▶│ PostgreSQL  │
│  Frontend   │      │   Backend    │      │  +pgvector  │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ├──────▶ OpenAI GPT-4
                            │
                            ├──────▶ Gmail API
                            │
                            ├──────▶ Google Calendar API
                            │
                            └──────▶ Hubspot API
```

## Key Components

### Backend Services

- **AIAgent**: Main orchestrator using OpenAI function calling
- **RAGService**: Vector search using pgvector and OpenAI embeddings
- **ToolExecutor**: Executes tools called by AI (send email, schedule meeting, etc.)
- **GmailService**: Gmail API integration
- **CalendarService**: Google Calendar API integration
- **HubspotService**: Hubspot CRM API integration

### Frontend Components

- **Chat**: Main chat interface with message history
- **ChatInput**: Message input with context selector
- **ChatMessages**: Message display with rich formatting
- **ChatSidebar**: Thread history and navigation
- **SetupPrompt**: First-time setup wizard

## API Endpoints

### Authentication
- `GET /auth/google/login` - Initiate Google OAuth
- `GET /auth/google/callback` - Google OAuth callback
- `GET /auth/hubspot/connect` - Initiate Hubspot OAuth
- `GET /auth/hubspot/callback` - Hubspot OAuth callback
- `GET /auth/me` - Get current user

### Chat
- `POST /chat/message` - Send message to AI agent
- `GET /chat/threads` - Get all conversation threads
- `GET /chat/threads/{id}` - Get specific thread with messages
- `PATCH /chat/threads/{id}` - Update thread (rename)
- `DELETE /chat/threads/{id}` - Delete thread

### Integrations
- `POST /integrations/sync/gmail` - Sync Gmail emails
- `POST /integrations/sync/calendar` - Sync calendar events
- `POST /integrations/sync/hubspot` - Sync Hubspot contacts
- `GET /integrations/sync/status` - Get sync status

### Webhooks
- `POST /webhooks/gmail` - Gmail webhook
- `POST /webhooks/calendar` - Calendar webhook
- `POST /webhooks/hubspot` - Hubspot webhook

## Contributing

This project was built as part of a coding challenge. Feel free to fork and improve!

## License

MIT

## Support

For questions or issues, please create an issue in the GitHub repository.

---

Built with ❤️ using AI assistance (as required by the challenge!)

