import streamlit as st
import requests

# Use your single API-FOOTBALL key for all sports APIs
API_KEY = st.secrets["api_football_key"]

def fetch_api_data(url, sport_name):
    st.info(f"[DEBUG] Fetching {sport_name} data from API")
    headers = {"x-apisports-key": API_KEY}
    try:
        response = requests.get(url, headers=headers)
        st.info(f"[DEBUG] {sport_name} API status: {response.status_code}")
        if response.status_code != 200:
            st.error(f"Failed to fetch {sport_name} data. Status code: {response.status_code}")
            return []
        data = response.json()
        items = data.get("response", [])
        st.info(f"[DEBUG] Retrieved {len(items)} {sport_name} teams")
        return items
    except Exception as e:
        st.error(f"Error fetching {sport_name} data: {e}")
        return []

def fetch_combined_sports_data():
    # API URLs for 2023 season teams (adjust league ids as needed)
    f1_url = "https://v3.formula-1.api-sports.io/teams?season=2023"
    hockey_url = "https://v3.icehockey.api-sports.io/teams?league=57&season=2023"
    afl_url = "https://v3.afl.api-sports.io/teams?league=1&season=2023"

    f1_data = fetch_api_data(f1_url, "Formula 1")
    hockey_data = fetch_api_data(hockey_url, "Hockey")
    afl_data = fetch_api_data(afl_url, "AFL")

    max_len = max(len(f1_data), len(hockey_data), len(afl_data))
    combined = []

    for i in range(max_len):
        if i < len(f1_data):
            combined.append({"sport": "Formula 1", "team": f1_data[i]["team"]["name"]})
        if i < len(hockey_data):
            combined.append({"sport": "Hockey", "team": hockey_data[i]["team"]["name"]})
        if i < len(afl_data):
            combined.append({"sport": "AFL", "team": afl_data[i]["team"]["name"]})

    st.info(f"[DEBUG] Combined list length: {len(combined)}")
    return combined

def main():
    st.title("Multi-Sport Teams Data Fetcher")

    combined_teams = fetch_combined_sports_data()

    if not combined_teams:
        st.warning("No teams data fetched.")
        return

    st.subheader("First 10 teams (alternating sports):")
    for idx, team_info in enumerate(combined_teams[:10], start=1):
        st.write(f"{idx}. {team_info['sport']} - {team_info['team']}")

if __name__ == "__main__":
    main()
