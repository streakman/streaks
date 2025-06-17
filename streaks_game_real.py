import streamlit as st
import http.client
import json
import time
import openai
import os

# Load API keys from secrets or environment variables
API_FOOTBALL_KEY = st.secrets.get("API_FOOTBALL_KEY") or os.getenv("API_FOOTBALL_KEY")
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

if not API_FOOTBALL_KEY or not OPENAI_API_KEY:
    st.error("Please set your API_FOOTBALL_KEY and OPENAI_API_KEY in Streamlit secrets or environment variables.")
    st.stop()

openai.api_key = OPENAI_API_KEY

def fetch_nfl_teams():
    st.info("Fetching NFL teams data from API-Football...")
    try:
        conn = http.client.HTTPSConnection("v3.football.api-sports.io")
        headers = {
            'x-apisports-key': API_FOOTBALL_KEY
        }
        conn.request("GET", "/teams?league=3&season=2023", headers=headers)
        res = conn.getresponse()
        data = res.read()
        data_json = json.loads(data.decode("utf-8"))

        if data_json.get("errors"):
            st.error(f"API error: {data_json['errors']}")
            return []

        teams = data_json.get("response", [])
        if not teams:
            st.warning("No NFL teams found in API response.")
            return []

        simplified = [{"name": team["team"]["name"], "stadium": team.get("venue", {}).get("name", "N/A")} for team in teams]
        return simplified

    except Exception as e:
        st.error(f"Error fetching NFL teams: {e}")
        return []

def generate_trivia_questions(teams_data, retries=3, wait=10):
    prompt = (
        "Create 10 sports trivia questions about NFL teams using the following teams data. "
        "Each question should have 4 multiple-choice options and the correct answer. "
        "Return the output as a JSON array with keys 'question', 'choices', and 'answer'.\n\n"
        f"Teams data: {json.dumps(teams_data, indent=2)}"
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

@st.cache_data(ttl=86400)
def get_daily_questions(teams_data):
    return generate_trivia_questions(teams_data)

def main():
    st.title("NFL Trivia Game Powered by API-Football & OpenAI")

    teams_data = fetch_nfl_teams()
    if not teams_data:
        st.warning("No NFL teams data available. Cannot generate trivia.")
        return

    st.info("Generating trivia questions, please wait...")
    questions = get_daily_questions(teams_data)
    if not questions:
        st.warning("Failed to generate trivia questions.")
        return

    st.write("---")
    st.write("### Today's NFL Trivia Questions:")

    # Collect user answers
    answers = []
    for idx, q in enumerate(questions, start=1):
        st.write(f"**Question {idx}:** {q['question']}")
        choice = st.radio("Select your answer:", q['choices'], key=f"q{idx}")
        answers.append(choice)
        st.write("---")

    if st.button("Submit All Answers"):
        score = sum(1 for ans, q in zip(answers, questions) if ans == q['answer'])
        st.success(f"You scored {score} out of {len(questions)}!")
        # Optionally show correct answers for review
        for idx, q in enumerate(questions, start=1):
            st.write(f"Question {idx} Correct Answer: **{q['answer']}**")

if __name__ == "__main__":
    main()
