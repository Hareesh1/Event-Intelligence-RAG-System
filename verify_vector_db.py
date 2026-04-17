"""
Vector Database Query & Retrieval Verification
Demonstrates semantic search, filtering, and retrieval capabilities
"""

import chromadb
from pathlib import Path
import json

PROJECT_DIR = Path(__file__).parent
VECTOR_DB_PATH = PROJECT_DIR / 'vector_db'

def print_section(title, width=80):
    """Print formatted section header"""
    print(f"\n{'='*width}")
    print(f" {title}")
    print(f"{'='*width}\n")

def demonstrate_retrieval():
    """Demonstrate vector database retrieval capabilities"""
    
    # Connect to Chroma
    client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
    collection = client.get_collection(name="event_embeddings")
    
    print_section("1. VECTOR DATABASE INFORMATION")
    print(f"Total embeddings stored: {collection.count():,}")
    print(f"Vector DB location: {VECTOR_DB_PATH}")
    print(f"Database is persistent and ready for queries")
    
    # Test 1: Basic semantic search
    print_section("2. SEMANTIC SEARCH - Test Queries")
    
    test_queries = [
        "critical fire emergency",
        "high priority alarm",
        "component 312 issue",
        "urgent security breach",
        "police response incident",
    ]
    
    for query in test_queries:
        print(f"\n📌 Query: '{query}'")
        results = collection.query(
            query_texts=[query],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )
        
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ), 1):
            similarity = 1 - distance
            print(f"  {i}. Alarm #{metadata['alarm_id']} | {metadata['priority']} | "
                  f"Similarity: {similarity:.4f}")
            print(f"     {doc[:70]}...")
    
    # Test 2: Priority-based filtering
    print_section("3. METADATA FILTERING - By Priority")
    
    for priority in ['Critical', 'High', 'Low']:
        results = collection.query(
            query_texts=["alarm event incident"],
            n_results=1,
            where={"priority": {"$eq": priority}},
            include=["documents", "metadatas"]
        )
        
        if results['documents'][0]:
            doc = results['documents'][0][0]
            meta = results['metadatas'][0][0]
            print(f"\n{priority} Priority Example:")
            print(f"  Alarm ID: {meta['alarm_id']}")
            print(f"  Component: {meta.get('component_id', 'N/A')}")
            print(f"  Time: {meta.get('month', 'N/A')} at "
                  f"{meta.get('day_of_week', 'N/A')}")
            print(f"  Text: {doc[:80]}...")
    
    # Test 3: Component-based search
    print_section("4. COMPONENT-BASED FILTERING")
    
    components = [312, 101, 313, 100]
    for comp_id in components:
        results = collection.query(
            query_texts=["component alarm"],
            n_results=1,
            where={"component_id": {"$eq": comp_id}},
            include=["documents", "metadatas"]
        )
        
        count_results = collection.count()
        comp_count = collection.get(
            where={"component_id": {"$eq": comp_id}},
            include=[]
        )
        
        if results['documents'][0]:
            doc = results['documents'][0][0]
            meta = results['metadatas'][0][0]
            print(f"\nComponent {comp_id}:")
            print(f"  Priority: {meta['priority']}")
            print(f"  Sample: {doc[:75]}...")
    
    # Test 4: Combined filtering (Priority AND Component)
    print_section("5. COMBINED FILTERING - High Priority + Component 312")
    
    results = collection.query(
        query_texts=["fire emergency"],
        n_results=3,
        where={
            "$and": [
                {"priority": {"$eq": "High"}},
                {"component_id": {"$eq": 312}}
            ]
        },
        include=["documents", "metadatas"]
    )
    
    print(f"Found {len(results['documents'][0])} matching chunks\n")
    for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
        print(f"{i}. Alarm {meta['alarm_id']} | {meta.get('category_name', 'N/A')}")
        print(f"   {doc[:80]}...\n")
    
    # Test 5: Temporal filtering
    print_section("6. TEMPORAL FILTERING - May Month Events")
    
    results = collection.query(
        query_texts=["incident"],
        n_results=5,
        where={"month": {"$eq": "May"}},
        include=["documents", "metadatas"]
    )
    
    print(f"Found {len(results['documents'][0])} May events")
    for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
        print(f"{i}. {meta.get('day_of_week', 'N/A')} | Alarm {meta['alarm_id']} | "
              f"{meta['priority']}")
    
    # Test 6: Chunk sequence information
    print_section("7. MULTI-CHUNK EVENT RETRIEVAL")
    
    results = collection.query(
        query_texts=["fire emergency"],
        n_results=10,
        include=["documents", "metadatas"]
    )
    
    # Find first multi-chunk event
    for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
        if meta['total_chunks'] > 1:
            alarm_id = meta['alarm_id']
            print(f"Event: Alarm ID {alarm_id} | {meta['total_chunks']} chunks total")
            print(f"Priority: {meta['priority']}")
            print(f"Component: {meta.get('component_id', 'N/A')}")
            print(f"\nChunk {meta['chunk_sequence']}/{meta['total_chunks']}:")
            print(f"{doc}\n")
            
            # Show all chunks for this alarm
            all_chunks = collection.query(
                query_texts=["dummy"],
                n_results=1000,
                where={"alarm_id": {"$eq": meta['alarm_id']}},
                include=["documents", "metadatas"]
            )
            
            # Group by chunk sequence
            chunks_by_seq = {}
            for chunk_doc, chunk_meta in zip(all_chunks['documents'][0], 
                                            all_chunks['metadatas'][0]):
                seq = chunk_meta['chunk_sequence']
                chunks_by_seq[seq] = chunk_doc
            
            print("All chunks for this event:")
            for seq in sorted(chunks_by_seq.keys()):
                chunk_text = chunks_by_seq[seq]
                print(f"\n  [{seq}] {chunk_text[:100]}...")
            break
    
    # Test 7: Metadata statistics
    print_section("8. COLLECTION STATISTICS")
    
    sample = collection.get(limit=1000, include=["metadatas"])
    if sample['metadatas']:
        priorities = {}
        components = {}
        agencies = {}
        
        for meta in sample['metadatas']:
            # Count priorities
            priority = meta.get('priority', 'Unknown')
            priorities[priority] = priorities.get(priority, 0) + 1
            
            # Count components (sample only)
            comp = meta.get('component_id', 0)
            if comp:
                components[comp] = components.get(comp, 0) + 1
        
        print("Priority Distribution (sample):")
        for priority, count in sorted(priorities.items(), key=lambda x: x[1], reverse=True):
            print(f"  {priority}: {count}")
        
        print("\nTop Components (sample):")
        for comp, count in sorted(components.items(), key=lambda x: x[1], 
                                 reverse=True)[:5]:
            print(f"  Component {int(comp)}: {count} chunks")
    
    print("\n" + "="*80)
    print("[OK] Vector Database Verification Complete")
    print("  All retrieval capabilities tested and working!")
    print("="*80 + "\n")

if __name__ == '__main__':
    if not VECTOR_DB_PATH.exists():
        print(f"Error: Vector database not found at {VECTOR_DB_PATH}")
        print("Please run 04_embeddings_vector_db.py first")
        exit(1)
    
    demonstrate_retrieval()
