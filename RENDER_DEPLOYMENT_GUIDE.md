# 🚀 Complete Render Deployment Guide

## Overview
This guide will walk you through deploying the AI Financial Advisor app to Render from scratch.

**Time Required:** ~45-60 minutes
**Cost:** Free tier available for all services

---

## Prerequisites Checklist

- [ ] GitHub account
- [ ] Render account (sign up at https://render.com)
- [ ] Google Cloud Console access (for OAuth)
- [ ] Hubspot Developer account
- [ ] OpenAI API key
- [ ] Code pushed to GitHub repository

---

## Part 1: Prepare Your Repository (10 minutes)

### Step 1.1: Push Code to GitHub

```bash
cd /Users/vinaybadhan/Desktop/jump

# Initialize git if not already done
git init

# Create .gitignore (very important!)
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Node
node_modules/
.pnpm-store/
dist/
build/

# Environment variables
.env
.env.local
.env.production

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Database
*.db
*.sqlite
EOF

# Add all files
git add .

# Commit
git commit -m "Initial commit - AI Financial Advisor"

# Create GitHub repo (go to github.com/new)
# Then push:
git remote add origin https://github.com/YOUR_USERNAME/ai-financial-advisor.git
git branch -M main
git push -u origin main
```

### Step 1.2: Create Render Configuration Files

#### Backend: `render.yaml` (root directory)

```bash
cat > render.yaml << 'EOF'
services:
  # PostgreSQL Database
  - type: pserv
    name: ai-advisor-db
    env: docker
    plan: free
    region: oregon
    ipAllowList: []
    databases:
      - name: ai_advisor_db
        user: ai_advisor

  # Backend API
  - type: web
    name: ai-advisor-backend
    env: python
    region: oregon
    plan: free
    buildCommand: cd backend && pip install -r requirements.txt
    startCommand: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: DATABASE_URL
        fromDatabase:
          name: ai-advisor-db
          property: connectionString
      - fromGroup: ai-advisor-secrets
    healthCheckPath: /health

  # Frontend
  - type: web
    name: ai-advisor-frontend
    env: static
    region: oregon
    plan: free
    buildCommand: cd frontend && npm install && npm run build
    staticPublishPath: frontend/dist
    envVars:
      - key: VITE_API_URL
        value: https://ai-advisor-backend.onrender.com
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
EOF
```

#### Backend: Update `requirements.txt`

```bash
cd backend
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
asyncpg==0.29.0
psycopg2-binary==2.9.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
openai==1.51.0
google-auth==2.25.2
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.110.0
requests==2.31.0
pgvector==0.2.4
pydantic==2.5.2
pydantic-settings==2.1.0
python-dotenv==1.0.0
httpx==0.27.2
greenlet==3.0.3
apscheduler==3.10.4
EOF
cd ..
```

#### Frontend: Update `package.json` build script

```bash
cd frontend
# Add to package.json scripts:
# "build": "tsc && vite build",
# "preview": "vite preview"
cd ..
```

### Step 1.3: Commit Configuration Files

```bash
git add render.yaml backend/requirements.txt
git commit -m "Add Render deployment configuration"
git push origin main
```

---

## Part 2: Deploy to Render (15 minutes)

### Step 2.1: Create Render Account

1. Go to https://render.com
2. Click "Get Started for Free"
3. Sign up with GitHub
4. Authorize Render to access your repositories

### Step 2.2: Create PostgreSQL Database

1. Click **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name:** `ai-advisor-db`
   - **Database:** `ai_advisor_db`
   - **User:** `ai_advisor`
   - **Region:** Oregon (or closest to you)
   - **Plan:** Free
3. Click **"Create Database"**
4. Wait ~2 minutes for provisioning
5. **Save these values** (Dashboard → Info):
   - Internal Database URL (starts with `postgresql://`)
   - External Database URL
   - Host
   - Port
   - Database Name
   - Username
   - Password

### Step 2.3: Setup Database Extension (CRITICAL!)

1. In Render Dashboard → Your Database → "Connect"
2. Click **"PSQL Command"** to open shell
3. Run these commands:

```sql
-- Connect to database
\c ai_advisor_db

-- Create pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify
\dx

-- Should see 'vector' in the list
-- Exit
\q
```

**Alternative method using local psql:**
```bash
# From your local machine (save the External Database URL from Render)
psql "postgresql://ai_advisor:[password]@[host]/ai_advisor_db"

CREATE EXTENSION IF NOT EXISTS vector;
\q
```

### Step 2.4: Create Environment Variable Group

1. Go to Render Dashboard → "Environment Groups"
2. Click **"New Environment Group"**
3. Name it: `ai-advisor-secrets`
4. Add these variables:

```bash
# Database (will be auto-set from database connection)
DATABASE_URL=[Auto-filled from database]

# Security
SECRET_KEY=[Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"]

# Google OAuth (from Google Cloud Console)
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Hubspot OAuth (from Hubspot Developer Portal)
HUBSPOT_CLIENT_ID=your_hubspot_client_id
HUBSPOT_CLIENT_SECRET=your_hubspot_client_secret

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# Optional: Custom OpenAI endpoint
OPENAI_API_BASE=https://api.openai.com/v1

# Frontend URL (update after frontend deployed)
FRONTEND_URL=https://ai-advisor-frontend.onrender.com

# CORS Origins
CORS_ORIGINS=https://ai-advisor-frontend.onrender.com,http://localhost:5173
```

5. Click **"Save"**

### Step 2.5: Deploy Backend

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:
   - **Name:** `ai-advisor-backend`
   - **Region:** Oregon (same as database)
   - **Branch:** `main`
   - **Root Directory:** Leave empty
   - **Runtime:** Python 3
   - **Build Command:** 
     ```bash
     cd backend && pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan:** Free
4. **Environment:**
   - Select the `ai-advisor-secrets` group
   - Add `DATABASE_URL` from your PostgreSQL database (click "Add from Database")
5. Click **"Create Web Service"**
6. Wait ~5-10 minutes for first deploy
7. **Save the URL:** `https://ai-advisor-backend.onrender.com`

### Step 2.6: Deploy Frontend

1. Click **"New +"** → **"Static Site"**
2. Connect your GitHub repository
3. Configure:
   - **Name:** `ai-advisor-frontend`
   - **Branch:** `main`
   - **Root Directory:** Leave empty
   - **Build Command:**
     ```bash
     cd frontend && npm install && npm run build
     ```
   - **Publish Directory:** `frontend/dist`
4. **Environment Variables:**
   ```bash
   VITE_API_URL=https://ai-advisor-backend.onrender.com
   ```
5. Click **"Create Static Site"**
6. Wait ~5 minutes for build
7. **Save the URL:** `https://ai-advisor-frontend.onrender.com`

---

## Part 3: Update OAuth Redirect URIs (10 minutes)

### Step 3.1: Update Google OAuth

1. Go to https://console.cloud.google.com
2. Select your project
3. **APIs & Services** → **Credentials**
4. Click your OAuth 2.0 Client ID
5. **Authorized JavaScript origins** - Add:
   ```
   https://ai-advisor-frontend.onrender.com
   ```
6. **Authorized redirect URIs** - Add:
   ```
   https://ai-advisor-backend.onrender.com/auth/google/callback
   ```
7. Click **"Save"**

### Step 3.2: Update Hubspot OAuth

1. Go to https://developers.hubspot.com
2. Select your app
3. **Auth** tab
4. **Redirect URLs** - Add:
   ```
   https://ai-advisor-backend.onrender.com/auth/hubspot/callback
   ```
5. Click **"Save"**

### Step 3.3: Update Frontend Environment Variable

1. Go to Render Dashboard → `ai-advisor-frontend`
2. **Environment** tab
3. Update `VITE_API_URL`:
   ```
   VITE_API_URL=https://ai-advisor-backend.onrender.com
   ```
4. Click **"Save Changes"**
5. Wait for automatic redeploy (~2 minutes)

---

## Part 4: Initialize Database (5 minutes)

### Step 4.1: Check Database Tables Created

1. Go to Render Dashboard → `ai-advisor-backend`
2. Click **"Logs"** tab
3. Look for:
   ```
   INFO: Application startup complete
   ```

If you see errors about tables not existing:

### Step 4.2: Manually Create Tables (if needed)

```bash
# Connect to your Render database
psql "YOUR_EXTERNAL_DATABASE_URL_FROM_RENDER"

# The tables should be auto-created by SQLAlchemy on startup
# If not, check the backend logs for errors
```

### Step 4.3: Verify Health Endpoint

```bash
curl https://ai-advisor-backend.onrender.com/health

# Should return:
# {"status":"healthy"}
```

---

## Part 5: Test the Deployment (10 minutes)

### Step 5.1: Access the Application

1. Open browser to: `https://ai-advisor-frontend.onrender.com`
2. You should see the login page

### Step 5.2: Test Google OAuth

1. Click **"Sign in with Google"**
2. Authorize the app
3. Should redirect back successfully
4. If you see errors, check:
   - Browser console (F12)
   - Backend logs in Render Dashboard

### Step 5.3: Test Hubspot Connection

1. After logging in, click **"Connect Hubspot"**
2. Authorize the app
3. Should redirect back successfully

### Step 5.4: Test Sync & Chat

1. Click the **"Sync"** button
2. Wait for sync to complete
3. Try a test query: "List all my contacts"

---

## Part 6: Production Configuration (5 minutes)

### Step 6.1: Enable Auto-Deploy

1. Render Dashboard → Each service
2. **Settings** → **Auto-Deploy**
3. Set to **"Yes"**

This will auto-deploy when you push to GitHub.

### Step 6.2: Set Up Monitoring

1. Render Dashboard → `ai-advisor-backend`
2. **Alerts** tab
3. Add email alerts for:
   - Service down
   - High error rate
   - High response time

### Step 6.3: Enable HTTPS (Already enabled by default)

Render provides free SSL certificates automatically!

---

## Troubleshooting Guide

### Issue: Backend Won't Start

**Check Logs:**
```
Render Dashboard → ai-advisor-backend → Logs
```

**Common Issues:**
1. **Missing dependencies:**
   ```
   Solution: Add to requirements.txt, push, redeploy
   ```

2. **Database connection failed:**
   ```
   Solution: Check DATABASE_URL is correct
   Verify: psql "DATABASE_URL" works
   ```

3. **Port binding error:**
   ```
   Solution: Use $PORT environment variable (already configured)
   ```

### Issue: Frontend Shows "API Error"

**Checks:**
1. Verify `VITE_API_URL` is correct:
   ```
   Render Dashboard → frontend → Environment
   Should be: https://ai-advisor-backend.onrender.com (no trailing slash)
   ```

2. Check backend is running:
   ```bash
   curl https://ai-advisor-backend.onrender.com/health
   ```

3. Check CORS settings:
   ```
   Backend logs should show: "CORS origins: https://ai-advisor-frontend.onrender.com"
   ```

### Issue: OAuth Redirects Failing

**For Google:**
1. Verify redirect URI exactly matches:
   ```
   https://ai-advisor-backend.onrender.com/auth/google/callback
   ```
2. Check JavaScript origins:
   ```
   https://ai-advisor-frontend.onrender.com
   ```
3. Ensure no trailing slashes

**For Hubspot:**
1. Verify redirect URI:
   ```
   https://ai-advisor-backend.onrender.com/auth/hubspot/callback
   ```
2. Check app is public or you're a test user

### Issue: Database Connection Timeout

**Solutions:**
1. **Free tier spin-down:** First request after 15 min takes ~30s
2. **Keep-alive:** Add a cron job to ping `/health` every 10 minutes
3. **Upgrade:** Consider paid plan for always-on

### Issue: Slow Performance

**Render Free Tier Limitations:**
- Spins down after 15 minutes of inactivity
- 512 MB RAM
- Shared CPU

**Solutions:**
1. **Upgrade to paid:** $7/month per service
2. **Optimize queries:** Use database indexes
3. **Cache:** Add Redis for caching (optional)

---

## Cost Breakdown

### Free Tier (Sufficient for Testing & Demo)
- PostgreSQL: Free (shared, 1GB storage)
- Backend: Free (512MB RAM, spins down after 15 min)
- Frontend: Free (100GB bandwidth/month)
- **Total: $0/month**

### Paid Tier (Production Ready)
- PostgreSQL: $7/month (2GB RAM, 20GB storage)
- Backend: $7/month (512MB RAM, always on)
- Frontend: Free
- **Total: $14/month**

---

## Post-Deployment Checklist

- [ ] Backend health endpoint working
- [ ] Frontend loads correctly
- [ ] Google OAuth login works
- [ ] Hubspot connection works
- [ ] Sync button imports data successfully
- [ ] Chat responds to queries
- [ ] Tools are called correctly
- [ ] RAG search returns results
- [ ] No errors in backend logs
- [ ] No errors in browser console

---

## Environment Variables Reference

### Backend Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:pass@host/db
SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx
HUBSPOT_CLIENT_ID=xxx
HUBSPOT_CLIENT_SECRET=xxx
OPENAI_API_KEY=sk-xxx
FRONTEND_URL=https://your-frontend.onrender.com

# Optional
OPENAI_API_BASE=https://api.openai.com/v1
CORS_ORIGINS=https://your-frontend.onrender.com
GOOGLE_PROJECT_ID=your-project-id
```

### Frontend Environment Variables

```bash
# Required
VITE_API_URL=https://your-backend.onrender.com
```

---

## Maintenance

### Update Application

```bash
# Local changes
git add .
git commit -m "Update feature"
git push origin main

# Render will auto-deploy (if enabled)
# Or manually trigger: Render Dashboard → Service → "Manual Deploy"
```

### View Logs

```bash
# Render Dashboard → Service → Logs
# Or install Render CLI:
npm install -g render-cli
render logs -s ai-advisor-backend -f
```

### Database Backup

```bash
# From Render Dashboard:
# PostgreSQL → Backups → Download

# Or use pg_dump:
pg_dump "YOUR_EXTERNAL_DATABASE_URL" > backup.sql
```

---

## Next Steps After Deployment

1. ✅ Test all functionality with QUICK_TEST_GUIDE.md
2. ✅ Add test user: `webshookeng@gmail.com` to Google OAuth
3. ✅ Submit URLs to challenge:
   - App URL: `https://ai-advisor-frontend.onrender.com`
   - GitHub: `https://github.com/YOUR_USERNAME/ai-financial-advisor`
4. ✅ Monitor logs for first 24 hours
5. ✅ Set up alerts for downtime

---

## Support Resources

- **Render Docs:** https://render.com/docs
- **Render Community:** https://community.render.com
- **Your Backend Logs:** Render Dashboard → ai-advisor-backend → Logs
- **Your Database:** Render Dashboard → ai-advisor-db → Connect

---

**Deployment Complete!** 🎉

Your app should now be live at:
- **Frontend:** `https://ai-advisor-frontend.onrender.com`
- **Backend:** `https://ai-advisor-backend.onrender.com`

Test it thoroughly and you're ready to submit! 🚀

