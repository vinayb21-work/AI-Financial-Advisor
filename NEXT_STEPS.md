# 🎯 Next Steps to Run Locally

## ✅ What's Already Done

- [x] PostgreSQL running in Docker
- [x] Backend virtual environment created
- [x] Backend dependencies installed
- [x] Backend .env file created
- [x] Frontend dependencies installed  
- [x] Frontend .env file created

## ⚙️ Step 1: Get API Keys (Required)

### 1. OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key
4. Edit `backend/.env` and replace `your-openai-key-here` with your actual key

### 2. Google OAuth (for Gmail + Calendar)
1. Go to https://console.cloud.google.com/
2. Create a new project
3. Enable these APIs:
   - Gmail API
   - Google Calendar API
4. Go to "Credentials" → "Create Credentials" → "OAuth client ID"
5. Application type: "Web application"
6. Add redirect URI: `http://localhost:8000/auth/google/callback`
7. Under "OAuth consent screen", add test user: `webshookeng@gmail.com`
8. Copy Client ID and Client Secret
9. Edit `backend/.env`:
   - Replace `your-google-client-id` with your Client ID
   - Replace `your-google-client-secret` with your Client Secret

### 3. Hubspot OAuth
1. Go to https://developers.hubspot.com/
2. Create a free developer account
3. Create a new app
4. Under "Auth" tab:
   - Add redirect URL: `http://localhost:8000/auth/hubspot/callback`
   - Add scopes: `crm.objects.contacts.read`, `crm.objects.contacts.write`, `crm.schemas.contacts.read`, `timeline`
5. Copy Client ID and Client Secret
6. Edit `backend/.env`:
   - Replace `your-hubspot-client-id` with your Client ID
   - Replace `your-hubspot-client-secret` with your Client Secret

## 🚀 Step 2: Start the Application

Open 2 terminal windows:

### Terminal 1 - Backend
```bash
cd /Users/vinaybadhan/Desktop/jump/backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Database initialized
INFO:     Database tables created successfully
INFO:     Application startup complete.
```

### Terminal 2 - Frontend
```bash
cd /Users/vinaybadhan/Desktop/jump/frontend
npm run dev
```

You should see:
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
```

## 🧪 Step 3: Test the Application

1. Open your browser: **http://localhost:3000**
2. Click "Continue with Google"
3. Login with your Google account
4. Grant permissions
5. Connect Hubspot
6. Sync your data (Gmail, Calendar, Hubspot)
7. Start chatting!

## 💬 Try These Commands

```
"What emails did I receive today?"
"What meetings do I have this week?"
"Schedule a meeting with John next Tuesday at 2pm"
"Send an email to jane@example.com"
"Who are my contacts?"
```

## 🔍 Troubleshooting

### Backend won't start
- Check if PostgreSQL is running: `docker ps`
- Make sure all API keys are set in `backend/.env`
- Check for errors in the terminal output

### Frontend won't connect
- Make sure backend is running first
- Check browser console (F12) for errors
- Verify `VITE_API_URL` in `frontend/.env` is `http://localhost:8000`

### OAuth errors
- Double-check redirect URIs match exactly
- Make sure test users are added in OAuth consent screens
- Clear browser cookies and try again

### Database errors
- Restart PostgreSQL: `docker restart postgres`
- Check DATABASE_URL in `backend/.env`

## 📚 Additional Resources

- Full setup guide: `LOCAL_SETUP.md`
- Main README: `README.md`
- Deployment guide: `DEPLOYMENT.md`

## ⏱️ Time Estimate

- Get API keys: ~20 minutes
- Start and test: ~5 minutes
- **Total: ~25 minutes**

## 🎉 Success!

Once you see the chat interface and can send messages, you're all set!

Next step: Deploy to production using `DEPLOYMENT.md`

