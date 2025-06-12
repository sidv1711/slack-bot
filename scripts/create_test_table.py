#!/usr/bin/env python3
"""Create test_history table and populate with sample data."""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from supabase import create_client
from config.settings import get_settings
from loguru import logger

def create_test_table():
    """Create test_history table and populate with sample data."""
    try:
        settings = get_settings()
        supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
        
        logger.info("Creating test_history table and sample data...")
        
        # First, let's check if the table already has data
        try:
            existing_data = supabase.table("test_history").select("*").limit(1).execute()
            if existing_data.data:
                logger.info("test_history table already has data, skipping creation")
                logger.info(f"Sample existing data: {existing_data.data[0]}")
                return
        except Exception as e:
            logger.info(f"Table doesn't exist yet or is empty: {e}")
        
        # Create sample test data
        now = datetime.now()
        sample_data = [
            {
                "id": str(uuid.uuid4()),
                "test_uid": "TEST_001",
                "execution_time": (now - timedelta(hours=1)).isoformat(),
                "status": "passed",
                "metadata": {"duration": 45, "environment": "staging"}
            },
            {
                "id": str(uuid.uuid4()),
                "test_uid": "TEST_002", 
                "execution_time": (now - timedelta(hours=2)).isoformat(),
                "status": "failed",
                "metadata": {"duration": 120, "error": "timeout", "environment": "production"}
            },
            {
                "id": str(uuid.uuid4()),
                "test_uid": "TEST_003",
                "execution_time": (now - timedelta(hours=3)).isoformat(),
                "status": "passed",
                "metadata": {"duration": 30, "environment": "staging"}
            },
            {
                "id": str(uuid.uuid4()),
                "test_uid": "TEST_001",
                "execution_time": (now - timedelta(days=1)).isoformat(),
                "status": "failed",
                "metadata": {"duration": 90, "error": "assertion failed", "environment": "staging"}
            },
            {
                "id": str(uuid.uuid4()),
                "test_uid": "TEST_004",
                "execution_time": (now - timedelta(days=2)).isoformat(),
                "status": "passed",
                "metadata": {"duration": 60, "environment": "production"}
            },
            {
                "id": str(uuid.uuid4()),
                "test_uid": "TEST_002",
                "execution_time": (now - timedelta(days=3)).isoformat(),
                "status": "passed",
                "metadata": {"duration": 75, "environment": "staging"}
            },
            {
                "id": str(uuid.uuid4()),
                "test_uid": "TEST_005",
                "execution_time": (now - timedelta(days=4)).isoformat(),
                "status": "running",
                "metadata": {"environment": "staging"}
            },
            {
                "id": str(uuid.uuid4()),
                "test_uid": "TEST_003",
                "execution_time": (now - timedelta(days=5)).isoformat(),
                "status": "skipped", 
                "metadata": {"reason": "dependency failure", "environment": "production"}
            },
            {
                "id": str(uuid.uuid4()),
                "test_uid": "TEST_006",
                "execution_time": (now - timedelta(days=6)).isoformat(),
                "status": "passed",
                "metadata": {"duration": 25, "environment": "staging"}
            },
            {
                "id": str(uuid.uuid4()),
                "test_uid": "TEST_001",
                "execution_time": (now - timedelta(weeks=1)).isoformat(),
                "status": "passed",
                "metadata": {"duration": 40, "environment": "production"}
            }
        ]
        
        # Insert sample data
        logger.info("Inserting sample test data...")
        result = supabase.table("test_history").insert(sample_data).execute()
        
        if result.data:
            logger.info(f"✅ Successfully inserted {len(result.data)} test records")
            logger.info("Sample data:")
            for i, row in enumerate(result.data[:3], 1):
                logger.info(f"  {i}. {row['test_uid']} - {row['status']} - {row['execution_time']}")
            if len(result.data) > 3:
                logger.info(f"  ... and {len(result.data) - 3} more records")
        else:
            logger.warning("No data was inserted")
        
        # Verify we can query the data
        logger.info("Verifying data access...")
        test_query = supabase.table("test_history").select("*").limit(5).execute()
        logger.info(f"✅ Can query test_history table: {len(test_query.data)} rows returned")
        
        logger.info("🎉 Test table setup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error creating test table: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting test table creation...")
    create_test_table() 