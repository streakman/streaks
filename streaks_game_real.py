import requests

url = "https://www.balldontlie.io/api/v1/teams"

try:
    res = requests.get(url)
    print("Status code:", res.status_code)
    print("Response:", res.json())
except Exception as e:
    print("Request error:", e)
