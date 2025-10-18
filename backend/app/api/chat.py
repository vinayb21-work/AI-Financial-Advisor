from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.message import Message, Thread, MessageRole
from app.services.ai_agent import AIAgent

router = APIRouter()

class MessageCreate(BaseModel):
    content: str
    thread_id: Optional[str] = None
    context: Optional[str] = None

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    tool_calls: Optional[dict] = None
    tool_results: Optional[dict] = None
    created_at: str

class ThreadResponse(BaseModel):
    id: str
    title: str
    context: Optional[str]
    created_at: str
    updated_at: str
    messages: List[MessageResponse] = []

@router.post("/message")
async def send_message(
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message to the AI agent"""
    try:
        # Get or create thread
        if message_data.thread_id:
            result = await db.execute(
                select(Thread).where(
                    Thread.id == message_data.thread_id,
                    Thread.user_id == current_user.id
                )
            )
            thread = result.scalar_one_or_none()
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")
        else:
            # Create new thread
            thread = Thread(
                user_id=current_user.id,
                context=message_data.context
            )
            db.add(thread)
            await db.commit()
            await db.refresh(thread)
        
        # Save user message
        user_message = Message(
            thread_id=thread.id,
            role=MessageRole.USER,
            content=message_data.content
        )
        db.add(user_message)
        await db.commit()
        
        # Get AI response
        ai_agent = AIAgent(db, current_user)
        response = await ai_agent.process_message(
            message_data.content,
            thread.id,
            message_data.context
        )
        
        # Save assistant message
        assistant_message = Message(
            thread_id=thread.id,
            role=MessageRole.ASSISTANT,
            content=response['content'],
            tool_calls=response.get('tool_calls'),
            tool_results=response.get('tool_results')
        )
        db.add(assistant_message)
        await db.commit()
        
        # Update thread title if it's the first message
        if not thread.title or thread.title == "New conversation":
            thread.title = message_data.content[:50] + ("..." if len(message_data.content) > 50 else "")
            await db.commit()
        
        return {
            "thread_id": str(thread.id),
            "user_message": {
                "id": str(user_message.id),
                "role": user_message.role.value,
                "content": user_message.content,
                "created_at": user_message.created_at.isoformat()
            },
            "assistant_message": {
                "id": str(assistant_message.id),
                "role": assistant_message.role.value,
                "content": assistant_message.content,
                "tool_calls": assistant_message.tool_calls,
                "tool_results": assistant_message.tool_results,
                "created_at": assistant_message.created_at.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/threads")
async def get_threads(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all threads for the current user"""
    result = await db.execute(
        select(Thread)
        .where(Thread.user_id == current_user.id)
        .order_by(desc(Thread.updated_at))
    )
    threads = result.scalars().all()
    
    return [
        {
            "id": str(thread.id),
            "title": thread.title,
            "context": thread.context,
            "created_at": thread.created_at.isoformat(),
            "updated_at": thread.updated_at.isoformat()
        }
        for thread in threads
    ]

@router.get("/threads/{thread_id}")
async def get_thread(
    thread_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific thread with all messages"""
    result = await db.execute(
        select(Thread)
        .where(Thread.id == thread_id, Thread.user_id == current_user.id)
    )
    thread = result.scalar_one_or_none()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Get messages
    messages_result = await db.execute(
        select(Message)
        .where(Message.thread_id == thread_id)
        .order_by(Message.created_at)
    )
    messages = messages_result.scalars().all()
    
    return {
        "id": str(thread.id),
        "title": thread.title,
        "context": thread.context,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat(),
        "messages": [
            {
                "id": str(msg.id),
                "role": msg.role.value,
                "content": msg.content,
                "tool_calls": msg.tool_calls,
                "tool_results": msg.tool_results,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }

@router.delete("/threads/{thread_id}")
async def delete_thread(
    thread_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a thread"""
    result = await db.execute(
        select(Thread)
        .where(Thread.id == thread_id, Thread.user_id == current_user.id)
    )
    thread = result.scalar_one_or_none()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    await db.delete(thread)
    await db.commit()
    
    return {"message": "Thread deleted successfully"}

