# Webhook Implementation Guide

## Overview
Webhooks have been implemented for real-time syncing of Google Calendar and Hubspot. Gmail webhooks require additional Google Cloud Pub/Sub setup.

## What's Implemented

### 1. **Google Calendar Webhooks** ✅
- Real-time notifications when calendar events change
- Automatic re-sync when changes detected
- 7-day expiration with auto-renewal support

### 2. **Hubspot Webhooks** ✅
- Real-time notifications for contact changes
- Automatic CRM data sync
- Persistent subscriptions

### 3. **Gmail Webhooks** ⏳
- Requires Google Cloud Pub/Sub setup (more complex)
- Currently falls back to manual sync

## How It Works

### Setup Process:
1. User completes initial sync (manual)
2. Backend automatically sets up webhooks
3. When data changes externally:
   - Service sends webhook notification → Your backend
   - Backend fetches latest data
   - RAG database updates automatically
   - User sees fresh data immediately

### Database:
New `webhook_subscriptions` table tracks:
- Which user
- Which service (calendar/hubspot)
- Subscription IDs
- Expiration dates

## How to Use

### 1. Setup Webhooks (Automatic on First Sync)
The webhooks are automatically set up when syncs complete, but you can also manually trigger:

```bash
POST /integrations/webhooks/setup
```

This will:
- Set up Calendar webhook (if Google connected)
- Set up Hubspot webhook (if Hubspot connected)

### 2. Webhook Endpoints

**Calendar Webhook:**
```
POST /webhooks/calendar
```
- Receives Google Calendar push notifications
- Automatically syncs new/updated events

**Hubspot Webhook:**
```
POST /webhooks/hubspot
```
- Receives Hubspot change notifications
- Automatically syncs contacts

### 3. Monitoring
Check logs for:
```
logger.info(f"Calendar webhook received...")
logger.info(f"Syncing calendar for user {user.id} due to webhook")
```

## Configuration Required

### For Calendar Webhooks:
1. Your backend must be **publicly accessible** (webhooks can't reach localhost)
2. Update `.env`:
```bash
BACKEND_URL=https://your-domain.com
```

### For Hubspot Webhooks:
1. Configure webhook URL in Hubspot Developer portal
2. Backend must be publicly accessible

### For Production:
- Deploy backend to Render/Fly.io/Heroku
- Use actual domain (not localhost)
- Webhooks will work automatically!

## Testing Locally

**Problem:** Webhooks can't reach localhost

**Solutions:**
1. **Use ngrok** (quick test):
```bash
ngrok http 8000
# Update BACKEND_URL to ngrok URL
```

2. **Deploy to staging** (recommended):
- Deploy to Render/Fly.io
- Test with real URLs

## Next Steps

1. **Restart Backend** to apply changes:
```bash
cd /Users/vinaybadhan/Desktop/jump/backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **Test webhook setup:**
```bash
curl -X POST http://localhost:8000/integrations/webhooks/setup \
  -H "Authorization: Bearer YOUR_TOKEN"
```

3. **For your new calendar event:**
- Once webhooks are set up, new events will auto-sync!
- For now, manually trigger sync or deploy to test

## Files Changed:
- ✅ `app/models/webhook_subscription.py` - New model
- ✅ `app/services/webhook_manager.py` - Webhook management
- ✅ `app/api/webhooks.py` - Webhook handlers
- ✅ `app/api/integrations.py` - Setup endpoint
- ✅ `app/core/config.py` - Config updates
- ✅ `app/core/database.py` - DB initialization

## Limitations:
- Gmail webhooks need Pub/Sub (additional setup)
- Local testing requires ngrok or similar
- Calendar webhooks expire after 7 days (auto-renewal implemented)

---

**Your calendar event will auto-sync once you deploy to production!** 🎉

