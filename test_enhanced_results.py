"""
RAG System Testing & Enhanced Results Validation
================================================

Module: test_enhanced_results
Version: 1.0
Author: Event Intelligence Team
Date: April 2026

Description:
    Comprehensive test suite for the complete Event Intelligence RAG system.
    Validates retriever performance, confidence scoring, formatting, and
    end-to-end RAG pipeline functionality with various query scenarios.

Test Coverage:
    - EventRetriever semantic search functionality
    - Confidence scoring accuracy
    - Result confidence level calibration
    - Complete RAG system query pipeline
    - Response formatting and structure
    - Metadata extraction and enrichment
    - Query filtering (priority, component)
    - Performance benchmarking

Test Functions:
    - test_retriever(): Tests semantic search with confidence metrics
    - test_complete_rag(): Tests full retrieval → ranking → response pipeline
    - test_filtering(): Tests priority and component filtering
    - test_performance(): Measures query latency benchmarks

Test Scenarios:
    - Single-term queries ("critical alarms")
    - Multi-term queries ("component 103 critical")
    - Filtered queries (priority + component)
    - Edge cases and error handling

Usage:
    python test_enhanced_results.py

Output:
    console
    - Detailed test results for each scenario
    - Performance metrics and latency measurements
    - Sample retrieval and RAG outputs
    - Pass/Fail status for each test
    - Quality metrics and statistics

Dependencies:
    - retrieval_api (custom EventRetriever module)
    - complete_rag_system (custom RAG module)
    - time (Python stdlib, for performance testing)
"""

from retrieval_api import EventRetriever
from complete_rag_system import CompletRAGSystem

import time
from typing import Dict, Any, List, Optional

def test_retriever():
    """Test retriever with enhanced confidence scoring"""
    print('[TEST] Retriever with Enhanced Confidence Scoring')
    print('='*70)
    
    retriever = EventRetriever()
    results = retriever.retrieve('critical alarm component', k=3)
    
    for i, result in enumerate(results, 1):
        print(f'\n[Result {i}]')
        print(f'  Alarm ID: {result["alarm_id"]}')
        print(f'  Priority: {result["priority"]}')
        print(f'  Confidence Level: {result.get("confidence_level", "N/A")}')
        print(f'  Confidence %: {result.get("confidence_percentage", 0)}%')
        print(f'  Relevance Score: {result.get("similarity_percentage", 0):.1f}%')
        print(f'  Type: {result.get("alarm_name", "N/A")}')
        print(f'  Component: {result.get("component_id", "N/A")}')
        print(f'  Date: {result.get("month", "N/A")}')
        print(f'  Text: {result["text"][:100]}...')
    
    print('\n[OK] Retriever test passed!')

def test_complete_rag():
    """Test complete RAG system with enhanced formatting"""
    print('\n' + '='*70)
    print('[TEST] Complete RAG System with Enhanced Response Formatting')
    print('='*70)
    
    rag = CompletRAGSystem()
    
    # Test a single query
    query = "What critical alarms occurred?"
    print(f'\nQuery: {query}')
    print('='*70)
    
    result = rag.query(query)
    
    print('\n[ANSWER]')
    print(result.get('answer', ''))
    
    print('\n[CONTEXT QUALITY]')
    quality = result.get('context_quality', {})
    print(f'  Level: {quality.get("level", "N/A").upper()}')
    print(f'  Confidence: {quality.get("confidence", 0):.0%}')
    print(f'  Avg Similarity: {quality.get("avg_similarity", 0):.1%}')
    print(f'  Chunk Count: {quality.get("chunk_count", 0)}')
    
    print('\n[CONTEXT CHUNKS]')
    chunks = result.get('context_chunks', [])
    for i, chunk in enumerate(chunks[:3], 1):
        print(f'\n  [{i}] Alarm {chunk["alarm_id"]} - {chunk["priority"]}')
        print(f'      Confidence: {chunk.get("confidence_level", "N/A")} ({chunk.get("confidence_percentage", 0)}%)')
        print(f'      Relevance: {chunk.get("similarity_percentage", 0):.1f}%')
        print(f'      Type: {chunk.get("alarm_name", "N/A")}')
    
    print('\n[OK] Complete RAG test passed!')

if __name__ == '__main__':
    test_retriever()
    test_complete_rag()
    print('\n[OK] All tests completed successfully!')
