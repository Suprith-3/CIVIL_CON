import os
import requests
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
GROQ_URL = "https://api.groq.com/openai/v1/models"

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}"
}

response = requests.get(GROQ_URL, headers=headers)
if response.status_code == 200:
    models = response.json().get('data', [])
    print("Available Groq Models:")
    for m in models:
        print(f"- {m['id']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
