# ⚡ Quick Test Guide - 10 Minute Validation

## Setup (2 minutes)

1. **Create Minimal Test Data:**

### Gmail - Send yourself 2 emails:

**Email 1:**
```
Subject: Baseball Talk
From: test@example.com

My son plays baseball! Also, I want to sell my AAPL stock.
```

**Email 2:**
```
Subject: Meeting Time?
From: john@example.com

When is our meeting scheduled?
```

### Calendar - Create 1 event:
```
Title: Client Meeting
Today + 2 hours
Attendees: john@example.com
```

### Hubspot - Create 1 contact:
```
Name: John Doe
Email: john@example.com
Company: Test Corp

Add Note: "Client's son plays baseball. Interested in portfolio review."
```

### Hubspot - Create 1 company:
```
Name: Test Corp
Annual Revenue: $2,000,000
Industry: Technology
```

2. **Sync Everything:**
   - Click "Sync" button
   - Wait for success messages

---

## 10 Critical Tests (8 minutes)

### ✅ Test 1: RAG - Email Search (30s)
```
Query: "Who mentioned baseball?"
Expected: Finds both email and Hubspot note
```

### ✅ Test 2: RAG - Stock Query (30s)
```
Query: "Why does someone want to sell AAPL?"
Expected: Returns email content about stock sale
```

### ✅ Test 3: Calendar Lookup (30s)
```
Query: "When is my meeting with John?"
Expected: Returns today's meeting time
Tool: list_calendar_events
```

### ✅ Test 4: List Contacts (30s)
```
Query: "List all my Hubspot clients"
Expected: Shows John Doe
Tool: list_all_hubspot_contacts
```

### ✅ Test 5: Contact Notes (30s)
```
Query: "Show me notes for John Doe"
Expected: Returns Hubspot note about baseball
Tool: list_contact_notes
```

### ✅ Test 6: Company Revenue (30s)
```
Query: "What's the revenue for Test Corp?"
Expected: Returns $2,000,000
Tool: get_company_details
```

### ✅ Test 7: Multi-Tool Schedule (1min)
```
Query: "Schedule a meeting with John tomorrow at 2pm"
Expected Tools:
1. search_hubspot_contacts
2. get_calendar_availability
3. create_calendar_event
4. send_email
5. add_hubspot_note
```

### ✅ Test 8: Create Contact (1min)
```
Query: "Create a Hubspot contact for test2@example.com named Test User"
Expected: Creates contact in Hubspot
Tool: create_hubspot_contact
```

### ✅ Test 9: Activity Timeline (1min)
```
Query: "Show me all activity for John Doe"
Expected: Returns notes, calls, meetings, emails
Tool: get_contact_activity_timeline
```

### ✅ Test 10: Ongoing Instruction (30s)
```
Query: "Remember: When someone new emails me, create a Hubspot contact"
Expected: Saves instruction
Tool: save_ongoing_instruction
```

---

## Pass/Fail Criteria

### ✅ PASS if:
- All 10 queries return relevant answers
- Tools are called correctly (visible in UI)
- No error messages
- Response time < 5 seconds per query

### ❌ FAIL if:
- Any query returns "no results" inappropriately
- Tools not called when expected
- Errors in backend logs
- Response time > 10 seconds

---

## Quick Verification Commands

```bash
# Check backend health
curl http://localhost:8000/health

# Check RAG document count
# Should see: emails, calendar, contacts, notes, companies
psql -U ai_advisor -d ai_advisor_db -c "SELECT source, COUNT(*) FROM documents GROUP BY source;"

# Check backend logs for errors
tail -f backend/logs/*.log | grep ERROR
```

---

## Troubleshooting

**"No results"** → Click Sync again, check logs for import count

**"Tool failed"** → Check OAuth tokens in backend logs

**Slow responses** → Check OpenAI API key validity

---

## Success = All ✅ Checked!

- [ ] Test 1: Baseball search
- [ ] Test 2: AAPL stock query
- [ ] Test 3: Meeting lookup
- [ ] Test 4: List contacts
- [ ] Test 5: Contact notes
- [ ] Test 6: Company revenue
- [ ] Test 7: Schedule meeting
- [ ] Test 8: Create contact
- [ ] Test 9: Activity timeline
- [ ] Test 10: Ongoing instruction

**Time:** ~10 minutes | **Confidence:** Production-ready if all pass

