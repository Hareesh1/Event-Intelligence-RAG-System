# QUICK START GUIDE - Web Interface

## Start in 3 Steps

### Step 1️⃣: Run the Server
```bash
cd "C:\Users\haree\OneDrive\Desktop\Event Intelligence RAG System"
python run_web_interface.py
```

**Or directly:**
```bash
python web_rag_interface.py
```

### Step 2️⃣: Open Browser
```
http://localhost:5000
```

### Step 3️⃣: Start Querying!
```
Type: "What critical alarms from component 103?"
Click: "Search" button
View: Results with confidence score
```

---

## What You'll See

```
┌─────────────────────────────────────────────────────────────────┐
│      🔍 Event Intelligence RAG System              System Active │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────┐   ┌──────────────────────────────┐   │
│  │  QUERY INPUT         │   │  RESULTS                     │   │
│  │                      │   │                              │   │
│  │  Your Question:      │   │  Q: What critical alarms...? │   │
│  │  [text field]        │   │  [OK] Quality: good (80%)       │   │
│  │                      │   │                              │   │
│  │  Priority: [▼]       │   │  ████████░░ 80% Confidence   │   │
│  │  Component: [input]  │   │                              │   │
│  │                      │   │  A: Based on operational...  │   │
│  │  [Search] [Clear]    │   │                              │   │
│  │                      │   │  Components: 103, 311, 315   │   │
│  │  📌 Suggestions:     │   │                              │   │
│  │  [Fire] [Critical]   │   │                              │   │
│  │  [Component] [Water] │   │                              │   │
│  └──────────────────────┘   └──────────────────────────────┘   │
│                                                                 │
│  💡 Tabs: [Single Query] [Batch Query]                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Try These Example Queries

### Basic Commands
```
1️⃣  "What critical alarms from component 103?"
    → Expected: ~80% confidence, Components 103/311/315

2️⃣  "How many fire emergencies in May?"
    → Expected: ~60% confidence, 5 events found

3️⃣  "Which components had water leakage?"
    → Expected: ~30% confidence, Components 312/313
```

### Advanced Queries
```
4️⃣  "Tell me about security malfunction alerts"
    → Gets specific event types

5️⃣  "Why so many high-priority incidents?"
    → Analyzes patterns

6️⃣  "What happened in September?"
    → Time-based query
```

### With Filters
```
7️⃣  Priority Filter: Select "Critical" → "What alarms?"
    → Only shows critical events

8️⃣  Component Filter: Enter "103" → "What happened?"
    → Only shows component 103 events
```

---

## 📱 Interface Sections

### Left Panel: Query Input
```
┌─ TAB OPTIONS ─────────────┐
│ [Single Query] [Batch]     │
├────────────────────────────┤
│ Your Question:             │
│ [text area for input]      │
│                            │
│ Priority Filter:           │
│ [All] [Critical] [High]    │
│                            │
│ Component Filter:          │
│ [input number]             │
│                            │
│ [🚀 Search] [Clear]        │
│                            │
│ 📌 Quick Suggestions:      │
│ [Fire] [Water] [Security]  │
│ [Component] [Critical]...  │
└────────────────────────────┘
```

### Right Panel: Results
```
┌─ RESULT DISPLAY ────────────────────┐
│ Question: "What critical alarms...?"│
│ [good] ← Quality Badge              │
│                                     │
│ Confidence: ████████░░ 80%          │
│                                     │
│ Answer:                             │
│ ┌───────────────────────────────┐   │
│ │ Based on operational data:    │   │
│ │                               │   │
│ │ Found 5 critical events...    │   │
│ │                               │   │
│ │ Details: Components 103, ...  │   │
│ └───────────────────────────────┘   │
│                                     │
│ Components: [103] [311] [315]       │
│ Priorities: [Critical]               │
│ Time:       [May] [Sep] [July]      │
│                                     │
│ TOP RESULT:                         │
│ Alarm #37764 - Building Security... │
└─────────────────────────────────────┘
```

---

## 🎨 Quality Indicators

| Badge | Confidence | Meaning | Action |
|-------|-----------|---------|--------|
| 🟢 **Excellent** | 95% | Perfect match | Trust fully |
| 🔵 **Good** | 80% | Very relevant | Use with confidence |
| 🟡 **Fair** | 60% | Somewhat relevant | May need refinement |
| 🔴 **Insufficient** | 30% | Limited context | Try different query |

---

## 🎮 Batch Query Mode

### How to Use
1. Click "Batch Query" tab
2. Enter multiple questions (one per line):
```
What critical alarms from component 103?
How many fire emergencies in May?
Which components had water leakage?
```
3. Click "Run Batch"
4. See results for all queries

### Example Output
```
Query 1: "What critical alarms from component 103?"
[OK] Found 5 events | Quality: good | Confidence: 80%

Query 2: "How many fire emergencies in May?"
[OK] Found 5 events | Quality: fair | Confidence: 60%

Query 3: "Which components had water leakage?"
[OK] Found 2 components | Quality: insufficient | Confidence: 30%
```

---

## 💻 Using the API

### Python Example
```python
import requests

# Single query
response = requests.post(
    'http://localhost:5000/api/query',
    json={'query': 'What critical alarms from component 103?'}
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']}%")
```

### Command Line (cURL)
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What critical alarms from component 103?"}'
```

### JavaScript
```javascript
fetch('http://localhost:5000/api/query', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        query: 'What critical alarms from component 103?'
    })
})
.then(r => r.json())
.then(data => console.log(data.answer));
```

---

## 🔗 Available Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Web interface |
| `/api/query` | POST | Single query |
| `/api/batch-query` | POST | Multiple queries |
| `/api/search` | GET | Suggestions |
| `/api/system-status` | GET | System info |
| `/api/export-results` | POST | Export results |

---

## ⚙️ Tips & Tricks

### Make Better Queries
```
[OK] GOOD:
   "What critical alarms from component 103?"
   "How many fire emergencies in May?"
   "Which components had water leakage?"

❌ AVOID:
   "Show me stuff"
   "Tell me about everything"
   "What happened?"
```

### Use Filters Effectively
```
For Priority:
└─ Select "Critical" for only critical events
└─ Leave blank to see all priorities

For Component:
└─ Enter "103" to filter to component 103
└─ Leave blank to see all components
```

### Understanding Low Confidence
```
If confidence < 40%:
1. Try different keywords
2. Be more specific with component/priority
3. Use known time period (May-Nov 2025)
4. Try simpler query
```

---

## 🐛 Troubleshooting

### "Connection refused"
```bash
# Check if server is running
# Run: python run_web_interface.py
# Then visit: http://localhost:5000
```

### "Port 5000 already in use"
```bash
# Kill existing process
netstat -ano | findstr :5000
taskkill /PID <process_id> /F

# Or use different port by editing web_rag_interface.py
# Change: port=5000 to port=8000
```

### "Flask not found"
```bash
# Install Flask
pip install flask
```

### "No results returned"
```
⚠️ Query might be outside data range (May-Nov 2025)
[OK] Try: "What happened in September?"
[OK] Try: "Fire emergencies?"
[OK] Use specific component IDs or priorities
```

---

## 📊 System Stats

```
[OK] Events Analyzed:        3,408
[OK] Text Chunks:            6,466
[OK] Embedding Dimension:    384
[OK] Time Period:            May - November 2025
[OK] Components:             10+
[OK] Query Speed:            100-300ms
[OK] With LLM:               500ms-2s
```

---

## 📚 Full Documentation

For more detailed information, see:

1. **WEB_INTERFACE_GUIDE.md**
   - Complete user guide
   - Detailed examples
   - Configuration tips

2. **API_REFERENCE.md**
   - API endpoints
   - Request/response formats
   - Code examples for Python, JavaScript, Java

3. **WEB_INTERFACE_SUMMARY.md**
   - Architecture overview
   - Feature highlights
   - Integration details

---

## 🎯 What You Can Do

### 1. Ask Questions
```
"What critical alarms from component 103?"
"How many fire emergencies in May?"
```

### 2. Analyze Events
```
"Why so many high-priority incidents?"
"What patterns do you see?"
```

### 3. Filter Results
```
Priority: Critical → "What happened?"
Component: 312 → "Any issues?"
```

### 4. Process Multiple Queries
```
Batch Mode: Submit 5+ questions at once
See Results: All answered together
```

### 5. Use the API
```
Python, JavaScript, cURL, etc.
Build custom applications
Integrate with other systems
```

---

## 🚀 Getting Started Right Now

### If You Haven't Started Yet:
```bash
# 1. Open Terminal/PowerShell
# 2. Navigate to project:
cd "C:\Users\haree\OneDrive\Desktop\Event Intelligence RAG System"

# 3. Start server:
python run_web_interface.py

# 4. Browser should open automatically
# Or manually visit: http://localhost:5000

# 5. Enter a query and click Search!
```

### If You Want to Use the API:
```bash
# In another terminal, test the API:
curl http://localhost:5000/api/system-status

# Or use Python:
python -c "import requests; print(requests.get('http://localhost:5000/api/system-status').json())"
```

---

## ✨ Key Features Summary

[OK] **Intuitive Interface** - Natural language queries  
[OK] **Instant Feedback** - Real-time processing  
[OK] **Quality Scores** - Know your confidence level  
[OK] **Batch Processing** - Multiple queries at once  
[OK] **Flexible Filtering** - By priority or component  
[OK] **REST API** - Build on top of this  
[OK] **Mobile Responsive** - Works on any device  
[OK] **Beautiful UI** - Modern design  
[OK] **Suggestions** - Quick query templates  
[OK] **Full Documentation** - Everything explained  

---

## 🎉 You're All Set!

The web interface is ready to use. 

**Start querying your Event Intelligence data now!**

---

**Questions?** Check the troubleshooting section  
**Need More Info?** See WEB_INTERFACE_GUIDE.md  
**Want to Code?** See API_REFERENCE.md  
**Curious about the System?** See README.md
