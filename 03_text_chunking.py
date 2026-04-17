"""
Step 3: Text Chunking Strategy
==============================

Module: 03_text_chunking
Version: 1.0
Author: Event Intelligence Team
Date: April 2026

Description:
    Third step of RAG pipeline. Implements intelligent chunking of event
    narratives for optimal retrieval context. Uses semantic-aware chunking
    with overlap to preserve context while maintaining manageable chunk sizes.

Functionality:
    - Semantic-aware sentence tokenization
    - Sliding window chunking with configurable overlap
    - Metadata preservation per chunk
    - Chunk quality validation
    - Context boundary detection
    - Chunk indexing and sequencing

Chunking Strategy:
    - Chunk Size: 300 characters (~48-50 tokens)
    - Overlap: 20% for context preservation
    - Sentence-aligned boundaries
    - Metadata attached to each chunk

Input:
    SQLite Table: event_details with event_text

Output:
    SQLite Table: event_chunks (chunk_id, alarm_id, chunk_text, metadata)

Usage:
    python 03_text_chunking.py

Dependencies:
    - sqlite3 (stdlib)
    - re (stdlib)
"""

import sqlite3
import re
import logging
from pathlib import Path
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setup paths
PROJECT_DIR = Path(__file__).parent
DB_FILE = PROJECT_DIR / 'event_intelligence.db'

class TextChunker:
    """Intelligent text chunking for RAG retrieval"""
    
    def __init__(self, db_path, chunk_size=300, overlap_percentage=20):
        """
        Initialize chunker with optimal parameters for embeddings
        
        Args:
            db_path: Path to SQLite database
            chunk_size: Target chunk size in characters (300-512 recommended)
            overlap_percentage: Percentage overlap between chunks (10-30 recommended)
        """
        self.db_path = db_path
        self.chunk_size = chunk_size
        self.overlap_size = int(chunk_size * (overlap_percentage / 100))
        self.conn = None
        self.chunk_id_counter = 0
    
    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        logger.info(f"Connected to database: {self.db_path}")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def create_chunks_table(self):
        """Create table for text chunks"""
        cursor = self.conn.cursor()
        
        # Drop existing table for clean setup
        cursor.execute('DROP TABLE IF EXISTS event_chunks')
        
        create_sql = '''
        CREATE TABLE event_chunks (
            -- Chunk identification
            chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- Reference to original event
            alarm_id INTEGER NOT NULL,
            chunk_sequence INTEGER NOT NULL,
            total_chunks_for_event INTEGER NOT NULL,
            
            -- Chunk content
            chunk_text TEXT NOT NULL,
            
            -- Metadata from original event
            priority TEXT,
            component_id INTEGER,
            severity TEXT,
            urgency TEXT,
            month TEXT,
            year INTEGER,
            day_of_week TEXT,
            
            -- Agency context
            primary_agency TEXT,
            secondary_agency TEXT,
            
            -- Operational context
            alarm_name TEXT,
            category_name TEXT,
            device_type TEXT,
            jurisdiction_name TEXT,
            
            -- Chunk characteristics
            char_count INTEGER,
            token_count_estimate INTEGER,
            is_first_chunk BOOLEAN,
            is_last_chunk BOOLEAN,
            
            -- References
            event_created_time TIMESTAMP,
            
            -- Audit
            record_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Index for efficient querying
            FOREIGN KEY (alarm_id) REFERENCES event_features(ALARM_ID)
        );
        '''
        
        cursor.execute(create_sql)
        
        # Create index on alarm_id for fast lookups
        cursor.execute('''
            CREATE INDEX idx_chunks_alarm_id ON event_chunks(alarm_id)
        ''')
        
        # Create index on priority for filtering
        cursor.execute('''
            CREATE INDEX idx_chunks_priority ON event_chunks(priority)
        ''')
        
        # Create index on component_id for component-based queries
        cursor.execute('''
            CREATE INDEX idx_chunks_component_id ON event_chunks(component_id)
        ''')
        
        self.conn.commit()
        logger.info("[OK] Created event_chunks table with indexes")
    
    def estimate_token_count(self, text: str) -> int:
        """
        Estimate token count using simple heuristic
        Approximation: 1 token ≈ 4 characters (conservative estimate)
        More accurate for English text
        """
        return len(text) // 4
    
    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences while preserving sentence integrity
        """
        # Split on common sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def chunk_text_with_overlap(self, text: str) -> List[str]:
        """
        Create chunks from text with intelligent overlap to preserve context
        
        Strategy:
        1. Split into sentences to maintain semantic boundaries
        2. Combine sentences into chunks of target size
        3. Add overlap between chunks (reinclude last N chars of previous chunk)
        4. Ensure chunk boundaries are at sentence ends
        """
        if not text or len(text) < 100:
            return [text]
        
        sentences = self.split_into_sentences(text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Add space between sentences
            if current_chunk:
                test_chunk = current_chunk + " " + sentence
            else:
                test_chunk = sentence
            
            # Check if adding this sentence exceeds chunk size
            if len(test_chunk) > self.chunk_size and current_chunk:
                # Save current chunk and start new one
                chunks.append(current_chunk)
                
                # Add overlap: start new chunk with part of previous chunk + new sentence
                if self.overlap_size > 0 and current_chunk:
                    # Include enough of previous chunk for context
                    overlap_text = current_chunk[-self.overlap_size:]
                    # Find sentence boundary in overlap
                    last_sentence_in_overlap = re.split(r'(?<=[.!?])\s+', overlap_text)[-1]
                    current_chunk = last_sentence_in_overlap + " " + sentence
                else:
                    current_chunk = sentence
            else:
                current_chunk = test_chunk
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def chunk_events(self):
        """Chunk all event narratives and store in database"""
        cursor = self.conn.cursor()
        
        logger.info("Reading event features...")
        cursor.execute('''
            SELECT ALARM_ID, event_text, priority, component_id, severity, urgency,
                   month, year, day_of_week, primary_agency, secondary_agency,
                   alarm_name, category_name, device_type, jurisdiction_name,
                   alarm_generated_time
            FROM event_features
            ORDER BY ALARM_ID
        ''')
        
        rows = cursor.fetchall()
        logger.info(f"[OK] Read {len(rows)} events for chunking")
        
        all_chunks = []
        logger.info("Creating chunks for each event...")
        
        for i, row in enumerate(rows):
            if (i + 1) % 500 == 0:
                logger.info(f"  Processing: {i + 1}/{len(rows)}")
            
            alarm_id = row['ALARM_ID']
            event_text = row['event_text']
            
            # Create chunks from event text
            text_chunks = self.chunk_text_with_overlap(event_text)
            
            # Create chunk records with metadata
            total_chunks = len(text_chunks)
            for chunk_seq, chunk_text in enumerate(text_chunks, 1):
                chunk_record = {
                    'alarm_id': alarm_id,
                    'chunk_sequence': chunk_seq,
                    'total_chunks_for_event': total_chunks,
                    'chunk_text': chunk_text,
                    'priority': row['priority'],
                    'component_id': row['component_id'],
                    'severity': row['severity'],
                    'urgency': row['urgency'],
                    'month': row['month'],
                    'year': row['year'],
                    'day_of_week': row['day_of_week'],
                    'primary_agency': row['primary_agency'],
                    'secondary_agency': row['secondary_agency'],
                    'alarm_name': row['alarm_name'],
                    'category_name': row['category_name'],
                    'device_type': row['device_type'],
                    'jurisdiction_name': row['jurisdiction_name'],
                    'char_count': len(chunk_text),
                    'token_count_estimate': self.estimate_token_count(chunk_text),
                    'is_first_chunk': chunk_seq == 1,
                    'is_last_chunk': chunk_seq == total_chunks,
                    'event_created_time': row['alarm_generated_time'],
                }
                all_chunks.append(chunk_record)
        
        logger.info(f"[OK] Created {len(all_chunks)} total chunks from {len(rows)} events")
        
        # Insert chunks into database
        logger.info("Inserting chunks into database...")
        
        import pandas as pd
        df_chunks = pd.DataFrame(all_chunks)
        df_chunks.to_sql('event_chunks', self.conn, if_exists='append', index=False)
        self.conn.commit()
        
        logger.info(f"[OK] Inserted {len(df_chunks)} chunks into event_chunks table")
    
    def verify_chunks(self):
        """Verify chunking results"""
        cursor = self.conn.cursor()
        
        logger.info("\nVerifying chunked data...")
        
        # Total chunks
        cursor.execute('SELECT COUNT(*) FROM event_chunks')
        total_chunks = cursor.fetchone()[0]
        logger.info(f"[OK] Total chunks created: {total_chunks:,}")
        
        # Average chunks per event
        cursor.execute('''
            SELECT COUNT(DISTINCT alarm_id) as num_events FROM event_chunks
        ''')
        num_events = cursor.fetchone()[0]
        avg_chunks_per_event = total_chunks / num_events if num_events > 0 else 0
        logger.info(f"[OK] Average chunks per event: {avg_chunks_per_event:.2f}")
        
        # Chunk size distribution
        logger.info("\n--- Chunk Size Distribution ---")
        cursor.execute('''
            SELECT 
                MIN(char_count) as min_size,
                MAX(char_count) as max_size,
                ROUND(AVG(char_count)) as avg_size
            FROM event_chunks
        ''')
        min_sz, max_sz, avg_sz = cursor.fetchone()
        logger.info(f"  Min: {min_sz} chars")
        logger.info(f"  Max: {max_sz} chars")
        logger.info(f"  Average: {avg_sz} chars")
        
        # Token distribution
        logger.info("\n--- Estimated Token Count Distribution ---")
        cursor.execute('''
            SELECT 
                MIN(token_count_estimate) as min_tokens,
                MAX(token_count_estimate) as max_tokens,
                ROUND(AVG(token_count_estimate)) as avg_tokens
            FROM event_chunks
        ''')
        min_tok, max_tok, avg_tok = cursor.fetchone()
        logger.info(f"  Min: {min_tok} tokens")
        logger.info(f"  Max: {max_tok} tokens")
        logger.info(f"  Average: {avg_tok} tokens")
        
        # Metadata completeness
        logger.info("\n--- Metadata Completeness ---")
        metadata_fields = ['priority', 'component_id', 'alarm_name', 'category_name']
        for field in metadata_fields:
            cursor.execute(f'''
                SELECT COUNT(*) as filled
                FROM event_chunks 
                WHERE {field} IS NOT NULL
            ''')
            filled = cursor.fetchone()[0]
            pct = (filled / total_chunks * 100) if total_chunks > 0 else 0
            logger.info(f"  {field}: {pct:.1f}% ({filled}/{total_chunks})")
        
        # Priority distribution in chunks
        logger.info("\n--- Priority Distribution in Chunks ---")
        cursor.execute('''
            SELECT priority, COUNT(*) as count
            FROM event_chunks
            WHERE priority IS NOT NULL
            GROUP BY priority
            ORDER BY count DESC
        ''')
        for priority, count in cursor.fetchall():
            pct = (count / total_chunks * 100)
            logger.info(f"  {priority}: {count:,} chunks ({pct:.1f}%)")
        
        # Sample chunks
        logger.info("\n--- Sample Chunks ---")
        cursor.execute('''
            SELECT alarm_id, chunk_sequence, total_chunks_for_event, 
                   priority, component_id, char_count, 
                   SUBSTR(chunk_text, 1, 100) as text_preview
            FROM event_chunks
            WHERE is_first_chunk = 1
            LIMIT 3
        ''')
        
        for row in cursor.fetchall():
            logger.info(f"\nAlarm {row[0]} (Chunk {row[1]}/{row[2]}):")
            logger.info(f"  Priority: {row[3]}, Component: {row[4]}")
            logger.info(f"  Size: {row[5]} chars")
            logger.info(f"  Preview: {row[6]}...")
        
        # Overlap verification
        logger.info("\n--- Overlap Context Verification ---")
        cursor.execute('''
            SELECT alarm_id, chunk_sequence
            FROM event_chunks
            WHERE chunk_sequence > 1
            LIMIT 1
        ''')
        result = cursor.fetchone()
        if result:
            alarm_id, seq = result
            cursor.execute('''
                SELECT chunk_text FROM event_chunks
                WHERE alarm_id = ? AND chunk_sequence = ?
            ''', (alarm_id, seq - 1))
            prev_chunk_result = cursor.fetchone()
            prev_chunk = prev_chunk_result[0] if prev_chunk_result else None
            
            cursor.execute('''
                SELECT chunk_text FROM event_chunks
                WHERE alarm_id = ? AND chunk_sequence = ?
            ''', (alarm_id, seq))
            curr_chunk_result = cursor.fetchone()
            if curr_chunk_result:
                curr_chunk = curr_chunk_result[0]
                logger.info(f"Sample: Alarm {alarm_id}, Chunks {seq-1} → {seq}")
                if prev_chunk:
                    logger.info(f"  Previous chunk ends: ...{prev_chunk[-50:]}")
                    logger.info(f"  Current chunk starts: {curr_chunk[:50]}...")


def main():
    """Main text chunking workflow"""
    logger.info("=" * 70)
    logger.info("Step 3: Text Chunking")
    logger.info("=" * 70)
    
    try:
        # Check database exists
        if not DB_FILE.exists():
            logger.error(f"[ERROR] Database not found: {DB_FILE}")
            logger.info("  Please run Steps 1-2 first (data ingestion & feature engineering)")
            return False
        
        # Initialize chunker with optimal parameters
        logger.info("\nInitializing text chunker...")
        logger.info("  - Chunk size: 300 characters (≈75 tokens)")
        logger.info("  - Overlap: 20% (60 characters)")
        
        chunker = TextChunker(
            db_path=DB_FILE,
            chunk_size=300,
            overlap_percentage=20
        )
        chunker.connect()
        
        # Create chunks table
        logger.info("\nCreating chunks table...")
        chunker.create_chunks_table()
        
        # Chunk all events
        logger.info("\nChunking events...")
        chunker.chunk_events()
        
        # Verify chunks
        logger.info("\nVerifying chunked data...")
        chunker.verify_chunks()
        
        # Close connection
        chunker.close()
        
        logger.info("\n" + "=" * 70)
        logger.info("[OK] Step 3 Complete: Text Chunking successful!")
        logger.info("=" * 70 + "\n")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Error during text chunking: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
