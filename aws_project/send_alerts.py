import subprocess
import requests
import sys
import os

OPSGENIE_API_KEY = os.getenv("OPSGENIE_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ALERT_PLATFORM = os.getenv("PLATFORM")

# Function to send alert to OpsGenie
def send_to_opsgenie(message):
    # Replace with your actual OpsGenie API key
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"GenieKey {OPSGENIE_API_KEY}"  # Corrected to use f-string for variable interpolation

    }

    payload = {
        "message": message,
        "priority": "P4"  # Optional: set priority (P1 to P5)
        # "alias": "unique_alias",  # Optional: provide a unique alias
        # "description": "Detailed description of the alert",  # Optional: add more details
        # "tags": ["tag1", "tag2"]  # Optional: add tags for categorization
    }

    url = "https://api.opsgenie.com/v2/alerts"
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 202:
        print("Alert successfully sent to OpsGenie.")
    else:
        print(f"Failed to send alert to OpsGenie. Status code: {response.status_code}")

# Function to send alert to Flock
def send_to_flock(message):
    # Replace with your actual Flock webhook URL
    webhook_url = WEBHOOK_URL

    payload = {
        "text": message
    }

    response = requests.post(webhook_url, json=payload)

    if response.status_code == 200:
        print("Alert successfully sent to Flock.")
    else:
        print(f"Failed to send alert to Flock. Status code: {response.status_code}")

if __name__ == "__main__":
    # Run alerts.py and capture its output
    try:
        result = subprocess.run(['python3', 'alerts.py'], capture_output=True, text=True)
        alerts = result.stdout.strip().split("\n")  # Split alerts into separate lines
    except subprocess.CalledProcessError as e:
        print(f"Error running alerts.py: {e}")
        sys.exit(1)

    # Take ALERT_PLATFORM as an input argument in lowercase
    service = ALERT_PLATFORM.lower() if ALERT_PLATFORM else None

    if alerts and not alerts[0] == '':
        for alert in alerts:
            message = alert.strip()  # Trim any extra whitespace
            if service == "flock":
                send_to_flock(message)
            elif service == "opsgenie":
                send_to_opsgenie(message)
            else:
                print("Unsupported service. Supported services: flock, opsgenie")
                sys.exit(1)