"""
Retrieval API Module
Clean interface for all retrieval strategies with formatting
"""

import chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import sqlite3
import re

PROJECT_DIR = Path(__file__).parent
VECTOR_DB_PATH = PROJECT_DIR / 'vector_db'
DB_FILE = PROJECT_DIR / 'event_intelligence.db'

class EventRetriever:
    """Simple, production-ready retriever for event RAG"""
    
    def __init__(self, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2'):
        """Initialize retriever"""
        self.model = SentenceTransformer(model_name)
        self.client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
        self.collection = self.client.get_collection(name="event_embeddings")
        self.sql_conn = sqlite3.connect(str(DB_FILE))
        self.sql_conn.row_factory = sqlite3.Row
    
    def retrieve(self, query: str, k: int = 5, 
                priority_filter: Optional[str] = None,
                component_filter: Optional[int] = None) -> List[Dict]:
        """
        Retrieve top-k chunks using semantic search with optional filtering
        
        Args:
            query: Search query
            k: Number of chunks to retrieve
            priority_filter: Filter by priority (Critical, High, Low)
            component_filter: Filter by component ID
            
        Returns:
            List of retrieved chunks with metadata
        """
        # Build filters
        filters = None
        if priority_filter or component_filter:
            conditions = []
            if priority_filter:
                conditions.append({"priority": {"$eq": priority_filter}})
            if component_filter:
                conditions.append({"component_id": {"$eq": component_filter}})
            
            if len(conditions) == 1:
                filters = conditions[0]
            else:
                filters = {"$and": conditions}
        
        # Query vector database
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=filters,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results with enhanced context and confidence
        retrieved = []
        similarities = []
        
        for doc, metadata, distance in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ):
            similarity_score = round(1 - distance, 4)
            similarities.append(similarity_score)
            
            # Calculate confidence score
            # Higher similarity = higher confidence
            if similarity_score > 0.6:
                confidence = 'HIGH'
                confidence_pct = 90
            elif similarity_score > 0.4:
                confidence = 'MEDIUM'
                confidence_pct = 70
            else:
                confidence = 'LOW'
                confidence_pct = 50
            
            retrieved.append({
                'text': doc,
                'alarm_id': metadata['alarm_id'],
                'priority': metadata['priority'],
                'component_id': int(metadata.get('component_id', 0)),
                'similarity': similarity_score,
                'similarity_percentage': round(similarity_score * 100, 1),
                'confidence_level': confidence,
                'confidence_percentage': confidence_pct,
                'month': metadata.get('month'),
                'alarm_name': metadata.get('alarm_name'),
                'category': metadata.get('category_name'),
                'device': metadata.get('device_type'),
                'chunk_sequence': metadata.get('chunk_sequence'),
                'total_chunks': metadata.get('total_chunks'),
                'location': metadata.get('location'),
                'agency': metadata.get('agency'),
                'escalation_level': metadata.get('escalation_level'),
                'related_events': metadata.get('related_events'),
            })
        
        return retrieved
    
    def retrieve_with_expansion(self, query: str, k: int = 5,
                               priority_filter: Optional[str] = None) -> List[Dict]:
        """
        Retrieve with context expansion for multi-chunk events
        Returns core results plus adjacent chunks for complete context
        """
        # Get core results
        core_results = self.retrieve(query, k=k, priority_filter=priority_filter)
        
        expanded = core_results.copy()
        
        # For each multi-chunk event, get full context
        for result in core_results:
            if result['total_chunks'] and result['total_chunks'] > 1:
                remaining_seq = list(range(1, result['total_chunks'] + 1))
                remaining_seq.remove(result['chunk_sequence'])
                
                for seq in remaining_seq:
                    context_results = self.collection.query(
                        query_texts=["context"],
                        n_results=1,
                        where={
                            "$and": [
                                {"alarm_id": {"$eq": result['alarm_id']}},
                                {"chunk_sequence": {"$eq": seq}}
                            ]
                        },
                        include=["documents", "metadatas"]
                    )
                    
                    if context_results['documents'][0]:
                        meta = context_results['metadatas'][0][0]
                        expanded.append({
                            'text': context_results['documents'][0][0],
                            'alarm_id': result['alarm_id'],
                            'priority': result['priority'],
                            'component_id': result['component_id'],
                            'similarity': 0,
                            'is_context': True,
                            'chunk_sequence': seq,
                            'total_chunks': result['total_chunks'],
                        })
        
        return expanded
    
    def search_by_priority(self, priority: str, k: int = 10) -> List[Dict]:
        """Get top alarms by priority"""
        return self.retrieve("alarm incident event", k=k, 
                           priority_filter=priority)
    
    def search_by_component(self, component_id: int, k: int = 10) -> List[Dict]:
        """Get top alarms for specific component"""
        return self.retrieve("component malfunction alert", k=k,
                           component_filter=component_id)
    
    def format_for_llm(self, results: List[Dict], 
                       include_metadata: bool = True) -> str:
        """
        Format retrieved chunks for LLM context
        
        Args:
            results: Retrieved chunks
            include_metadata: Whether to include metadata in output
            
        Returns:
            Formatted context string
        """
        context = "=== RETRIEVED EVENT CONTEXT ===\n\n"
        
        for i, result in enumerate(results, 1):
            is_context = result.get('is_context', False)
            marker = "[SUPPORTING]" if is_context else "[PRIMARY]"
            
            context += f"{marker} Result {i}:\n"
            context += result['text'] + "\n"
            
            if include_metadata:
                seq_info = ""
                if result.get('chunk_sequence'):
                    seq_info = f" [{result['chunk_sequence']}/{result.get('total_chunks', '?')}]"
                
                context += f"\n--- Metadata: Alarm #{result['alarm_id']}, "
                context += f"{result['priority']}, Component {result['component_id']}"
                context += seq_info + " ---\n"
            
            context += "\n"
        
        return context
    
    def close(self):
        """Clean up resources"""
        if self.sql_conn:
            self.sql_conn.close()


def quick_demo():
    """Quick demonstration of retriever API"""
    retriever = EventRetriever()
    
    print("=" * 70)
    print("EVENT RETRIEVER API - QUICK DEMO")
    print("=" * 70)
    
    # Test 1: Basic retrieval
    print("\n1. Basic Semantic Search")
    print("-" * 70)
    query = "critical fire emergency"
    results = retriever.retrieve(query, k=3)
    for result in results:
        print(f"Alarm #{result['alarm_id']} | {result['priority']} | "
              f"Similarity: {result['similarity']}")
        print(f"  {result['text'][:80]}...\n")
    
    # Test 2: Filtered search
    print("\n2. Critical Alarms from Component 103")
    print("-" * 70)
    results = retriever.retrieve(
        "component malfunction",
        k=3,
        priority_filter="Critical",
        component_filter=103
    )
    for result in results:
        print(f"Alarm #{result['alarm_id']} | Component {result['component_id']}")
        print(f"  {result['text'][:80]}...\n")
    
    # Test 3: With context expansion
    print("\n3. Multi-Chunk Event with Context")
    print("-" * 70)
    results = retriever.retrieve_with_expansion("critical alarm", k=2)
    for result in results:
        marker = "[CONTEXT]" if result.get('is_context') else "[RESULT]"
        seq = f" [{result.get('chunk_sequence', '?')}/{result.get('total_chunks', '?')}]" \
              if result.get('chunk_sequence') else ""
        print(f"{marker} Alarm #{result['alarm_id']}{seq}")
        print(f"  {result['text'][:80]}...\n")
    
    # Test 4: Format for LLM
    print("\n4. LLM Context Formatting")
    print("-" * 70)
    results = retriever.retrieve("water leakage high priority", k=2)
    llm_context = retriever.format_for_llm(results)
    print(llm_context)
    
    retriever.close()
    print("[OK] Demo Complete!")


if __name__ == '__main__':
    quick_demo()
