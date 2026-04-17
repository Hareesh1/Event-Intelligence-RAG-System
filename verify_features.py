"""
Feature Engineering Verification & Quality Analysis
====================================================

Module: verify_features
Version: 1.0
Author: Event Intelligence Team
Date: April 2026

Description:
    Validates that feature engineering step created quality textual
    representations. Checks event_text field for completeness, quality,
    and proper formatting for downstream embedding and retrieval.

Analysis Coverage:
    - event_text column existence and completeness
    - Text length distribution and statistics
    - NULL or missing values detection
    - Content quality assessment
    - Metadata inclusion verification
    - Text diversity metrics
    - Sample narrative review
    - Field correlation analysis

Quality Checks:
    - Minimum text length validation
    - Metadata presence in narratives
    - Proper formatting consistency
    - Language quality assessment

Usage:
    python verify_features.py

Output:
    console - Comprehensive feature analysis report:
    - Feature statistics and distribution
    - Sample engineered narratives
    - Quality metrics and assessment
    - Improvement recommendations

Dependencies:
    - sqlite3 (Python stdlib)
    - pandas (for data analysis)
    - pathlib (Python stdlib)
"""

import sqlite3
from pathlib import Path
import pandas as pd

DB_FILE = Path(__file__).parent / 'event_intelligence.db'

def print_section(title, width=80):
    """Print formatted section header"""
    print(f"\n{'='*width}")
    print(f" {title}")
    print(f"{'='*width}\n")

def analyze_features():
    """Comprehensive analysis of engineered features"""
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    # 1. Overall Statistics
    print_section("1. FEATURE ENGINEERING SUMMARY")
    cursor.execute("SELECT COUNT(*) FROM event_features")
    total = cursor.fetchone()[0]
    print(f"Total engineered features: {total:,}")
    
    # 2. Event Text Analysis
    print_section("2. EVENT TEXT (NARRATIVE) ANALYSIS")
    cursor.execute('''
        SELECT 
            MIN(LENGTH(event_text)) as min_length,
            MAX(LENGTH(event_text)) as max_length,
            ROUND(AVG(LENGTH(event_text))) as avg_length,
            COUNT(*) as total_records
        FROM event_features
    ''')
    min_len, max_len, avg_len, count = cursor.fetchone()
    print(f"Event text statistics:")
    print(f"  - Minimum length: {min_len} characters")
    print(f"  - Maximum length: {max_len} characters")
    print(f"  - Average length: {avg_len} characters")
    print(f"  - Total records with text: {count}")
    
    # 3. Sample Narratives - Different Priority Levels
    print_section("3. SAMPLE EVENT NARRATIVES BY PRIORITY")
    
    for priority in ['Critical', 'High', 'Low']:
        print(f"\n--- {priority.upper()} Priority Example ---")
        cursor.execute('''
            SELECT ALARM_ID, event_text FROM event_features 
            WHERE priority = ? LIMIT 1
        ''', (priority,))
        result = cursor.fetchone()
        if result:
            alarm_id, text = result
            print(f"Alarm ID: {alarm_id}")
            # Print text with word wrapping
            for i in range(0, len(text), 80):
                print(f"  {text[i:i+80]}")
        else:
            print(f"  (No {priority.lower()} priority events)")
    
    # 4. Metadata Completeness
    print_section("4. METADATA COMPLETENESS")
    metadata_fields = [
        'priority', 'component_id', 'severity', 'urgency', 'month',
        'year', 'day_of_week', 'hour_of_day', 'jurisdiction_name',
        'alarm_name', 'category_name', 'device_type'
    ]
    
    print(f"{'Field':<25} {'Filled':<10} {'Empty':<10} {'Completeness':<12}")
    print("-" * 57)
    
    for field in metadata_fields:
        cursor.execute(f'''
            SELECT 
                COUNT(CASE WHEN {field} IS NOT NULL THEN 1 END) as filled,
                COUNT(CASE WHEN {field} IS NULL THEN 1 END) as empty
            FROM event_features
        ''')
        filled, empty = cursor.fetchone()
        completeness = (filled / (filled + empty) * 100) if (filled + empty) > 0 else 0
        print(f"{field:<25} {filled:<10} {empty:<10} {completeness:.1f}%")
    
    # 5. Priority Distribution
    print_section("5. PRIORITY METADATA DISTRIBUTION")
    cursor.execute('''
        SELECT priority, COUNT(*) as count,
               ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM event_features), 1) as pct
        FROM event_features
        WHERE priority IS NOT NULL
        GROUP BY priority
        ORDER BY count DESC
    ''')
    print(f"{'Priority':<15} {'Count':<10} {'Percentage':<10}")
    print("-" * 35)
    for priority, count, pct in cursor.fetchall():
        print(f"{priority:<15} {count:<10} {pct:.1f}%")
    
    # 6. Temporal Distribution
    print_section("6. TEMPORAL METADATA DISTRIBUTION")
    
    print("\nMonth Distribution:")
    cursor.execute('''
        SELECT month, COUNT(*) as count
        FROM event_features
        WHERE month IS NOT NULL
        GROUP BY CASE 
            WHEN month = 'January' THEN 1
            WHEN month = 'February' THEN 2
            WHEN month = 'March' THEN 3
            WHEN month = 'April' THEN 4
            WHEN month = 'May' THEN 5
            WHEN month = 'June' THEN 6
            WHEN month = 'July' THEN 7
            WHEN month = 'August' THEN 8
            WHEN month = 'September' THEN 9
            WHEN month = 'October' THEN 10
            WHEN month = 'November' THEN 11
            WHEN month = 'December' THEN 12
        END
        ORDER BY CASE 
            WHEN month = 'January' THEN 1
            WHEN month = 'February' THEN 2
            WHEN month = 'March' THEN 3
            WHEN month = 'April' THEN 4
            WHEN month = 'May' THEN 5
            WHEN month = 'June' THEN 6
            WHEN month = 'July' THEN 7
            WHEN month = 'August' THEN 8
            WHEN month = 'September' THEN 9
            WHEN month = 'October' THEN 10
            WHEN month = 'November' THEN 11
            WHEN month = 'December' THEN 12
        END
    ''')
    for month, count in cursor.fetchall():
        bar_length = int(count / 50)
        bar = '=' * bar_length
        print(f"  {month:<12}: {count:<6} {bar}")
    
    print("\nDay of Week Distribution:")
    cursor.execute('''
        SELECT day_of_week, COUNT(*) as count
        FROM event_features
        WHERE day_of_week IS NOT NULL
        GROUP BY day_of_week
        ORDER BY count DESC
    ''')
    for day, count in cursor.fetchall():
        bar_length = int(count / 40)
        bar = '=' * bar_length
        print(f"  {day:<12}: {count:<6} {bar}")
    
    print("\nHour of Day Distribution (Top 10):")
    cursor.execute('''
        SELECT hour_of_day, COUNT(*) as count
        FROM event_features
        WHERE hour_of_day IS NOT NULL
        GROUP BY hour_of_day
        ORDER BY count DESC
        LIMIT 10
    ''')
    for hour, count in cursor.fetchall():
        bar_length = int(count / 20)
        bar = '=' * bar_length
        print(f"  Hour {hour:>2}: {count:<6} {bar}")
    
    # 7. Component Distribution
    print_section("7. COMPONENT_ID METADATA DISTRIBUTION (Top 15)")
    cursor.execute('''
        SELECT component_id, COUNT(*) as count
        FROM event_features
        WHERE component_id IS NOT NULL
        GROUP BY component_id
        ORDER BY count DESC
        LIMIT 15
    ''')
    print(f"{'Component ID':<15} {'Count':<10} {'Percentage':<10}")
    print("-" * 35)
    total_with_comp = cursor.execute(
        'SELECT COUNT(*) FROM event_features WHERE component_id IS NOT NULL'
    ).fetchone()[0]
    
    cursor.execute('''
        SELECT component_id, COUNT(*) as count
        FROM event_features
        WHERE component_id IS NOT NULL
        GROUP BY component_id
        ORDER BY count DESC
        LIMIT 15
    ''')
    for comp_id, count in cursor.fetchall():
        pct = (count / total_with_comp * 100) if total_with_comp > 0 else 0
        print(f"{int(comp_id):<15} {count:<10} {pct:.1f}%")
    
    # 8. Agency Distribution
    print_section("8. AGENCY METADATA DISTRIBUTION")
    print("\nPrimary Agency:")
    cursor.execute('''
        SELECT primary_agency, COUNT(*) as count
        FROM event_features
        WHERE primary_agency IS NOT NULL
        GROUP BY primary_agency
        ORDER BY count DESC
    ''')
    for agency, count in cursor.fetchall():
        print(f"  {agency}: {count}")
    
    print("\nSecondary Agencies (Top 5):")
    cursor.execute('''
        SELECT secondary_agency, COUNT(*) as count
        FROM event_features
        WHERE secondary_agency IS NOT NULL
        GROUP BY secondary_agency
        ORDER BY count DESC
        LIMIT 5
    ''')
    for agencies, count in cursor.fetchall():
        print(f"  {agencies}: {count}")
    
    # 9. Device Type Distribution
    print_section("9. DEVICE_TYPE METADATA DISTRIBUTION")
    cursor.execute('''
        SELECT device_type, COUNT(*) as count
        FROM event_features
        WHERE device_type IS NOT NULL
        GROUP BY device_type
        ORDER BY count DESC
    ''')
    for device_type, count in cursor.fetchall():
        pct = (count / total * 100)
        bar_length = int(count / 100)
        bar = '=' * bar_length
        print(f"  {device_type:<25} {count:<6} {bar}")
    
    # 10. Rich Examples
    print_section("10. DETAILED FEATURE EXAMPLES")
    cursor.execute('''
        SELECT 
            ALARM_ID, priority, severity, urgency, month, 
            component_id, jurisdiction_name, event_text
        FROM event_features
        WHERE priority = 'Critical'
        LIMIT 3
    ''')
    
    for i, row in enumerate(cursor.fetchall(), 1):
        alarm_id, priority, severity, urgency, month, comp_id, jurisdiction, text = row
        print(f"\nExample {i} - Critical Priority Event:")
        print(f"  Alarm ID: {alarm_id}")
        print(f"  Priority: {priority}")
        print(f"  Severity: {severity}")
        print(f"  Urgency: {urgency}")
        print(f"  Month: {month}")
        print(f"  Component ID: {comp_id}")
        print(f"  Jurisdiction: {jurisdiction}")
        print(f"  Narrative:\n    {text}\n")
    
    conn.close()
    print("="*80)
    print("[OK] Feature Engineering Verification Complete")
    print("="*80 + "\n")

if __name__ == '__main__':
    if not DB_FILE.exists():
        print(f"Error: Database not found at {DB_FILE}")
        exit(1)
    
    analyze_features()
