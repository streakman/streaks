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

HEADERS = {
    "x-apisports-key": API_FOOTBALL_KEY
}

# Fetch NFL teams for the 2023 season
def fetch_nfl_teams():
    url = "https://v1.americanfootball.api-sports.io/teams?season=2023"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        teams = data.get("response", [])
        # Extract team names and cities
        simplified_teams = [{
            "name": team["team"]["name"],
            "city": team["team"]["city"],
            "conference": team["team"].get("conference", "N/A"),
            "division": team["team"].get("division", "N/A"),
        } for team in teams]
        return simplified_teams
    except Exception as e:
        st.error(f"Error fetching NFL teams from API-Football: {e}")
        return []

# Generate trivia questions using OpenAI
def generate_trivia_questions(data_summary, retries=3, wait=10):
    prompt = (
        "Create 10 interesting NFL trivia questions with 4 multiple-choice answers each. "
        "Use the following NFL teams data to create questions about teams, cities, conferences, or divisions:\n"
        f"{json.dumps(data_summary, indent=2)}\n"
        "Return the questions in JSON format as a list. Each item should have 'question', 'choices' (list of 4 strings), and 'answer' (correct choice string)."
    )

    for attempt in range(retries):
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
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
        except json.JSONDecodeError:
            st.error("Failed to decode JSON from OpenAI response. Response was:\n" + questions_json)
            return []
        except Exception as e:
            st.error(f"OpenAI error: {e}")
            return []

@st.cache_data(ttl=86400)
def get_daily_questions(data_summary):
    return generate_trivia_questions(data_summary)

def main():
    st.title("NFL Trivia Game - Powered by API-Football & OpenAI")

    st.info("Fetching NFL teams data...")
    nfl_teams = fetch_nfl_teams()

    if not nfl_teams:
        st.warning("No NFL teams data available. Cannot generate trivia.")
        return

    st.info("Generating trivia questions (this may take a few seconds)...")
    questions = get_daily_questions(nfl_teams)

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
