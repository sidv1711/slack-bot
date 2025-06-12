"""Service for generating shareable test report links."""
import aiohttp
import asyncio
from typing import Optional, Dict, Any
from loguru import logger
from ..config.settings import get_settings

class ReportService:
    """Service for generating shareable test report links from Cognisim backend."""
    
    def __init__(self):
        """Initialize the report service."""
        settings = get_settings()
        self.base_url = settings.cognisim_base_url
        self.propelauth_api_key = settings.propelauth_api_key
        self.propelauth_url = settings.propelauth_url
        self.timeout = aiohttp.ClientTimeout(total=30)
        
        logger.info("ReportService initialized")
        if self.propelauth_api_key:
            logger.info("PropelAuth API key is configured for report generation")
        else:
            logger.warning("PropelAuth API key not configured - reports will use fallback approach")
        
        # Report link strategy configuration
        self.fallback_strategies = [
            "api_v1",           # Try main API first
            "api_v2",           # Try alternative API endpoints
            "direct_url",       # Try direct URL construction
            "metadata_url",     # Use metadata URLs as fallback
        ]
        
    async def generate_shareable_link(
        self, 
        test_id: str, 
        history_id: str, 
        origin: str = "https://app.example.com"
    ) -> Optional[str]:
        """
        Generate a shareable report link for a test execution.
        
        Args:
            test_id: The test identifier (maps to testId parameter)
            history_id: The execution history ID (not used in the API call directly)
            origin: The origin URL for the report
            
        Returns:
            The shareable report URL or None if failed
        """
        if not self.propelauth_api_key:
            logger.debug("No PropelAuth API key configured, skipping report link generation")
            return None
            
        try:
            # Use the correct endpoint and method based on API documentation
            url = f"{self.base_url}/api/v1/report/async-run/shared-report"
            
            # Use query parameters instead of JSON payload
            params = {
                "testId": test_id,  # Use testId as per API docs
                "token": self.propelauth_api_key,  # Use token query param for authentication
                "executionId": history_id  # Add the execution ID as the API expects a UUID
            }
            
            # Simple headers without Authorization (since we use token query param)
            headers = {
                "User-Agent": "Slack-Bot/1.0",
                "Accept": "application/json"
            }
            
            logger.debug(f"Making report API request to {url} with params: testId={test_id}, executionId={history_id}, token=***")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Use GET method with query parameters
                async with session.get(url, params=params, headers=headers) as response:
                    logger.debug(f"Report API response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"Report API response data: {data}")
                        
                        # Based on API docs, successful response contains history_id and status
                        if isinstance(data, dict) and data.get("status") == "success":
                            # The API might return a shareable link or we might need to construct it
                            history_id_from_response = data.get("history_id")
                            if history_id_from_response:
                                # Construct the shareable report URL
                                shareable_url = f"{origin}/report/shared/{history_id_from_response}"
                                logger.info(f"Generated report link for test {test_id}: {shareable_url}")
                                return shareable_url
                            else:
                                logger.warning(f"No history_id in successful response: {data}")
                                return None
                        elif isinstance(data, dict) and "shareable_link" in data:
                            logger.info(f"Generated report link for test {test_id}")
                            return data["shareable_link"]
                        elif isinstance(data, dict) and "url" in data:
                            logger.info(f"Generated report link for test {test_id}")
                            return data["url"]
                        else:
                            logger.warning(f"Unexpected response format: {data}")
                            return None
                    elif response.status == 401:
                        logger.error("Unauthorized: PropelAuth API token may be invalid")
                        return None
                    elif response.status == 404:
                        logger.warning(f"Test execution not found: test_id={test_id}")
                        return None
                    elif response.status == 422:
                        error_text = await response.text()
                        logger.error(f"Validation Error (422): {error_text}")
                        return None
                    else:
                        error_text = await response.text()
                        logger.error(f"Report API error {response.status}: {error_text}")
                        
                        # Try alternative approach on API failure
                        logger.debug(f"Trying alternative approach for test {test_id}")
                        return await self.generate_shareable_link_v2(test_id, history_id, origin)
                        
        except asyncio.TimeoutError:
            logger.error(f"Timeout generating report link for test {test_id}")
            # Try alternative approach on timeout
            return await self.generate_shareable_link_v2(test_id, history_id, origin)
        except Exception as e:
            logger.error(f"Error generating report link for test {test_id}: {e}")
            # Try alternative approach on exception
            return await self.generate_shareable_link_v2(test_id, history_id, origin)
            
    async def generate_multiple_links(
        self, 
        executions: list, 
        origin: str = "https://app.example.com"
    ) -> Dict[str, Optional[str]]:
        """
        Generate shareable links for multiple test executions.
        
        Args:
            executions: List of execution dictionaries with 'test_uid' and 'id' fields
            origin: The origin URL for the reports
            
        Returns:
            Dictionary mapping execution IDs to their shareable links
        """
        if not self.propelauth_api_key:
            logger.debug("No PropelAuth API key configured, skipping all report link generation")
            return {str(execution.get("id", "")): None for execution in executions}
            
        tasks = []
        execution_ids = []
        
        for execution in executions:
            test_id = execution.get("test_uid")
            history_id = str(execution.get("id"))
            
            if test_id and history_id:
                task = self.generate_shareable_link(test_id, history_id, origin)
                tasks.append(task)
                execution_ids.append(history_id)
        
        if not tasks:
            return {}
            
        # Execute all requests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Map results back to execution IDs
        link_map = {}
        for i, result in enumerate(results):
            execution_id = execution_ids[i]
            execution = executions[i]  # Get the original execution data
            
            if isinstance(result, Exception):
                logger.error(f"Error generating link for execution {execution_id}: {result}")
                # Try fallback approach
                fallback_link = self.generate_fallback_link(execution)
                if fallback_link:
                    logger.info(f"Using fallback link for execution {execution_id}: {fallback_link}")
                link_map[execution_id] = fallback_link
            elif result is None:
                # API call succeeded but returned None (no link generated)
                logger.warning(f"API returned no link for execution {execution_id}, trying fallback")
                fallback_link = self.generate_fallback_link(execution)
                if fallback_link:
                    logger.info(f"Using fallback link for execution {execution_id}: {fallback_link}")
                link_map[execution_id] = fallback_link
            else:
                # API call succeeded and returned a link
                link_map[execution_id] = result
                
        return link_map
    
    def format_link_for_slack(self, link: Optional[str], text: str = "📊 Report") -> str:
        """
        Format a report link for Slack display.
        
        Args:
            link: The report URL or None
            text: The link text to display
            
        Returns:
            Formatted Slack link or fallback text
        """
        if link:
            return f"<{link}|{text}>"
        else:
            return "N/A"

    def generate_fallback_link(self, execution: dict) -> Optional[str]:
        """
        Generate a fallback report link using metadata URL when API fails.
        
        Args:
            execution: The execution dictionary with metadata
            
        Returns:
            A report link derived from metadata or None
        """
        metadata = execution.get("metadata")
        
        if not metadata or not isinstance(metadata, str):
            return None
            
        # Check if metadata is already a usable URL
        if metadata.startswith(("http://", "https://")):
            # Priority 1: For Supabase URLs, they might be direct metadata links that contain useful data
            if "supabase.co" in metadata:
                # These are JSON metadata files, might be useful as fallback
                # Return them as-is since they're signed URLs and contain test data
                logger.info(f"Using Supabase metadata URL as fallback: {metadata[:100]}...")
                return metadata
                
            # Priority 2: For S3 URLs, try to construct app URLs from the pattern
            elif "test-metadata-your_company.s3.amazonaws.com" in metadata:
                # Extract the file name pattern: testId-timestamp.json
                parts = metadata.split("/")
                if len(parts) > 0:
                    filename = parts[-1].split("?")[0]  # Remove query params
                    if filename.endswith(".json"):
                        # Remove .json extension and try to extract execution info
                        base_name = filename[:-5]
                        if "-" in base_name:
                            # Pattern: <UUID>-20250403-192353
                            parts = base_name.split("-")
                            if len(parts) >= 6:  # UUID has 5 parts, plus timestamp parts
                                test_id = "-".join(parts[:5])  # Reconstruct UUID
                                execution_id = execution.get("id")
                                
                                # Try multiple URL patterns that might work
                                patterns = [
                                    f"https://app.example.com/test/{test_id}/run/{execution_id}",
                                    f"https://app.example.com/execution/{execution_id}",
                                    f"https://app.example.com/results/{test_id}/{execution_id}",
                                    f"https://app.example.com/test/{test_id}/history/{execution_id}",
                                ]
                                
                                # Return the first pattern for now
                                constructed_url = patterns[0]
                                logger.info(f"Constructed URL from S3 metadata: {constructed_url}")
                                return constructed_url
                
                # If construction fails, return the S3 URL as a last resort
                logger.info(f"Using S3 metadata URL as fallback: {metadata[:100]}...")
                return metadata
                
        return None

    async def generate_shareable_link_v2(
        self, 
        test_id: str, 
        history_id: str, 
        origin: str = "https://app.example.com"
    ) -> Optional[str]:
        """
        Alternative approach to generate a shareable report link.
        Try different API parameters or construction methods.
        
        Args:
            test_id: The test identifier
            history_id: The execution history ID
            origin: The origin URL for the report
            
        Returns:
            The shareable report URL or None if failed
        """
        if not self.propelauth_api_key:
            logger.debug("No PropelAuth API key configured, skipping v2 report link generation")
            return None
            
        # Method 1: Try direct URL construction without API call
        try:
            # Use the correct URL format with query parameters as shown in the API example
            direct_url = f"{origin}/report?testId={test_id}&token={self.propelauth_api_key}"
            logger.info(f"Generated direct report URL for test {test_id}: {direct_url}")
            return direct_url
        except Exception as e:
            logger.error(f"Error constructing direct URL for test {test_id}: {e}")
            
        # Method 2: Try different API endpoint
        try:
            url = f"{self.base_url}/api/v1/reports/{history_id}/share"
            
            headers = {
                "Authorization": f"Bearer {self.propelauth_api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Slack-Bot/1.0"
            }
            
            payload = {
                "test_id": test_id,
                "history_id": history_id,
                "origin": origin
            }
            
            logger.debug(f"Trying alternative API endpoint: {url}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, dict) and "url" in data:
                            logger.info(f"Generated report link via v2 API for test {test_id}")
                            return data["url"]
                    else:
                        logger.debug(f"Alternative API endpoint failed with status {response.status}")
                        
        except Exception as e:
            logger.debug(f"Alternative API approach failed for test {test_id}: {e}")
            
        return None 

    async def generate_shareable_link_with_user_token(
        self, 
        test_id: str, 
        history_id: str,
        user_token: str,
        origin: str = "https://app.example.com"
    ) -> Optional[str]:
        """
        Generate a shareable report link using a user's JWT access token.
        Uses the proper API endpoints: first POST to generate_shareable_report_link,
        then returns the shared-report URL.
        
        Args:
            test_id: The test identifier
            history_id: The execution history ID
            user_token: The user's JWT access token from PropelAuth
            origin: The origin URL for the report (should be your API base URL)
            
        Returns:
            The shareable report URL or None if failed
        """
        if not user_token:
            logger.debug("No user token provided, cannot generate user-authenticated report link")
            return None
            
        if not self.base_url:
            logger.error("No base URL configured for API calls")
            return None
            
        try:
            # Step 1: Call the generate_shareable_report_link API endpoint
            generate_url = f"{self.base_url}/api/v1/report/async-run/generate_shareable_report_link"
            
            headers = {
                "Authorization": f"Bearer {user_token}",
                "Content-Type": "application/json",
                "User-Agent": "Slack-Bot/1.0"
            }
            
            payload = {
                "test_id": test_id,
                "history_id": history_id
            }
            
            logger.info(f"Calling generate_shareable_report_link API for test {test_id}")
            logger.debug(f"POST {generate_url} with payload: test_id={test_id}, history_id={history_id}, token=***")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(generate_url, json=payload, headers=headers) as response:
                    logger.debug(f"Generate link API response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"Generate link API response: {data}")
                        
                        # Use the shareable_link directly from the API response
                        if isinstance(data, dict) and "shareable_link" in data:
                            shareable_url = data["shareable_link"]
                            logger.info(f"Generated user-authenticated report URL for test {test_id}: {shareable_url}")
                            return shareable_url
                        else:
                            logger.warning(f"No shareable_link in API response: {data}")
                            return None
                        
                    elif response.status == 401:
                        logger.error(f"Unauthorized access for test {test_id}: Invalid or expired token")
                        return None
                    elif response.status == 404:
                        logger.warning(f"Test execution not found: test_id={test_id}")
                        return None
                    elif response.status == 422:
                        error_text = await response.text()
                        logger.error(f"Validation Error (422) for test {test_id}: {error_text}")
                        return None
                    else:
                        error_text = await response.text()
                        logger.error(f"Generate link API error {response.status} for test {test_id}: {error_text}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error(f"Timeout calling generate_shareable_report_link API for test {test_id}")
            return None
        except Exception as e:
            logger.error(f"Error calling generate_shareable_report_link API for test {test_id}: {e}")
            return None

    async def generate_multiple_links_with_user_token(
        self, 
        executions: list,
        user_token: str,
        origin: str = "https://app.example.com"
    ) -> Dict[str, Optional[str]]:
        """
        Generate shareable links for multiple test executions using user token.
        Makes parallel API calls for faster processing.
        
        Args:
            executions: List of execution dictionaries
            user_token: The user's JWT access token
            origin: The origin URL for the reports
            
        Returns:
            Dictionary mapping execution IDs to their shareable links
            
        Raises:
            Exception: If user_token is not provided
        """
        if not user_token:
            error_msg = "No user token provided - cannot generate user-authenticated report links"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        # Prepare tasks for parallel execution
        tasks = []
        execution_map = {}  # Map task index to execution info
        
        for i, execution in enumerate(executions):
            test_id = execution.get("test_uid")
            history_id = str(execution.get("id"))
            
            if test_id and history_id:
                task = self.generate_shareable_link_with_user_token(
                    test_id, history_id, user_token, origin
                )
                tasks.append(task)
                execution_map[len(tasks) - 1] = history_id
            
        # Execute all API calls in parallel
        logger.info(f"Making {len(tasks)} parallel API calls for report links")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build the result map
        link_map = {}
        
        for i, result in enumerate(results):
            history_id = execution_map.get(i)
            if history_id:
                if isinstance(result, Exception):
                    logger.error(f"Error generating link for execution {history_id}: {result}")
                    link_map[history_id] = None
                else:
                    link_map[history_id] = result
        
        # Add None entries for executions that couldn't be processed
        for execution in executions:
            history_id = str(execution.get("id"))
            if history_id not in link_map:
                link_map[history_id] = None
                
        return link_map

    async def generate_multiple_links_with_propelauth_user(
        self, 
        executions: list,
        propelauth_user_id: str,
        origin: str = "https://app.example.com"
    ) -> Dict[str, Optional[str]]:
        """
        Generate shareable links for multiple test executions using PropelAuth user ID.
        
        Creates an access token for the user and uses it to generate authenticated links.
        No fallback - will raise exception if PropelAuth is not properly configured.
        
        Args:
            executions: List of execution dictionaries with 'test_uid' and 'id' fields
            propelauth_user_id: The PropelAuth user ID to create access token for
            origin: The origin URL for the reports
            
        Returns:
            Dictionary mapping execution IDs to their shareable links
            
        Raises:
            Exception: If PropelAuth API key is not configured or access token creation fails
        """
        logger.info(f"Generating report URLs for {len(executions)} executions using PropelAuth access token API")
        
        # Check PropelAuth API key is configured
        if not self.propelauth_api_key:
            error_msg = "PropelAuth API key is not configured - cannot generate authenticated report links"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Create access token for the user
        from propelauth_fastapi import init_auth
        from ..config.settings import get_settings
        
        settings = get_settings()
        auth = init_auth(settings.propelauth_url, settings.propelauth_api_key)
        
        logger.info(f"Creating access token for PropelAuth user: {propelauth_user_id}")
        
        try:
            token_response = auth.create_access_token(
                user_id=propelauth_user_id,
                duration_in_minutes=60  # 1 hour access token
            )
            
            user_token = token_response.access_token
            logger.info(f"Successfully created access token for user {propelauth_user_id}")
            
            # Use the user token to generate authenticated report links
            return await self.generate_multiple_links_with_user_token(executions, user_token, origin)
            
        except Exception as e:
            error_msg = f"Failed to create access token for user {propelauth_user_id}: {e}"
            logger.error(error_msg)
            raise Exception(error_msg) from e 