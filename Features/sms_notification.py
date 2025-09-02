import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def send_sms_notification(contact, name, timestamp, action):
    base_url = os.getenv("BASE_URL")
    api_key = os.getenv("API_KEY")
    device_id = os.getenv("DEVICE_ID")


    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    formatted_datetime = dt.strftime("%B %d, %Y at %I:%M %p")


    message = (
        f"Good day! This is Saviour School Inc. We would like to inform you "
        f"{name} has {'successfully entered' if action == 'Entry' else 'exited'} the school gate on "
        f"{formatted_datetime}. Thank you!"
    )

    # Send the SMS
    response = requests.post(
        f'{base_url}/api/v1/gateway/devices/{device_id}/send-sms',
        json={
            'recipients': [f'+63{contact.lstrip("0")}'],
            'message': message
        },
        headers={'x-api-key': api_key}
    )

    print(response.json())