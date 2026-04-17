"""
Web Interface for Event Intelligence RAG System
Provides a Flask-based web application for querying the RAG system
"""

import json
import logging
from flask import Flask, render_template, request, jsonify
from complete_rag_system import CompletRAGSystem
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Global RAG system instance
rag_system = None

def init_rag_system():
    """Initialize the RAG system on app startup"""
    global rag_system
    try:
        logger.info("Initializing RAG System...")
        rag_system = CompletRAGSystem()
        logger.info("RAG System initialized successfully!")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize RAG System: {e}")
        return False

@app.route('/')
def index():
    """Serve the main interface page"""
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def query_rag():
    """
    API endpoint for querying the RAG system
    
    Request JSON:
    {
        "query": "What critical alarms from component 103?",
        "priority_filter": "Critical",  # Optional
        "component_filter": 103         # Optional
    }
    
    Response JSON with enhanced formatting:
    {
        "success": true,
        "query": "...",
        "answer": "...",
        "status": "success",
        "context_quality": "good",
        "overall_confidence": 80,
        "context_details": [{
            "alarm_id": "ALM-001",
            "priority": "Critical",
            "confidence_level": "HIGH",
            "confidence_percentage": 90,
            "relevance_score": 85.5,
            "text": "...",
            "metadata": {...}
        }],
        "summary": {
            "total_events": 5,
            "components": [103, 201],
            "priorities": {"Critical": 3, "High": 2},
            "time_periods": ["May-2025"]
        }
    }
    """
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query cannot be empty'
            }), 400
        
        if not rag_system:
            return jsonify({
                'success': False,
                'error': 'RAG System not initialized'
            }), 500
        
        logger.info(f"Processing query: {query}")
        
        # Execute query
        result = rag_system.query(query)
        
        # Extract context chunks with enhanced metadata
        context_chunks = result.get('context_chunks', [])
        context_details = []
        
        for chunk in context_chunks:
            context_details.append({
                'alarm_id': chunk.get('alarm_id'),
                'priority': chunk.get('priority'),
                'confidence_level': chunk.get('confidence_level', 'N/A'),
                'confidence_percentage': chunk.get('confidence_percentage', 0),
                'relevance_score': chunk.get('similarity_percentage', 0),
                'alarm_type': chunk.get('alarm_name'),
                'component_id': chunk.get('component_id'),
                'device_type': chunk.get('device'),
                'category': chunk.get('category'),
                'date': chunk.get('month'),
                'location': chunk.get('location'),
                'agency': chunk.get('agency'),
                'text': chunk.get('text'),
                'total_chunks': chunk.get('total_chunks'),
                'chunk_sequence': chunk.get('chunk_sequence')
            })
        
        # Extract quality info
        context_quality = result.get('context_quality', {})
        
        # Build summary
        priorities = {}
        components = set()
        for chunk in context_chunks:
            p = chunk.get('priority')
            if p:
                priorities[p] = priorities.get(p, 0) + 1
            c = chunk.get('component_id')
            if c:
                components.add(c)
        
        summary = {
            'total_events': len(context_chunks),
            'components': sorted(list(components)),
            'priority_distribution': priorities,
            'average_confidence': round(sum(c.get('confidence_percentage', 0) for c in context_details) / len(context_details) if context_details else 0),
            'average_relevance': round(sum(c.get('relevance_score', 0) for c in context_details) / len(context_details) if context_details else 0)
        }
        
        # Format response with full context
        response = {
            'success': True,
            'query': query,
            'answer': result.get('answer', ''),
            'status': result.get('status', 'unknown'),
            'context_quality': context_quality.get('level', 'unknown'),
            'overall_confidence': int(context_quality.get('confidence', 0) * 100),
            'context_details': context_details,
            'summary': summary,
            'sources': result.get('sources', [])
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Query processing error: {e}")
        return jsonify({
            'success': False,
            'error': f'Error processing query: {str(e)}'
        }), 500

@app.route('/api/batch-query', methods=['POST'])
def batch_query():
    """
    API endpoint for batch queries with enhanced formatting
    
    Request JSON:
    {
        "queries": [
            "What critical alarms from component 103?",
            "How many fire emergencies in May?"
        ]
    }
    
    Response JSON with full context and confidence:
    {
        "success": true,
        "total_queries": 2,
        "batch_summary": {
            "total_events_found": 25,
            "average_confidence": 82,
            "average_relevance": 78.5
        },
        "results": [
            {
                "query": "...",
                "status": "success",
                "answer": "...",
                "context_details": [...],
                "summary": {...}
            }
        ]
    }
    """
    try:
        data = request.get_json()
        queries = data.get('queries', [])
        
        if not queries:
            return jsonify({
                'success': False,
                'error': 'No queries provided'
            }), 400
        
        if len(queries) > 20:
            return jsonify({
                'success': False,
                'error': 'Maximum 20 queries allowed per batch'
            }), 400
        
        if not rag_system:
            return jsonify({
                'success': False,
                'error': 'RAG System not initialized'
            }), 500
        
        logger.info(f"Processing batch of {len(queries)} queries")
        
        # Execute batch queries
        batch_results = rag_system.batch_query(queries)
        
        # Format results with enhanced context
        formatted_results = []
        total_events = 0
        confidences = []
        relevances = []
        
        for result in batch_results:
            context_chunks = result.get('context_chunks', [])
            context_quality = result.get('context_quality', {})
            
            # Build context details
            context_details = []
            for chunk in context_chunks:
                context_details.append({
                    'alarm_id': chunk.get('alarm_id'),
                    'priority': chunk.get('priority'),
                    'confidence_level': chunk.get('confidence_level', 'N/A'),
                    'confidence_percentage': chunk.get('confidence_percentage', 0),
                    'relevance_score': chunk.get('similarity_percentage', 0),
                    'alarm_type': chunk.get('alarm_name'),
                    'component_id': chunk.get('component_id'),
                    'date': chunk.get('month'),
                    'text': chunk.get('text')[:150] + '...' if chunk.get('text') else ''
                })
            
            # Build summary for this result
            priorities = {}
            for chunk in context_chunks:
                p = chunk.get('priority')
                if p:
                    priorities[p] = priorities.get(p, 0) + 1
            
            summary = {
                'total_events': len(context_chunks),
                'priority_distribution': priorities,
                'average_confidence': round(sum(c.get('confidence_percentage', 0) for c in context_details) / len(context_details) if context_details else 0),
                'average_relevance': round(sum(c.get('relevance_score', 0) for c in context_details) / len(context_details) if context_details else 0)
            }
            
            formatted_result = {
                'query': result.get('question', ''),
                'status': result.get('status', 'unknown'),
                'answer': result.get('answer', ''),
                'context_quality': context_quality.get('level', 'unknown'),
                'overall_confidence': int(context_quality.get('confidence', 0) * 100),
                'context_details': context_details,
                'summary': summary
            }
            
            formatted_results.append(formatted_result)
            
            # Aggregate stats
            total_events += len(context_chunks)
            confidences.append(context_quality.get('confidence', 0) * 100)
            for chunk in context_chunks:
                relevances.append(chunk.get('similarity_percentage', 0))
        
        # Batch summary
        batch_summary = {
            'total_events_found': total_events,
            'average_confidence': round(sum(confidences) / len(confidences) if confidences else 0),
            'average_relevance': round(sum(relevances) / len(relevances) if relevances else 0),
            'queries_successful': sum(1 for r in formatted_results if r['status'] == 'success')
        }
        
        return jsonify({
            'success': True,
            'total_queries': len(queries),
            'batch_summary': batch_summary,
            'results': formatted_results
        }), 200
        
    except Exception as e:
        logger.error(f"Batch query processing error: {e}")
        return jsonify({
            'success': False,
            'error': f'Error processing batch: {str(e)}'
        }), 500

@app.route('/api/search', methods=['GET'])
def search():
    """
    API endpoint for quick search suggestions
    
    Query parameters:
    - q: search term (optional)
    
    Returns suggestions based on available data
    """
    try:
        search_term = request.args.get('q', '').lower()
        
        # Sample suggestions based on data
        suggestions = {
            'components': [100, 103, 311, 312, 313, 315, 319],
            'priorities': ['Critical', 'High', 'Low'],
            'event_types': [
                'Fire Emergency',
                'Water Leakage',
                'Building Security Malfunction',
                'ADAS Event',
                'Driver Not Identified'
            ],
            'time_periods': [
                'May 2025', 'June 2025', 'July 2025', 'August 2025',
                'September 2025', 'October 2025', 'November 2025'
            ]
        }
        
        # Filter based on search term
        if search_term:
            filtered_suggestions = {}
            for key, values in suggestions.items():
                filtered_suggestions[key] = [
                    v for v in values 
                    if search_term in str(v).lower()
                ]
            suggestions = filtered_suggestions
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        }), 200
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/system-status', methods=['GET'])
def system_status():
    """
    API endpoint for system status and statistics
    
    Returns information about the RAG system
    """
    try:
        status = {
            'initialized': rag_system is not None,
            'statistics': {
                'total_events': 3408,
                'total_chunks': 6466,
                'embedding_dimension': 384,
                'model': 'sentence-transformers/all-MiniLM-L6-v2',
                'time_period': 'May - November 2025',
                'components': 10,
                'priority_levels': 3
            },
            'capabilities': [
                'Semantic search',
                'Context quality evaluation',
                'Batch query processing',
                'Priority filtering',
                'Component filtering',
                'Temporal filtering'
            ]
        }
        
        return jsonify({
            'success': True,
            'status': status
        }), 200
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/export-results', methods=['POST'])
def export_results():
    """
    API endpoint to export results
    
    Request JSON:
    {
        "results": [...],
        "format": "json"  # or "csv"
    }
    """
    try:
        data = request.get_json()
        results = data.get('results', [])
        export_format = data.get('format', 'json')
        
        if not results:
            return jsonify({
                'success': False,
                'error': 'No results to export'
            }), 400
        
        if export_format == 'json':
            filename = 'rag_export.json'
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported format: {export_format}'
            }), 400
        
        return jsonify({
            'success': True,
            'message': f'Results exported to {filename}',
            'filename': filename
        }), 200
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize RAG system
    if init_rag_system():
        logger.info("Starting Flask web interface...")
        logger.info("Open browser to http://localhost:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        logger.error("Failed to start application - RAG System initialization failed")
        exit(1)
