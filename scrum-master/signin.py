#!/usr/bin/env python3
import os
import json
import requests
import time
from pathlib import Path

# Try to load environment variables from .env
try:
    from dotenv import load_dotenv
    # Look for .env in the same directory as the script
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

def load_config():
    """Load Slack configuration from environment variables."""
    return {
        "slack_token": os.environ.get("SLACK_USER_TOKEN", ""),
        "slack_channel": os.environ.get("SLACK_CHANNEL", "beetle-scrum-sync")
    }

def post_to_slack(text, config):
    """Send a simple message to Slack."""
    token = config["slack_token"]
    channel = config["slack_channel"]
    
    if not token:
        print("Error: SLACK_USER_TOKEN not found in .env or environment.")
        return False
    if not channel:
        print("Error: SLACK_CHANNEL not found in .env or environment.")
        return False
    
    try:
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "channel": channel,
                "text": text,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            print(f"Slack API error: {data.get('error', 'unknown')}")
            return False
        return True
    except Exception as e:
        print(f"Failed to post to Slack: {e}")
        return False

def start_quickshell_timer():
    """Update Quickshell's persistent state to start the stopwatch."""
    state_path = Path.home() / ".local/state/quickshell/states.json"
    if not state_path.exists():
        print(f"Quickshell state not found at {state_path}")
        return False
    
    try:
        # Read current state
        with open(state_path, 'r') as f:
            state = json.load(f)
        
        # Ensure the timer structure exists
        if 'timer' not in state: state['timer'] = {}
        if 'stopwatch' not in state['timer']: state['timer']['stopwatch'] = {}
        
        # Quickshell stopwatch uses 10ms intervals (Date.now() / 10)
        now_10ms = int(time.time() * 100)
        
        # Start the stopwatch
        state['timer']['stopwatch']['running'] = True
        state['timer']['stopwatch']['start'] = now_10ms
        state['timer']['stopwatch']['laps'] = []
        
        # Write back the state
        with open(state_path, 'w') as f:
            json.dump(state, f, indent=4)
        
        print(f"Quickshell stopwatch started at {time.strftime('%H:%M:%S')}.")
        return True
    except Exception as e:
        print(f"Failed to update Quickshell state: {e}")
        return False

def main():
    config = load_config()
    
    # 1. Send "Signing in" to Slack
    # print("Action 1: Sending 'Signing in' to Slack...")
    # if post_to_slack("Signing in", config):
    #     print("  - Successfully posted to Slack.")
    # else:
    #     print("  - Failed to post to Slack.")
    
    # 2. Start the timer in Quickshell
    print("Action 2: Starting Quickshell timer...")
    if start_quickshell_timer():
        print("  - Quickshell timer started.")
    else:
        print("  - Failed to start Quickshell timer.")

if __name__ == "__main__":
    main()
