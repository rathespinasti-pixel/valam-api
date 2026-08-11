import os
import requests
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY", "")
print(f"Testing OpenAI API key with dall-e-3: {openai_api_key[:15]}...")

url = "https://api.openai.com/v1/images/generations"
headers = {
    "Authorization": f"Bearer {openai_api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "dall-e-3",
    "prompt": "Botanical photograph of a healthy young tomato plant seedling with green leaves in fertile brown soil.",
    "n": 1,
    "size": "1024x1024"
}

try:
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    print("Response JSON:", response.json())
except Exception as e:
    print("Error:", e)
