import streamlit as st
import requests
import json
import time
import os
import openai

# Load API keys from Streamlit secrets or env vars
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
API_FOOTBALL_KEY = st.secrets.get("API_FOOTBALL_KEY") or os.getenv("API_FOOTBALL_KEY")

if not OPENAI_API_KEY or not API_FOOTBALL_KEY:
    st.error("Please set your OPENAI_API_KEY and API_FOOTBALL_KEY in Streamlit secrets or environment variables.")
    st.stop()

openai.api_key = OPENAI_API_KEY

# Fetch NFL teams from API-Football v3
def fetch_nfl_teams(season=2023, league_id=3):  # NFL league_id usually 3; confirm on your dashboard
    url = "https://v3.americanfootball.api-sports.io/teams"
    headers = {
        "x-apisports-key": API_FOOTBALL_KEY,
    }
    params = {
        "season": season,
        "league": league_id,
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "response" not in data or not data["response"]:
            st.warning("No NFL teams data found in API response.")
            return []
        teams = []
        for team in data["response"]:
            teams.append({
                "name": team["team"]["name"],
                "city": team["team"]["city"],
                "country": team["team"]["country"],
                "founded": team["team"]["founded"],
                "venue": team["venue"]["name"] if "venue" in team else "Unknown"
            })
        return teams
    except Exception as e:
        st.error(f"Error fetching NFL teams from API-Football: {e}")
        return []

# Generate trivia questions using OpenAI GPT, with retry & backoff
def generate_trivia_questions(data_summary, retries=3, wait=10):
    prompt = (
        "Generate 10 interesting NFL trivia questions with 4 multiple-choice answers each. "
        "Use the following NFL teams data as context:\n"
        f"{json.dumps(data_summary, indent=2)}\n"
        "Return the questions as a JSON list, each with 'question', 'choices' (list of 4), and 'answer' (correct choice)."
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
                st.warning(f"Rate limit reached. Retrying in {wait} seconds...")
                time.sleep(wait)
            else:
                st.error("Rate limit exceeded. Please try again later.")
                return []
        except Exception as e:
            st.error(f"OpenAI error: {e}")
            return []

# Cache daily questions so you don't get charged multiple times per day
@st.cache_data(ttl=86400)
def get_daily_questions(data_summary):
    return generate_trivia_questions(data_summary)

def main():
    st.title("Streaks-Style NFL Trivia Game")

    st.info("Fetching NFL teams data...")
    nfl_teams = fetch_nfl_teams()

    if not nfl_teams:
        st.warning("No NFL teams data available, cannot generate trivia.")
        return

    st.info("Generating trivia questions (this may take a few seconds)...")
    questions = get_daily_questions(nfl_teams)

    if not questions:
        st.warning("No trivia questions were generated.")
        return

    st.write("---")
    st.write("### Today's NFL Trivia Questions:")

    for idx, q in enumerate(questions, start=1):
        st.write(f"**Question {idx}:** {q['question']}")
        choice = st.radio("Select your answer:", q['choices'], key=f"q{idx}")

        if st.button("Submit Answer", key=f"submit_{idx}"):
            if choice == q["answer"]:
                st.success("Correct! 🎉")
            else:
                st.error(f"Wrong. The correct answer is: {q['answer']}")
        st.write("---")

if __name__ == "__main__":
    main()
