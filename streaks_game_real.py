import streamlit as st
import requests
import json
import time
import os
import openai

# Load API keys
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
API_SPORTS_KEY = st.secrets.get("API_SPORTS_API_KEY") or os.getenv("API_SPORTS_API_KEY")

if not OPENAI_API_KEY or not API_SPORTS_KEY:
    st.error("Please set your OPENAI_API_KEY and API_SPORTS_API_KEY in Streamlit secrets or environment variables.")
    st.stop()

openai.api_key = OPENAI_API_KEY

# This is the **correct** base URL for direct api-sports.io subscription (check your docs)
API_SPORTS_BASE_URL = "https://api.api-sports.io/basketball"

headers = {
    "Authorization": f"Bearer {API_SPORTS_KEY}",
    "Content-Type": "application/json"
}

def fetch_nba_teams():
    """
    Fetch NBA teams from API-SPORTS direct API.
    League ID for NBA is 12, season example is 2023.
    """
    url = f"{API_SPORTS_BASE_URL}/teams"
    params = {"league": "12", "season": "2023"}
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()

        if not data or "response" not in data:
            st.warning("Unexpected API response structure.")
            return []
        
        teams = []
        for team in data["response"]:
            teams.append({
                "name": team["team"]["name"],
                "city": team["team"]["city"],
                "abbreviation": team["team"]["abbreviation"],
                "logo": team["team"]["logo"]
            })
        return teams

    except requests.exceptions.RequestException as e:
        st.error(f"Network/API error fetching NBA teams: {e}")
        return []

def generate_trivia_questions(data_summary, retries=3, wait=10):
    prompt = (
        "Generate 10 multiple-choice NBA trivia questions using this teams data:\n"
        f"{json.dumps(data_summary, indent=2)}\n"
        "Format as a JSON list of objects with 'question', 'choices' (list of 4 strings), and 'answer' (correct choice)."
    )

    for attempt in range(retries):
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1100,
                temperature=0.7,
            )
            questions_json = response.choices[0].message.content
            return json.loads(questions_json)
        except openai.error.RateLimitError:
            if attempt < retries - 1:
                st.warning(f"Rate limit hit. Retrying in {wait} seconds...")
                time.sleep(wait)
            else:
                st.error("Rate limit exceeded. Try again later.")
                return []
        except Exception as e:
            st.error(f"OpenAI error: {e}")
            return []

@st.cache_data(ttl=86400)
def get_daily_questions(data_summary):
    return generate_trivia_questions(data_summary)

def main():
    st.title("NBA Teams Trivia with API-SPORTS")

    st.info("Fetching NBA teams data...")
    teams = fetch_nba_teams()

    if not teams:
        st.warning("No NBA teams data available.")
        return

    st.info("Generating trivia questions...")
    questions = get_daily_questions(teams)

    if not questions:
        st.warning("No questions generated.")
        return

    for i, q in enumerate(questions, 1):
        st.write(f"### Question {i}: {q['question']}")
        choice = st.radio("Select your answer:", q["choices"], key=f"q{i}")

        if st.button("Submit Answer", key=f"submit_{i}"):
            if choice == q["answer"]:
                st.success("Correct! 🎉")
            else:
                st.error(f"Wrong. The correct answer is: {q['answer']}")
        st.write("---")

if __name__ == "__main__":
    main()
