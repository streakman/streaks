import requests

API_KEY = "1"  # free key to test

url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookuptable.php?l=4387&s=2023-2024"

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    print("Raw response:")
    print(response.text)
except Exception as e:
    print(f"Error fetching data: {e}")
