import requests, sys
BASE = "http://127.0.0.1:5000/api"
login_url = f"{BASE}/auth/login"
payload = {"email": "test@example.com", "password": "Test1234"}
resp = requests.post(login_url, json=payload)
print('Login status:', resp.status_code)
print('Login response:', resp.text)
if resp.status_code != 200:
    sys.exit(1)
access = resp.json().get('data', {}).get('access_token')
print('Access token:', access)
# Add a crop
add_url = f"{BASE}/crops"
headers = {"Authorization": f"Bearer {access}"}
crop_data = {"crop_name": "TestCrop", "planting_date": "2023-01-01"}
resp2 = requests.post(add_url, json=crop_data, headers=headers)
print('Add crop status:', resp2.status_code)
print('Add crop response:', resp2.text)
