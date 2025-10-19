# 📋 Deployment Checklist - Quick Reference

## Before You Start (5 minutes)

### Get These Ready:
- [ ] **Google Cloud Console** - https://console.cloud.google.com
  - OAuth Client ID and Secret
  - Add test user: `webshookeng@gmail.com`
  
- [ ] **Hubspot Developer Portal** - https://developers.hubspot.com
  - App Client ID and Secret
  
- [ ] **OpenAI API Key** - https://platform.openai.com/api-keys
  - Active API key with credits
  
- [ ] **GitHub Account** - Repository ready
  
- [ ] **Render Account** - https://render.com (sign up free)

---

## Deployment Steps (45 minutes)

### Phase 1: Prepare Repository (10 min)
- [ ] 1. Code is committed and pushed to GitHub
- [ ] 2. `.gitignore` includes `.env`, `node_modules/`, `venv/`
- [ ] 3. `render.yaml` is in root directory
- [ ] 4. `backend/requirements.txt` is up to date

### Phase 2: Create Services on Render (15 min)
- [ ] 5. Create PostgreSQL database (`ai-advisor-db`)
- [ ] 6. Save database credentials
- [ ] 7. Connect to database and run: `CREATE EXTENSION vector;`
- [ ] 8. Create environment variable group (`ai-advisor-secrets`)
- [ ] 9. Add all environment variables (see below)
- [ ] 10. Deploy backend service (`ai-advisor-backend`)
- [ ] 11. Wait for build to complete (~5 min)
- [ ] 12. Check backend health: `https://[backend-url]/health`
- [ ] 13. Deploy frontend service (`ai-advisor-frontend`)
- [ ] 14. Wait for build to complete (~5 min)

### Phase 3: Update OAuth URLs (10 min)
- [ ] 15. Google Cloud Console → Add redirect URI:
  ```
  https://ai-advisor-backend.onrender.com/auth/google/callback
  ```
- [ ] 16. Google Cloud Console → Add JavaScript origin:
  ```
  https://ai-advisor-frontend.onrender.com
  ```
- [ ] 17. Hubspot Developer → Add redirect URI:
  ```
  https://ai-advisor-frontend.onrender.com/hubspot/callback
  ```
- [ ] 18. Add test user to Google OAuth: `webshookeng@gmail.com`

### Phase 4: Test Deployment (10 min)
- [ ] 19. Open frontend URL in browser
- [ ] 20. Test Google OAuth login
- [ ] 21. Test Hubspot connection
- [ ] 22. Click Sync button
- [ ] 23. Send test query: "List all my contacts"
- [ ] 24. Verify tools are called
- [ ] 25. Check no errors in logs

---

## Environment Variables to Set

Copy these to Render Environment Group `ai-advisor-secrets`:

```bash
# Generate a new secret key:
# python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your-generated-secret-key

# From Google Cloud Console
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx

# From Hubspot Developer Portal
HUBSPOT_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
HUBSPOT_CLIENT_SECRET=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# From OpenAI Platform
OPENAI_API_KEY=sk-proj-xxxxx

# After frontend deployed, update this:
FRONTEND_URL=https://ai-advisor-frontend.onrender.com

# After frontend deployed, update this:
CORS_ORIGINS=https://ai-advisor-frontend.onrender.com,http://localhost:5173

# Optional - for custom LiteLLM endpoint
# OPENAI_API_BASE=https://api.openai.com/v1

# Database URL will be auto-added from PostgreSQL service
```

---

## Quick Commands

### Check Backend Health
```bash
curl https://ai-advisor-backend.onrender.com/health
```

### Connect to Database
```bash
psql "postgresql://ai_advisor:[password]@[host]/ai_advisor_db"
CREATE EXTENSION IF NOT EXISTS vector;
\dx
\q
```

### View Backend Logs
```
Render Dashboard → ai-advisor-backend → Logs
```

### Redeploy After Changes
```bash
git add .
git commit -m "Update"
git push origin main
# Auto-deploys if enabled
```

---

## Common Issues & Fixes

### Backend won't start
- Check logs for errors
- Verify all environment variables are set
- Check DATABASE_URL is connected

### Frontend shows "API Error"
- Verify VITE_API_URL is correct (no trailing slash)
- Check backend is running: curl health endpoint
- Check CORS_ORIGINS includes frontend URL

### OAuth redirects fail
- Verify redirect URIs exactly match (no trailing slashes)
- Check OAuth app is public or you're a test user
- Clear browser cookies and try again

### Database connection fails
- Verify vector extension installed: `CREATE EXTENSION vector;`
- Check DATABASE_URL environment variable
- Test connection with psql

### Slow first request
- Free tier spins down after 15 min inactivity
- First request takes ~30 seconds to wake up
- This is normal for free tier

---

## After Deployment

### Test with QUICK_TEST_GUIDE.md
- [ ] Create test data
- [ ] Run 10 quick tests
- [ ] Verify all pass

### Submit Challenge
- [ ] App URL: `https://ai-advisor-frontend.onrender.com`
- [ ] GitHub URL: `https://github.com/[username]/ai-financial-advisor`
- [ ] Test user added: `webshookeng@gmail.com`

---

## URLs to Save

**Frontend:** `https://ai-advisor-frontend.onrender.com`
**Backend:** `https://ai-advisor-backend.onrender.com`
**Database:** `postgresql://ai_advisor:[pass]@[host]/ai_advisor_db`
**GitHub:** `https://github.com/[username]/ai-financial-advisor`

---

## Support

- **Full Guide:** See RENDER_DEPLOYMENT_GUIDE.md
- **Render Docs:** https://render.com/docs
- **Render Community:** https://community.render.com

---

**Estimated Total Time:** 45-60 minutes
**Cost:** $0 (Free tier)

Good luck! 🚀

