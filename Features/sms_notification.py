import os
import requests
from dotenv import load_dotenv

load_dotenv()


def send_sms_notification(contact, name, timestamp, action):
    base_url = os.getenv("BASE_URL")
    api_key = os.getenv("API_KEY")
    device_id = os.getenv("DEVICE_ID")

    response = requests.post(f'{base_url}/api/v1/gateway/devices/{device_id}/send-sms', json={'recipients': [f'+63{contact.lstrip("0")}'],
                                                                                  'message': f'{name} has {"Entered" if action == "Entry" else "Exited"} the school'},
                             headers={'x-api-key': api_key})

    print(response.json())
