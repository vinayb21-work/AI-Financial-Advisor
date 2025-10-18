from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional
import json
import logging

from app.core.config import settings
from app.models.user import User
from app.models.document import Document

logger = logging.getLogger(__name__)

class RAGService:
    """RAG (Retrieval Augmented Generation) service using pgvector"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        # Initialize OpenAI client with optional custom base URL (for LiteLLM, etc.)
        client_kwargs = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_API_BASE:
            client_kwargs["base_url"] = settings.OPENAI_API_BASE
        self.client = AsyncOpenAI(**client_kwargs)
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI"""
        try:
            response = await self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            raise
    
    async def import_emails(self, emails: List[Dict[str, Any]]):
        """Import emails into vector database"""
        for email in emails:
            try:
                # Create document content
                content = f"""
From: {email.get('from', 'Unknown')}
To: {email.get('to', 'Unknown')}
Subject: {email.get('subject', 'No subject')}
Date: {email.get('date', '')}

{email.get('body', '')}
                """.strip()
                
                # Get embedding
                embedding = await self.get_embedding(content)
                
                # Check if document already exists
                result = await self.db.execute(
                    select(Document).where(
                        Document.user_id == self.user.id,
                        Document.source == "gmail",
                        Document.source_id == email['id']
                    )
                )
                existing_doc = result.scalar_one_or_none()
                
                if existing_doc:
                    # Update existing document
                    existing_doc.content = content
                    existing_doc.embedding = embedding
                    existing_doc.title = email.get('subject', 'No subject')
                    existing_doc.doc_metadata = json.dumps(email)
                else:
                    # Create new document
                    document = Document(
                        user_id=self.user.id,
                        source="gmail",
                        source_id=email['id'],
                        document_type="email",
                        content=content,
                        title=email.get('subject', 'No subject'),
                        embedding=embedding,
                        doc_metadata=json.dumps(email)
                    )
                    self.db.add(document)
                
                await self.db.commit()
                
            except Exception as e:
                logger.error(f"Error importing email {email.get('id')}: {e}")
                continue
    
    async def import_calendar_events(self, events: List[Dict[str, Any]]):
        """Import calendar events into vector database"""
        logger.info(f"Importing {len(events)} calendar events")
        for event in events:
            try:
                # Create document content
                attendees = ", ".join([a.get('email', '') for a in event.get('attendees', [])])
                content = f"""
Event: {event.get('summary', 'Untitled')}
Date: {event.get('start', '')} to {event.get('end', '')}
Attendees: {attendees}
Description: {event.get('description', '')}
                """.strip()
                
                logger.info(f"Importing event: {event.get('summary')} on {event.get('start')}")
                
                # Get embedding
                embedding = await self.get_embedding(content)
                
                # Check if document already exists
                result = await self.db.execute(
                    select(Document).where(
                        Document.user_id == self.user.id,
                        Document.source == "calendar",
                        Document.source_id == event['id']
                    )
                )
                existing_doc = result.scalar_one_or_none()
                
                if existing_doc:
                    existing_doc.content = content
                    existing_doc.embedding = embedding
                    existing_doc.title = event.get('summary', 'Untitled')
                    existing_doc.doc_metadata = json.dumps(event)
                else:
                    document = Document(
                        user_id=self.user.id,
                        source="calendar",
                        source_id=event['id'],
                        document_type="event",
                        content=content,
                        title=event.get('summary', 'Untitled'),
                        embedding=embedding,
                        doc_metadata=json.dumps(event)
                    )
                    self.db.add(document)
                
                await self.db.commit()
                
            except Exception as e:
                logger.error(f"Error importing event {event.get('id')}: {e}")
                continue
    
    async def import_hubspot_contacts(self, contacts: List[Dict[str, Any]]):
        """Import Hubspot contacts into vector database"""
        for contact in contacts:
            try:
                # Create document content
                properties = contact.get('properties', {})
                content = f"""
Contact: {properties.get('firstname', '')} {properties.get('lastname', '')}
Email: {properties.get('email', '')}
Company: {properties.get('company', '')}
Phone: {properties.get('phone', '')}
Notes: {properties.get('notes', '')}
                """.strip()
                
                # Get embedding
                embedding = await self.get_embedding(content)
                
                # Check if document already exists
                result = await self.db.execute(
                    select(Document).where(
                        Document.user_id == self.user.id,
                        Document.source == "hubspot_contact",
                        Document.source_id == contact['id']
                    )
                )
                existing_doc = result.scalar_one_or_none()
                
                name = f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip()
                
                if existing_doc:
                    existing_doc.content = content
                    existing_doc.embedding = embedding
                    existing_doc.title = name
                    existing_doc.doc_metadata = json.dumps(contact)
                else:
                    document = Document(
                        user_id=self.user.id,
                        source="hubspot_contact",
                        source_id=contact['id'],
                        document_type="contact",
                        content=content,
                        title=name,
                        embedding=embedding,
                        doc_metadata=json.dumps(contact)
                    )
                    self.db.add(document)
                
                await self.db.commit()
                
            except Exception as e:
                logger.error(f"Error importing contact {contact.get('id')}: {e}")
                continue
    
    async def search(self, query: str, limit: int = 5, context: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for relevant documents using vector similarity with optional context filtering"""
        try:
            logger.info(f"Searching RAG for query: {query} (context: {context})")
            
            # Get query embedding
            query_embedding = await self.get_embedding(query)
            
            # Convert embedding to string for pgvector
            embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            # Build context-based filter
            context_filter = ""
            if context == "all meetings":
                context_filter = " AND source = 'calendar'"
                logger.info("Filtering for calendar events only")
            elif context == "recent emails":
                # Filter for emails from last 30 days
                context_filter = " AND source = 'gmail' AND created_at > NOW() - INTERVAL '30 days'"
                logger.info("Filtering for recent emails only")
            elif context == "contacts":
                context_filter = " AND source = 'hubspot_contact'"
                logger.info("Filtering for Hubspot contacts only")
            elif context == "upcoming events":
                # Filter for future calendar events
                context_filter = " AND source = 'calendar' AND created_at > NOW() - INTERVAL '1 day'"
                logger.info("Filtering for upcoming events only")
            # 'all data' or None = no filter
            
            # Perform vector similarity search
            # Use SQLAlchemy text() with bindparams for proper parameter handling
            sql = text(f"""
                SELECT 
                    id, 
                    source, 
                    source_id, 
                    document_type, 
                    content, 
                    title, 
                    doc_metadata,
                    embedding <=> CAST(:query_embedding AS vector) AS distance
                FROM documents
                WHERE user_id = :user_id{context_filter}
                ORDER BY embedding <=> CAST(:query_embedding AS vector)
                LIMIT :result_limit
            """).bindparams(
                query_embedding=embedding_str,
                user_id=self.user.id,
                result_limit=limit
            )
            
            result = await self.db.execute(sql)
            rows = result.fetchall()
            
            results = [
                {
                    "id": str(row[0]),
                    "source": row[1],
                    "source_id": row[2],
                    "document_type": row[3],
                    "content": row[4],
                    "title": row[5],
                    "doc_metadata": json.loads(row[6]) if row[6] else {},
                    "distance": float(row[7])
                }
                for row in rows
            ]
            
            logger.info(f"Found {len(results)} documents. Top result: {results[0]['title'] if results else 'None'}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []

