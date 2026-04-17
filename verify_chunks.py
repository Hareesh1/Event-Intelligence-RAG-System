"""
Text Chunking Verification & Analysis
Detailed inspection of created chunks
"""

import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent / 'event_intelligence.db'

def print_section(title, width=80):
    """Print formatted section header"""
    print(f"\n{'='*width}")
    print(f" {title}")
    print(f"{'='*width}\n")

def analyze_chunks():
    """Comprehensive analysis of text chunks"""
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    # 1. Chunking Summary
    print_section("1. TEXT CHUNKING SUMMARY")
    cursor.execute('''
        SELECT 
            COUNT(*) as total_chunks,
            COUNT(DISTINCT alarm_id) as num_events,
            MAX(chunk_sequence) as max_chunks_for_event
        FROM event_chunks
    ''')
    total_chunks, num_events, max_seq = cursor.fetchone()
    avg_chunks = total_chunks / num_events if num_events > 0 else 0
    
    print(f"Total chunks created: {total_chunks:,}")
    print(f"Original events: {num_events:,}")
    print(f"Average chunks per event: {avg_chunks:.2f}")
    print(f"Max chunks for single event: {max_seq}")
    
    # 2. Chunk Distribution
    print_section("2. CHUNK DISTRIBUTION BY EVENT")
    cursor.execute('''
        SELECT total_chunks_for_event, COUNT(DISTINCT alarm_id) as num_events
        FROM event_chunks
        WHERE is_first_chunk = 1
        GROUP BY total_chunks_for_event
        ORDER BY total_chunks_for_event
    ''')
    print(f"{'Chunks/Event':<15} {'Number of Events':<20} {'Percentage':<10}")
    print("-" * 45)
    
    event_chunk_dist = []
    for chunks, count in cursor.fetchall():
        pct = (count / num_events * 100)
        event_chunk_dist.append((chunks, count))
        print(f"{chunks:<15} {count:<20} {pct:.1f}%")
    
    # 3. Chunk Size Analysis
    print_section("3. CHUNK SIZE ANALYSIS")
    cursor.execute('''
        SELECT 
            MIN(char_count) as min_chars,
            MAX(char_count) as max_chars,
            ROUND(AVG(char_count)) as avg_chars,
            MIN(token_count_estimate) as min_tokens,
            MAX(token_count_estimate) as max_tokens,
            ROUND(AVG(token_count_estimate)) as avg_tokens
        FROM event_chunks
    ''')
    min_c, max_c, avg_c, min_t, max_t, avg_t = cursor.fetchone()
    
    print(f"Character Count:")
    print(f"  - Min: {min_c} chars")
    print(f"  - Max: {max_c} chars")
    print(f"  - Average: {avg_c} chars")
    
    print(f"\nEstimated Token Count:")
    print(f"  - Min: {min_t} tokens")
    print(f"  - Max: {max_t} tokens")
    print(f"  - Average: {avg_t} tokens")
    
    # 4. Size Distribution Histogram
    print_section("4. CHUNK SIZE DISTRIBUTION")
    cursor.execute('''
        SELECT 
            CASE 
                WHEN char_count < 100 THEN '<100'
                WHEN char_count < 150 THEN '100-149'
                WHEN char_count < 200 THEN '150-199'
                WHEN char_count < 250 THEN '200-249'
                ELSE '250+'
            END as size_range,
            COUNT(*) as count
        FROM event_chunks
        GROUP BY size_range
        ORDER BY size_range
    ''')
    
    print(f"{'Size Range':<15} {'Count':<10} {'Percentage':<10} {'Visualization':<40}")
    print("-" * 65)
    
    for size_range, count in cursor.fetchall():
        pct = (count / total_chunks * 100)
        bar_width = int(pct / 2)
        bar = '=' * bar_width
        print(f"{size_range:<15} {count:<10} {pct:.1f}%{bar:<40}")
    
    # 5. Metadata Preservation
    print_section("5. METADATA PRESERVATION IN CHUNKS")
    
    metadata_fields = ['priority', 'component_id', 'alarm_name', 'category_name', 
                      'device_type', 'jurisdiction_name', 'month']
    
    print(f"{'Field':<25} {'Complete':<12} {'Partial':<12} {'None':<12}")
    print("-" * 61)
    
    for field in metadata_fields:
        cursor.execute(f'''
            SELECT 
                SUM(CASE WHEN {field} IS NOT NULL THEN 1 ELSE 0 END) as filled
            FROM event_chunks
        ''')
        filled = cursor.fetchone()[0]
        none_count = total_chunks - filled
        pct_filled = (filled / total_chunks * 100) if total_chunks > 0 else 0
        
        print(f"{field:<25} {filled:<12} {0:<12} {none_count:<12}")
    
    # 6. Priority Distribution
    print_section("6. PRIORITY DISTRIBUTION IN CHUNKS")
    cursor.execute('''
        SELECT priority, COUNT(*) as count
        FROM event_chunks
        WHERE priority IS NOT NULL
        GROUP BY priority
        ORDER BY count DESC
    ''')
    print(f"{'Priority':<15} {'Chunks':<10} {'Percentage':<10} {'Bar':<40}")
    print("-" * 65)
    
    for priority, count in cursor.fetchall():
        pct = (count / total_chunks * 100)
        bar_width = int(pct / 2)
        bar = '=' * bar_width
        print(f"{priority:<15} {count:<10} {pct:.1f}%{bar:<40}")
    
    # 7. Component Distribution
    print_section("7. TOP 10 COMPONENTS IN CHUNKS")
    cursor.execute('''
        SELECT component_id, COUNT(*) as count
        FROM event_chunks
        WHERE component_id IS NOT NULL
        GROUP BY component_id
        ORDER BY count DESC
        LIMIT 10
    ''')
    print(f"{'Component ID':<15} {'Chunks':<10} {'Percentage':<10}")
    print("-" * 35)
    
    comp_total = cursor.execute('''
        SELECT COUNT(*) FROM event_chunks WHERE component_id IS NOT NULL
    ''').fetchone()[0]
    
    cursor.execute('''
        SELECT component_id, COUNT(*) as count
        FROM event_chunks
        WHERE component_id IS NOT NULL
        GROUP BY component_id
        ORDER BY count DESC
        LIMIT 10
    ''')
    
    for comp_id, count in cursor.fetchall():
        pct = (count / comp_total * 100) if comp_total > 0 else 0
        print(f"{int(comp_id):<15} {count:<10} {pct:.1f}%")
    
    # 8. First vs Last Chunks
    print_section("8. FIRST AND LAST CHUNK DISTRIBUTION")
    cursor.execute("SELECT COUNT(*) FROM event_chunks WHERE is_first_chunk = 1")
    first_chunks = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM event_chunks WHERE is_last_chunk = 1")
    last_chunks = cursor.fetchone()[0]
    
    print(f"First chunks (chunk_sequence = 1): {first_chunks:,} ({first_chunks/total_chunks*100:.1f}%)")
    print(f"Last chunks: {last_chunks:,} ({last_chunks/total_chunks*100:.1f}%)")
    print(f"Middle chunks: {total_chunks - first_chunks - last_chunks + last_chunks:,}")
    
    # 9. Context Overlap Examples
    print_section("9. CONTEXT OVERLAP EXAMPLES (Multi-Chunk Events)")
    
    cursor.execute('''
        SELECT DISTINCT alarm_id 
        FROM event_chunks 
        WHERE chunk_sequence > 1
        LIMIT 2
    ''')
    
    multi_chunk_events = cursor.fetchall()
    for i, (alarm_id,) in enumerate(multi_chunk_events, 1):
        print(f"\n--- Event {i}: Alarm ID {alarm_id} ---")
        cursor.execute('''
            SELECT chunk_sequence, total_chunks_for_event, 
                   SUBSTR(chunk_text, 1, 80) as preview
            FROM event_chunks
            WHERE alarm_id = ?
            ORDER BY chunk_sequence
        ''', (alarm_id,))
        
        for seq, total, preview in cursor.fetchall():
            print(f"  Chunk {seq}/{total}: {preview}...")
        
        print(f"\n  Full overlap context:")
        cursor.execute('''
            SELECT chunk_text FROM event_chunks
            WHERE alarm_id = ? AND chunk_sequence = 1
        ''', (alarm_id,))
        prev_text = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT chunk_text FROM event_chunks
            WHERE alarm_id = ? AND chunk_sequence = 2
        ''', (alarm_id,))
        curr_text = cursor.fetchone()[0]
        
        if prev_text and curr_text:
            # Find overlap
            for j in range(len(prev_text), 0, -1):
                if curr_text.startswith(prev_text[j:]):
                    overlap = prev_text[j:]
                    print(f"    Overlap text: '{overlap}'")
                    break
    
    # 10. Sample Chunks with Full Metadata
    print_section("10. SAMPLE CHUNKS WITH FULL METADATA")
    
    cursor.execute('''
        SELECT 
            chunk_id, alarm_id, chunk_sequence, total_chunks_for_event,
            priority, component_id, month, category_name,
            char_count, token_count_estimate, chunk_text
        FROM event_chunks
        WHERE is_first_chunk = 1
        LIMIT 2
    ''')
    
    for i, row in enumerate(cursor.fetchall(), 1):
        (chunk_id, alarm_id, seq, total, priority, comp, month, 
         category, chars, tokens, text) = row
        
        print(f"\nSample {i}:")
        print(f"  Chunk ID: {chunk_id}")
        print(f"  Alarm ID: {alarm_id} (Chunk {seq}/{total})")
        print(f"  Priority: {priority}")
        print(f"  Component: {comp}")
        print(f"  Month: {month}")
        print(f"  Category: {category}")
        print(f"  Size: {chars} chars / {tokens} tokens")
        print(f"  Text: {text}")
    
    conn.close()
    print("\n" + "="*80)
    print("[OK] Chunk Analysis Complete")
    print("="*80 + "\n")

if __name__ == '__main__':
    if not DB_FILE.exists():
        print(f"Error: Database not found at {DB_FILE}")
        exit(1)
    
    analyze_chunks()
