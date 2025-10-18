from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import requests
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.user import User
from app.api.dependencies import get_current_user

router = APIRouter()

# Google OAuth scopes
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.freebusy',
    'openid'
]

@router.get("/google/login")
async def google_login():
    """Initiate Google OAuth flow"""
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
            }
        },
        scopes=GOOGLE_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    return {"authorization_url": authorization_url, "state": state}

@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Handle Google OAuth callback"""
    try:
        # Exchange code for tokens
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
                }
            },
            scopes=GOOGLE_SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Get user info
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        
        # Check if user exists
        result = await db.execute(
            select(User).where(User.email == user_info['email'])
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Create new user
            user = User(
                email=user_info['email'],
                name=user_info.get('name'),
                picture=user_info.get('picture')
            )
            db.add(user)
        
        # Update tokens
        user.google_access_token = credentials.token
        user.google_refresh_token = credentials.refresh_token
        user.google_token_expiry = credentials.expiry
        
        await db.commit()
        await db.refresh(user)
        
        # Create JWT token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Redirect to frontend with token
        redirect_url = f"{settings.FRONTEND_URL}/auth/callback?token={access_token}"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/hubspot/connect")
async def hubspot_connect():
    """Initiate Hubspot OAuth flow"""
    auth_url = (
        f"https://app.hubspot.com/oauth/authorize"
        f"?client_id={settings.HUBSPOT_CLIENT_ID}"
        f"&redirect_uri={settings.HUBSPOT_REDIRECT_URI}"
        f"&scope=crm.objects.contacts.read%20crm.objects.contacts.write%20crm.schemas.contacts.read%20timeline"
    )
    
    return {"authorization_url": auth_url}

@router.post("/hubspot/disconnect")
async def hubspot_disconnect(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Disconnect Hubspot account"""
    current_user.hubspot_access_token = None
    current_user.hubspot_refresh_token = None
    current_user.hubspot_token_expiry = None
    current_user.hubspot_connected = False
    current_user.hubspot_synced = False
    
    await db.commit()
    
    return {"message": "Hubspot disconnected successfully"}

@router.get("/hubspot/callback")
async def hubspot_callback(code: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Hubspot OAuth callback"""
    try:
        # Exchange code for access token
        token_url = "https://api.hubapi.com/oauth/v1/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.HUBSPOT_CLIENT_ID,
            "client_secret": settings.HUBSPOT_CLIENT_SECRET,
            "redirect_uri": settings.HUBSPOT_REDIRECT_URI,
            "code": code
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        
        # Get user from request (you'd extract this from JWT in real implementation)
        # For now, we'll get the most recent user (this should be improved)
        result = await db.execute(select(User).order_by(User.created_at.desc()).limit(1))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update user with Hubspot tokens
        user.hubspot_access_token = token_data['access_token']
        user.hubspot_refresh_token = token_data['refresh_token']
        user.hubspot_token_expiry = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
        user.hubspot_connected = True
        
        await db.commit()
        
        # Redirect to frontend
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/?hubspot=connected")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me")
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    """Get current user info"""
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
    from app.core.security import decode_access_token
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "hubspot_connected": user.hubspot_connected,
        "gmail_synced": user.gmail_synced,
        "calendar_synced": user.calendar_synced,
        "hubspot_synced": user.hubspot_synced
    }

