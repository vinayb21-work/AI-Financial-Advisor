# Comprehensive Test Data Plan

## Overview
Based on the requirements in `paid_challenge.md`, this document outlines test data scenarios to validate all features and identify implementation gaps.

---

## 1. RAG System - Gmail Test Data

### Email Conversations to Create

#### Scenario 1: Client with Baseball Kid
**From:** greg.anderson@example.com  
**Subject:** Quick update on the portfolio  
**Body:**
```
Hi [Your Name],

Hope you're doing well! Just wanted to give you a quick update on our family. 
My son Tommy just made the varsity baseball team - he's been practicing non-stop! 
We're all very proud.

Regarding the portfolio, I've been thinking about selling some of my AAPL stock. 
I'm concerned about the tech sector volatility and would like to diversify. 
Can we schedule a time to discuss this?

Best,
Greg
```

#### Scenario 2: New Client Inquiry (Not in Hubspot)
**From:** sarah.johnson@newclient.com  
**Subject:** Financial advisory services inquiry  
**Body:**
```
Hello,

I was referred to you by Michael Chen. I'm looking for a financial advisor 
to help with retirement planning. I have about $500k to invest and would 
like to schedule an initial consultation.

Please let me know your availability.

Thanks,
Sarah Johnson
```

#### Scenario 3: Client Asking About Meeting
**From:** linda.martinez@example.com  
**Subject:** When is our meeting?  
**Body:**
```
Hi,

I can't find the invite for our upcoming meeting. Can you remind me when 
we're scheduled to meet?

Thanks,
Linda
```

#### Scenario 4: Soccer Mom Client
**From:** jennifer.wilson@example.com  
**Subject:** Portfolio review feedback  
**Body:**
```
Hi,

Thanks for the portfolio review last week. I'm happy with the rebalancing 
suggestions. By the way, my daughter Emma just started playing soccer - 
she's loving it! Between soccer practice and games, our weekends are packed.

Let's move forward with the changes we discussed.

Jennifer
```

#### Scenario 5: Client Response to Scheduling
**From:** sara.smith@example.com  
**Subject:** Re: Meeting Request  
**Body:**
```
Hi,

Thanks for reaching out! I'd love to schedule a meeting. Unfortunately, 
the times you suggested don't work for me. Do you have availability 
next Thursday afternoon or Friday morning?

Best,
Sara
```

---

## 2. Google Calendar Test Events

### Events to Create

#### Event 1: Existing Client Meeting
**Title:** Portfolio Review - Linda Martinez  
**Date:** Today + 2 days  
**Time:** 2:00 PM - 3:00 PM  
**Description:** Quarterly portfolio review  
**Attendees:** linda.martinez@example.com

#### Event 2: New Client Consultation
**Title:** Initial Consultation - Sarah Johnson  
**Date:** Today + 5 days  
**Time:** 10:00 AM - 11:00 AM  
**Description:** Retirement planning discussion  
**Attendees:** sarah.johnson@newclient.com

#### Event 3: Team Meeting
**Title:** Weekly Team Sync  
**Date:** Today + 1 day  
**Time:** 9:00 AM - 9:30 AM  
**Attendees:** team@yourcompany.com

#### Event 4: Personal Event
**Title:** Dentist Appointment  
**Date:** Today + 3 days  
**Time:** 4:00 PM - 4:30 PM  
**Attendees:** None

---

## 3. Hubspot CRM Test Data

### Contacts to Create

#### Contact 1: Greg Anderson
- **Email:** greg.anderson@example.com
- **Phone:** (555) 123-4567
- **Notes:** 
  - "Client since 2020. Conservative investor."
  - "Son Tommy plays baseball - varsity team"
  - "Concerned about AAPL stock volatility"

#### Contact 2: Linda Martinez
- **Email:** linda.martinez@example.com
- **Phone:** (555) 234-5678
- **Notes:**
  - "Client since 2019. Prefers quarterly reviews."
  - "Next meeting scheduled for portfolio review"

#### Contact 3: Jennifer Wilson
- **Email:** jennifer.wilson@example.com
- **Phone:** (555) 345-6789
- **Notes:**
  - "Client since 2021. Moderate risk tolerance."
  - "Daughter Emma plays soccer"
  - "Recently rebalanced portfolio"

#### Contact 4: Sara Smith
- **Email:** sara.smith@example.com
- **Phone:** (555) 456-7890
- **Notes:**
  - "Prospective client. Interested in estate planning."
  - "Referred by John Davis"

---

## 4. Test Scenarios & Expected Behaviors

### A. Q&A Scenarios (RAG System)

#### Test 1: Sports Interest Query
**Question:** "Who mentioned their kid plays baseball?"  
**Expected:** Should identify Greg Anderson and mention his son Tommy

#### Test 2: Stock Concern Query
**Question:** "Why did Greg say he wanted to sell AAPL stock?"  
**Expected:** Should mention tech sector volatility and diversification

#### Test 3: Multiple Sports Query
**Question:** "Which clients have kids in sports?"  
**Expected:** Should list Greg (baseball) and Jennifer (soccer)

#### Test 4: Meeting Lookup
**Question:** "When is my meeting with Linda?"  
**Expected:** Should find the calendar event and provide date/time

#### Test 5: Client Background
**Question:** "Tell me about Jennifer Wilson"  
**Expected:** Should combine Hubspot notes and email context

---

### B. Tool Calling Scenarios

#### Test 1: Schedule Appointment (Happy Path)
**Prompt:** "Schedule an appointment with Sara Smith"  
**Expected Actions:**
1. Look up Sara Smith in Hubspot
2. Check my calendar availability
3. Send email with available times
4. Wait for response
5. Add to calendar when confirmed
6. Create note in Hubspot

#### Test 2: Schedule with Unavailable Times
**Prompt:** "Schedule an appointment with Sara Smith"  
**Follow-up:** Sara responds saying times don't work  
**Expected Actions:**
1. Find alternative times
2. Send new options
3. Continue until confirmed

#### Test 3: Email Draft
**Prompt:** "Draft an email to Greg about diversification strategies"  
**Expected:** Create email using context from his concerns

#### Test 4: Calendar Query
**Prompt:** "What meetings do I have this week?"  
**Expected:** List all meetings with details

---

### C. Ongoing Instructions & Proactive Actions

#### Test 1: Auto-Create Hubspot Contact
**Instruction:** "When someone emails me that is not in Hubspot, create a contact with a note about the email"  
**Trigger:** Email from sarah.johnson@newclient.com  
**Expected:**
1. Detect new sender not in Hubspot
2. Create contact automatically
3. Add note about initial inquiry

#### Test 2: Thank You Email
**Instruction:** "When I create a contact in Hubspot, send them an email thanking them for being a client"  
**Trigger:** Manually create new contact  
**Expected:** Automatically send thank you email

#### Test 3: Meeting Notification
**Instruction:** "When I add an event to my calendar, email attendees about the meeting"  
**Trigger:** Create new calendar event  
**Expected:** Send email to all attendees with details

#### Test 4: Auto-Respond to Meeting Query
**Trigger:** Linda emails asking "When is our meeting?"  
**Expected:**
1. Detect question about meeting
2. Look up calendar
3. Auto-respond with meeting details

---

## 5. Implementation Gaps Identified

### Critical Gaps

#### Gap 1: ❌ Task/Memory System
**Current:** No persistent task storage  
**Required:** Database table to track multi-step tasks
- Task ID
- Status (pending/in_progress/completed)
- Context/history
- Next action

**Impact:** Can't handle "Schedule with Sara Smith" that requires waiting for email response

#### Gap 2: ❌ Ongoing Instructions Storage
**Current:** `OngoingInstruction` model exists but not fully integrated  
**Required:** 
- Store user-defined rules
- Trigger evaluation on webhook events
- Match events to instructions

**Impact:** Can't execute "When someone emails me that is not in Hubspot, create contact"

#### Gap 3: ❌ Proactive Agent Execution
**Current:** Agent only responds to chat messages  
**Required:** 
- Webhook handler triggers agent evaluation
- Agent checks ongoing instructions
- Agent decides if action needed
- Executes tools autonomously

**Impact:** No automatic responses to emails or calendar events

#### Gap 4: ❌ Email Sending Tool
**Current:** No tool to send emails  
**Required:** 
- `send_email` tool using Gmail API
- Template support
- Draft preview

**Impact:** Can't send scheduling requests or follow-ups

#### Gap 5: ⚠️ Calendar Creation Tool
**Current:** `create_calendar_event` exists but not tested  
**Required:** Verify it works end-to-end  
**Impact:** Can't complete "Schedule appointment" workflow

#### Gap 6: ❌ Hubspot Contact Creation Tool
**Current:** No tool to create Hubspot contacts  
**Required:**
- `create_hubspot_contact` tool
- `create_hubspot_note` tool

**Impact:** Can't execute "create contact when someone new emails"

#### Gap 7: ❌ Email Detection & Filtering
**Current:** No logic to detect new emails and match to instructions  
**Required:**
- Compare email sender to Hubspot contacts
- Detect if sender is new
- Extract key information from email

**Impact:** Can't trigger automatic actions on new emails

#### Gap 8: ⚠️ Multi-Step Task Continuity
**Current:** No state machine for complex workflows  
**Required:**
- Track workflow state
- Resume after waiting for external input
- Handle multiple conversation turns

**Impact:** Can't handle "Sara says times don't work, send new times"

---

### Nice-to-Have Improvements

#### Improvement 1: Better RAG Context Selection
**Current:** Returns top 5 documents  
**Suggested:** 
- Filter by relevance threshold
- Deduplicate similar content
- Prioritize recent data

#### Improvement 2: Conversation Threading
**Current:** Each chat is independent  
**Suggested:** Link related messages across integrations

#### Improvement 3: Undo/Confirmation
**Current:** Actions execute immediately  
**Suggested:** Preview before executing sensitive actions

#### Improvement 4: Rich Formatting
**Current:** Plain text responses  
**Suggested:** Format calendar events, contact cards, etc.

---

## 6. Testing Checklist

### Phase 1: Basic RAG (✅ Working)
- [✅] Import emails to vector DB
- [✅] Import calendar events to vector DB
- [✅] Import Hubspot contacts to vector DB
- [✅] Search returns relevant results
- [✅] AI uses RAG context in responses

### Phase 2: Q&A Capabilities (✅ Working)
- [✅] Answer questions about clients
- [✅] Answer questions about meetings
- [✅] Combine data from multiple sources

### Phase 3: Basic Tool Calling (⚠️ Partial)
- [✅] Get calendar availability
- [⚠️] Create calendar event (needs testing)
- [❌] Send email
- [❌] Create Hubspot contact
- [❌] Create Hubspot note

### Phase 4: Memory & Tasks (❌ Not Implemented)
- [❌] Store ongoing instructions
- [❌] Track multi-step tasks
- [❌] Resume tasks after waiting

### Phase 5: Proactive Actions (❌ Not Implemented)
- [❌] Process webhook events
- [❌] Evaluate ongoing instructions on events
- [❌] Execute autonomous actions
- [❌] Handle email responses

### Phase 6: Complex Workflows (❌ Not Implemented)
- [❌] Schedule appointment end-to-end
- [❌] Handle back-and-forth in scheduling
- [❌] Auto-create contacts from new emails
- [❌] Auto-respond to client queries

---

## 7. Priority Action Items

### Must-Have for Submission

1. **Implement Email Sending Tool** (4 hours)
   - Add Gmail API send functionality
   - Create `send_email` tool
   - Test with draft and send

2. **Implement Hubspot Write Tools** (3 hours)
   - Add `create_hubspot_contact` tool
   - Add `create_hubspot_note` tool
   - Test contact creation

3. **Build Task System** (6 hours)
   - Create Task database table
   - Add task creation/update logic
   - Implement task resumption

4. **Ongoing Instructions Integration** (4 hours)
   - Add UI to manage instructions
   - Store instructions in DB
   - Evaluate on webhook events

5. **Proactive Agent Logic** (6 hours)
   - Webhook triggers agent
   - Agent evaluates instructions
   - Agent executes tools autonomously
   - Add logging/audit trail

6. **End-to-End Testing** (4 hours)
   - Test all scenarios above
   - Fix bugs
   - Document any limitations

**Total: ~27 hours** (Challenging but possible with AI assistance)

---

## 8. Quick Win Test Data Setup Script

```python
# Quick test data insertion script
test_emails = [
    {
        "from": "greg.anderson@example.com",
        "subject": "Quick update",
        "body": "My son Tommy made the varsity baseball team! Also want to discuss selling AAPL stock due to tech volatility."
    },
    {
        "from": "jennifer.wilson@example.com", 
        "subject": "Portfolio feedback",
        "body": "My daughter Emma just started playing soccer. Happy with the portfolio rebalancing."
    },
    {
        "from": "linda.martinez@example.com",
        "subject": "When is our meeting?",
        "body": "Can you remind me when we're scheduled to meet?"
    }
]

# Create these in your Gmail account or use Gmail API to import
```

---

## Summary

**Currently Working:** ✅ Basic RAG Q&A system  
**Critical Gaps:** ❌ Tool calling, tasks, proactive actions, ongoing instructions  
**Time Estimate:** ~27 hours to complete all requirements  
**Recommendation:** Prioritize the 6 must-have items above to get a working demo of the complex workflows

