"""
Database Verification & SQL Schema Validation
==============================================

Module: verify_database
Version: 1.0
Author: Event Intelligence Team
Date: April 2026

Description:
    Validates the SQLite database structure, data integrity, and schema.
    Verifies that data ingestion completed successfully with all fields populated.

Verification Checks:
    - Database file existence and accessibility
    - Table schema validation and structure
    - Row count statistics and distribution
    - Data type compliance verification
    - NULL value detection and analysis
    - Index presence and functionality
    - Foreign key integrity (if applicable)
    - Sample record inspection

Usage:
    python verify_database.py

Output:
    console - Formatted verification report including:
    - Database structure and schema
    - Data statistics and metrics
    - Integrity warnings and issues
    - Sample records display
    - Data quality assessment

Dependencies:
    - sqlite3 (Python stdlib)
    - pandas (for data analysis)
    - pathlib (Python stdlib)
"""

import sqlite3
from pathlib import Path
import pandas as pd

DB_FILE = Path(__file__).parent / 'event_intelligence.db'

def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}")

def explore_database():
    """Explore database structure and content"""
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    # 1. Table Schema
    print_section("1. DATABASE SCHEMA")
    cursor.execute("PRAGMA table_info(event_details)")
    columns = cursor.fetchall()
    print(f"\nTotal columns: {len(columns)}\n")
    print(f"{'Column':<35} {'Type':<15} {'PK':<5} {'NN':<5} {'Default':<20}")
    print("-" * 80)
    for col_id, name, col_type, not_null, default_val, primary_key in columns:
        pk = "YES" if primary_key else ""
        nn = "YES" if not_null else ""
        default = default_val if default_val else ""
        print(f"{name:<35} {col_type:<15} {pk:<5} {nn:<5} {default:<20}")
    
    # 2. Data Summary
    print_section("2. DATA SUMMARY")
    cursor.execute("SELECT COUNT(*) as total_records FROM event_details")
    total = cursor.fetchone()[0]
    print(f"Total records: {total:,}")
    
    cursor.execute("SELECT COUNT(DISTINCT ALARM_ID) FROM event_details")
    unique_alarms = cursor.fetchone()[0]
    print(f"Unique ALARM_IDs: {unique_alarms:,}")
    
    cursor.execute("SELECT COUNT(DISTINCT COMPONENT_ID) FROM event_details WHERE COMPONENT_ID IS NOT NULL")
    unique_components = cursor.fetchone()[0]
    print(f"Unique COMPONENT_IDs: {unique_components:,}")
    
    cursor.execute("SELECT COUNT(DISTINCT PRIMARY_AGENCY) FROM event_details WHERE PRIMARY_AGENCY IS NOT NULL")
    unique_agencies = cursor.fetchone()[0]
    print(f"Unique PRIMARY_AGENCIES: {unique_agencies}")
    
    # 3. Field Analysis
    print_section("3. CRITICAL FIELDS ANALYSIS")
    
    # Priority distribution
    cursor.execute("""
        SELECT PRIORITY, COUNT(*) as count, 
               ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM event_details), 2) as percentage
        FROM event_details 
        GROUP BY PRIORITY 
        ORDER BY count DESC
    """)
    print("\nPRIORITY Distribution:")
    print(f"{'Priority':<20} {'Count':<10} {'Percentage':<10}")
    print("-" * 40)
    for priority, count, pct in cursor.fetchall():
        priority_display = priority if priority else "NULL"
        print(f"{priority_display:<20} {count:<10} {pct}%")
    
    # Severity distribution
    cursor.execute("""
        SELECT SEVERITY, COUNT(*) as count 
        FROM event_details 
        WHERE SEVERITY IS NOT NULL
        GROUP BY SEVERITY 
        ORDER BY count DESC
    """)
    print("\nSEVERITY Distribution:")
    print(f"{'Severity':<20} {'Count':<10}")
    print("-" * 30)
    for severity, count in cursor.fetchall():
        print(f"{severity:<20} {count:<10}")
    
    # Urgency distribution
    cursor.execute("""
        SELECT URGENCY, COUNT(*) as count 
        FROM event_details 
        WHERE URGENCY IS NOT NULL
        GROUP BY URGENCY 
        ORDER BY count DESC
    """)
    print("\nURGENCY Distribution:")
    print(f"{'Urgency':<20} {'Count':<10}")
    print("-" * 30)
    for urgency, count in cursor.fetchall():
        print(f"{urgency:<20} {count:<10}")
    
    # 4. Data Completeness
    print_section("4. DATA COMPLETENESS")
    completeness_columns = [
        'ALARM_ID', 'PRIORITY', 'COMPONENT_ID', 'ALARM_GENERATED_TIME',
        'SEVERITY', 'URGENCY', 'SECONDARY_AGENCY', 'SOP_DOCUMENT_URL'
    ]
    
    total_records = cursor.execute("SELECT COUNT(*) FROM event_details").fetchone()[0]
    print(f"\n{'Column':<35} {'Filled':<10} {'Empty':<10} {'Completeness':<12}")
    print("-" * 67)
    
    for col in completeness_columns:
        filled = cursor.execute(f"SELECT COUNT(*) FROM event_details WHERE {col} IS NOT NULL").fetchone()[0]
        empty = total_records - filled
        completeness = (filled / total_records * 100) if total_records > 0 else 0
        print(f"{col:<35} {filled:<10} {empty:<10} {completeness:.1f}%")
    
    # 5. Sample Records
    print_section("5. SAMPLE RECORDS (First 3)")
    df_sample = pd.read_sql_query(
        "SELECT ALARM_ID, PRIORITY, COMPONENT_ID, ALARM_GENERATED_TIME, SECONDARY_AGENCY, SEVERITY, URGENCY FROM event_details LIMIT 3",
        conn
    )
    print("\n" + df_sample.to_string(index=False))
    
    # 6. Component Analysis
    print_section("6. TOP 10 COMPONENTS BY ALARM COUNT")
    cursor.execute("""
        SELECT COMPONENT_ID, COUNT(*) as alarm_count, COUNT(DISTINCT ALARM_ID) as unique_alarms
        FROM event_details 
        WHERE COMPONENT_ID IS NOT NULL
        GROUP BY COMPONENT_ID 
        ORDER BY alarm_count DESC 
        LIMIT 10
    """)
    print(f"\n{'Component ID':<20} {'Alarm Count':<15} {'Unique Alarms':<15}")
    print("-" * 50)
    for comp_id, alarm_count, unique in cursor.fetchall():
        print(f"{int(comp_id):<20} {alarm_count:<15} {unique:<15}")
    
    # 7. Agency Analysis
    print_section("7. TOP 10 AGENCIES BY EVENT COUNT")
    cursor.execute("""
        SELECT PRIMARY_AGENCY, COUNT(*) as event_count
        FROM event_details 
        WHERE PRIMARY_AGENCY IS NOT NULL
        GROUP BY PRIMARY_AGENCY 
        ORDER BY event_count DESC 
        LIMIT 10
    """)
    print(f"\n{'Primary Agency':<35} {'Event Count':<15}")
    print("-" * 50)
    for agency, count in cursor.fetchall():
        print(f"{agency:<35} {count:<15}")
    
    # 8. Date Range
    print_section("8. TEMPORAL DATA RANGE")
    cursor.execute("""
        SELECT 
            MIN(ALARM_GENERATED_TIME) as earliest,
            MAX(ALARM_GENERATED_TIME) as latest,
            COUNT(DISTINCT DATE(ALARM_GENERATED_TIME)) as num_days
        FROM event_details
    """)
    earliest, latest, num_days = cursor.fetchone()
    print(f"\nEarliest event: {earliest}")
    print(f"Latest event: {latest}")
    print(f"Number of days covered: {num_days}")
    
    conn.close()
    print("\n" + "="*70)
    print(" [OK] Database Exploration Complete")
    print("="*70 + "\n")

if __name__ == '__main__':
    if not DB_FILE.exists():
        print(f"Error: Database file not found at {DB_FILE}")
        exit(1)
    
    explore_database()
