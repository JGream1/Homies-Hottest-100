import requests

url = "https://homies-hottest-100.onrender.com/submissions"
data = requests.get(url).json()

submissions = data["submissions"]