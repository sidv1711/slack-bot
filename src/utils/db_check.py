"""Database check utilities."""
from supabase import create_client
from ..config.settings import get_settings
from loguru import logger

async def check_table_exists():
    """Check if the tables exist and print their structure."""
    try:
        settings = get_settings()
        supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)
        
        # Check user_mappings table
        logger.info("\nChecking user_mappings table:")
        result = supabase.table('user_mappings').select("*").limit(1).execute()
        logger.info("✅ user_mappings table exists!")
        
        table_info = supabase.table('user_mappings').select("*").execute()
        logger.info(f"User mappings data: {table_info.data if table_info.data else 'Empty table'}")
        
        # Check slack_installations table
        logger.info("\nChecking slack_installations table:")
        result = supabase.table('slack_installations').select("*").limit(1).execute()
        logger.info("✅ slack_installations table exists!")
        
        table_info = supabase.table('slack_installations').select("*").execute()
        logger.info(f"Slack installations data: {table_info.data if table_info.data else 'Empty table'}")
        
        # Check RLS policies for both tables
        logger.info("\nChecking RLS policies:")
        policies_query = """
        SELECT tablename, policyname, permissive, roles, cmd, qual
        FROM pg_policies 
        WHERE tablename IN ('user_mappings', 'slack_installations');
        """
        policies = supabase.query(policies_query).execute()
        logger.info("RLS Policies:")
        for policy in policies.data:
            logger.info(f"Policy: {policy}")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking tables: {str(e)}")
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(check_table_exists()) 