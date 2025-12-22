import requests
import os
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")

url = "https://api.resend.com/emails"
headers = {
    "Authorization": f"Bearer {RESEND_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "from": "onboarding@resend.dev",
    "to": ["elektraizeproje@gmail.com"],
    "subject": "Test Email",
    "html": "<p>This is a test email</p>"
}

response = requests.post(url, json=payload, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
