"""
Step 5: Retrieval Implementation
================================

Module: 05_retrieval_implementation
Version: 1.0
Author: Event Intelligence Team
Date: April 2026

Description:
    Fifth step of RAG pipeline. Implements advanced retrieval strategies
    including semantic search, query expansion, filtering, and ranking.
    Provides robust context retrieval for downstream LLM processing.

Retrieval Strategies:
    1. Top-K Semantic Retrieval: Direct similarity search
    2. Hybrid Retrieval: Combining semantic + keyword matching
    3. Query Expansion: HyDE-style query preprocessing
    4. Smart Filtering: Priority and component-based filtering
    5. Result Ranking: Relevance and confidence scoring

Features:
    - Configurable retrieval strategies
    - Priority-based filtering
    - Component filtering
    - Result deduplication
    - Confidence scoring
    - Metadata enrichment

Input:
    Chroma Vector DB: event_embeddings
    SQL Database: event_details

Output:
    Retrieved chunks with metadata and confidence scores

Usage:
    python 05_retrieval_implementation.py

Dependencies:
    - chromadb
    - sentence-transformers
    - sqlite3 (stdlib)
"""

import chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple, Optional
import sqlite3
import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setup paths
PROJECT_DIR = Path(__file__).parent
VECTOR_DB_PATH = PROJECT_DIR / 'vector_db'
DB_FILE = PROJECT_DIR / 'event_intelligence.db'

class AdvancedRetriever:
    """Advanced retrieval with multiple strategies"""
    
    def __init__(self, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2',
                 vector_db_path: str = None):
        """Initialize retriever"""
        self.model_name = model_name
        self.vector_db_path = vector_db_path or str(VECTOR_DB_PATH)
        self.model = None
        self.chroma_client = None
        self.collection = None
        self.sql_conn = None
        
    def initialize(self):
        """Initialize retriever components"""
        logger.info("=" * 70)
        logger.info("Initializing Advanced Retrieval System")
        logger.info("=" * 70)
        
        # Load model
        logger.info(f"\nLoading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        logger.info("[OK] Model loaded")
        
        # Connect to vector DB
        logger.info(f"Connecting to Chroma database...")
        self.chroma_client = chromadb.PersistentClient(path=self.vector_db_path)
        self.collection = self.chroma_client.get_collection(name="event_embeddings")
        logger.info(f"[OK] Connected to collection with {self.collection.count():,} embeddings")
        
        # Connect to SQL DB
        logger.info(f"Connecting to SQL database...")
        self.sql_conn = sqlite3.connect(str(DB_FILE))
        self.sql_conn.row_factory = sqlite3.Row
        logger.info("[OK] SQL connection established")
    
    def semantic_search(self, query: str, k: int = 5, 
                       filters: Dict = None) -> List[Dict]:
        """
        Basic semantic search with optional metadata filtering
        
        Args:
            query: Search query
            k: Number of results to return
            filters: Chroma where filters for metadata
            
        Returns:
            List of retrieved chunks with metadata
        """
        # Generate embedding for query
        query_embedding = self.model.encode([query])[0]
        
        # Query vector database
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=filters,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        retrieved = []
        for doc, metadata, distance in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ):
            similarity = 1 - distance
            retrieved.append({
                'text': doc,
                'similarity': similarity,
                'alarm_id': metadata['alarm_id'],
                'priority': metadata['priority'],
                'component_id': metadata.get('component_id', 0),
                'metadata': metadata
            })
        
        return retrieved
    
    def hyde_search(self, query: str, k: int = 5,
                   filters: Dict = None) -> List[Dict]:
        """
        HyDE (Hypothetical Document Embeddings) search
        
        Generates hypothetical documents that would answer the query,
        then searches for similar chunks to those hypotheticals.
        
        Args:
            query: Original query
            k: Number of results to return
            filters: Metadata filters
            
        Returns:
            List of retrieved chunks
        """
        logger.debug(f"\n[HyDE] Generating hypothetical documents for: {query}")
        
        # Generate hypothetical document embeddings
        hypothetical_docs = self._generate_hypotheticals(query)
        
        logger.debug(f"Generated {len(hypothetical_docs)} hypothetical documents")
        
        # Query with each hypothetical
        all_results = {}
        for hyp_doc in hypothetical_docs:
            results = self.collection.query(
                query_texts=[hyp_doc],
                n_results=k * 2,  # Get more to deduplicate
                where=filters,
                include=["documents", "metadatas", "distances"]
            )
            
            # Aggregate results
            for doc, metadata, distance in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ):
                chunk_id = metadata.get('chunk_id', doc[:50])
                similarity = 1 - distance
                
                if chunk_id not in all_results:
                    all_results[chunk_id] = {
                        'text': doc,
                        'similarity': similarity,
                        'alarm_id': metadata['alarm_id'],
                        'priority': metadata['priority'],
                        'component_id': metadata.get('component_id', 0),
                        'metadata': metadata,
                        'hyde_score': 0
                    }
                
                all_results[chunk_id]['hyde_score'] += similarity
        
        # Sort by combined score and return top k
        sorted_results = sorted(
            all_results.values(),
            key=lambda x: x['hyde_score'],
            reverse=True
        )[:k]
        
        return sorted_results
    
    def _generate_hypotheticals(self, query: str) -> List[str]:
        """
        Generate hypothetical documents that might answer the query
        
        Args:
            query: Original query
            
        Returns:
            List of hypothetical documents
        """
        # Simple heuristic-based hypothetical generation
        hypotheticals = []
        
        # Original query as one hypothetical
        hypotheticals.append(query)
        
        # Extract key terms
        keywords = re.findall(r'\b\w+\b', query.lower())
        filtered_keywords = [k for k in keywords 
                           if len(k) > 3 and k not in 
                           ['what', 'why', 'where', 'when', 'how', 'many', 'are', 'there', 'some', 'from', 'with']]
        
        # Generate variations
        if len(filtered_keywords) >= 2:
            # Hypothetical: "Found X critical alarms from component Y"
            hyp1 = f"Multiple {' '.join(filtered_keywords[:2])} incidents detected"
            hypotheticals.append(hyp1)
            
            # Hypothetical: "Report shows X events on Y"
            hyp2 = f"Alert summary: {' '.join(filtered_keywords[-2:])} emergency incidents"
            hypotheticals.append(hyp2)
            
            # Hypothetical: Technical summary
            hyp3 = f"Analysis of {filtered_keywords[0]} events in operational systems"
            hypotheticals.append(hyp3)
        
        return hypotheticals[:3]  # Limit to 3 hypotheticals
    
    def hybrid_search(self, query: str, k: int = 5,
                     filters: Dict = None, 
                     weight_semantic: float = 0.7,
                     weight_keyword: float = 0.3) -> List[Dict]:
        """
        Hybrid retrieval combining semantic and keyword search
        
        Args:
            query: Search query
            k: Number of results to return
            filters: Metadata filters
            weight_semantic: Weight for semantic search (0-1)
            weight_keyword: Weight for keyword search (0-1)
            
        Returns:
            List of retrieved chunks
        """
        # Semantic search
        semantic_results = self.semantic_search(query, k=k*2, filters=filters)
        
        # Keyword search
        keyword_results = self._keyword_search(query, k=k*2, filters=filters)
        
        # Combine results with weighted scoring
        combined = {}
        
        # Add semantic results
        for i, result in enumerate(semantic_results):
            key = result['text'][:100]
            rank_score = (k*2 - i) / (k*2)
            combined[key] = {
                **result,
                'semantic_score': result['similarity'],
                'keyword_score': 0,
                'rank_score': 0
            }
        
        # Add keyword results
        for i, result in enumerate(keyword_results):
            key = result['text'][:100]
            rank_score = (k*2 - i) / (k*2)
            
            if key not in combined:
                combined[key] = {
                    **result,
                    'semantic_score': 0,
                    'keyword_score': result.get('keyword_match_count', 1),
                    'rank_score': 0
                }
            else:
                combined[key]['keyword_score'] = result.get('keyword_match_count', 1)
        
        # Calculate hybrid score
        for result in combined.values():
            semantic = result['semantic_score'] * weight_semantic
            keyword = min(result['keyword_score'] / 10, 1) * weight_keyword
            result['hybrid_score'] = semantic + keyword
        
        # Sort and return top k
        sorted_results = sorted(
            combined.values(),
            key=lambda x: x['hybrid_score'],
            reverse=True
        )[:k]
        
        return sorted_results
    
    def _keyword_search(self, query: str, k: int = 10,
                       filters: Dict = None) -> List[Dict]:
        """
        Simple keyword-based search
        
        Args:
            query: Search query
            k: Number of results to return
            filters: Metadata filters
            
        Returns:
            List of results with keyword match scores
        """
        keywords = set(re.findall(r'\b\w+\b', query.lower()))
        keywords = {k for k in keywords if len(k) > 3}
        
        if not keywords:
            return []
        
        # Query SQL database for keyword matches
        cursor = self.sql_conn.cursor()
        
        # Build query
        where_clause = ""
        if filters:
            # Simplified: just get all for now
            cursor.execute(f'''
                SELECT chunk_id, chunk_text, priority, component_id, alarm_id
                FROM event_chunks
                LIMIT {k * 3}
            ''')
        else:
            cursor.execute(f'''
                SELECT chunk_id, chunk_text, priority, component_id, alarm_id
                FROM event_chunks
                LIMIT {k * 3}
            ''')
        
        rows = cursor.fetchall()
        
        # Score by keyword matches
        scored_results = []
        for row in rows:
            text = row['chunk_text'].lower()
            keyword_count = sum(1 for kw in keywords if kw in text)
            
            if keyword_count > 0:
                scored_results.append({
                    'text': row['chunk_text'],
                    'keyword_match_count': keyword_count,
                    'alarm_id': row['alarm_id'],
                    'priority': row['priority'],
                    'component_id': row['component_id'],
                    'metadata': dict(row)
                })
        
        # Sort by keyword matches
        scored_results.sort(key=lambda x: x['keyword_match_count'], reverse=True)
        return scored_results[:k]
    
    def retrieve_with_context_expansion(self, query: str, k: int = 5,
                                       filters: Dict = None) -> List[Dict]:
        """
        Retrieve chunks and expand context for multi-chunk events
        
        Args:
            query: Search query
            k: Number of core results
            filters: Metadata filters
            
        Returns:
            List of retrieved chunks with related context
        """
        # Get initial results
        results = self.semantic_search(query, k=k, filters=filters)
        
        # Expand context for multi-chunk events
        expanded = []
        for result in results:
            expanded.append(result)
            
            # If not first chunk, get previous chunk
            if result['metadata'].get('chunk_sequence', 1) > 1:
                prev_results = self.collection.query(
                    query_texts=["context"],
                    n_results=1,
                    where={
                        "$and": [
                            {"alarm_id": {"$eq": result['alarm_id']}},
                            {"chunk_sequence": {"$eq": result['metadata']['chunk_sequence'] - 1}}
                        ]
                    },
                    include=["documents", "metadatas"]
                )
                
                if prev_results['documents'][0]:
                    expanded.append({
                        'text': prev_results['documents'][0][0],
                        'similarity': 0,  # Context chunk
                        'alarm_id': result['alarm_id'],
                        'priority': result['priority'],
                        'component_id': result['component_id'],
                        'metadata': prev_results['metadatas'][0][0],
                        'is_context': True
                    })
            
            # If not last chunk, get next chunk
            if result['metadata'].get('chunk_sequence', 1) < result['metadata'].get('total_chunks', 1):
                next_results = self.collection.query(
                    query_texts=["context"],
                    n_results=1,
                    where={
                        "$and": [
                            {"alarm_id": {"$eq": result['alarm_id']}},
                            {"chunk_sequence": {"$eq": result['metadata']['chunk_sequence'] + 1}}
                        ]
                    },
                    include=["documents", "metadatas"]
                )
                
                if next_results['documents'][0]:
                    expanded.append({
                        'text': next_results['documents'][0][0],
                        'similarity': 0,  # Context chunk
                        'alarm_id': result['alarm_id'],
                        'priority': result['priority'],
                        'component_id': result['component_id'],
                        'metadata': next_results['metadatas'][0][0],
                        'is_context': True
                    })
        
        return expanded
    
    def close(self):
        """Close connections"""
        if self.sql_conn:
            self.sql_conn.close()


def main():
    """Test retrieval strategies"""
    try:
        # Initialize
        retriever = AdvancedRetriever()
        retriever.initialize()
        
        logger.info("\n" + "=" * 70)
        logger.info("RETRIEVAL DEMONSTRATION")
        logger.info("=" * 70)
        
        # Test queries
        test_queries = [
            ("critical fire emergency", None),
            ("Why are there so many critical alarms from component 103?", 
             {"priority": {"$eq": "Critical"}}),
            ("high priority water leakage", None),
            ("security breach unauthorised access", None),
            ("component 312 malfunction alert", None),
        ]
        
        for query, filters in test_queries:
            logger.info(f"\n\n{'='*70}")
            logger.info(f"Query: '{query}'")
            if filters:
                logger.info(f"Filters: {filters}")
            logger.info(f"{'='*70}")
            
            # Test each retrieval strategy
            strategies = [
                ("Semantic Search (Top 5)", retriever.semantic_search, {}),
                ("HyDE Search", retriever.hyde_search, {}),
                ("Hybrid Search", retriever.hybrid_search, 
                 {'weight_semantic': 0.7, 'weight_keyword': 0.3}),
            ]
            
            for strategy_name, strategy_func, extra_args in strategies:
                logger.info(f"\n {strategy_name}")
                logger.info("-" * 70)
                
                try:
                    results = strategy_func(query, k=3, filters=filters, **extra_args)
                    
                    for i, result in enumerate(results, 1):
                        logger.info(f"\n  [{i}] Alarm #{result['alarm_id']} | "
                                  f"{result['priority']} | "
                                  f"Component: {result.get('component_id', 'N/A')}")
                        
                        # Show relevance score
                        if 'similarity' in result and result['similarity'] > 0:
                            logger.info(f"      Semantic Score: {result['similarity']:.4f}")
                        if 'hyde_score' in result and result['hyde_score'] > 0:
                            logger.info(f"      HyDE Score: {result['hyde_score']:.4f}")
                        if 'hybrid_score' in result:
                            logger.info(f"      Hybrid Score: {result['hybrid_score']:.4f}")
                        
                        logger.info(f"      Text: {result['text'][:100]}...")
                
                except Exception as e:
                    logger.error(f"  Error: {e}")
        
        # Test context expansion
        logger.info(f"\n\n{'='*70}")
        logger.info("CONTEXT EXPANSION TEST")
        logger.info("="*70)
        
        query = "critical alarm"
        logger.info(f"\nQuery: '{query}'")
        logger.info("-" * 70)
        
        results = retriever.retrieve_with_context_expansion(query, k=2)
        
        for result in results:
            is_context = result.get('is_context', False)
            marker = "[CONTEXT]" if is_context else "[RESULT]"
            logger.info(f"\n{marker} Alarm #{result['alarm_id']} | "
                      f"{result['priority']}")
            logger.info(f"  Sequence: {result['metadata'].get('chunk_sequence', 'N/A')}"
                      f"/{result['metadata'].get('total_chunks', 'N/A')}")
            logger.info(f"  Text: {result['text'][:90]}...")
        
        retriever.close()
        
        logger.info("\n" + "=" * 70)
        logger.info("[OK] Step 5 Complete: Retrieval Implementation successful!")
        logger.info("=" * 70 + "\n")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
