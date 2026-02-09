import requests
import json

url = "https://homies-hottest-100.onrender.com/submissions"
data = requests.get(url).json()

print(json.dumps(data, indent=2))