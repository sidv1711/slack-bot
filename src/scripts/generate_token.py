from propelauth_fastapi import init_auth
from loguru import logger
import os
from dotenv import load_dotenv
import traceback
import secrets
import string
import uuid

# Load environment variables
load_dotenv()

def generate_secure_password(length=16):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_random_email():
    """Generate a random email address."""
    random_id = str(uuid.uuid4())[:8]
    return f"test+{random_id}@example.com"

def generate_test_token():
    """Generate a test access token using PropelAuth API."""
    try:
        # Get configuration from environment
        auth_url = os.getenv("PROPELAUTH_URL")
        api_key = os.getenv("PROPELAUTH_API_KEY")
        
        logger.info(f"Using auth URL: {auth_url}")
        
        if not auth_url or not api_key:
            logger.error("Missing required environment variables: PROPELAUTH_URL and PROPELAUTH_API_KEY")
            return None
            
        # Initialize PropelAuth client
        auth = init_auth(auth_url, api_key)
        
        # Generate a secure password and random email
        secure_password = generate_secure_password()
        random_email = generate_random_email()
        
        # First create a test user
        user_response = auth.create_user(
            email=random_email,
            email_confirmed=True,
            password=secure_password,
            username=f"testuser_{str(uuid.uuid4())[:8]}"  # Random username too
        )
        
        user_id = user_response["user_id"]
        logger.info(f"Created test user with ID: {user_id}")
        logger.info(f"Test user email: {random_email}")
        logger.info(f"Test user password: {secure_password}")
        
        # Now create an access token for this user
        token_response = auth.create_access_token(
            user_id=user_id,
            duration_in_minutes=60 * 24  # 24 hours
        )
        
        # The response is an object with an access_token attribute
        token = token_response.access_token
        logger.info("Successfully generated test access token")
        logger.info(f"Token: {token}")
        return token
        
    except Exception as e:
        logger.error(f"Error generating token: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    generate_test_token() 