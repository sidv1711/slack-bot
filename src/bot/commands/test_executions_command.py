"""Test executions command handler for Slack bot."""
import re
from typing import Dict, Any
from loguru import logger

from ..types import SlackCommand, SlackResponse
from .base import BaseCommandHandler
from ...services.database_service import DatabaseService
from ...services.report_service import ReportService
from ...auth.mapping_service import UserMappingService
from ...auth.dependencies import get_user_mapping_service
from ...config.settings import get_settings
from ...auth.user_store import MemoryUserMappingStore
from ...auth.supabase_store import SupabaseUserMappingStore

class TestExecutionsCommandHandler(BaseCommandHandler):
    """Handler for test executions slash command."""
    
    def __init__(self, slack_client):
        """Initialize the test executions command handler."""
        super().__init__(slack_client)
        self.database_service = DatabaseService()
        self.report_service = ReportService()
        
        # Initialize user mapping service
        settings = get_settings()
        if settings.development_mode:
            store = MemoryUserMappingStore()
        else:
            store = SupabaseUserMappingStore(settings)
        
        self.user_mapping_service = UserMappingService(store=store, slack_client=slack_client)
        
    async def handle(self, command_data: dict) -> dict:
        """Handle the test executions command."""
        try:
            text = command_data.get("text", "").strip()
            channel_id = command_data.get("channel_id")
            user_name = command_data.get("user_name", "User")
            user_id = command_data.get("user_id")
            team_id = command_data.get("team_id")
            
            # Check if user is authenticated
            propelauth_user_id = await self.user_mapping_service.get_propelauth_user_for_slack(user_id, team_id)
            if not propelauth_user_id:
                await self.slack_client.send_message(
                    channel=channel_id,
                    text=f"🔐 **Authentication Required**\n\nHi {user_name}! You need to connect your Slack account to PropelAuth first.\n\n**Please run:** `/connect-slack`\n\nThis will link your accounts so you can access personalized test reports."
                )
                return {"ok": True, "message": "Authentication required", "error": None, "received": command_data}
            
            if text.lower() == "list":
                return await self._handle_list_tests(channel_id, user_name, command_data)
            
            # Parse the command
            test_id, limit = self._parse_command(text)
            
            if not test_id:
                await self._send_help_message(channel_id, user_name)
                return {"ok": True, "message": "Help message sent", "error": None, "received": command_data}
            
            # Send immediate response to avoid timeout - BEFORE any processing
            processing_msg = await self.slack_client.send_message(
                channel=channel_id,
                text=f"🔄 **Processing test executions for `{test_id}`**\n\nQuerying database and generating report links... Please wait."
            )
            
            # Process everything else in background and return immediately
            import asyncio
            asyncio.create_task(self._process_test_executions_async(
                test_id, limit, channel_id, user_name, propelauth_user_id, processing_msg, command_data
            ))
            
            return {"ok": True, "message": "Processing started", "error": None, "received": command_data}
            
        except Exception as e:
            logger.error(f"Error processing test executions command: {str(e)}")
            await self.slack_client.send_message(
                channel=channel_id,
                text=f"❌ **Error**\n\nSorry {user_name}, there was an error processing your request:\n`{str(e)}`"
            )
            return {"ok": False, "error": str(e), "received": command_data}
    
    def _parse_command(self, text: str) -> tuple:
        """Parse command text to extract test_id and limit."""
        if not text:
            return None, 5
        
        parts = text.strip().split()
        if not parts:
            return None, 5
        
        test_id = parts[0]
        limit = 5  # default
        
        # Look for limit in remaining parts
        for part in parts[1:]:
            if part.isdigit():
                limit = min(int(part), 20)  # cap at 20
                break
            elif part.startswith("limit="):
                try:
                    limit = min(int(part.split("=")[1]), 20)
                    break
                except (ValueError, IndexError):
                    continue
        
        return test_id, limit
    
    async def _send_help_message(self, channel_id: str, user_name: str):
        """Send help message for the command."""
        help_text = f"""📋 **Test Executions Command Help**

Hi {user_name}! Here's how to use the `/test-executions` command:

**📖 Usage:**
• `/test-executions <test-id>` - Show last 5 executions
• `/test-executions <test-id> <number>` - Show last N executions (max 20)
• `/test-executions <test-id> limit=<number>` - Alternative format
• `/test-executions list` - Show available test IDs

**📝 Examples:**
• `/test-executions abc123` - Last 5 executions for test abc123
• `/test-executions abc123 10` - Last 10 executions for test abc123
• `/test-executions list` - Show all available tests

**🔐 Note:** You must be connected to PropelAuth to access reports. Run `/connect-slack` if needed."""
        
        await self.slack_client.send_message(channel=channel_id, text=help_text)
    
    async def _generate_table_message(self, test_id: str, executions: list, propelauth_user_id: str) -> str:
        """Generate formatted table message for executions."""
        if not executions:
            return f"📋 No executions found for test `{test_id}`"
        
        # Generate shareable links for all executions using ReportService first
        logger.info(f"Generating shareable links for {len(executions)} executions via Cognisim API")
        report_links = await self.report_service.generate_multiple_links_with_propelauth_user(
            executions, propelauth_user_id
        )
        logger.info(f"Generated {len([link for link in report_links.values() if link])} shareable links")
        
        # Start message lines (table will include its own header)
        message_lines = [
            f"📊 **Test Executions for `{test_id}`**",
            f"Found {len(executions)} execution(s)",
            ""
        ]
        
        # Create aligned table with clickable links in Report column
        # Use monospace for structure but outside code block to allow links
        table_lines = [
            "` # | Status       | Execution Time | Duration | Report`",
            "`---+--------------+----------------+----------+-------`"
        ]
        
        # Process each execution
        for i, execution in enumerate(executions, 1):
            try:
                # Extract data
                success = execution.get("success")
                execution_time = execution.get("execution_time", "Unknown")
                duration = execution.get("duration", "Unknown")
                execution_id = execution.get("id", "")
                
                # Format execution time
                if execution_time and execution_time != "Unknown":
                    try:
                        from datetime import datetime
                        if isinstance(execution_time, str):
                            dt = datetime.fromisoformat(execution_time.replace('Z', '+00:00'))
                        else:
                            dt = execution_time
                        formatted_time = dt.strftime("%m/%d %H:%M")
                    except:
                        formatted_time = str(execution_time)[:10]
                else:
                    formatted_time = "Unknown"
                
                # Format duration
                if duration and duration != "Unknown":
                    try:
                        if isinstance(duration, (int, float)):
                            formatted_duration = f"{duration:.1f}s"
                        else:
                            formatted_duration = str(duration)
                    except:
                        formatted_duration = "Unknown"
                else:
                    formatted_duration = "Unknown"
                
                # Status - use simple reliable symbols
                if success is True:
                    status_text = "✅ PASS"  # Green checkmark (should render properly)
                elif success is False:
                    status_text = "❌ FAIL"  # Red X (should render properly)
                else:
                    status_text = "❓ UNK"   # Question mark for unknown
                
                # Get report link
                shareable_link = report_links.get(str(execution_id))
                if shareable_link:
                    report_cell = f"<{shareable_link}|View>"
                else:
                    report_cell = "N/A"
                
                # Format row with proper spacing (use backticks for monospace sections)
                row = f"`{i:2} | {status_text:12} | {formatted_time:14} | {formatted_duration:8} |` {report_cell}"
                table_lines.append(row)
                
            except Exception as e:
                logger.warning(f"Error formatting execution {i}: {e}")
                table_lines.append(f"`{i:2} | {'ERROR':12}  | {'-':14} | {'-':8} |` N/A")
        
        # Add the table to message
        message_lines.extend(table_lines)
        message_lines.append("")
        
        # Add summary statistics
        total_executions = len(executions)
        passed_count = sum(1 for ex in executions if ex.get("success") is True)
        failed_count = sum(1 for ex in executions if ex.get("success") is False)
        unknown_count = total_executions - passed_count - failed_count
        
        summary_lines = ["**Summary:**"]
        if passed_count > 0:
            summary_lines.append(f"• ✅ {passed_count} passed")
        if failed_count > 0:
            summary_lines.append(f"• ❌ {failed_count} failed")
        if unknown_count > 0:
            summary_lines.append(f"• 🟡 {unknown_count} unknown")
        
        message_lines.extend(summary_lines)
        message_lines.append("")
        
        # Add clean footer
        message_lines.extend([
            "",
            "💡 Click report links above to view detailed test results."
        ])
        
        return "\n".join(message_lines)
    
    async def _handle_list_tests(self, channel_id: str, user_name: str, command_data: dict):
        """Handle the list command to show available test IDs."""
        try:
            # First, let's check if there's any data in the table at all
            debug_query = "SELECT COUNT(*) as total_rows FROM test_history"
            debug_result = await self.database_service.execute_query(debug_query)
            
            logger.info(f"Debug query executed with service role authentication")
            logger.info(f"Database service using Supabase URL: {self.database_service.supabase_url if hasattr(self.database_service, 'supabase_url') else 'Unknown'}")
            
            if debug_result["success"]:
                total_rows = debug_result["data"][0].get("total_rows", 0) if debug_result["data"] else 0
                logger.info(f"Total rows in test_history table: {total_rows}")
                logger.info(f"Full debug result: {debug_result}")
                
                # If we can access the table, let's try to get a sample row to see the structure
                if total_rows == 0:
                    # Try a simple SELECT to see if we can access the table at all
                    sample_query = "SELECT * FROM test_history LIMIT 1"
                    sample_result = await self.database_service.execute_query(sample_query)
                    logger.info(f"Sample query result: {sample_result}")
                    
                    # Also try to see if there are any rows without filtering
                    count_all_query = "SELECT * FROM test_history"
                    count_all_result = await self.database_service.execute_query(count_all_query)
                    logger.info(f"All rows query result: {count_all_result}")
                    
                    # Let's also try to check if RLS is affecting us
                    logger.warning("Service role seeing 0 rows - this suggests RLS policies are restricting access")
                    logger.warning("Check Supabase Authentication > Policies for test_history table")
            else:
                logger.error(f"Failed to query test_history table: {debug_result}")
            
            # Skip the complex table investigation since it's not supported
            
            # Query for distinct test IDs
            sql_query = """
            SELECT DISTINCT test_uid, COUNT(*) as execution_count, MAX(execution_time) as latest_execution
            FROM test_history 
            GROUP BY test_uid 
            ORDER BY latest_execution DESC 
            LIMIT 20
            """
            
            result = await self.database_service.execute_query(sql_query)
            
            if not result["success"]:
                await self.slack_client.send_message(
                    channel=channel_id,
                    text=f"❌ Failed to fetch test list: {result.get('error', 'Unknown error')}"
                )
                return {"ok": False, "error": result.get("error", "Failed to fetch test list"), "message": None, "received": command_data}
            
            tests = result["data"]
            
            if not tests:
                # Check if the table is completely empty
                if debug_result["success"] and debug_result["data"]:
                    total_rows = debug_result["data"][0].get("total_rows", 0)
                    if total_rows == 0:
                        await self.slack_client.send_message(
                            channel=channel_id,
                            text=f"📋 **Database Investigation Results**\n\nHi {user_name}! The `test_history` table is completely empty (0 total rows).\n\n**This could mean:**\n• 🚀 No tests have been executed yet in the your_company app\n• 🔄 Tests are stored in a different table\n• 🔗 The bot is connected to a different database than the app\n• 📊 The testing system is still in setup phase\n\n**Next Steps:**\n1. **Try running some tests** in the your_company app first\n2. **Check database connection** - Verify bot connects to same DB as app\n3. **Contact your admin** if tests should already exist\n\n💡 The bot has also logged available database tables for debugging."
                        )
                    else:
                        await self.slack_client.send_message(
                            channel=channel_id,
                            text=f"📋 **Database Status**\n\nHi {user_name}! Found {total_rows} total rows in `test_history` but no distinct test IDs.\n\nThis suggests there might be data structure issues. Please contact support."
                        )
                else:
                    await self.slack_client.send_message(
                        channel=channel_id,
                        text="📋 No tests found in the database."
                    )
                return {"ok": True, "message": "No tests found in the database", "error": None, "received": command_data}
            
            # Format the test list
            lines = [
                f"📋 **Available Test IDs** (showing last 20)",
                f"Hi {user_name}! Here are the test IDs you can use:",
                ""
            ]
            
            for i, test in enumerate(tests, 1):
                test_uid = test.get("test_uid", "Unknown")
                count = test.get("execution_count", 0)
                latest = test.get("latest_execution", "")
                
                # Format the latest execution time
                if latest:
                    time_str = str(latest).split('+')[0].replace('T', ' ')
                    time_parts = time_str.split(' ')
                    if len(time_parts) >= 2:
                        date_part = time_parts[0]
                        time_display = f"{date_part}"
                    else:
                        time_display = time_str
                else:
                    time_display = "Unknown"
                
                lines.append(f"{i}. `{test_uid}` ({count} executions, latest: {time_display})")
            
            lines.extend([
                "",
                "**Usage Examples:**",
                f"• `/test-executions {tests[0].get('test_uid', 'TEST_ID')} 5`",
                f"• `/test-executions {tests[0].get('test_uid', 'TEST_ID')} limit=10`"
            ])
            
            formatted_text = "\n".join(lines)
            
            await self.slack_client.send_message(
                channel=channel_id,
                text=formatted_text
            )
            
            return {"ok": True, "message": "Test list sent", "error": None, "received": command_data}
            
        except Exception as e:
            logger.error(f"Error listing tests: {e}")
            await self.slack_client.send_message(
                channel=channel_id,
                text=f"❌ Error fetching test list: {str(e)}"
            )
            return {"ok": False, "error": str(e), "message": None, "received": command_data}
    
    async def _process_test_executions_async(
        self, 
        test_id: str, 
        limit: int, 
        channel_id: str, 
        user_name: str, 
        propelauth_user_id: str, 
        processing_msg: dict, 
        command_data: dict
    ):
        """Process test executions asynchronously in the background."""
        try:
            # Query the database with correct column names
            sql_query = f"""
            SELECT 
                id,
                test_uid,
                execution_time,
                success,
                metadata,
                duration,
                created_at,
                updated_at
            FROM test_history 
            WHERE test_uid = '{test_id}'
            ORDER BY execution_time DESC 
            LIMIT {limit}
            """
            
            logger.info(f"Executing query for test_id: {test_id}, limit: {limit}")
            result = await self.database_service.execute_query(sql_query)
            
            if not result["success"]:
                logger.error(f"Database query failed: {result.get('error', 'Unknown error')}")
                
                # Update the processing message with error
                error_msg = f"❌ **Database Error**\n\nSorry {user_name}, there was an error querying the database:\n`{result.get('error', 'Unknown error')}`"
                
                if processing_msg.get("ts"):
                    await self.slack_client.update_message(
                        channel=channel_id,
                        ts=processing_msg["ts"],
                        text=error_msg
                    )
                else:
                    await self.slack_client.send_message(
                        channel=channel_id,
                        text=error_msg
                    )
                
                return
            
            executions = result.get("data", [])
            logger.info(f"Query returned {len(executions)} executions")
            
            if not executions:
                # Update the processing message with no results
                no_results_msg = f"📋 **No Executions Found**\n\nHi {user_name}! No executions found for test ID: `{test_id}`\n\n**Possible reasons:**\n• Test ID doesn't exist\n• No executions have been run for this test\n• You don't have access to this test\n\n💡 Try `/test-executions list` to see available tests."
                
                if processing_msg.get("ts"):
                    await self.slack_client.update_message(
                        channel=channel_id,
                        ts=processing_msg["ts"],
                        text=no_results_msg
                    )
                else:
                    await self.slack_client.send_message(
                        channel=channel_id,
                        text=no_results_msg
                    )
                
                return
            
            # Convert tuples to dictionaries if needed
            column_names = ["id", "test_uid", "execution_time", "success", "metadata", "duration", "created_at", "updated_at"]
            processed_executions = []
            
            for execution in executions:
                if isinstance(execution, tuple):
                    # Convert tuple to dictionary
                    execution_dict = dict(zip(column_names, execution))
                    processed_executions.append(execution_dict)
                elif isinstance(execution, dict):
                    processed_executions.append(execution)
                else:
                    logger.warning(f"Unexpected execution data type: {type(execution)}")
                    continue
            
            logger.info(f"Processed {len(processed_executions)} executions successfully")
            
            # Generate the table asynchronously
            table_message = await self._generate_table_message(test_id, processed_executions, propelauth_user_id)
            
            # Create interactive blocks with help button
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": table_message
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📋 Having issues?"
                            },
                            "action_id": "test_executions_help",
                            "value": test_id,
                            "style": "primary"
                        }
                    ]
                }
            ]
            
            # Update the processing message with final results
            if processing_msg.get("ts"):
                await self.slack_client.update_message(
                    channel=channel_id,
                    ts=processing_msg["ts"],
                    text=f"Test executions for {test_id}",  # Fallback text
                    blocks=blocks
                )
            else:
                # Fallback: send new message if update fails
                await self.slack_client.send_message(
                    channel=channel_id,
                    text=f"Test executions for {test_id}",  # Fallback text
                    blocks=blocks
                )
            
            return
            
        except Exception as e:
            logger.error(f"Error processing test executions command: {str(e)}")
            await self.slack_client.send_message(
                channel=channel_id,
                text=f"❌ **Error**\n\nSorry {user_name}, there was an error processing your request:\n`{str(e)}`"
            )
            return 