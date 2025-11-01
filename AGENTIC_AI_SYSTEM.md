# Agentic AI System Documentation

## Overview

Your RecruitAI system is now a **truly agentic AI-based** recruitment platform with autonomous AI agents that make decisions, reason about their actions, and provide explainability through real-time notifications.

## 🧠 Autonomous AI Agents

### 1. **Interview Scheduler Agent**
- **Role**: Optimizes interview scheduling
- **Autonomous Actions**:
  - Fetches HR calendar availability
  - Analyzes free time slots
  - Proposes optimal interview times
  - Creates calendar events automatically
  - Explains scheduling logic

### 2. **Resume and Matching Agent**
- **Role**: Automatically matches resumes to job descriptions
- **Autonomous Actions**:
  - Analyzes resume content semantically
  - Scores matches using LLM reasoning
  - Decides ACCEPT/REJECT based on thresholds
  - Explains reasoning for each decision

### 3. **Job Description Agent**
- **Role**: Parses job descriptions from PDFs
- **Autonomous Actions**:
  - Extracts text from PDF documents
  - Parses structured information using LLM
  - Extracts job title, company, skills, requirements
  - Stores structured job data
  - Explains parsing logic

### 4. **Shortlisting Agent**
- **Role**: Evaluates candidate test performance
- **Autonomous Actions**:
  - Analyzes Codeforces submission data
  - Calculates performance scores
  - Makes SHORTLIST/REJECT decisions
  - Recommends candidates for interviews
  - Explains evaluation criteria

## 📢 Explainability & Notifications

### Notification Center Features:
- **Real-time AI Agent Notifications**: See what each agent is doing
- **AI Reasoning Display**: Every decision includes explanation
- **Color-coded Types**:
  - 🧠 **Decision** (Purple): AI making autonomous decisions
  - ✅ **Success** (Green): Successful operations
  - ⚠️ **Warning** (Yellow): Issues or recommendations
  - ℹ️ **Info** (Blue): General information
  - ⏰ **Processing** (Gray): Ongoing operations

### Example Notifications:
```
🧠 Resume Matcher Agent
"✅ Resume matched: Score 85.3/100 - ACCEPTED"
AI Reasoning: "Resume shows strong alignment with job requirements in 
Python, ML, and 5+ years experience. Keywords match 90% threshold."

📅 Interview Scheduler Agent  
"✅ Found 12 available time slots from HR calendar"
AI Reasoning: "Analyzed calendar and computed free 30-minute slots 
between busy periods"
```

## 🔄 Agent Communication

Agents communicate through:
1. **Shared Notification System**: All agents post notifications
2. **Sequential Workflow**: 
   - Job Description Agent → Resume and Matching Agent → Shortlisting Agent → Interview Scheduler
3. **Reasoning Propagation**: Each agent sees previous agent reasoning

## 🚀 How It Works

### Autonomous Decision Flow:

1. **Job Description Upload**:
   - Job Description Agent parses PDF
   - Notifies: "Successfully parsed job description: [Title]"
   - Explains extracted information

2. **Resume Application**:
   - Resume and Matching Agent automatically scores application
   - Notifies: "Resume matched: Score X/100"
   - Explains why score was given

3. **Test Completion**:
   - Shortlisting Agent evaluates performance
   - Notifies: "Candidate X - 75% completion → SHORTLIST"
   - Explains shortlisting criteria

4. **Interview Scheduling**:
   - Interview Scheduler Agent analyzes calendar
   - Notifies: "Proposed 5 optimal interview slots"
   - Explains slot selection logic
   - Creates calendar events automatically

## 💡 Key Agentic Features

✅ **Autonomous Decision-Making**: Agents make decisions without human intervention  
✅ **Explainable AI**: Every decision includes reasoning  
✅ **Real-time Transparency**: Notifications show agent actions live  
✅ **Reasoning Chain**: Decisions build on previous agent reasoning  
✅ **Error Handling**: Agents gracefully handle failures  
✅ **Self-Learning**: Agents improve through feedback loops

## 🎯 Usage

1. **View Notifications**: Click the brain icon (🧠) in bottom-right corner
2. **Read AI Reasoning**: Click any notification to see detailed reasoning
3. **Monitor Agents**: Watch agents work autonomously in real-time
4. **Trust Decisions**: See exactly why each AI decision was made

## 🔧 Configuration

Agents use environment variables:
- `HF_TOKEN`: For LLM reasoning (optional, falls back to rule-based)
- Agents work even without LLM, using rule-based reasoning

## 🎓 Example Agent Workflow

```
1. Job Description uploaded → Job Description Agent
   📢 "📄 Parsing job description from job.pdf..."
   📢 "✅ Successfully parsed job description: Software Engineer"
   📢 Reasoning: "Extracted job title, company, skills, and requirements from PDF"

2. Candidate applies → Resume and Matching Agent
   📢 "Analyzing resume against job XYZ..."
   📢 "✅ Resume matched: Score 78/100 - ACCEPTED"
   📢 Reasoning: "Strong Python skills, 4 years experience matches requirements"

3. Candidate takes test → Shortlisting Agent
   📢 "🧠 Evaluating candidate@email.com for shortlisting..."
   📢 "📊 Evaluation: 85% completion → SHORTLIST"
   📢 Reasoning: "Excellent problem-solving: solved 8/10 questions including hard ones"

4. HR schedules interview → Interview Scheduler Agent
   📢 "📅 Fetching calendar availability..."
   📢 "✅ Found 15 available time slots"
   📢 "🎯 Proposed 5 optimal interview slots"
   📢 Reasoning: "Selected morning slots to maximize HR availability"
```

Your system is now **truly agentic**! 🎉

