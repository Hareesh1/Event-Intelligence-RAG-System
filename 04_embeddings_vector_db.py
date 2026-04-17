"""
Step 4: Embeddings & Vector Database
Generate embeddings for chunks and store in vector database for semantic search.
Uses Chroma for vector storage and sentence-transformers for embeddings.
"""

import sqlite3
import chromadb
import logging
from pathlib import Path
from sentence_transformers import SentenceTransformer
import json
from typing import List, Dict
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setup paths
PROJECT_DIR = Path(__file__).parent
DB_FILE = PROJECT_DIR / 'event_intelligence.db'
VECTOR_DB_DIR = PROJECT_DIR / 'vector_db'

class EmbeddingGenerator:
    """Generate embeddings and manage vector database"""
    
    def __init__(self, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2', 
                 vector_db_path: str = None):
        """
        Initialize embedding generator
        
        Args:
            model_name: HuggingFace model identifier
            vector_db_path: Path for Chroma database
        
        Recommended models for RAG:
        - 'sentence-transformers/all-MiniLM-L6-v2' (384 dims, fast, good quality)
        - 'sentence-transformers/all-mpnet-base-v2' (768 dims, better quality, slower)
        - 'sentence-transformers/bge-small-en-v1.5' (384 dims, BGE family)
        - 'sentence-transformers/bge-base-en-v1.5' (768 dims, BGE family)
        """
        self.model_name = model_name
        self.vector_db_path = vector_db_path or str(VECTOR_DB_DIR)
        self.model = None
        self.chroma_client = None
        self.collection = None
        self.sql_conn = None
        
    def initialize(self):
        """Initialize model and vector database"""
        logger.info("=" * 70)
        logger.info("Initializing Embedding & Vector Database System")
        logger.info("=" * 70)
        
        # Load embedding model
        logger.info(f"\nLoading embedding model: {self.model_name}")
        logger.info("This may take a moment on first run (downloading model)...")
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"[OK] Model loaded successfully")
            logger.info(f"  - Model dimension: {self.model.get_embedding_dimension()}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to load model: {e}")
            raise
        
        # Initialize Chroma client
        logger.info(f"\nInitializing Chroma vector database: {self.vector_db_path}")
        VECTOR_DB_DIR.mkdir(exist_ok=True)
        
        try:
            # Create persistent client using new API
            self.chroma_client = chromadb.PersistentClient(
                path=self.vector_db_path
            )
            logger.info("[OK] Chroma client initialized")
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize Chroma: {e}")
            raise
        
        # Create collection
        logger.info("\nCreating/accessing vector collection...")
        try:
            # Delete existing collection to start fresh
            try:
                self.chroma_client.delete_collection(name="event_embeddings")
                logger.info("  Removed existing collection")
            except:
                pass
            
            # Create new collection with metadata filtering enabled
            self.collection = self.chroma_client.get_or_create_collection(
                name="event_embeddings",
                metadata={
                    "description": "Event Intelligence RAG embeddings",
                    "model": self.model_name,
                    "chunk_size": 300,
                    "chunk_overlap": 60
                },
                embedding_function=None  # We'll embed manually for better control
            )
            logger.info("[OK] Vector collection created/accessed")
        except Exception as e:
            logger.error(f"[ERROR] Failed to create collection: {e}")
            raise
        
        # Connect to SQL database
        logger.info(f"\nConnecting to SQL database: {DB_FILE}")
        try:
            self.sql_conn = sqlite3.connect(str(DB_FILE))
            self.sql_conn.row_factory = sqlite3.Row
            logger.info("[OK] SQL connection established")
        except Exception as e:
            logger.error(f"[ERROR] Failed to connect to database: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str], batch_size: int = 32):
        """
        Generate embeddings for texts in batches
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            List of embeddings
        """
        embeddings = []
        total = len(texts)
        
        logger.info(f"\nGenerating embeddings for {total} chunks (batch_size={batch_size})...")
        
        for i in range(0, total, batch_size):
            batch = texts[i:i+batch_size]
            start_idx = i
            end_idx = min(i + batch_size, total)
            
            if (end_idx - start_idx) % 500 == 0 or end_idx == total:
                logger.info(f"  Processing: {end_idx}/{total} chunks")
            
            try:
                batch_embeddings = self.model.encode(batch, show_progress_bar=False)
                embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"[ERROR] Error generating embeddings for batch {i}-{end_idx}: {e}")
                raise
        
        logger.info(f"[OK] Generated {len(embeddings)} embeddings")
        return embeddings
    
    def store_embeddings(self, batch_size: int = 100):
        """
        Generate and store embeddings in vector database
        
        Args:
            batch_size: Batch size for Chroma inserts
        """
        cursor = self.sql_conn.cursor()
        
        # Fetch all chunks with metadata
        logger.info("\nReading chunks from database...")
        cursor.execute('''
            SELECT 
                chunk_id, alarm_id, chunk_text, priority, component_id,
                severity, urgency, month, year, day_of_week, alarm_name,
                category_name, device_type, jurisdiction_name,
                char_count, token_count_estimate, is_first_chunk, is_last_chunk,
                chunk_sequence, total_chunks_for_event
            FROM event_chunks
            ORDER BY chunk_id
        ''')
        
        chunks = cursor.fetchall()
        logger.info(f"[OK] Read {len(chunks)} chunks from database")
        
        # Extract texts for embedding
        texts = [chunk['chunk_text'] for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.generate_embeddings(texts, batch_size=32)
        
        # Prepare data for Chroma storage
        logger.info("\nPreparing data for vector database storage...")
        
        chunk_ids = []
        documents = []
        metadatas = []
        embeddings_list = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            if (i + 1) % 500 == 0:
                logger.info(f"  Prepared: {i + 1}/{len(chunks)}")
            
            chunk_ids.append(str(chunk['chunk_id']))
            documents.append(chunk['chunk_text'])
            
            # Prepare metadata (Chroma filters numeric and string types)
            metadata = {
                'alarm_id': int(chunk['alarm_id']),
                'priority': chunk['priority'] or 'Unknown',
                'component_id': int(chunk['component_id']) if chunk['component_id'] else 0,
                'alarm_name': chunk['alarm_name'] or 'Unknown',
                'month': chunk['month'] or 'Unknown',
                'year': int(chunk['year']) if chunk['year'] else 0,
                'day_of_week': chunk['day_of_week'] or 'Unknown',
                'category_name': chunk['category_name'] or 'Unknown',
                'device_type': str(chunk['device_type']) if chunk['device_type'] else 'Unknown',
                'jurisdiction_name': chunk['jurisdiction_name'] or 'Unknown',
                'char_count': int(chunk['char_count']),
                'token_count': int(chunk['token_count_estimate']),
                'is_first_chunk': int(chunk['is_first_chunk']),
                'is_last_chunk': int(chunk['is_last_chunk']),
                'chunk_sequence': int(chunk['chunk_sequence']),
                'total_chunks': int(chunk['total_chunks_for_event']),
            }
            
            metadatas.append(metadata)
            embeddings_list.append(embedding.tolist())
        
        logger.info(f"[OK] Prepared {len(chunk_ids)} items for storage")
        
        # Store in Chroma with batching
        logger.info(f"\nStoring embeddings in Chroma (batch_size={batch_size})...")
        
        for i in range(0, len(chunk_ids), batch_size):
            batch_end = min(i + batch_size, len(chunk_ids))
            
            try:
                self.collection.add(
                    ids=chunk_ids[i:batch_end],
                    documents=documents[i:batch_end],
                    embeddings=embeddings_list[i:batch_end],
                    metadatas=metadatas[i:batch_end]
                )
                
                if batch_end % (batch_size * 5) == 0 or batch_end == len(chunk_ids):
                    logger.info(f"  Stored: {batch_end}/{len(chunk_ids)}")
            except Exception as e:
                logger.error(f"[ERROR] Error storing batch {i}-{batch_end}: {e}")
                raise
        
        logger.info(f"[OK] Successfully stored all {len(chunk_ids)} embeddings in Chroma")
    
    def verify_embeddings(self):
        """Verify embeddings were stored correctly"""
        logger.info("\nVerifying stored embeddings...")
        
        # Get collection count
        collection_count = self.collection.count()
        logger.info(f"[OK] Total embeddings in collection: {collection_count:,}")
        
        # Sample retrieval test
        logger.info("\nTesting retrieval...")
        try:
            # Test semantic search
            test_query = "critical fire emergency alarm component 103"
            results = self.collection.query(
                query_texts=[test_query],
                n_results=3,
                include=["documents", "metadatas", "distances"]
            )
            
            logger.info(f"[OK] Sample query: '{test_query}'")
            logger.info(f"  Found {len(results['documents'][0])} similar chunks\n")
            
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ), 1):
                similarity = 1 - distance  # Convert distance to similarity
                logger.info(f"  Result {i}:")
                logger.info(f"    Alarm ID: {metadata['alarm_id']}, Priority: {metadata['priority']}")
                logger.info(f"    Similarity: {similarity:.4f}")
                logger.info(f"    Text: {doc[:80]}...")
        except Exception as e:
            logger.error(f"[ERROR] Error during test retrieval: {e}")
            raise
        
        # Metadata filtering test
        logger.info("\nTesting metadata filtering...")
        try:
            results = self.collection.query(
                query_texts=["high priority alarm"],
                n_results=5,
                where={"priority": {"$eq": "Critical"}},
                include=["documents", "metadatas"]
            )
            logger.info(f"[OK] Found {len(results['documents'][0])} Critical priority chunks")
        except Exception as e:
            logger.error(f"[ERROR] Error during metadata filtering: {e}")
        
        # Component filtering test
        logger.info("\nTesting component-based filtering...")
        try:
            results = self.collection.query(
                query_texts=["component alarm"],
                n_results=5,
                where={"component_id": {"$eq": 312}},
                include=["documents", "metadatas"]
            )
            logger.info(f"[OK] Found {len(results['documents'][0])} chunks for Component 312")
        except Exception as e:
            logger.error(f"[ERROR] Error during component filtering: {e}")
    
    def get_collection_stats(self):
        """Get detailed collection statistics"""
        logger.info("\n" + "=" * 70)
        logger.info("VECTOR DATABASE STATISTICS")
        logger.info("=" * 70)
        
        count = self.collection.count()
        logger.info(f"Total embeddings: {count:,}")
        logger.info(f"Model: {self.model_name}")
        logger.info(f"Embedding dimension: {self.model.get_embedding_dimension()}")
        logger.info(f"Vector DB path: {self.vector_db_path}")
        
        # Query a few to check metadata
        sample = self.collection.get(limit=5, include=["metadatas"])
        if sample['metadatas']:
            logger.info(f"\nSample metadata fields:")
            for key in sample['metadatas'][0].keys():
                logger.info(f"  - {key}")
    
    def close(self):
        """Close connections"""
        if self.sql_conn:
            self.sql_conn.close()


def main():
    """Main embedding and vector database workflow"""
    try:
        # Check database exists
        if not DB_FILE.exists():
            logger.error(f"[ERROR] Database not found: {DB_FILE}")
            logger.info("  Please run Steps 1-3 first")
            return False
        
        # Initialize embedding generator
        generator = EmbeddingGenerator(
            model_name='sentence-transformers/all-MiniLM-L6-v2'
        )
        
        generator.initialize()
        
        # Generate and store embeddings
        logger.info("\nGenerating and storing embeddings...")
        generator.store_embeddings(batch_size=100)
        
        # Verify
        logger.info("\nVerifying embeddings...")
        generator.verify_embeddings()
        
        # Get statistics
        generator.get_collection_stats()
        
        # Close connections
        generator.close()
        
        logger.info("\n" + "=" * 70)
        logger.info("[OK] Step 4 Complete: Embeddings & Vector Database successful!")
        logger.info("=" * 70 + "\n")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Error during embedding generation: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
