"""
Step 1: Data Ingestion & SQL Setup
Load CSV data into SQLite database with proper schema
"""

import pandas as pd
import sqlite3
from datetime import datetime
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setup paths
PROJECT_DIR = Path(__file__).parent
CSV_FILE = PROJECT_DIR / 'V_EVENT_DETAILS_202512311554.csv'
DB_FILE = PROJECT_DIR / 'event_intelligence.db'

def create_database_schema(conn):
    """Create event_details table with appropriate schema"""
    cursor = conn.cursor()
    
    # Drop existing table for clean setup
    cursor.execute('DROP TABLE IF EXISTS event_details')
    
    # Create event_details table
    create_table_sql = '''
    CREATE TABLE IF NOT EXISTS event_details (
        -- Primary Key
        ALARM_ID INTEGER PRIMARY KEY,
        
        -- Core event information
        PRIORITY TEXT,
        COMPONENT_ID INTEGER,
        ALARM_GENERATED_TIME TIMESTAMP,
        SEVERITY TEXT,
        URGENCY TEXT,
        
        -- Agency and operational information
        SECONDARY_AGENCY TEXT,
        PRIMARY_AGENCY TEXT,
        EVENT_AGENCY TEXT,
        
        -- Escalation and status tracking
        BPM_ESCULATION_COUNT INTEGER,
        ALARM_STATUS TEXT,
        EVENT_STATUS TEXT,
        
        -- Documentation and details
        SOP_DOCUMENT_URL TEXT,
        SOP_NAME TEXT,
        SOP_ID INTEGER,
        ALARM_NAME TEXT,
        
        -- Location information
        LATITUDE REAL,
        LONGITUDE REAL,
        LOCATION TEXT,
        JURISDICTION_NAME TEXT,
        SITE_NAME TEXT,
        
        -- Device and component information
        DEVICE_NAME TEXT,
        DEVICE_TYPE TEXT,
        DEVICE_TYPE_NAME TEXT,
        
        -- Event and incident tracking
        EVENT_ID TEXT,
        EVENT_CREATED_TIME TIMESTAMP,
        EVENT_OCCURRENCE_TIME TIMESTAMP,
        INCIDENT_TIME_TO_COMPLETE TEXT,
        
        -- Complaint and reference
        COMPLAINT_ID TEXT,
        CATEGORY_NAME TEXT,
        CATEGORY_ID INTEGER,
        
        -- Additional tracking
        COMPANY_ID INTEGER,
        COMPANY_CODE TEXT,
        USER_NAME TEXT,
        CREATED_BY TEXT,
        
        -- Metadata status flags
        IS_SEEN INTEGER,
        IS_EVIDENCE INTEGER,
        IS_IMPACT INTEGER,
        
        -- Operational notes
        REASON_FOR_SOP_CLOSE TEXT,
        EXTRA_DETAILS_5 TEXT,
        ADDITIONAL_DETAILS TEXT,
        
        -- URLs and media
        IMAGE_URL TEXT,
        SOP_DOCUMENT_URL_BACKUP TEXT,
        
        -- Timestamps for reconciliation
        RECORD_CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        RECORD_UPDATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    '''
    
    cursor.execute(create_table_sql)
    conn.commit()
    logger.info("[OK] Created event_details table")


def load_csv_data(conn, csv_path):
    """Load CSV data into SQLite database"""
    logger.info(f"Reading CSV from: {csv_path}")
    
    # Read CSV file
    df = pd.read_csv(csv_path)
    logger.info(f"[OK] Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
    
    # Select relevant columns for the event_details table
    relevant_columns = [
        'ALARM_ID', 'PRIORITY', 'COMPONENT_ID', 'ALARM_GENERATED_TIME',
        'SEVERITY', 'URGENCY', 'SECONDARY_AGENCY', 'PRIMARY_AGENCY',
        'EVENT_AGENCY', 'BPM_ESCULATION_COUNT', 'ALARM_STATUS', 'EVENT_STATUS',
        'SOP_DOCUMENT_URL', 'SOP_NAME', 'SOP_ID', 'ALARM_NAME',
        'LATITUDE', 'LONGITUDE', 'LOCATION', 'JURISDICTION_NAME', 'SITE_NAME',
        'DEVICE_NAME', 'DEVICE_TYPE', 'DEVICE_TYPE_NAME', 'EVENT_ID',
        'EVENT_CREATED_TIME', 'EVENT_OCCURRENCE_TIME', 'INCIDENT_TIME_TO_COMPLETE',
        'COMPLAINT_ID', 'CATEGORY_NAME', 'CATEGORY_ID', 'COMPANY_ID',
        'COMPANY_CODE', 'USER_NAME', 'CREATED_BY', 'IS_SEEN', 'IS_EVIDENCE',
        'IS_IMPACT', 'REASON_FOR_SOP_CLOSE', 'EXTRA_DETAILS_5',
        'ADDITIONAL_DETAILS', 'IMAGE_URL'
    ]
    
    # Filter to available columns
    available_cols = [col for col in relevant_columns if col in df.columns]
    df_filtered = df[available_cols].copy()
    
    logger.info(f"[OK] Selected {len(available_cols)} relevant columns for storage")
    
    # Data type conversions
    # Convert timestamps
    timestamp_columns = [col for col in ['ALARM_GENERATED_TIME', 'EVENT_CREATED_TIME', 
                                         'EVENT_OCCURRENCE_TIME'] if col in df_filtered.columns]
    for col in timestamp_columns:
        try:
            df_filtered[col] = pd.to_datetime(df_filtered[col], errors='coerce')
        except Exception as e:
            logger.warning(f"Could not parse {col}: {e}")
    
    # Convert numeric columns
    numeric_columns = ['ALARM_ID', 'COMPONENT_ID', 'BPM_ESCULATION_COUNT', 
                      'SOP_ID', 'CATEGORY_ID', 'COMPANY_ID', 'LATITUDE', 'LONGITUDE']
    for col in numeric_columns:
        if col in df_filtered.columns:
            df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')
    
    # Convert boolean/integer flags
    flag_columns = ['IS_SEEN', 'IS_EVIDENCE', 'IS_IMPACT']
    for col in flag_columns:
        if col in df_filtered.columns:
            df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce').fillna(0).astype(int)
    
    # Drop duplicates based on ALARM_ID
    df_filtered = df_filtered.drop_duplicates(subset=['ALARM_ID'], keep='first')
    logger.info(f"[OK] After deduplication: {len(df_filtered)} unique records")
    
    # Insert data into database
    try:
        df_filtered.to_sql('event_details', conn, if_exists='append', index=False)
        conn.commit()
        logger.info(f"[OK] Successfully loaded {len(df_filtered)} records into event_details table")
    except Exception as e:
        logger.error(f"[ERROR] Error loading data: {e}")
        raise


def verify_data_integrity(conn):
    """Verify data loaded successfully"""
    cursor = conn.cursor()
    
    # Check record count
    cursor.execute('SELECT COUNT(*) FROM event_details')
    total_records = cursor.fetchone()[0]
    logger.info(f"[OK] Total records in database: {total_records}")
    
    # Check schema
    cursor.execute("PRAGMA table_info(event_details)")
    columns = cursor.fetchall()
    logger.info(f"[OK] Table columns: {len(columns)}")
    
    # Sample data verification
    cursor.execute('SELECT * FROM event_details LIMIT 1')
    sample = cursor.fetchone()
    if sample:
        logger.info("[OK] Sample record retrieved successfully")
    
    # Check data distribution
    cursor.execute('SELECT PRIORITY, COUNT(*) as count FROM event_details GROUP BY PRIORITY')
    priority_dist = cursor.fetchall()
    logger.info("[OK] Priority distribution:")
    for priority, count in priority_dist:
        logger.info(f"  - {priority}: {count} records")
    
    # Check date range
    cursor.execute('SELECT MIN(ALARM_GENERATED_TIME), MAX(ALARM_GENERATED_TIME) FROM event_details')
    date_range = cursor.fetchone()
    logger.info(f"[OK] Data date range: {date_range[0]} to {date_range[1]}")
    
    # Check null values in key columns
    key_columns = ['ALARM_ID', 'PRIORITY', 'COMPONENT_ID', 'ALARM_GENERATED_TIME']
    cursor.execute('SELECT * FROM event_details LIMIT 0')
    for col in key_columns:
        cursor.execute(f'SELECT COUNT(*) FROM event_details WHERE {col} IS NULL')
        null_count = cursor.fetchone()[0]
        logger.info(f"[OK] NULL values in {col}: {null_count}")


def main():
    """Main data ingestion workflow"""
    logger.info("=" * 60)
    logger.info("Step 1: Data Ingestion & SQL Setup")
    logger.info("=" * 60)
    
    try:
        # Check if CSV exists
        if not CSV_FILE.exists():
            logger.error(f"[ERROR] CSV file not found: {CSV_FILE}")
            return False
        
        logger.info(f"CSV file found: {CSV_FILE}")
        
        # Connect to SQLite database
        logger.info(f"Connecting to database: {DB_FILE}")
        conn = sqlite3.connect(str(DB_FILE))
        
        # Create schema
        logger.info("Creating database schema...")
        create_database_schema(conn)
        
        # Load data
        logger.info("Loading CSV data into database...")
        load_csv_data(conn, CSV_FILE)
        
        # Verify data integrity
        logger.info("\nVerifying data integrity...")
        verify_data_integrity(conn)
        
        # Close connection
        conn.close()
        logger.info(f"\n[OK] Database saved to: {DB_FILE}")
        logger.info("=" * 60)
        logger.info("[OK] Step 1 Complete: Data ingestion successful!")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Error during data ingestion: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
