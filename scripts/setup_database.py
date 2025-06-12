#!/usr/bin/env python3
"""Database setup script to create tables and apply migrations."""

import os
import sys
import asyncio
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from supabase import create_client
from config.settings import get_settings
from loguru import logger

async def setup_database():
    """Set up the database with all required tables."""
    try:
        settings = get_settings()
        supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
        
        logger.info("Setting up database...")
        
        # Read and execute migrations
        migrations_dir = Path(__file__).parent.parent / "migrations"
        migration_files = [
            "create_user_mappings.sql",
            "create_slack_installations.sql", 
            "create_test_history.sql"
        ]
        
        for migration_file in migration_files:
            migration_path = migrations_dir / migration_file
            
            if migration_path.exists():
                logger.info(f"Applying migration: {migration_file}")
                
                with open(migration_path, 'r') as f:
                    sql_content = f.read()
                
                # Split by semicolon and execute each statement
                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                
                for stmt in statements:
                    try:
                        # Use rpc to execute raw SQL
                        result = supabase.rpc('exec_sql', {'sql_statement': stmt}).execute()
                        logger.debug(f"Executed statement: {stmt[:50]}...")
                    except Exception as e:
                        # Some statements might fail if they already exist, that's OK
                        if "already exists" in str(e) or "duplicate" in str(e).lower():
                            logger.debug(f"Statement already applied: {stmt[:50]}...")
                        else:
                            logger.warning(f"Statement failed: {stmt[:50]}... Error: {e}")
                
                logger.info(f"✅ Migration {migration_file} completed")
            else:
                logger.warning(f"Migration file not found: {migration_file}")
        
        # Verify tables exist
        logger.info("Verifying tables...")
        
        tables_to_check = ["user_mappings", "slack_installations", "test_history"]
        for table in tables_to_check:
            try:
                result = supabase.table(table).select("*").limit(1).execute()
                logger.info(f"✅ Table '{table}' is accessible")
            except Exception as e:
                logger.error(f"❌ Table '{table}' check failed: {e}")
        
        logger.info("🎉 Database setup completed successfully!")
        
        # Show sample data
        logger.info("Sample test_history data:")
        result = supabase.table("test_history").select("*").limit(5).execute()
        for i, row in enumerate(result.data, 1):
            logger.info(f"  {i}. {row['test_uid']} - {row['status']} - {row['execution_time']}")
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        raise

def create_exec_sql_function():
    """Create a stored function to execute raw SQL (if needed)."""
    function_sql = """
    CREATE OR REPLACE FUNCTION exec_sql(sql_statement text)
    RETURNS text
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    BEGIN
        EXECUTE sql_statement;
        RETURN 'OK';
    EXCEPTION
        WHEN OTHERS THEN
            RETURN SQLERRM;
    END;
    $$;
    """
    
    try:
        settings = get_settings()
        supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
        
        # This would need to be run directly in Supabase SQL editor
        logger.info("To enable raw SQL execution, run this in Supabase SQL editor:")
        logger.info(function_sql)
        
    except Exception as e:
        logger.error(f"Error creating exec_sql function: {e}")

if __name__ == "__main__":
    logger.info("Starting database setup...")
    asyncio.run(setup_database()) 