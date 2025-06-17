import streamlit as st
import requests
import json
import time
import os
import openai

# Load API keys from Streamlit secrets or environment variables
API_FOOTBALL_KEY = st.secrets.get("API_FOOTBALL_KEY") or os.getenv("API_FOOTBALL_KEY")
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

if not API_FOOTBALL_KEY or not OPENAI_API_KEY:
    st.error("Please set your API_FOOTBALL_KEY and OPENAI_API_KEY in Streamlit secrets or environment variables.")
    st.stop()

openai.api_key = OPENAI_API_KEY

# Fetch NFL teams from API-Football
def fetch_nfl_teams(season=2023):
    url = "https://v3.api-football.com/americanfootball/teams"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    params = {"season": season}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        # You may want to explore the full structure of data and adjust accordingly:
        if "response" in data:
            teams = data["response"]
            simplified = []
            for team_info in teams:
                team = team_info.get("team", {})
                simplified.append({
                    "id": team.get("id"),
                    "name": team.get("name"),
                    "city": team.get("city"),
                    "logo": team.get("logo"),
                })
            return simplified
        else:
            st.error("Unexpected data format from API-Football.")
            return []
    except Exception as e:
        st.error(f"Error fetching NFL teams from API-Football: {e}")
        return []

# Generate trivia questions using OpenAI GPT
def generate_trivia_questions(teams_data, retries=3, wait=10):
    prompt = (
        "Generate 10 multiple-choice sports trivia questions based on the following NFL teams data. "
        "Format as a JSON list of questions with 'question', 'choices' (4 options), and 'answer' (correct choice).\n\n"
        f"{json.dumps(teams_data, indent=2)}"
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
                st.error("Rate limit exceeded. Please try again later.")
                return []
        except Exception as e:
            st.error(f"OpenAI error: {e}")
            return []

@st.cache_data(ttl=86400)
def get_daily_questions(teams_data):
    return generate_trivia_questions(teams_data)

def main():
    st.title("NFL Trivia with API-Football & OpenAI")

    st.info("Fetching NFL teams data...")
    teams = fetch_nfl_teams()

    if not teams:
        st.warning("No NFL teams data available, cannot generate trivia.")
        return

    st.write("### NFL Teams Retrieved:")
    for team in teams:
        st.write(f"- {team['name']} ({team['city']})")

    st.info("Generating trivia questions...")
    questions = get_daily_questions(teams)

    if not questions:
        st.warning("No trivia questions generated.")
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
