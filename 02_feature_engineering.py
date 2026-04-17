"""
Step 2: Feature Engineering
===========================

Module: 02_feature_engineering
Version: 1.0
Author: Event Intelligence Team
Date: April 2026

Description:
    Second step of RAG pipeline. Transforms raw event data into rich textual
    representations optimized for embedding and semantic search. Creates
    narrative descriptions combining structured metadata into cohesive text.

Functionality:
    - Text normalization and cleaning
    - Narrative generation from event data
    - Structured metadata formatting
    - Feature enrichment
    - Text quality validation
    - SQL column updates

Features Created:
    - event_text: Narrative description combining all relevant event info
    - Component information
    - Priority context
    - Temporal markers
    - Agency information

Input:
    SQLite Table: event_details

Output:
    SQLite Table: event_details (updated with event_text column)

Usage:
    python 02_feature_engineering.py

Dependencies:
    - pandas
    - sqlite3 (stdlib)
    - re (stdlib)
"""

import sqlite3
import pandas as pd
from datetime import datetime
import logging
from pathlib import Path
import re
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setup paths
PROJECT_DIR = Path(__file__).parent
DB_FILE = PROJECT_DIR / 'event_intelligence.db'

class FeatureEngineer:
    """Transform raw event data into enriched features for RAG system"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        logger.info(f"Connected to database: {self.db_path}")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def create_features_table(self):
        """Create table for enriched features"""
        cursor = self.conn.cursor()
        
        # Drop existing table for clean setup
        cursor.execute('DROP TABLE IF EXISTS event_features')
        
        create_sql = '''
        CREATE TABLE event_features (
            ALARM_ID INTEGER PRIMARY KEY,
            
            -- Narrative text for embedding
            event_text TEXT NOT NULL,
            
            -- Structured metadata for filtering/retrieval
            priority TEXT,
            component_id INTEGER,
            severity TEXT,
            urgency TEXT,
            month TEXT,
            
            -- Additional contextual metadata
            year INTEGER,
            day_of_week TEXT,
            hour_of_day INTEGER,
            
            -- Agency and operational context
            primary_agency TEXT,
            secondary_agency TEXT,
            
            -- Location context
            latitude REAL,
            longitude REAL,
            jurisdiction_name TEXT,
            
            -- Event classification
            alarm_name TEXT,
            category_name TEXT,
            device_type TEXT,
            
            -- Status tracking
            alarm_status TEXT,
            event_status TEXT,
            
            -- Escalation context
            bpm_esculation_count INTEGER,
            
            -- Timestamps
            alarm_generated_time TIMESTAMP,
            event_created_time TIMESTAMP,
            
            -- Audit
            record_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''
        
        cursor.execute(create_sql)
        self.conn.commit()
        logger.info("[OK] Created event_features table")
    
    def create_event_narrative(self, row):
        """
        Create rich narrative text from event data
        Combines multiple fields into coherent, human-readable format
        """
        narrative_parts = []
        
        # 1. Event Type and Priority
        event_type = row['ALARM_NAME'] or 'Incident'
        priority = row['PRIORITY'] or 'Unknown Priority'
        alarm_id = row['ALARM_ID']
        
        narrative_parts.append(
            f"Alarm ID {alarm_id}: {priority.upper()} priority {event_type} event"
        )
        
        # 2. Time Information
        if row['ALARM_GENERATED_TIME']:
            time_str = row['ALARM_GENERATED_TIME']
            narrative_parts.append(f"occurred on {time_str}")
        
        # 3. Location Information
        location_parts = []
        if row['LOCATION']:
            location_parts.append(row['LOCATION'])
        if row['JURISDICTION_NAME']:
            location_parts.append(f"in {row['JURISDICTION_NAME']}")
        if location_parts:
            narrative_parts.append(", ".join(location_parts))
        
        # 4. Geographical Coordinates
        if row['LATITUDE'] and row['LONGITUDE']:
            narrative_parts.append(
                f"at coordinates ({row['LATITUDE']:.4f}, {row['LONGITUDE']:.4f})"
            )
        
        # 5. Device/Component Information
        if row['COMPONENT_ID']:
            component_context = self._get_component_context(row['COMPONENT_ID'])
            narrative_parts.append(f"affecting Component {row['COMPONENT_ID']} ({component_context})")
        
        if row['DEVICE_NAME']:
            device_detail = f"Device: {row['DEVICE_NAME']}"
            if row['DEVICE_TYPE']:
                device_detail += f" (Type: {row['DEVICE_TYPE']})"
            narrative_parts.append(device_detail)
        
        # 6. Severity and Urgency
        details = []
        if row['SEVERITY']:
            details.append(f"Severity: {row['SEVERITY']}")
        if row['URGENCY']:
            details.append(f"Urgency: {row['URGENCY']}")
        if details:
            narrative_parts.append(". ".join(details))
        
        # 7. Agency Information
        agencies = []
        if row['PRIMARY_AGENCY']:
            agencies.append(f"Primary: {row['PRIMARY_AGENCY']}")
        if row['SECONDARY_AGENCY']:
            secondary_list = row['SECONDARY_AGENCY'].split(',')
            secondary_clean = [a.strip() for a in secondary_list]
            agencies.append(f"Secondary: {', '.join(secondary_clean)}")
        if agencies:
            narrative_parts.append(f"Responding agencies: {' | '.join(agencies)}")
        
        # 8. Category and Operational Context
        if row['CATEGORY_NAME']:
            narrative_parts.append(f"Category: {row['CATEGORY_NAME']}")
        
        # 9. SOP and Status Information
        if row['SOP_NAME']:
            narrative_parts.append(f"SOP: {row['SOP_NAME']}")
        if row['ALARM_STATUS']:
            narrative_parts.append(f"Status: {row['ALARM_STATUS']}")
        if row['EVENT_STATUS']:
            narrative_parts.append(f"Event Status: {row['EVENT_STATUS']}")
        
        # 10. Escalation Status
        if row['BPM_ESCULATION_COUNT'] and row['BPM_ESCULATION_COUNT'] > 0:
            narrative_parts.append(
                f"Escalation Count: {row['BPM_ESCULATION_COUNT']} escalations"
            )
        
        # 11. Additional Context
        if row['REASON_FOR_SOP_CLOSE']:
            narrative_parts.append(f"Close Reason: {row['REASON_FOR_SOP_CLOSE']}")
        
        # Combine all parts into coherent narrative
        full_narrative = ". ".join(filter(None, narrative_parts))
        # Add period if missing
        if not full_narrative.endswith('.'):
            full_narrative += '.'
        
        return full_narrative
    
    def _get_component_context(self, component_id):
        """Get contextual description for component"""
        component_descriptions = {
            100: 'Enterprise System',
            101: 'Database Server',
            102: 'API Gateway',
            103: 'IoT Sensor Hub',
            312: 'Primary Monitor',
            313: 'Secondary Monitor',
            319: 'Network Infrastructure',
            325: 'Mobile Device',
            327: 'Edge Device',
        }
        return component_descriptions.get(component_id, 'System Component')
    
    def extract_metadata(self, row):
        """Extract and transform metadata from event"""
        metadata = {}
        
        # Basic priority and severity
        metadata['priority'] = row['PRIORITY']
        metadata['severity'] = row['SEVERITY']
        metadata['urgency'] = row['URGENCY']
        
        # Component ID
        metadata['component_id'] = row['COMPONENT_ID']
        
        # Temporal metadata
        if row['ALARM_GENERATED_TIME']:
            try:
                dt = datetime.fromisoformat(row['ALARM_GENERATED_TIME'].replace(' ', 'T'))
                months = ['January', 'February', 'March', 'April', 'May', 'June',
                         'July', 'August', 'September', 'October', 'November', 'December']
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                
                metadata['month'] = months[dt.month - 1]
                metadata['year'] = dt.year
                metadata['day_of_week'] = days[dt.weekday()]
                metadata['hour_of_day'] = dt.hour
            except Exception as e:
                logger.warning(f"Could not parse timestamp for ALARM_ID {row['ALARM_ID']}: {e}")
                metadata['month'] = None
                metadata['year'] = None
                metadata['day_of_week'] = None
                metadata['hour_of_day'] = None
        else:
            metadata['month'] = None
            metadata['year'] = None
            metadata['day_of_week'] = None
            metadata['hour_of_day'] = None
        
        # Operational metadata
        metadata['primary_agency'] = row['PRIMARY_AGENCY']
        metadata['secondary_agency'] = row['SECONDARY_AGENCY']
        metadata['alarm_status'] = row['ALARM_STATUS']
        metadata['event_status'] = row['EVENT_STATUS']
        
        # Location metadata
        metadata['latitude'] = row['LATITUDE']
        metadata['longitude'] = row['LONGITUDE']
        metadata['jurisdiction_name'] = row['JURISDICTION_NAME']
        
        # Context metadata
        metadata['alarm_name'] = row['ALARM_NAME']
        metadata['category_name'] = row['CATEGORY_NAME']
        metadata['device_type'] = row['DEVICE_TYPE']
        
        # Escalation metadata
        metadata['bpm_esculation_count'] = row['BPM_ESCULATION_COUNT']
        
        # Timestamps
        metadata['alarm_generated_time'] = row['ALARM_GENERATED_TIME']
        metadata['event_created_time'] = row['EVENT_CREATED_TIME']
        
        return metadata
    
    def engineer_features(self):
        """Transform raw data into enriched features"""
        cursor = self.conn.cursor()
        
        logger.info("Reading raw event data...")
        # Read all events
        cursor.execute('SELECT * FROM event_details')
        rows = cursor.fetchall()
        logger.info(f"[OK] Read {len(rows)} events from database")
        
        # Process each event
        logger.info("Engineering features for each event...")
        features_list = []
        
        for i, row in enumerate(rows):
            if (i + 1) % 500 == 0:
                logger.info(f"  Processing: {i + 1}/{len(rows)}")
            
            # Create narrative
            event_text = self.create_event_narrative(row)
            
            # Extract metadata
            metadata = self.extract_metadata(row)
            
            # Build feature record
            feature_record = {
                'ALARM_ID': row['ALARM_ID'],
                'event_text': event_text,
                'priority': metadata['priority'],
                'component_id': metadata['component_id'],
                'severity': metadata['severity'],
                'urgency': metadata['urgency'],
                'month': metadata['month'],
                'year': metadata['year'],
                'day_of_week': metadata['day_of_week'],
                'hour_of_day': metadata['hour_of_day'],
                'primary_agency': metadata['primary_agency'],
                'secondary_agency': metadata['secondary_agency'],
                'latitude': metadata['latitude'],
                'longitude': metadata['longitude'],
                'jurisdiction_name': metadata['jurisdiction_name'],
                'alarm_name': metadata['alarm_name'],
                'category_name': metadata['category_name'],
                'device_type': metadata['device_type'],
                'alarm_status': metadata['alarm_status'],
                'event_status': metadata['event_status'],
                'bpm_esculation_count': metadata['bpm_esculation_count'],
                'alarm_generated_time': metadata['alarm_generated_time'],
                'event_created_time': metadata['event_created_time'],
            }
            
            features_list.append(feature_record)
        
        logger.info(f"[OK] Engineered features for {len(features_list)} events")
        
        # Insert into features table
        logger.info("Inserting engineered features into database...")
        df_features = pd.DataFrame(features_list)
        df_features.to_sql('event_features', self.conn, if_exists='append', index=False)
        self.conn.commit()
        logger.info(f"[OK] Inserted {len(df_features)} feature records")
    
    def verify_features(self):
        """Verify features were created successfully"""
        cursor = self.conn.cursor()
        
        logger.info("\nVerifying feature engineering...")
        
        # Count records
        cursor.execute('SELECT COUNT(*) FROM event_features')
        total = cursor.fetchone()[0]
        logger.info(f"[OK] Total feature records: {total}")
        
        # Check for event_text
        cursor.execute('SELECT COUNT(*) FROM event_features WHERE event_text IS NOT NULL')
        with_text = cursor.fetchone()[0]
        logger.info(f"[OK] Records with event_text: {with_text}")
        
        # Check metadata completeness
        cursor.execute('SELECT COUNT(*) FROM event_features WHERE priority IS NOT NULL')
        with_priority = cursor.fetchone()[0]
        logger.info(f"[OK] Records with priority metadata: {with_priority}")
        
        cursor.execute('SELECT COUNT(*) FROM event_features WHERE month IS NOT NULL')
        with_month = cursor.fetchone()[0]
        logger.info(f"[OK] Records with month metadata: {with_month}")
        
        # Sample narrative text
        logger.info("\n--- Sample Event Narratives ---")
        cursor.execute('SELECT ALARM_ID, event_text FROM event_features LIMIT 3')
        for alarm_id, text in cursor.fetchall():
            logger.info(f"\nAlarm {alarm_id}:\n  {text}")
        
        # Metadata distribution
        logger.info("\n--- Priority Distribution ---")
        cursor.execute('''
            SELECT priority, COUNT(*) as count 
            FROM event_features 
            WHERE priority IS NOT NULL
            GROUP BY priority 
            ORDER BY count DESC
        ''')
        for priority, count in cursor.fetchall():
            logger.info(f"  {priority}: {count}")
        
        logger.info("\n--- Month Distribution ---")
        cursor.execute('''
            SELECT month, COUNT(*) as count 
            FROM event_features 
            WHERE month IS NOT NULL
            GROUP BY month 
            ORDER BY count DESC
        ''')
        for month, count in cursor.fetchall():
            logger.info(f"  {month}: {count}")
        
        # Average text length
        cursor.execute('SELECT AVG(LENGTH(event_text)) FROM event_features')
        avg_length = cursor.fetchone()[0]
        logger.info(f"\n[OK] Average narrative length: {avg_length:.0f} characters")


def main():
    """Main feature engineering workflow"""
    logger.info("=" * 70)
    logger.info("Step 2: Feature Engineering")
    logger.info("=" * 70)
    
    try:
        # Check database exists
        if not DB_FILE.exists():
            logger.error(f"[ERROR] Database not found: {DB_FILE}")
            logger.info("  Please run Step 1 (01_data_ingestion.py) first")
            return False
        
        # Initialize feature engineer
        engineer = FeatureEngineer(DB_FILE)
        engineer.connect()
        
        # Create features table
        logger.info("\nCreating features table...")
        engineer.create_features_table()
        
        # Engineer features
        logger.info("\nEngineering features...")
        engineer.engineer_features()
        
        # Verify
        logger.info("\nVerifying engineered features...")
        engineer.verify_features()
        
        # Close connection
        engineer.close()
        
        logger.info("\n" + "=" * 70)
        logger.info("[OK] Step 2 Complete: Feature Engineering successful!")
        logger.info("=" * 70 + "\n")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Error during feature engineering: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
