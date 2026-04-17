# REST API Reference

## Event Intelligence RAG System - API Documentation

Complete API reference for the Event Intelligence RAG web interface.

**Base URL**: `http://localhost:5000/api/`

---

## Endpoints

### 1. Single Query

**Endpoint**: `POST /api/query`

**Purpose**: Submit a single natural language query

**Request**:
```json
{
  "query": "What critical alarms from component 103?",
  "priority_filter": "Critical",
  "component_filter": 103
}
```

**Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| query | string | Yes | Natural language question |
| priority_filter | string | No | Critical\|High\|Low |
| component_filter | integer | No | Component ID |

**Response** (200):
```json
{
  "success": true,
  "query": "What critical alarms from component 103?",
  "answer": "Based on the operational data:\n\nComponents involved: 103, 311, 315...",
  "quality": "good",
  "confidence": 80,
  "context_chunks": 5,
  "components_found": [103, 311, 315],
  "priority_levels": ["Critical"],
  "time_periods": ["September", "July", "May"],
  "top_result": "Alarm #37764 (Critical) - Building Security Malfunction Alert...",
  "status": "success"
}
```

**Error Response** (400):
```json
{
  "success": false,
  "error": "Query cannot be empty"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What critical alarms from component 103?"
  }'
```

**Python Example**:
```python
import requests

response = requests.post(
    'http://localhost:5000/api/query',
    json={'query': 'What critical alarms from component 103?'}
)

data = response.json()
print(data['answer'])
print(f"Confidence: {data['confidence']}%")
```

---

### 2. Batch Query

**Endpoint**: `POST /api/batch-query`

**Purpose**: Submit multiple queries for processing

**Request**:
```json
{
  "queries": [
    "What critical alarms from component 103?",
    "How many fire emergencies in May?",
    "Which components had water leakage?"
  ]
}
```

**Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| queries | array | Yes | Array of query strings (max 20) |

**Response** (200):
```json
{
  "success": true,
  "total_queries": 3,
  "results": [
    {
      "query": "What critical alarms from component 103?",
      "answer": "...",
      "quality": "good",
      "confidence": 80,
      "status": "success"
    },
    {
      "query": "How many fire emergencies in May?",
      "answer": "...",
      "quality": "fair",
      "confidence": 60,
      "status": "success"
    },
    {
      "query": "Which components had water leakage?",
      "answer": "...",
      "quality": "insufficient",
      "confidence": 30,
      "status": "success"
    }
  ]
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:5000/api/batch-query \
  -H "Content-Type: application/json" \
  -d '{
    "queries": [
      "What critical alarms from component 103?",
      "How many fire emergencies in May?"
    ]
  }'
```

**Python Example**:
```python
import requests

queries = [
    "What critical alarms from component 103?",
    "How many fire emergencies in May?",
    "Which components had water leakage?"
]

response = requests.post(
    'http://localhost:5000/api/batch-query',
    json={'queries': queries}
)

data = response.json()
for result in data['results']:
    print(f"Q: {result['query']}")
    print(f"A: {result['answer']}\n")
```

---

### 3. Search Suggestions

**Endpoint**: `GET /api/search`

**Purpose**: Get search suggestions and autocomplete data

**Request**:
```
http://localhost:5000/api/search?q=fire
```

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q | string | No | Search term for filtering |

**Response** (200):
```json
{
  "success": true,
  "suggestions": {
    "components": [100, 103, 312, 313, 315],
    "priorities": ["Critical", "High", "Low"],
    "event_types": [
      "Fire Emergency",
      "Water Leakage",
      "Building Security Malfunction",
      "ADAS Event",
      "Driver Not Identified"
    ],
    "time_periods": [
      "May 2025",
      "June 2025",
      "July 2025",
      "August 2025",
      "September 2025",
      "October 2025",
      "November 2025"
    ]
  }
}
```

**cURL Example**:
```bash
# Get all suggestions
curl http://localhost:5000/api/search

# Search for "fire" related suggestions
curl http://localhost:5000/api/search?q=fire
```

**Python Example**:
```python
import requests

response = requests.get('http://localhost:5000/api/search')
suggestions = response.json()['suggestions']

print("Available components:", suggestions['components'])
print("Available priorities:", suggestions['priorities'])
```

---

### 4. System Status

**Endpoint**: `GET /api/system-status`

**Purpose**: Get system information and statistics

**Request**:
```
http://localhost:5000/api/system-status
```

**Response** (200):
```json
{
  "success": true,
  "status": {
    "initialized": true,
    "statistics": {
      "total_events": 3408,
      "total_chunks": 6466,
      "embedding_dimension": 384,
      "model": "sentence-transformers/all-MiniLM-L6-v2",
      "time_period": "May - November 2025",
      "components": 10,
      "priority_levels": 3
    },
    "capabilities": [
      "Semantic search",
      "Context quality evaluation",
      "Batch query processing",
      "Priority filtering",
      "Component filtering",
      "Temporal filtering"
    ]
  }
}
```

**cURL Example**:
```bash
curl http://localhost:5000/api/system-status
```

**Python Example**:
```python
import requests

response = requests.get('http://localhost:5000/api/system-status')
status = response.json()['status']

print("System Initialized:", status['initialized'])
print("Total Events:", status['statistics']['total_events'])
print("Capabilities:", status['capabilities'])
```

---

### 5. Export Results

**Endpoint**: `POST /api/export-results`

**Purpose**: Export query results to file

**Request**:
```json
{
  "results": [
    {
      "query": "What critical alarms from component 103?",
      "answer": "...",
      "quality": "good"
    }
  ],
  "format": "json"
}
```

**Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| results | array | Yes | Array of result objects |
| format | string | No | Export format: json\|csv (default: json) |

**Response** (200):
```json
{
  "success": true,
  "message": "Results exported to rag_export.json",
  "filename": "rag_export.json"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:5000/api/export-results \
  -H "Content-Type: application/json" \
  -d '{
    "results": [...],
    "format": "json"
  }'
```

---

## Response Formats

### Result Object

```json
{
  "query": "string",           // Original query
  "answer": "string",          // Generated answer
  "quality": "string",         // excellent|good|fair|insufficient
  "confidence": "number",      // 0-100
  "context_chunks": "number",  // Number of context chunks
  "components_found": "[array]", // Component IDs
  "priority_levels": "[array]", // Priority strings
  "time_periods": "[array]",   // Time period strings
  "top_result": "string",      // Highlighted result
  "status": "string"           // success|error
}
```

### Quality Levels

| Quality | Confidence | Similarity Range | Meaning |
|---------|-----------|------------------|---------|
| excellent | 95% | >0.5 | Highly relevant context |
| good | 80% | 0.3-0.5 | Good context available |
| fair | 60% | 0.15-0.3 | Limited context |
| insufficient | 30% | <0.15 | Very limited context |

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Query processed successfully |
| 400 | Bad Request | Missing required parameter |
| 404 | Not Found | Endpoint doesn't exist |
| 500 | Server Error | RAG system initialization failed |

### Error Response Format

```json
{
  "success": false,
  "error": "Description of error"
}
```

### Common Errors

**Empty Query**:
```json
{
  "success": false,
  "error": "Query cannot be empty"
}
```

**System Not Initialized**:
```json
{
  "success": false,
  "error": "RAG System not initialized"
}
```

**Too Many Queries**:
```json
{
  "success": false,
  "error": "Maximum 20 queries allowed per batch"
}
```

---

## Rate Limiting

No explicit rate limiting implemented, but consider:
- Max 20 queries per batch request
- Query processing time typically 100-300ms per query
- 500ms-2s with LLM generation

---

## Examples

### Example 1: Component Analysis

```python
import requests
import json

# Query component analysis
response = requests.post(
    'http://localhost:5000/api/query',
    json={
        'query': 'What happened with component 103?',
        'component_filter': 103
    }
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Quality: {result['quality']}")
print(f"Confidence: {result['confidence']}%")
```

### Example 2: Batch Analysis

```python
import requests

queries = [
    'Critical alarms?',
    'Fire emergencies in May?',
    'Water leakage issues?'
]

response = requests.post(
    'http://localhost:5000/api/batch-query',
    json={'queries': queries}
)

results = response.json()['results']

for r in results:
    print(f"{r['query']}")
    print(f"  Confidence: {r['confidence']}%")
    print(f"  Quality: {r['quality']}")
    print()
```

### Example 3: Priority Filtering

```python
import requests

response = requests.post(
    'http://localhost:5000/api/query',
    json={
        'query': 'What happened?',
        'priority_filter': 'Critical'
    }
)

result = response.json()
if result['success']:
    print(f"Critical events found: {len(result.get('priority_levels', []))}")
```

---

## Integration Examples

### JavaScript/Fetch

```javascript
const query = 'What critical alarms from component 103?';

fetch('http://localhost:5000/api/query', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({query})
})
.then(r => r.json())
.then(data => {
    console.log(data.answer);
    console.log(`Confidence: ${data.confidence}%`);
});
```

### Node.js

```javascript
const fetch = require('node-fetch');

async function queryRAG(query) {
    const response = await fetch('http://localhost:5000/api/query', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({query})
    });
    
    return await response.json();
}

queryRAG('What critical alarms from component 103?')
    .then(result => console.log(result.answer));
```

### Java

```java
import org.apache.http.client.methods.HttpPost;
import org.apache.http.entity.StringEntity;
import org.json.JSONObject;

HttpPost request = new HttpPost("http://localhost:5000/api/query");
JSONObject json = new JSONObject();
json.put("query", "What critical alarms from component 103?");

request.setEntity(new StringEntity(json.toString()));
request.setHeader("Content-Type", "application/json");

HttpResponse response = client.execute(request);
```

---

## Testing

### Test All Endpoints

```bash
# Test Query
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What critical alarms?"}'

# Test Batch Query  
curl -X POST http://localhost:5000/api/batch-query \
  -H "Content-Type: application/json" \
  -d '{"queries": ["Query 1?", "Query 2?"]}'

# Test Suggestions
curl http://localhost:5000/api/search

# Test System Status
curl http://localhost:5000/api/system-status

# Test 404
curl http://localhost:5000/api/invalid
```

---

## Notes

- All timestamps are in UTC
- Confidence levels are calculated based on semantic similarity
- Max batch size: 20 queries
- Time period covered: May - November 2025
- No authentication required (development version)

---

For web interface usage, see [WEB_INTERFACE_GUIDE.md](WEB_INTERFACE_GUIDE.md)
