# Context Dropdown - How It Works

## 📍 Overview

The context dropdown in the chat interface allows users to specify the focus area for their query. It's located in the chat input area, showing options like:
- `all meetings`
- `recent emails`
- `contacts`
- `upcoming events`
- `all data`

---

## 🔄 Current Implementation

### Frontend (ChatInput.tsx)

```typescript
const contexts = [
  'all meetings',
  'recent emails',
  'contacts',
  'upcoming events',
  'all data',
]

// Context is stored in state and passed to API
<button onClick={() => setShowContextMenu(!showContextMenu)}>
  {context}  {/* Shows current selection */}
</button>
```

### Flow:
1. **User selects context** → `onContextChange(ctx)` updates state in `Chat.tsx`
2. **User sends message** → Context is included in API request
3. **Backend receives** → `message_data.context` in `/chat/message` endpoint
4. **Thread stores context** → Saved to `Thread.context` field in database
5. **AI receives context** → Passed to `ai_agent.process_message()`

---

## 🤖 How Context is Used by AI

### In `ai_agent.py`:

```python
def _get_system_prompt(self, rag_context: str, instructions: str, context: Optional[str] = None):
    # ... base prompt ...
    
    if context:
        prompt += f"\nThe user has set the context to: {context}\n"
    
    # ... rest of prompt ...
```

### What Happens:

**Context is passed to the system prompt** as informational text:
```
The user has set the context to: all meetings
```

---

## ⚠️ Current Issues & Limitations

### 1. **Context is NOT Actively Filtering RAG Search** 🔴

**Current Behavior:**
```python
# In ai_agent.py, line 41
rag_results = await self.rag_service.search(message, limit=5)
# ☝️ Searches ALL documents, ignoring context setting
```

**What's Missing:**
- Context doesn't filter RAG results by source type
- "all meetings" still searches emails, contacts, etc.
- "recent emails" still includes old emails and calendar events

### 2. **Context is Passive, Not Active** 🟡

**Current:**
- Context is just a hint to the AI in the system prompt
- AI might consider it, might ignore it
- No guarantee it affects behavior

**Example:**
```
User: "What meetings do I have?"
Context: "recent emails"

Current: AI might still answer about meetings (ignoring context)
Ideal: AI should say "You've set context to emails, but you're asking about meetings"
```

### 3. **No Visual Feedback** 🟢

**Current:**
- Context shown in ChatHeader: "Context set to {context}"
- ✅ This is good!

---

## 🚀 Recommended Improvements

### Option 1: Active RAG Filtering (BEST)

Modify `rag_service.py` to accept context parameter:

```python
async def search(
    self, 
    query: str, 
    limit: int = 5,
    context: Optional[str] = None  # Add this
) -> List[Dict[str, Any]]:
    """Search with optional context filtering"""
    
    # Build WHERE clause based on context
    filter_clause = "user_id = :user_id"
    
    if context == "all meetings":
        filter_clause += " AND (source = 'calendar' OR document_type = 'event')"
    elif context == "recent emails":
        filter_clause += " AND source = 'gmail' AND created_at > NOW() - INTERVAL '30 days'"
    elif context == "contacts":
        filter_clause += " AND (source = 'hubspot_contact' OR document_type = 'contact')"
    elif context == "upcoming events":
        filter_clause += " AND source = 'calendar' AND created_at > NOW()"
    # 'all data' = no additional filter
    
    sql = text(f"""
        SELECT ... 
        FROM documents
        WHERE {filter_clause}
        ORDER BY embedding <=> CAST(:query_embedding AS vector)
        LIMIT :result_limit
    """)
```

**Benefits:**
- ✅ Context directly filters data sources
- ✅ Faster queries (fewer documents to search)
- ✅ More relevant results
- ✅ Predictable behavior

---

### Option 2: Enhanced System Prompt (QUICK FIX)

Make the system prompt more directive:

```python
if context:
    if context == "all meetings":
        prompt += "\n🎯 CONTEXT: The user wants to focus on MEETINGS and CALENDAR EVENTS only. Do not mention emails or contacts unless directly relevant.\n"
    elif context == "recent emails":
        prompt += "\n🎯 CONTEXT: The user wants to focus on RECENT EMAILS only. Prioritize email information over calendar or contacts.\n"
    # ... etc
```

**Benefits:**
- ✅ Quick to implement
- ✅ No RAG changes needed
- ⚠️ Still relies on AI to follow instructions

---

### Option 3: Hybrid Approach (RECOMMENDED)

1. **RAG Filtering** - Apply source filters in database query
2. **Enhanced Prompt** - Reinforce context in system prompt
3. **Smart Defaults** - Auto-detect context from query if not set

```python
# Auto-detect context from query
def detect_context(query: str) -> str:
    query_lower = query.lower()
    if any(word in query_lower for word in ["meeting", "calendar", "schedule", "appointment"]):
        return "all meetings"
    elif any(word in query_lower for word in ["email", "inbox", "message"]):
        return "recent emails"
    elif any(word in query_lower for word in ["contact", "client", "person"]):
        return "contacts"
    return "all data"
```

---

## 📊 Context Mapping to Data Sources

| Context Selection | Should Search              | Database Filter                    |
|-------------------|----------------------------|------------------------------------|
| `all meetings`    | Calendar events only       | `source = 'calendar'`              |
| `recent emails`   | Emails from last 30 days   | `source = 'gmail' AND recent`      |
| `contacts`        | Hubspot contacts           | `source = 'hubspot_contact'`       |
| `upcoming events` | Future calendar events     | `source = 'calendar' AND future`   |
| `all data`        | Everything                 | No filter                          |

---

## 🔧 Quick Implementation

### Minimal Change (10 minutes):

**In `ai_agent.py`, line 41:**

```python
# Before:
rag_results = await self.rag_service.search(message, limit=5)

# After:
rag_results = await self.rag_service.search(
    message, 
    limit=5,
    context=context  # Pass context to RAG
)
```

**In `rag_service.py`, line 197:**

```python
# Before:
async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:

# After:
async def search(
    self, 
    query: str, 
    limit: int = 5,
    context: Optional[str] = None
) -> List[Dict[str, Any]]:
    # ... existing code ...
    
    # Add context-based filtering
    context_filter = ""
    if context == "all meetings":
        context_filter = " AND source = 'calendar'"
    elif context == "recent emails":
        context_filter = " AND source = 'gmail'"
    elif context == "contacts":
        context_filter = " AND source = 'hubspot_contact'"
    elif context == "upcoming events":
        context_filter = " AND source = 'calendar'"
    
    sql = text(f"""
        SELECT 
            id, source, source_id, document_type, content, title, doc_metadata,
            embedding <=> CAST(:query_embedding AS vector) AS distance
        FROM documents
        WHERE user_id = :user_id{context_filter}
        ORDER BY embedding <=> CAST(:query_embedding AS vector)
        LIMIT :result_limit
    """).bindparams(...)
```

---

## 🎯 Current State Summary

| Feature                        | Status | Impact  |
|--------------------------------|--------|---------|
| Context dropdown UI            | ✅ Done | Good    |
| Context stored in thread       | ✅ Done | Good    |
| Context in system prompt       | ✅ Done | Minimal |
| Context filters RAG search     | ❌ Missing | High    |
| Context affects AI behavior    | ⚠️ Weak | Medium  |

**Conclusion**: The context dropdown **exists and is plumbed through**, but it's **not effectively used** by the RAG search. It's currently just a suggestion to the AI, not an active filter.

---

## 💡 Recommendation

**For production deployment**, implement **Option 1 (Active RAG Filtering)** because:

1. ✅ Makes context dropdown actually functional
2. ✅ Improves search relevance
3. ✅ Faster queries (fewer documents)
4. ✅ Better UX (predictable behavior)
5. ✅ Only ~30 lines of code

**Estimated time**: 20-30 minutes

Would you like me to implement this improvement?

