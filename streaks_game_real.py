import requests

# Replace with your actual API key or "1" to test the free key
API_KEY = "1"

# NBA standings URL for 2023-2024 season
url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookuptable.php?l=4387&s=2023-2024"

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    
    print("Raw API response:")
    print(response.text)  # full raw JSON response

    data = response.json()
    if "table" in data:
        print("\nTop 5 teams:")
        for entry in data["table"][:5]:
            print(f"{entry.get('name')} - Rank: {entry.get('intRank')}, Wins: {entry.get('intWin')}, Losses: {entry.get('intLoss')}")
    else:
        print("No 'table' data found in the response.")
except Exception as e:
    print(f"Error fetching data: {e}")
