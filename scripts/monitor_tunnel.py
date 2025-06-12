#!/usr/bin/env python3
"""Monitor Cloudflare tunnel and send notifications if it goes down."""
import requests
import subprocess
import time
import os
from datetime import datetime
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('<HOME>/Library/Logs/tunnel_monitor.log'),
        logging.StreamHandler()
    ]
)

# Configuration
HEALTH_CHECK_URL = "https://api.example.com/health"
TUNNEL_NAME = "your_company-bot"
CHECK_INTERVAL = 60  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def check_tunnel_status() -> bool:
    """Check if the tunnel is running using cloudflared CLI."""
    try:
        result = subprocess.run(
            ["cloudflared", "tunnel", "info", TUNNEL_NAME],
            capture_output=True,
            text=True
        )
        return "active connection" in result.stdout.lower()
    except Exception as e:
        logging.error(f"Error checking tunnel status: {e}")
        return False

def check_endpoint_health() -> bool:
    """Check if the endpoint is accessible."""
    try:
        response = requests.get(HEALTH_CHECK_URL, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Error checking endpoint health: {e}")
        return False

def restart_tunnel() -> bool:
    """Attempt to restart the tunnel."""
    try:
        # Stop any existing tunnel processes
        subprocess.run(["pkill", "-f", "cloudflared"])
        time.sleep(2)
        
        # Start the tunnel
        subprocess.Popen(
            ["cloudflared", "tunnel", "run", TUNNEL_NAME],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for tunnel to start
        time.sleep(10)
        return True
    except Exception as e:
        logging.error(f"Error restarting tunnel: {e}")
        return False

def send_slack_notification(message: str):
    """Send notification to Slack."""
    try:
        # Get Slack webhook URL from environment
        webhook_url = os.getenv("SLACK_MONITOR_WEBHOOK")
        if not webhook_url:
            logging.warning("Slack webhook URL not configured")
            return
            
        requests.post(webhook_url, json={"text": message})
    except Exception as e:
        logging.error(f"Error sending Slack notification: {e}")

def main():
    """Main monitoring loop."""
    logging.info("Starting Cloudflare tunnel monitor")
    consecutive_failures = 0
    
    while True:
        tunnel_running = check_tunnel_status()
        endpoint_healthy = check_endpoint_health()
        
        if not tunnel_running or not endpoint_healthy:
            consecutive_failures += 1
            logging.warning(
                f"Health check failed (attempt {consecutive_failures}/{MAX_RETRIES}). "
                f"Tunnel running: {tunnel_running}, Endpoint healthy: {endpoint_healthy}"
            )
            
            if consecutive_failures >= MAX_RETRIES:
                error_message = (
                    f"🚨 *Cloudflare Tunnel Alert*\n"
                    f"Tunnel `{TUNNEL_NAME}` is down!\n"
                    f"• Tunnel running: {'✅' if tunnel_running else '❌'}\n"
                    f"• Endpoint healthy: {'✅' if endpoint_healthy else '❌'}\n"
                    f"• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Attempting automatic recovery..."
                )
                send_slack_notification(error_message)
                
                # Attempt recovery
                if restart_tunnel():
                    recovery_message = (
                        f"✅ *Tunnel Recovery Attempted*\n"
                        f"Tunnel `{TUNNEL_NAME}` has been restarted.\n"
                        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    send_slack_notification(recovery_message)
                    consecutive_failures = 0
                else:
                    failure_message = (
                        f"❌ *Tunnel Recovery Failed*\n"
                        f"Failed to restart tunnel `{TUNNEL_NAME}`.\n"
                        f"Manual intervention required.\n"
                        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    send_slack_notification(failure_message)
        else:
            consecutive_failures = 0
            logging.info("Health check passed")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main() 