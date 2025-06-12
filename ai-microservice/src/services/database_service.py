"""Database service for executing SQL queries safely."""
from typing import List, Dict, Any, Optional
from loguru import logger
from supabase import create_client, Client
from ..config.settings import get_settings

class DatabaseService:
    """Service for executing SQL queries against the database."""
    
    def __init__(self):
        """Initialize the database service."""
        self.settings = get_settings()
        self.supabase: Client = create_client(
            self.settings.supabase_url,
            self.settings.supabase_service_role_key
        )
        logger.info("Database service initialized")
    
    async def execute_query(self, sql_query: str) -> Dict[str, Any]:
        """
        Execute a SQL query safely and return results.
        
        Args:
            sql_query: The SQL query to execute
            
        Returns:
            Dictionary with query results and metadata
            
        Raises:
            Exception: If query execution fails
        """
        try:
            logger.info(f"Executing SQL query: {sql_query}")
            
            # Validate that it's a SELECT query
            if not sql_query.strip().upper().startswith("SELECT"):
                raise ValueError("Only SELECT queries are allowed")
            
            # Execute the query using Supabase RPC (for raw SQL)
            # Note: This requires a stored procedure in the database
            # For now, we'll use the table() method for basic queries
            
            # Parse simple queries to use Supabase's table API
            result = await self._execute_via_supabase_client(sql_query)
            
            return {
                "success": True,
                "data": result,
                "row_count": len(result) if result else 0,
                "query": sql_query
            }
            
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": sql_query,
                "data": []
            }
    
    async def _execute_via_supabase_client(self, sql_query: str) -> List[Dict[str, Any]]:
        """
        Execute query using Supabase client.
        
        For complex queries, we'll need to use RPC calls.
        For now, this handles basic SELECT queries.
        """
        # For demonstration, let's handle the most common case
        # In a production system, you'd want to use stored procedures or RPC
        
        # Extract basic components (this is a simplified parser)
        query_upper = sql_query.upper().strip()
        
        # Handle COUNT queries specially
        if query_upper.startswith("SELECT COUNT(*)"):
            # For COUNT queries, we need to use RPC or handle them differently
            # For now, let's try to execute the raw SQL using Supabase's RPC functionality
            try:
                # Use Supabase's rpc method to execute raw SQL
                # Note: This requires a stored procedure in the database
                result = self.supabase.rpc('execute_sql', {'query': sql_query}).execute()
                if result.data:
                    return result.data
                else:
                    # Fallback: try to simulate the count by getting the data and counting
                    return await self._simulate_count_query(sql_query)
            except Exception as e:
                logger.warning(f"RPC execution failed, trying fallback: {e}")
                # Fallback to simulation
                return await self._simulate_count_query(sql_query)
        
        elif "FROM TEST_HISTORY" in query_upper:
            # Build Supabase query for regular SELECT queries
            query = self.supabase.table("test_history").select("*")
            
            # Parse WHERE conditions (simplified)
            if "WHERE" in query_upper:
                # Extract WHERE clause
                where_part = sql_query.split("WHERE", 1)[1].split("ORDER BY")[0].split("LIMIT")[0].strip()
                query = self._apply_where_conditions(query, where_part)
            
            # Parse ORDER BY
            if "ORDER BY" in query_upper:
                if "EXECUTION_TIME DESC" in query_upper:
                    query = query.order("execution_time", desc=True)
                elif "EXECUTION_TIME ASC" in query_upper:
                    query = query.order("execution_time", desc=False)
            
            # Parse LIMIT
            if "LIMIT" in query_upper:
                limit_part = sql_query.split("LIMIT")[1].strip().rstrip(";")
                try:
                    limit = int(limit_part)
                    query = query.limit(limit)
                except ValueError:
                    pass
            
            # Execute the query
            result = query.execute()
            return result.data if result.data else []
        
        else:
            # For now, fallback to RPC for complex queries
            # This would require creating stored procedures in Supabase
            raise ValueError("Complex queries not yet supported. Use simple SELECT queries on test_history.")
    
    async def _simulate_count_query(self, sql_query: str) -> List[Dict[str, Any]]:
        """
        Simulate a COUNT query by executing the inner query and counting results.
        This is a fallback when RPC is not available.
        """
        try:
            # Extract the subquery from COUNT(*) FROM (subquery)
            if "FROM (" in sql_query.upper():
                # Find the subquery
                start = sql_query.upper().find("FROM (") + 6
                # Find the matching closing parenthesis
                paren_count = 1
                end = start
                for i, char in enumerate(sql_query[start:], start):
                    if char == '(':
                        paren_count += 1
                    elif char == ')':
                        paren_count -= 1
                        if paren_count == 0:
                            end = i
                            break
                
                subquery = sql_query[start:end].strip()
                
                # Execute the subquery to get the data
                subquery_results = await self._execute_via_supabase_client(subquery)
                
                # Apply any WHERE conditions after the subquery
                remaining_sql = sql_query[end+1:].strip()
                if remaining_sql.upper().startswith("AS") and "WHERE" in remaining_sql.upper():
                    where_part = remaining_sql.split("WHERE", 1)[1].strip().rstrip(";")
                    # Filter the results based on the WHERE condition
                    filtered_results = []
                    for row in subquery_results:
                        if self._evaluate_where_condition(row, where_part):
                            filtered_results.append(row)
                    count = len(filtered_results)
                else:
                    count = len(subquery_results)
                
                # Return the count as a single row
                return [{"count": count}]
            
            else:
                # Simple COUNT without subquery
                # Get all data and count
                all_data = self.supabase.table("test_history").select("*").execute()
                return [{"count": len(all_data.data) if all_data.data else 0}]
                
        except Exception as e:
            logger.error(f"Error simulating count query: {e}")
            return [{"count": 0}]
    
    def _evaluate_where_condition(self, row: Dict[str, Any], where_clause: str) -> bool:
        """
        Evaluate a WHERE condition against a row of data.
        This is a simple evaluator for basic conditions.
        """
        try:
            # Handle "success = false" condition
            if "success = false" in where_clause.lower():
                return row.get("success") == False
            elif "success = true" in where_clause.lower():
                return row.get("success") == True
            # Add more conditions as needed
            return True
        except:
            return True
    
    def _apply_where_conditions(self, query, where_clause: str):
        """Apply WHERE conditions to Supabase query (simplified parser)."""
        # This is a basic parser - in production you'd want more robust parsing
        conditions = where_clause.replace("AND", "||AND||").split("||AND||")
        
        for condition in conditions:
            condition = condition.strip()
            
            if "test_uid =" in condition.lower():
                # Extract test_uid value
                value = condition.split("=")[1].strip().strip("'\"")
                query = query.eq("test_uid", value)
            
            elif "status =" in condition.lower():
                # Extract status value
                value = condition.split("=")[1].strip().strip("'\"")
                query = query.eq("status", value)
            
            elif "execution_time >" in condition.lower() and "interval" in condition.lower():
                # Handle time-based conditions - this is complex, 
                # for now we'll skip and let the full query be handled by RPC
                pass
        
        return query
    
    def format_results_as_table(self, results: List[Dict[str, Any]], max_rows: int = 20) -> str:
        """
        Format query results as a Slack-friendly table with improved formatting.
        
        Args:
            results: List of result dictionaries
            max_rows: Maximum number of rows to display
            
        Returns:
            Formatted table string for Slack
        """
        if not results:
            return "📊 No results found."
        
        # Check if this is a count result (single row with count column)
        if len(results) == 1 and "count" in results[0] and len(results[0]) == 1:
            count_value = results[0]["count"]
            return f"📊 **Result:** {count_value}"
        
        # Limit results
        limited_results = results[:max_rows]
        truncated = len(results) > max_rows
        
        # Get column names (excluding internal columns and reorder for better display)
        all_columns = [col for col in limited_results[0].keys() 
                      if col not in ['created_at', 'updated_at']]
        
        # Prioritize important columns first
        priority_order = ['test_uid', 'success', 'execution_time', 'id', 'metadata', 'duration']
        columns = []
        for col in priority_order:
            if col in all_columns:
                columns.append(col)
        # Add any remaining columns
        for col in all_columns:
            if col not in columns:
                columns.append(col)
        
        # Format data for better readability
        formatted_results = []
        for row in limited_results:
            formatted_row = {}
            for col in columns:
                value = row.get(col, '')
                
                if col == 'execution_time' and value:
                    # Format timestamp to be more readable
                    try:
                        from datetime import datetime
                        if 'T' in str(value):
                            dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
                            formatted_row[col] = dt.strftime('%m/%d %H:%M')
                        else:
                            formatted_row[col] = str(value)[:16]  # Truncate long timestamps
                    except:
                        formatted_row[col] = str(value)[:16]
                
                elif col == 'metadata' and value:
                    # Format metadata more compactly
                    try:
                        if isinstance(value, dict):
                            # Show key info only
                            parts = []
                            if 'duration' in value:
                                parts.append(f"{value['duration']}s")
                            if 'environment' in value:
                                parts.append(f"env:{value['environment']}")
                            if 'error' in value:
                                parts.append(f"err:{value['error'][:20]}...")
                            formatted_row[col] = " | ".join(parts) if parts else str(value)[:25]
                        else:
                            formatted_row[col] = str(value)[:25]
                    except:
                        formatted_row[col] = str(value)[:25]
                
                elif col == 'id':
                    # Show shorter UUID
                    formatted_row[col] = str(value)[:8] + "..." if len(str(value)) > 8 else str(value)
                
                elif col == 'success':
                    # Add emoji indicators for success/failure
                    if isinstance(value, bool):
                        if value:
                            formatted_row[col] = f"✅ Passed"
                        else:
                            formatted_row[col] = f"❌ Failed"
                    else:
                        formatted_row[col] = str(value)
                
                elif col == 'duration' and value:
                    # Format duration nicely
                    try:
                        duration_val = float(value)
                        if duration_val < 60:
                            formatted_row[col] = f"{duration_val:.1f}s"
                        else:
                            minutes = int(duration_val // 60)
                            seconds = duration_val % 60
                            formatted_row[col] = f"{minutes}m {seconds:.1f}s"
                    except:
                        formatted_row[col] = str(value)
                
                else:
                    formatted_row[col] = str(value)
            
            formatted_results.append(formatted_row)
        
        # Calculate column widths dynamically
        col_widths = {}
        for col in columns:
            max_width = max(
                len(str(col)),
                max(len(str(row.get(col, ''))) for row in formatted_results)
            )
            # Set reasonable min/max widths
            col_widths[col] = min(max(max_width, 8), 25)
        
        # Build table with improved formatting
        lines = []
        
        # Header with better formatting
        header_parts = []
        for col in columns:
            # Clean up column names
            display_name = col.replace('_', ' ').title()
            if col == 'test_uid':
                display_name = 'Test ID'
            elif col == 'execution_time':
                display_name = 'Time'
            elif col == 'success':
                display_name = 'Result'
            
            header_parts.append(display_name.ljust(col_widths[col]))
        
        header = " │ ".join(header_parts)
        lines.append(f"┌{'─' * len(header)}┐")
        lines.append(f"│ {header} │")
        lines.append(f"├{'─' * len(header)}┤")
        
        # Data rows
        for row in formatted_results:
            row_parts = []
            for col in columns:
                value = str(row.get(col, '')).ljust(col_widths[col])[:col_widths[col]]
                row_parts.append(value)
            
            row_line = " │ ".join(row_parts)
            lines.append(f"│ {row_line} │")
        
        lines.append(f"└{'─' * len(header)}┘")
        
        table = "\n".join(lines)
        
        # Add enhanced metadata
        metadata_lines = [
            f"📊 **{len(limited_results)} rows displayed**"
        ]
        
        if truncated:
            metadata_lines.append(f"📄 _(First {max_rows} of {len(results)} total results)_")
        
        return f"```\n{table}\n```\n" + " • ".join(metadata_lines)
    
    def format_results_as_slack_blocks(self, results: List[Dict[str, Any]], max_rows: int = 10) -> List[Dict[str, Any]]:
        """
        Format results as Slack Block Kit elements for rich visual formatting.
        
        Args:
            results: List of result dictionaries
            max_rows: Maximum number of rows to display
            
        Returns:
            List of Slack block elements with enhanced formatting
        """
        if not results:
            return [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "📊 *No results found*\n_Try adjusting your query criteria_"
                    }
                }
            ]
        
        blocks = []
        limited_results = results[:max_rows]
        
        # Enhanced header with stats
        total_passed = sum(1 for r in results if r.get('success') == True)
        total_failed = sum(1 for r in results if r.get('success') == False)
        
        header_text = f"📊 *Query Results* ({len(limited_results)} of {len(results)} rows)"
        if 'success' in results[0]:
            header_text += f"\n✅ {total_passed} passed • ❌ {total_failed} failed"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": header_text
            }
        })
        
        # Add divider
        blocks.append({"type": "divider"})
        
        # Format each row as an enhanced card
        for i, row in enumerate(limited_results, 1):
            # Determine row color based on success
            success = row.get('success')
            if success is True:
                status_color = '✅'
                status_text = 'Passed'
            elif success is False:
                status_color = '❌'
                status_text = 'Failed'
            else:
                status_color = '🔹'
                status_text = 'Unknown'
            
            # Create main content
            main_fields = []
            
            # Test ID (prominent)
            if 'test_uid' in row:
                main_fields.append({
                    "type": "mrkdwn",
                    "text": f"*🆔 Test ID:*\n`{row['test_uid']}`"
                })
            
            # Success status (with emoji)
            if 'success' in row:
                main_fields.append({
                    "type": "mrkdwn",
                    "text": f"*📊 Result:*\n{status_color} {status_text}"
                })
            
            # Execution time (formatted)
            if 'execution_time' in row:
                try:
                    from datetime import datetime
                    time_str = str(row['execution_time'])
                    if 'T' in time_str:
                        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        formatted_time = dt.strftime('%b %d, %H:%M')
                    else:
                        formatted_time = time_str[:16]
                    
                    main_fields.append({
                        "type": "mrkdwn",
                        "text": f"*🕐 Time:*\n{formatted_time}"
                    })
                except:
                    main_fields.append({
                        "type": "mrkdwn",
                        "text": f"*🕐 Time:*\n{str(row['execution_time'])[:16]}"
                    })
            
            # Create the main section
            blocks.append({
                "type": "section",
                "fields": main_fields[:6]  # Limit to 6 fields for clean layout
            })
            
            # Add metadata as context if available
            if 'metadata' in row and row['metadata']:
                try:
                    metadata = row['metadata']
                    context_elements = []
                    
                    if isinstance(metadata, dict):
                        # Duration
                        if 'duration' in metadata:
                            context_elements.append(f"⏱️ {metadata['duration']}s")
                        
                        # Environment
                        if 'environment' in metadata:
                            env_emoji = {'production': '🔴', 'staging': '🟡', 'development': '🟢'}
                            emoji = env_emoji.get(metadata['environment'], '🔵')
                            context_elements.append(f"{emoji} {metadata['environment']}")
                        
                        # Error message (if failed)
                        if 'error' in metadata and status_text == 'Failed':
                            error_msg = str(metadata['error'])[:50]
                            if len(str(metadata['error'])) > 50:
                                error_msg += "..."
                            context_elements.append(f"⚠️ {error_msg}")
                    
                    if context_elements:
                        blocks.append({
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": " • ".join(context_elements)
                                }
                            ]
                        })
                except:
                    pass
            
            # Add divider between rows (except last)
            if i < len(limited_results):
                blocks.append({"type": "divider"})
        
        # Add summary footer if truncated
        if len(results) > max_rows:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📄 *Showing first {max_rows} of {len(results)} total results* | Use LIMIT in your query to see more specific results"
                    }
                ]
            })
        
        return blocks
    
    def format_results_as_compact_table(self, results: List[Dict[str, Any]], max_rows: int = 15) -> str:
        """
        Format results as a compact, mobile-friendly table.
        
        Args:
            results: List of result dictionaries
            max_rows: Maximum number of rows to display
            
        Returns:
            Compact table string optimized for mobile
        """
        if not results:
            return "📊 No results found."
        
        # Check if this is a count result (single row with count column)
        if len(results) == 1 and "count" in results[0] and len(results[0]) == 1:
            count_value = results[0]["count"]
            return f"📊 **Answer:** {count_value}"
        
        limited_results = results[:max_rows]
        lines = []
        
        for i, row in enumerate(limited_results, 1):
            # Row header
            test_id = row.get('test_uid', f'Row {i}')
            success = row.get('success')
            
            # Success/failure emoji and text
            if success is True:
                status_emoji = '✅'
                status_text = 'Passed'
            elif success is False:
                status_emoji = '❌'
                status_text = 'Failed'
            else:
                status_emoji = '🔹'
                status_text = 'Unknown'
            
            lines.append(f"{status_emoji} **{test_id}** - {status_text}")
            
            # Time
            if 'execution_time' in row:
                try:
                    from datetime import datetime
                    time_str = str(row['execution_time'])
                    if 'T' in time_str:
                        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        formatted_time = dt.strftime('%m/%d %H:%M')
                    else:
                        formatted_time = str(row['execution_time'])[:16]
                    lines.append(f"   🕐 {formatted_time}")
                except:
                    lines.append(f"   🕐 {str(row['execution_time'])[:16]}")
            
            # Metadata highlights
            if 'metadata' in row and row['metadata']:
                try:
                    metadata = row['metadata']
                    if isinstance(metadata, dict):
                        details = []
                        if 'duration' in metadata:
                            details.append(f"⏱️{metadata['duration']}s")
                        if 'environment' in metadata:
                            details.append(f"🌍{metadata['environment']}")
                        if details:
                            lines.append(f"   {' '.join(details)}")
                except:
                    pass
            
            lines.append("")  # Spacing
        
        # Remove last empty line
        if lines and lines[-1] == "":
            lines.pop()
        
        result = "\n".join(lines)
        
        # Add footer
        if len(results) > max_rows:
            result += f"\n\n📄 _Showing {max_rows} of {len(results)} results_"
        
        return result 