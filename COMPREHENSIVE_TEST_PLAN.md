# 🧪 Comprehensive Test Plan - AI Financial Advisor

## Table of Contents
1. [Initial Setup](#initial-setup)
2. [Data Creation](#data-creation)
3. [Test Scenarios](#test-scenarios)
4. [Expected Results](#expected-results)

---

## Initial Setup

### Prerequisites
- ✅ Backend running on `localhost:8000`
- ✅ Frontend running on `localhost:5173`
- ✅ Logged in with Google OAuth
- ✅ Hubspot connected
- ✅ PostgreSQL with pgvector running

### Environment Check
```bash
# Check backend
curl http://localhost:8000/health

# Check frontend
curl http://localhost:5173

# Check database
psql -U ai_advisor -d ai_advisor_db -c "\dt"
```

---

## Data Creation

### Phase 1: Create Test Data in Gmail

**📧 Email 1: Baseball Conversation**
```
From: john.doe@example.com
To: your_email@gmail.com
Subject: Weekend Plans

Hi,

Thanks for the great meeting yesterday! My son Tommy just made 
the varsity baseball team - we're so proud! He's been practicing 
all summer. 

By the way, I wanted to discuss our Q4 portfolio strategy. 
Can we schedule a meeting next week?

Best,
John Doe
```

**📧 Email 2: Stock Sale Discussion**
```
From: greg.smith@example.com
To: your_email@gmail.com
Subject: Portfolio Changes - AAPL

Hello,

I've been thinking about our conversation regarding Apple stock. 
After reviewing the market trends and tech sector volatility, 
I've decided I want to sell my AAPL holdings. The stock has 
performed well, but I'm concerned about the upcoming earnings 
report and want to lock in gains.

Can you help me execute this transaction?

Thanks,
Greg Smith
```

**📧 Email 3: New Contact (Not in Hubspot)**
```
From: sara.jones@newclient.com
To: your_email@gmail.com
Subject: Financial Advisory Services

Hi,

I was referred to you by John Doe. I'm looking for a financial 
advisor to help with retirement planning. Could we set up an 
introductory meeting?

Best regards,
Sara Jones
CEO, NewClient Corp
Phone: 555-0123
```

**📧 Email 4: Meeting Time Inquiry**
```
From: john.doe@example.com
To: your_email@gmail.com
Subject: Quick Question

Hey,

I forgot - when is our meeting scheduled for this week? 
I want to make sure I have it in my calendar.

Thanks,
John
```

**📧 Email 5: Revenue Discussion**
```
From: michael.brown@acmecorp.com
To: your_email@gmail.com
Subject: Company Performance Update

Hi,

Great news! Acme Corp just closed Q3 with $5.2M in revenue, 
up 30% from last quarter. We're expanding to 75 employees 
and opening a new office in Austin. 

Let's discuss investment opportunities for the company's 
growth capital.

Best,
Michael Brown
CFO, Acme Corp
```

### Phase 2: Create Test Data in Google Calendar

**📅 Event 1: Client Meeting**
```
Title: Portfolio Review - John Doe
Date: Today + 2 hours
Duration: 1 hour
Attendees: john.doe@example.com
Description: Quarterly portfolio review. Discuss baseball team success, 
Q4 strategy, risk tolerance assessment.
```

**📅 Event 2: Call with Greg**
```
Title: AAPL Stock Discussion - Greg Smith
Date: Tomorrow 10:00 AM
Duration: 30 minutes
Attendees: greg.smith@example.com
Description: Review Apple holdings and discuss sale strategy. 
Consider tax implications and replacement investments.
```

**📅 Event 3: New Client Meeting**
```
Title: Introductory Meeting - Sara Jones
Date: Tomorrow 2:00 PM
Duration: 45 minutes
Attendees: sara.jones@newclient.com
Description: Initial consultation for retirement planning. 
Discuss goals, risk tolerance, current portfolio.
```

**📅 Event 4: Team Meeting**
```
Title: Internal Team Strategy
Date: Today 4:00 PM
Duration: 1 hour
Attendees: team@yourcompany.com
Description: Review client portfolio performance and market outlook.
```

### Phase 3: Create Test Data in Hubspot

**👤 Contact 1: John Doe**
```
First Name: John
Last Name: Doe
Email: john.doe@example.com
Company: Doe Enterprises
Phone: 555-1001
Industry: Technology
```

**Notes for John Doe:**
```
Note 1 (2 weeks ago):
"Initial consultation completed. Client has $500K portfolio. 
Mentioned his son Tommy plays baseball - very proud parent! 
Risk tolerance: Moderate. Timeline: 10+ years."

Note 2 (1 week ago):
"Follow-up call. Discussed diversification strategy. 
Client interested in tech sector but wants to balance with bonds. 
Scheduled quarterly review."

Note 3 (3 days ago):
"Confirmed Q4 portfolio review meeting. Client asked about 
529 education savings plan for Tommy's college fund."
```

**Call Record for John Doe:**
```
Call Title: Q3 Performance Review
Date: 2 weeks ago
Duration: 45 minutes
Notes: "Reviewed portfolio performance (+12% YTD). Discussed son's 
baseball team success and college planning. Client very satisfied 
with returns. Wants to increase tech allocation."
```

**Meeting Record for John Doe:**
```
Meeting Title: Strategy Planning Session
Date: 1 month ago
Start: 10:00 AM
End: 11:30 AM
Outcome: COMPLETED
Notes: "Comprehensive portfolio review. Established goals for next 5 years. 
Discussed son Tommy's upcoming college expenses. Agreed on conservative 
growth strategy with 60/40 stocks/bonds split."
```

**👤 Contact 2: Greg Smith**
```
First Name: Greg
Last Name: Smith
Email: greg.smith@example.com
Company: Smith Holdings
Phone: 555-1002
Industry: Real Estate
```

**Notes for Greg Smith:**
```
Note 1 (1 month ago):
"New client onboarding. $750K portfolio. Heavy in tech stocks, 
particularly AAPL (25% of portfolio). Risk tolerance: Aggressive."

Note 2 (2 weeks ago):
"Discussed market volatility. Client nervous about tech sector. 
Expressed interest in selling some AAPL to lock in gains. 
Waiting for right timing."

Note 3 (1 week ago):
"Client reviewed earnings forecasts. Concerned about AAPL performance. 
Decided to sell entire AAPL position (~$187K). Will reallocate to 
dividend stocks and bonds."
```

**Email Record for Greg Smith:**
```
Email Subject: AAPL Sale Confirmation
Date: 5 days ago
Direction: OUTBOUND
Body: "Following up on our discussion to sell AAPL holdings. 
Market timing looks favorable. Concerns about Q4 earnings justify 
taking profits now. Will execute trade next week."
```

**Call Record for Greg Smith:**
```
Call Title: AAPL Position Review
Date: 1 week ago
Duration: 30 minutes
Notes: "Analyzed AAPL performance and upcoming risks. Discussed 
alternative investments. Client firm on decision to sell due to 
valuation concerns and sector rotation strategy."
```

**👤 Contact 3: Michael Brown**
```
First Name: Michael
Last Name: Brown
Email: michael.brown@acmecorp.com
Company: Acme Corp
Phone: 555-1003
Title: CFO
Industry: Manufacturing
```

**🏢 Company: Acme Corp**
```
Name: Acme Corp
Domain: acmecorp.com
Industry: Manufacturing
Annual Revenue: $5,200,000
Number of Employees: 75
City: Austin
State: TX
Phone: 555-2000
Description: Fast-growing manufacturing company specializing in 
industrial equipment. Recently expanded operations and seeking 
growth capital for further expansion.
```

**Notes for Michael Brown:**
```
Note 1 (2 weeks ago):
"CFO of Acme Corp. Company had strong Q3 with $5.2M revenue. 
Planning expansion to Austin office. Needs corporate investment 
advisory for growth capital."

Note 2 (1 week ago):
"Discussed investment strategy for $2M growth capital. 
Company planning to hire 25 more employees. Wants conservative 
approach with 5-year horizon."
```

**👤 Contact 4: Sarah Wilson**
```
First Name: Sarah
Last Name: Wilson
Email: sarah.wilson@example.com
Company: Wilson Family Trust
Phone: 555-1004
Industry: Retired - Education
```

**Notes for Sarah Wilson:**
```
Note 1 (1 month ago):
"Retired school teacher. Grandchildren play youth sports - 
one grandson excels at baseball, granddaughter in soccer. 
Wants to set up education funds for both."

Note 2 (2 weeks ago):
"Discussed 529 plans for grandchildren. Baseball grandson 
(age 12) might get athletic scholarship but wants backup plan. 
Setting up $50K per grandchild."
```

### Phase 4: Sync All Data

**🔄 Important: Sync in this order:**

1. **Sync Gmail** → Click "Sync" button
   - Wait for "Gmail synced successfully"
   - Check: ~5 emails imported

2. **Sync Calendar** → Automatic with Gmail sync
   - Check: ~4 events imported

3. **Sync Hubspot** → Click "Sync" button
   - Wait for "Hubspot synced successfully"
   - Check: 4 contacts, 10+ notes, companies imported

4. **Verify RAG Import** → Check backend logs:
```bash
# Should see:
Imported 5 emails
Imported 4 calendar events
Imported 4 contacts
Imported 10 notes, 2 emails, 3 calls, 2 meetings
Imported 1 companies
```

---

## Test Scenarios

### Category 1: RAG Search - Email Content

#### Test 1.1: Baseball Mention
```
Query: "Who mentioned their kid plays baseball?"

Expected Sources:
- Gmail: John Doe's email about Tommy's baseball team
- Hubspot Notes: Multiple notes mentioning Tommy's baseball
- Hubspot Notes: Sarah Wilson's notes about grandson's baseball

Expected Response:
"Based on your communications, several people have mentioned baseball:
1. John Doe - His son Tommy just made the varsity baseball team
2. Sarah Wilson - Her grandson plays youth baseball and might get an athletic scholarship"
```

#### Test 1.2: Stock Sale Reason
```
Query: "Why did Greg say he wanted to sell AAPL stock?"

Expected Sources:
- Gmail: Greg's email explaining AAPL sale reasoning
- Hubspot Notes: Notes about Greg's concerns
- Hubspot Email: Confirmation about sale
- Hubspot Call: Discussion about valuation concerns

Expected Response:
"Greg Smith wants to sell his AAPL holdings for several reasons:
1. Concerns about upcoming earnings report
2. Tech sector volatility
3. Valuation concerns and overvaluation
4. Wants to lock in gains (portfolio is 25% AAPL)
5. Plans to reallocate to dividend stocks and bonds"
```

#### Test 1.3: Revenue Query
```
Query: "What companies generate over $1M in revenue?"

Expected Sources:
- Gmail: Michael Brown's email about $5.2M revenue
- Hubspot Company: Acme Corp with $5.2M revenue

Expected Response:
"Based on the data, Acme Corp generates $5.2M in annual revenue, 
which is well above $1M. They recently had a strong Q3 and are 
planning expansion to Austin with 75 employees."
```

#### Test 1.4: Multiple Source Query
```
Query: "Tell me everything about John Doe"

Expected Sources:
- Gmail: 2 emails from John
- Calendar: Portfolio review meeting
- Hubspot Contact: Basic info
- Hubspot Notes: 3 notes with portfolio details
- Hubspot Call: Performance review
- Hubspot Meeting: Strategy session

Expected Response:
"John Doe is a client with a $500K portfolio. Key details:
- Contact: john.doe@example.com, 555-1001, Doe Enterprises
- Family: Son Tommy plays varsity baseball, planning for college
- Portfolio: 60/40 stocks/bonds, +12% YTD performance
- Risk: Moderate tolerance, 10+ year timeline
- Recent: Quarterly review scheduled, interested in 529 plans
- Upcoming: Meeting scheduled for [date] to discuss Q4 strategy"
```

### Category 2: RAG Search - Calendar Events

#### Test 2.1: Meeting Lookup
```
Query: "When is my meeting with John Doe?"

Expected Tool: list_calendar_events (should be called)

Expected Response:
"Your meeting with John Doe is scheduled for [today + 2 hours] 
for a Portfolio Review. The meeting is 1 hour long and will cover 
quarterly portfolio review and Q4 strategy."
```

#### Test 2.2: Today's Schedule
```
Query: "What events do I have today?"

Expected Tool: list_calendar_events("2025-10-19", "2025-10-19")

Expected Response:
"You have 2 events today:
1. Portfolio Review - John Doe at [time] (1 hour)
2. Internal Team Strategy at 4:00 PM (1 hour)"
```

#### Test 2.3: Tomorrow's Schedule
```
Query: "What meetings are scheduled for tomorrow?"

Expected Tool: list_calendar_events (tomorrow's date)

Expected Response:
"Tomorrow you have 2 meetings:
1. AAPL Stock Discussion - Greg Smith at 10:00 AM (30 minutes)
2. Introductory Meeting - Sara Jones at 2:00 PM (45 minutes)"
```

### Category 3: Tool Calling - Basic Actions

#### Test 3.1: Search Contacts
```
Query: "Find contact information for Greg Smith"

Expected Tool: search_hubspot_contacts("Greg Smith")

Expected Response:
"Here's Greg Smith's contact information:
- Email: greg.smith@example.com
- Phone: 555-1002
- Company: Smith Holdings
- Industry: Real Estate"
```

#### Test 3.2: List All Contacts
```
Query: "List all my clients in Hubspot"

Expected Tool: list_all_hubspot_contacts()

Expected Response:
"You have 4 contacts in Hubspot:
1. John Doe - Doe Enterprises (john.doe@example.com)
2. Greg Smith - Smith Holdings (greg.smith@example.com)
3. Michael Brown - Acme Corp (michael.brown@acmecorp.com)
4. Sarah Wilson - Wilson Family Trust (sarah.wilson@example.com)"
```

#### Test 3.3: List Contact Notes
```
Query: "Show me all notes for John Doe"

Expected Tool: list_contact_notes("john.doe@example.com")

Expected Response:
"Here are all notes for John Doe:
1. [2 weeks ago] Initial consultation - $500K portfolio, son plays baseball...
2. [1 week ago] Follow-up call - diversification strategy...
3. [3 days ago] Confirmed Q4 review, interested in 529 plans..."
```

#### Test 3.4: Company Details
```
Query: "What's the revenue for Acme Corp?"

Expected Tool: get_company_details("Acme Corp")

Expected Response:
"Acme Corp details:
- Industry: Manufacturing
- Annual Revenue: $5,200,000
- Employees: 75
- Location: Austin, TX
- Recent: Strong Q3 performance, planning expansion"
```

#### Test 3.5: Company Contacts
```
Query: "Who are the contacts at Acme Corp?"

Expected Tool: get_company_contacts("Acme Corp")

Expected Response:
"Contact at Acme Corp:
- Michael Brown (CFO) - michael.brown@acmecorp.com, 555-1003"
```

### Category 4: Tool Calling - Complex Actions

#### Test 4.1: Schedule Meeting (Multi-Step)
```
Query: "Schedule a meeting with Greg Smith tomorrow at 3pm"

Expected Tools (in order):
1. search_hubspot_contacts("Greg Smith")
2. get_calendar_availability(tomorrow, tomorrow)
3. create_calendar_event(
     title="Meeting with Greg Smith",
     start_time="tomorrow 3pm",
     end_time="tomorrow 4pm",
     attendees=["greg.smith@example.com"]
   )
4. send_email(
     to="greg.smith@example.com",
     subject="Meeting Scheduled",
     body="Meeting confirmed for tomorrow at 3pm"
   )
5. add_hubspot_note(
     contact_email="greg.smith@example.com",
     note="Scheduled meeting for [date] at 3pm"
   )

Expected Response:
"I've scheduled a meeting with Greg Smith for tomorrow at 3:00 PM. 
I've sent him a confirmation email and added a note to his Hubspot 
record."
```

#### Test 4.2: Create Contact from Email
```
Query: "Create a Hubspot contact for sara.jones@newclient.com from 
the email I received"

Expected Tools (in order):
1. search_emails("sara.jones@newclient.com")
2. create_hubspot_contact(
     email="sara.jones@newclient.com",
     firstname="Sara",
     lastname="Jones",
     company="NewClient Corp",
     phone="555-0123"
   )
3. add_hubspot_note(
     contact_email="sara.jones@newclient.com",
     note="Contact created from email inquiry about financial advisory..."
   )

Expected Response:
"I've created a Hubspot contact for Sara Jones with the following details:
- Email: sara.jones@newclient.com
- Company: NewClient Corp
- Phone: 555-0123
I've also added a note about her initial inquiry."
```

#### Test 4.3: Update Contact Information
```
Query: "Update John Doe's phone number to 555-9999"

Expected Tools:
1. search_hubspot_contacts("John Doe")
2. update_hubspot_contact(
     contact_email="john.doe@example.com",
     properties={"phone": "555-9999"}
   )

Expected Response:
"I've updated John Doe's phone number to 555-9999 in Hubspot."
```

#### Test 4.4: Get Complete Activity Timeline
```
Query: "Show me all activity for Greg Smith"

Expected Tool: get_contact_activity_timeline("greg.smith@example.com")

Expected Response:
"Here's the complete activity timeline for Greg Smith:

Notes (3):
- [1 month ago] New client onboarding, $750K portfolio, heavy in AAPL
- [2 weeks ago] Discussed market volatility, considering AAPL sale
- [1 week ago] Decision to sell entire AAPL position

Emails (1):
- [5 days ago] AAPL Sale Confirmation (OUTBOUND)

Calls (1):
- [1 week ago] AAPL Position Review (30 minutes)

Meetings: None

Total Activities: 5"
```

### Category 5: Ongoing Instructions

#### Test 5.1: Set Ongoing Instruction
```
Query: "When someone emails me who is not in Hubspot, automatically 
create a contact with a note about the email"

Expected Tool: save_ongoing_instruction(
  instruction="When someone emails me who is not in Hubspot, create a 
  contact with a note about the email",
  trigger_type="gmail"
)

Expected Response:
"I've saved this as an ongoing instruction. From now on, when you 
receive an email from someone not in Hubspot, I'll automatically 
create a contact and add a note about the email."
```

#### Test 5.2: Set Welcome Email Instruction
```
Query: "When I create a contact in Hubspot, send them an email saying 
'Thank you for becoming a client'"

Expected Tool: save_ongoing_instruction(
  instruction="When a contact is created in Hubspot, send them a thank 
  you email",
  trigger_type="hubspot"
)

Expected Response:
"I've saved this instruction. Whenever you create a new contact in 
Hubspot, I'll automatically send them a welcome email."
```

#### Test 5.3: List Current Instructions
```
Query: "What ongoing instructions do I have?"

API Call: GET /integrations/instructions

Expected Response:
"You have 2 ongoing instructions:
1. [Gmail] When someone emails who is not in Hubspot, create contact 
   with note
2. [Hubspot] When contact is created, send thank you email"
```

### Category 6: Proactive Agent

#### Test 6.1: Respond to Meeting Inquiry
```
Setup: Have someone send email: "When is our meeting?"

Trigger: Gmail polling (wait 5 minutes) OR manual sync

Expected Proactive Action:
1. Detects new email from John Doe
2. Checks ongoing instructions
3. Uses list_calendar_events to find meeting
4. Uses send_email to respond:
   "Your meeting is scheduled for [date] at [time] for Portfolio Review"

Verification:
- Check sent emails in Gmail
- Check backend logs for proactive agent trigger
```

#### Test 6.2: Auto-Create Contact from New Sender
```
Setup: 
1. Set ongoing instruction (Test 5.1)
2. Have new person email you (not in Hubspot)

Trigger: Gmail polling (wait 5 minutes) OR manual sync

Expected Proactive Action:
1. Detects new email from unknown sender
2. Checks Hubspot (not found)
3. Extracts info from email
4. Creates Hubspot contact
5. Adds note about email

Verification:
- Check Hubspot for new contact
- Verify note was added with email context
```

#### Test 6.3: Welcome New Contact
```
Setup:
1. Set ongoing instruction (Test 5.2)
2. Manually create a new contact in Hubspot UI

Trigger: Hubspot webhook (immediate) OR manual sync

Expected Proactive Action:
1. Detects new contact in Hubspot
2. Checks ongoing instructions
3. Sends welcome email to new contact

Verification:
- Check sent emails in Gmail
- Verify email sent to new contact
```

### Category 7: Context Dropdown

#### Test 7.1: Filter by Calendar
```
Setup: Select "all meetings" from context dropdown
Query: "What do I have scheduled?"

Expected Behavior:
- RAG search filters to source='calendar'
- Only calendar events returned
- No emails or contacts in results

Expected Response:
"Your scheduled events: [lists only calendar events]"
```

#### Test 7.2: Filter by Recent Emails
```
Setup: Select "recent emails" from context dropdown
Query: "What did people say about baseball?"

Expected Behavior:
- RAG search filters to source='gmail' AND last 30 days
- Only recent emails returned

Expected Response:
"In recent emails, John Doe mentioned his son Tommy's baseball team..."
```

#### Test 7.3: Filter by Contacts
```
Setup: Select "contacts" from context dropdown
Query: "List everyone"

Expected Behavior:
- RAG search filters to source='hubspot_contact'
- Tool: list_all_hubspot_contacts() might also be called

Expected Response:
"Your Hubspot contacts: [lists all contacts]"
```

### Category 8: Task Management

#### Test 8.1: Create Task
```
Query: "Create a task to follow up with Greg after he confirms the 
AAPL sale"

Expected Tool: create_task(
  description="Follow up with Greg Smith after AAPL sale confirmation",
  waiting_for="Email confirmation from Greg",
  context={...}
)

Expected Response:
"I've created a task to follow up with Greg Smith after he confirms 
the AAPL sale."
```

#### Test 8.2: List Tasks
```
Query: "What pending tasks do I have?"

Expected Tool: list_tasks(status="pending")

Expected Response:
"You have 1 pending task:
- Follow up with Greg Smith after AAPL sale confirmation
  (Waiting for: Email confirmation from Greg)"
```

#### Test 8.3: Update Task
```
Query: "Mark the Greg follow-up task as completed"

Expected Tools:
1. list_tasks(status="pending")
2. update_task(task_id="xxx", status="completed")

Expected Response:
"I've marked the task 'Follow up with Greg Smith' as completed."
```

### Category 9: Edge Cases & Error Handling

#### Test 9.1: Contact Not Found
```
Query: "Show me notes for xyz@unknown.com"

Expected Response:
"I couldn't find a contact with that email address. Would you like me 
to search for them or create a new contact?"
```

#### Test 9.2: No Available Time Slots
```
Query: "Schedule a meeting with John today"
Scenario: Calendar is fully booked today

Expected Response:
"There are no available time slots today. Would you like to schedule 
for tomorrow? I have slots available at [times]."
```

#### Test 9.3: Ambiguous Contact
```
Query: "Schedule meeting with John"
Scenario: Multiple Johns in Hubspot

Expected Response:
"I found multiple contacts named John:
1. John Doe - Doe Enterprises
2. John Smith - Smith Corp
Which one would you like to schedule with?"
```

#### Test 9.4: Invalid Date
```
Query: "What events do I have on February 30th?"

Expected Response:
"February 30th is not a valid date. Did you mean February 28th or 
March 1st?"
```

### Category 10: Performance & Limits

#### Test 10.1: Large Result Set
```
Query: "List all companies in Hubspot"

Expected Behavior:
- Tool handles pagination (limit=100)
- Returns all results
- UI displays all companies

Expected Response:
"You have X companies in Hubspot: [lists all]"
```

#### Test 10.2: Complex Multi-Tool Query
```
Query: "Find all clients who mentioned baseball, check their next 
meetings, and send them a reminder"

Expected Tools (multiple):
1. RAG search for "baseball"
2. list_calendar_events for each contact
3. send_email to each contact

Expected Response:
"I found 2 clients who mentioned baseball:
1. John Doe - Meeting scheduled for [date]
   ✓ Sent reminder email
2. Sarah Wilson - No upcoming meetings
   Would you like to schedule one?"
```

---

## Expected Results Summary

### RAG Performance
- ✅ Finds mentions across all sources (emails, notes, calls, meetings)
- ✅ Combines data from multiple sources
- ✅ Semantic search (not just keyword matching)
- ✅ Returns relevant context with source attribution

### Tool Calling
- ✅ Calls appropriate tools for task
- ✅ Multi-step workflows executed correctly
- ✅ Error handling when tool fails
- ✅ Proper sequencing (search before action)

### Proactive Agent
- ✅ Triggers on Gmail polling (every 5 min)
- ✅ Triggers on Hubspot webhooks (immediate)
- ✅ Triggers on Calendar webhooks (immediate)
- ✅ Respects ongoing instructions
- ✅ Makes intelligent decisions

### UI/UX
- ✅ Tool calls visible with IDs
- ✅ Results displayed clearly
- ✅ Context dropdown filters correctly
- ✅ Loading states shown
- ✅ Errors displayed clearly

---

## Testing Checklist

### Before Testing
- [ ] Backend running and healthy
- [ ] Frontend running
- [ ] Google OAuth connected
- [ ] Hubspot connected
- [ ] Test data created in Gmail
- [ ] Test data created in Calendar
- [ ] Test data created in Hubspot
- [ ] All data synced (check logs)

### Category Testing
- [ ] RAG Search - Email Content (4 tests)
- [ ] RAG Search - Calendar Events (3 tests)
- [ ] Tool Calling - Basic Actions (5 tests)
- [ ] Tool Calling - Complex Actions (4 tests)
- [ ] Ongoing Instructions (3 tests)
- [ ] Proactive Agent (3 tests)
- [ ] Context Dropdown (3 tests)
- [ ] Task Management (3 tests)
- [ ] Edge Cases (4 tests)
- [ ] Performance & Limits (2 tests)

### After Testing
- [ ] Review backend logs for errors
- [ ] Check database for correct data storage
- [ ] Verify all emails sent correctly
- [ ] Confirm all calendar events created
- [ ] Validate Hubspot data updated
- [ ] Test data cleanup (optional)

---

## Quick Test Script

For rapid testing, run these queries in sequence:

```
1. "Who mentioned their kid plays baseball?"
2. "Why did Greg want to sell AAPL stock?"
3. "When is my meeting with John Doe?"
4. "What events do I have today?"
5. "List all my clients"
6. "Show me notes for John Doe"
7. "What's the revenue for Acme Corp?"
8. "Schedule a meeting with Greg tomorrow at 3pm"
9. "Create a contact for sara.jones@newclient.com"
10. "Show me all activity for Greg Smith"
```

**Expected Time:** ~15 minutes for full sequence

---

## Troubleshooting

### Issue: "No results found"
- **Check:** Was data synced? Look for "X items imported" in logs
- **Fix:** Click Sync button again

### Issue: "Contact not found"
- **Check:** Email address exact match in Hubspot
- **Fix:** Create contact or adjust query

### Issue: "Tool call failed"
- **Check:** Backend logs for specific error
- **Fix:** Check OAuth tokens, API limits

### Issue: "Proactive agent not triggering"
- **Check:** Gmail polling running? (every 5 min)
- **Fix:** Restart backend or manual sync

---

## Success Criteria

✅ **All RAG queries return relevant results**
✅ **Tools execute successfully**  
✅ **Multi-step workflows complete**
✅ **Proactive agent responds correctly**
✅ **Ongoing instructions persist and execute**
✅ **Error handling graceful**
✅ **Performance acceptable (<3s responses)**

---

**Total Test Time:** ~2-3 hours for comprehensive testing
**Priority Tests:** Tests 1.1, 1.2, 2.1, 3.2, 4.1, 5.1, 6.1

Good luck! 🚀

