# 🧪 Your Test Queries - Copy & Paste These

## Test 1: RAG Search - Baseball (30 seconds)
```
Who mentioned baseball?
```
**Expected:** Should find both the email from John Doe AND the Hubspot note mentioning Tommy's baseball team.

---

## Test 2: RAG Search - Stock Reasoning (30 seconds)
```
Why does someone want to sell AAPL stock?
```
**Expected:** Should explain John wants to sell AAPL due to market uncertainty and wanting to lock in gains before earnings.

---

## Test 3: Calendar Lookup (30 seconds)
```
When is my meeting with John Doe?
```
**Expected:** Should show today's meeting time. Look for tool call: `list_calendar_events`

---

## Test 4: List Contacts (30 seconds)
```
List all my Hubspot clients
```
**Expected:** Should show at least John Doe. Look for tool call: `list_all_hubspot_contacts`

---

## Test 5: Contact Notes (30 seconds)
```
Show me notes for John Doe
```
**Expected:** Should return the note about baseball and portfolio. Look for tool call: `list_contact_notes`

---

## Test 6: Company Revenue (30 seconds)
```
What's the revenue for Acme Corporation?
```
**Expected:** Should return $2,000,000. Look for tool call: `get_company_details`

---

## Test 7: Schedule Meeting (1 minute)
```
Schedule a meeting with John Doe tomorrow at 2pm for 1 hour
```
**Expected Tools (watch for these):**
1. 🔧 search_hubspot_contacts
2. 🔧 get_calendar_availability
3. 🔧 create_calendar_event
4. 🔧 send_email
5. 🔧 add_hubspot_note

---

## Test 8: Create Contact (1 minute)
```
Create a Hubspot contact for test.user@example.com named Test User at Example Company
```
**Expected:** Contact created. Look for tool call: `create_hubspot_contact`

---

## Test 9: Activity Timeline (30 seconds)
```
Show me all activity for John Doe
```
**Expected:** Should show contact info, notes, and any other activity. Look for tool call: `get_contact_activity_timeline`

---

## Test 10: Ongoing Instruction (30 seconds)
```
Remember this: When someone new emails me who is not in Hubspot, create a contact for them with a note about the email
```
**Expected:** Instruction saved. Look for tool call: `save_ongoing_instruction`

---

## 🎯 Success Criteria

### ✅ PASS if:
- All queries return relevant answers
- Tool calls visible in the UI (🔧 icons)
- No error messages in responses
- Responses come back in < 5 seconds

### ❌ FAIL if:
- "No results found" when data exists
- Tools not called when expected
- Error messages in responses
- Backend errors in terminal

---

## 📊 Quick Results Tracker

| Test | Query | Pass/Fail | Notes |
|------|-------|-----------|-------|
| 1 | Baseball mention | ⬜ | |
| 2 | AAPL stock reason | ⬜ | |
| 3 | Meeting time | ⬜ | |
| 4 | List contacts | ⬜ | |
| 5 | Contact notes | ⬜ | |
| 6 | Company revenue | ⬜ | |
| 7 | Schedule meeting | ⬜ | |
| 8 | Create contact | ⬜ | |
| 9 | Activity timeline | ⬜ | |
| 10 | Ongoing instruction | ⬜ | |

---

## 🐛 Troubleshooting

**Issue: "No results found"**
→ Check backend logs: `tail -f backend/logs/*.log`
→ Re-sync data: Click sync button again
→ Verify data was created in Gmail/Calendar/Hubspot

**Issue: Tool not called**
→ Check backend logs for errors
→ Verify OAuth tokens valid
→ Check OpenAI API key

**Issue: Slow responses**
→ Check OpenAI API status
→ Check database connection
→ Restart backend if needed

---

## 🚀 After All Tests Pass

1. ✅ Check all boxes in tracker above
2. ✅ Test a few edge cases from COMPREHENSIVE_TEST_PLAN.md
3. ✅ Test proactive agent (wait 5 min after sending email, or click sync)
4. ✅ Ready for production/submission!

---

**Estimated Time:** 10-15 minutes
**Last Updated:** Ready to test now!

