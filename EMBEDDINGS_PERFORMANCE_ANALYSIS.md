# Embeddings Performance Analysis

## 🔍 Current Implementation Review

### What's Currently Happening:
```python
# In rag_service.py
async def import_emails(self, emails: List[Dict[str, Any]]):
    for email in emails:
        embedding = await self.get_embedding(content)  # ❌ Individual API call
        # ... save to DB
        await self.db.commit()  # ❌ Individual commit
```

---

## ⚠️ Performance Issues Identified

### 1. **Individual API Calls** (MAJOR ISSUE)
**Problem**: Each document makes a separate embedding API call
- 100 emails = 100 API requests
- High latency (100ms per request = 10+ seconds total)
- Rate limit concerns
- Expensive (more API calls = more cost)

**Impact**: 🔴 HIGH - This is the biggest bottleneck

### 2. **Individual Database Commits** (MAJOR ISSUE)
**Problem**: Committing after each document
- 100 documents = 100 database transactions
- Very slow for bulk imports
- Database connection overhead

**Impact**: 🔴 HIGH - Significantly slows down sync

### 3. **No Embedding Caching** (MEDIUM ISSUE)
**Problem**: Re-generates embeddings even if content hasn't changed
- Wastes API calls and cost
- Slows down re-syncs

**Impact**: 🟡 MEDIUM - Affects re-syncs

### 4. **Model Choice** (OPTIMAL)
**Current**: `text-embedding-3-small` (1536 dimensions)
✅ Good choice! It's:
- Fast
- Cost-effective ($0.02 per 1M tokens)
- Good quality for this use case
- Smaller storage footprint

**Impact**: ✅ No issue - Already optimized

### 5. **Content Formatting** (MINOR ISSUE)
**Problem**: Includes formatting/whitespace that adds tokens
```python
content = f"""
From: {email.get('from', 'Unknown')}  # Extra whitespace/newlines
To: {email.get('to', 'Unknown')}
...
""".strip()
```

**Impact**: 🟢 LOW - Minor cost increase

---

## 🚀 Recommended Improvements

### Priority 1: Batch Embedding API Calls (HIGH IMPACT)

**Current:**
```python
for email in emails:
    embedding = await self.get_embedding(content)  # 1 call per email
```

**Improved:**
```python
async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
    """Get embeddings for multiple texts in one API call"""
    response = await self.client.embeddings.create(
        model="text-embedding-3-small",
        input=texts  # Up to 2048 texts per call!
    )
    return [item.embedding for item in response.data]

# Usage
contents = [format_email_content(email) for email in emails]
embeddings = await self.get_embeddings_batch(contents)
```

**Benefits:**
- ✅ 100 emails: 100 requests → 1 request
- ✅ ~10 seconds → ~0.5 seconds
- ✅ Lower cost (fewer request overhead)

---

### Priority 2: Batch Database Operations (HIGH IMPACT)

**Current:**
```python
for email in emails:
    # process email
    await self.db.commit()  # Commit each time
```

**Improved:**
```python
for email in emails:
    # process email
    # Don't commit yet

# Commit once at the end
await self.db.commit()
```

**Benefits:**
- ✅ 100 emails: 100 transactions → 1 transaction
- ✅ ~5 seconds → ~0.5 seconds
- ✅ Better database performance

---

### Priority 3: Add Content Hash Caching (MEDIUM IMPACT)

**Add to Document model:**
```python
content_hash = Column(String)  # SHA256 of content
```

**Logic:**
```python
import hashlib

content_hash = hashlib.sha256(content.encode()).hexdigest()

# Check if content changed
if existing_doc and existing_doc.content_hash == content_hash:
    # Content unchanged, skip embedding generation
    continue
else:
    # Generate new embedding
    embedding = await self.get_embedding(content)
    doc.content_hash = content_hash
```

**Benefits:**
- ✅ Skip API calls for unchanged content
- ✅ Faster re-syncs
- ✅ Cost savings

---

### Priority 4: Optimize Content Format (LOW IMPACT)

**Current:**
```python
content = f"""
From: {email.get('from', 'Unknown')}
To: {email.get('to', 'Unknown')}
Subject: {email.get('subject', 'No subject')}
Date: {email.get('date', '')}

{email.get('body', '')}
""".strip()
```

**Improved:**
```python
content = (
    f"From: {email.get('from', 'Unknown')} "
    f"To: {email.get('to', 'Unknown')} "
    f"Subject: {email.get('subject', 'No subject')} "
    f"Date: {email.get('date', '')} "
    f"Body: {email.get('body', '')}"
).strip()
```

**Benefits:**
- ✅ Fewer tokens = lower cost
- ✅ Slightly faster processing

---

## 📊 Performance Comparison

### Current Implementation:
```
100 emails:
- API calls: 100 × 100ms = 10 seconds
- DB commits: 100 × 50ms = 5 seconds
- Total: ~15 seconds
```

### With Improvements:
```
100 emails:
- API calls: 1 × 500ms = 0.5 seconds (batch)
- DB commits: 1 × 100ms = 0.1 seconds
- Total: ~0.6 seconds

🚀 25x faster!
```

---

## 💰 Cost Comparison

### Current:
```
100 emails × 500 tokens each = 50,000 tokens
Cost: $0.001 (minimal, but inefficient requests)
```

### Optimized:
```
Same 50,000 tokens, but:
- Fewer HTTP requests (lower overhead)
- Cached embeddings on re-sync (50-90% savings)
- Optimized content (10-15% token reduction)
```

---

## 🛠️ Implementation Priority

### MUST DO (Before Production):
1. ✅ Batch embedding API calls
2. ✅ Batch database commits

### SHOULD DO (For Better UX):
3. ⚠️ Add content hash caching

### NICE TO HAVE (Marginal gains):
4. 💡 Optimize content formatting

---

## 🔧 Quick Win Implementation

Here's a drop-in replacement for the most critical fix:

```python
async def import_emails_optimized(self, emails: List[Dict[str, Any]]):
    """Optimized email import with batching"""
    if not emails:
        return
    
    # Step 1: Prepare all content
    email_data = []
    for email in emails:
        content = self._format_email_content(email)
        email_data.append({
            'email': email,
            'content': content
        })
    
    # Step 2: Get all embeddings in ONE API call
    contents = [item['content'] for item in email_data]
    embeddings = await self.get_embeddings_batch(contents)
    
    # Step 3: Process all documents (no commits yet)
    for item, embedding in zip(email_data, embeddings):
        email = item['email']
        content = item['content']
        
        # Check if exists
        result = await self.db.execute(
            select(Document).where(
                Document.user_id == self.user.id,
                Document.source == "gmail",
                Document.source_id == email['id']
            )
        )
        existing_doc = result.scalar_one_or_none()
        
        if existing_doc:
            existing_doc.content = content
            existing_doc.embedding = embedding
            existing_doc.title = email.get('subject', 'No subject')
            existing_doc.doc_metadata = json.dumps(email)
        else:
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
    
    # Step 4: Single commit for all documents
    try:
        await self.db.commit()
        logger.info(f"Successfully imported {len(emails)} emails")
    except Exception as e:
        await self.db.rollback()
        logger.error(f"Error importing emails: {e}")
        raise
```

---

## ⚡ Expected Results

### For typical sync (100 documents):
- **Before**: ~15 seconds
- **After**: ~0.6 seconds
- **Improvement**: 25x faster ⚡

### For first-time sync (1000 emails):
- **Before**: ~150 seconds (2.5 minutes)
- **After**: ~6 seconds
- **Improvement**: 25x faster ⚡

---

## ✅ Conclusion

**Current Status**: ⚠️ Functional but not optimized
**Main Issues**: Individual API calls and DB commits
**Quick Fix**: Batch operations (2 code changes)
**Impact**: 25x performance improvement

**Recommendation**: Implement batching before deployment for better user experience during initial sync!

