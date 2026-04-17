# Web Interface User Guide

## Event Intelligence RAG System - Web Interface

A modern, user-friendly web interface for querying the Event Intelligence RAG system. Ask natural language questions about operational events, alarms, and incidents.

---

## 🚀 Quick Start

### Installation

1. **Ensure all core dependencies are installed**:
```bash
pip install flask
```

2. **Navigate to the project directory**:
```bash
cd "C:\Users\haree\OneDrive\Desktop\Event Intelligence RAG System"
```

3. **Start the web interface**:
```bash
python run_web_interface.py
```

Or directly:
```bash
python web_rag_interface.py
```

### Access

- **Web Interface**: Open browser to `http://localhost:5000`
- **API Endpoint**: `http://localhost:5000/api/`
- **Port**: 5000 (configurable in `web_rag_interface.py`)

---

### Interface Features

### Query Input Panel (Left Side)

#### Single Query Mode
- **Query Input**: Enter natural language questions
- **Priority Filter**: Optionally filter by Critical/High/Low
- **Component Filter**: Optionally filter by component ID
- **Quick Suggestions**: Pre-populated suggestions for common searches

#### Batch Query Mode
- **Multiple Queries**: Enter multiple questions (one per line)
- **Max 20 queries** per batch
- **Process all** at once

### Results Panel (Right Side)

- **Query Display**: Shows the question asked
- **Quality Badge**: Visual indicator of context quality
  - 🟢 Excellent (95% confidence)
  - 🔵 Good (80% confidence)
  - 🟡 Fair (60% confidence)
  - 🔴 Insufficient (30% confidence)
- **Confidence Bar**: Visual confidence percentage
- **Answer Section**: Main answer with relevant information
- **Metadata Tags**: Components, priorities, time periods found
- **Top Result**: Specific alarm or event highlighted

---

## 📝 Example Queries

### Event-Based Questions
```
What critical alarms occurred from component 103?
How many fire emergency events happened in May?
Which components experienced water leakage issues?
```

### Analysis Questions
```
Why do we have so many high-priority incidents?
Tell me about security malfunction alerts
What's the pattern in equipment failures?
```

### Time-Based Questions
```
What happened in September 2025?
Any incidents in August from component 312?
How many events in July?
```

### Component-Based Questions
```
Show me all events from component 100
What's happening with component 315?
Which components had the most incidents?
```

---

## How to Use

### Single Query Workflow

1. **Enter Question**: Type your question in the text area
   - Example: "What critical alarms from component 103?"

2. **Optional Filters** (not required):
   - Priority: Select Critical, High, or Low
   - Component: Enter specific component ID

3. **Click "Search"**: Execute the query

4. **View Results**:
   - Read the answer in the results panel
   - Check confidence level
   - Review metadata tags
   - See top result

5. **Clear** (if needed): Click "Clear" to reset form

### Batch Query Workflow

1. **Switch to "Batch Query" tab**

2. **Enter Multiple Queries** (one per line):
   ```
   What critical alarms from component 103?
   How many fire emergencies in May?
   Which components had water leakage?
   ```

3. **Click "Run Batch"**: Process all queries

4. **View All Results**: Results display for each query

---

## Understanding Results

### Quality Levels

**Excellent** (>0.5 similarity)
- Highly relevant context found
- High confidence in answer
- Use with confidence

**Good** (0.3-0.5 similarity)
- Good context available
- Medium-high confidence
- Reliable for most use cases

**Fair** (0.15-0.3 similarity)
- Limited context
- Medium confidence
- May need refinement

**Insufficient** (<0.15 similarity)
- Very limited context
- Low confidence (30%)
- Consider rephrasing query

### Confidence Percentage

- **80-100%**: Use answer confidently
- **60-79%**: Answer is likely correct
- **30-59%**: Consider refinement
- **<30%**: Try different keywords

### Metadata Fields

- **Components**: Which system components are affected
- **Priorities**: Alert priority levels (Critical, High, Low)
- **Time Periods**: When incidents occurred (month/year)
- **Context Chunks**: Number of relevant text chunks retrieved

---

## 🎯 Tips & Best Practices

### Query Tips

1. **Be Specific**:
   - [OK] "What critical alarms from component 103?"
   - ❌ "Show me stuff"

2. **Use Keywords**:
   - [OK] "Water leakage events"
   - ❌ "Leak situation"

3. **Ask One Thing at a Time**:
   - [OK] "How many fire emergencies?"
   - ❌ "Tell me about fires and water and alarms"

4. **Give Context**:
   - [OK] "Security malfunction alerts in July"
   - ❌ "Security issues"

### When to Use Filters

- **Priority Filter**: When you care about severity level
  - "Show me only critical incidents"
  
- **Component Filter**: When focusing on specific equipment
  - "Events from component 103"

### Interpreting Low Confidence

**If confidence is low (<40%)**:
- Try different keywords
- Be more specific
- Use component ID or priority filter
- Check if time period is in May-November 2025

---

## 🔌 API Endpoints

The web interface uses these REST API endpoints:

### POST /api/query

**Single query endpoint**

Request:
```json
{
  "query": "What critical alarms from component 103?",
  "priority_filter": "Critical",  // Optional
  "component_filter": 103         // Optional
}
```

Response:
```json
{
  "success": true,
  "query": "What critical alarms from component 103?",
  "answer": "Based on the operational data...",
  "quality": "good",
  "confidence": 80,
  "context_chunks": 5,
  "components_found": [103, 311, 315],
  "priority_levels": ["Critical"],
  "time_periods": ["September", "July", "May"],
  "top_result": "Alarm #37764..."
}
```

### POST /api/batch-query

**Batch query endpoint**

Request:
```json
{
  "queries": [
    "What critical alarms from component 103?",
    "How many fire emergencies in May?"
  ]
}
```

Response:
```json
{
  "success": true,
  "total_queries": 2,
  "results": [...]
}
```

### GET /api/search

**Search suggestions endpoint**

Query params:
```
?q=fire
```

Response:
```json
{
  "success": true,
  "suggestions": {
    "components": [100, 103, 312],
    "priorities": ["Critical", "High"],
    "event_types": ["Fire Emergency", "Water Leakage"],
    "time_periods": ["May 2025", "July 2025"]
  }
}
```

### GET /api/system-status

**System information endpoint**

Response:
```json
{
  "success": true,
  "status": {
    "initialized": true,
    "statistics": {
      "total_events": 3408,
      "total_chunks": 6466,
      "embedding_dimension": 384
    },
    "capabilities": [...]
  }
}
```

---

## 🔧 Configuration

### Server Settings

Edit `web_rag_interface.py` to customize:

```python
if __name__ == '__main__':
    # ...
    app.run(
        debug=True,           # Debug mode
        host='0.0.0.0',       # Bind to all interfaces
        port=5000,            # Change port here
        threaded=True         # Enable threading
    )
```

### Common Ports

- 5000: Default
- 8000: Alternative
- 3000: Another option

---

## 🐛 Troubleshooting

### Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Change port in web_rag_interface.py
# Or kill the process:
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Flask Not Found

**Error**: `ModuleNotFoundError: No module named 'flask'`

**Solution**:
```bash
pip install flask
```

### RAG System Not Initializing

**Error**: `RAG System not initialized`

**Solution**:
- Check if `complete_rag_system.py` exists
- Verify SQLite database exists (`event_intelligence.db`)
- Check if Chroma vector_db folder exists
- Run: `python complete_rag_system.py` to verify

### Slow Queries

**Performance**: Queries taking >5 seconds

**Solutions**:
- Server is processing - normal for first query (model loading)
- Use specific filters (priority, component)
- Try fewer/simpler queries
- Check internet connection (for model downloads)

### No Results Returned

**Issue**: Empty answers

**Solutions**:
- Try different keywords
- Check quality badge (if <30%, context limited)
- Ensure query is relevant to May-November 2025
- Use component ID or priority filter

---

## 📈 Advanced Usage

### Curl Examples

**Single Query**:
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What critical alarms from component 103?"}'
```

**Batch Query**:
```bash
curl -X POST http://localhost:5000/api/batch-query \
  -H "Content-Type: application/json" \
  -d '{"queries": ["Query 1?", "Query 2?"]}'
```

**System Status**:
```bash
curl http://localhost:5000/api/system-status
```

### Python Integration

```python
import requests

# Query the API
response = requests.post(
    'http://localhost:5000/api/query',
    json={'query': 'What critical alarms from component 103?'}
)

result = response.json()
print(result['answer'])
print(f"Confidence: {result['confidence']}%")
```

---

## 📚 Dataset Information

**Events**: 3,408 operational incidents  
**Text Chunks**: 6,466 semantic chunks  
**Time Period**: May - November 2025  
**Components**: 10+ system components  
**Priority Levels**: Critical, High, Low  
**Embedding Model**: sentence-transformers/all-MiniLM-L6-v2  
**Embedding Dimension**: 384

---

## [OK] Verification

### After Starting

- [ ] Web interface opens at `http://localhost:5000`
- [ ] "System Active" indicator appears
- [ ] Query input box is responsive
- [ ] Suggestions load below input
- [ ] Tabs switch correctly
- [ ] Example queries return results

### First Query

```
Try: "What critical alarms from component 103?"
Expected: Should return results with 80%+ confidence
Result should show component 103 in metadata tags
```

---

## 📞 Support

If experiencing issues:

1. Check browser console for errors (F12)
2. Check terminal output for server errors
3. Verify all dependencies installed
4. Check if RAG system initialized correctly
5. Try system-status endpoint

---

## 🎉 You're Ready!

The web interface is ready to use. Start querying your operational event data!

For more information, see:
- [README.md](README.md) - System overview
- [STEP6_COMPLETE_DOCUMENTATION.md](STEP6_COMPLETE_DOCUMENTATION.md) - RAG details
- [complete_rag_system.py](complete_rag_system.py) - Python API
