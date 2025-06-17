import streamlit as st
import http.client
import json
import time
import openai
import os
import re
from openai.error import RateLimitError

# Load API keys
API_FOOTBALL_KEY = st.secrets.get("API_FOOTBALL_KEY") or os.getenv("API_FOOTBALL_KEY")
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

if not API_FOOTBALL_KEY or not OPENAI_API_KEY:
    st.error("Missing API keys. Please set API_FOOTBALL_KEY and OPENAI_API_KEY.")
    st.stop()

openai.api_key = OPENAI_API_KEY

def fetch_nfl_teams():
    st.info("Fetching NFL teams data from API-Football...")
    try:
        conn = http.client.HTTPSConnection("v3.football.api-sports.io")
        headers = {'x-apisports-key': API_FOOTBALL_KEY}
        conn.request("GET", "/teams?league=3&season=2023", headers=headers)
        res = conn.getresponse()
        data = res.read()
        data_json = json.loads(data.decode("utf-8"))
        if data_json.get("errors"):
            st.error(f"API error: {data_json['errors']}")
            return []
        teams = data_json.get("response", [])
        return [{"name": t["team"]["name"], "stadium": t.get("venue", {}).get("name", "N/A")} for t in teams]
    except Exception as e:
        st.error(f"Error fetching teams: {e}")
        return []

def extract_json(text):
    match = re.search(r"\[.*\]", text, re.DOTALL)
    return match.group(0) if match else None

def call_openai_for_questions(teams_data):
    prompt = (
        "Create 10 NFL trivia questions as a JSON array. Each item should be a JSON object with keys: "
        "'question' (string), 'choices' (list of 4 strings), and 'answer' (the correct string). "
        "Use the following team data:\n\n"
        f"{json.dumps(teams_data, indent=2)}"
    )

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1100,
        temperature=0.7,
    )

    raw_content = response.choices[0].message.content
    st.code(raw_content, language="json")  # Debug view in Streamlit

    json_block = extract_json(raw_content)
    if not json_block:
        raise ValueError("Could not extract JSON from OpenAI output.")

    try:
        parsed = json.loads(json_block)
        if isinstance(parsed, list) and all(isinstance(q, dict) for q in parsed):
            return parsed
        else:
            raise ValueError("Parsed content is not a list of dicts.")
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON decode error: {e}")

def generate_trivia_questions_with_retry(teams_data, retries=3, wait=10):
    for attempt in range(retries):
        try:
            return call_openai_for_questions(teams_data)
        except RateLimitError:
            if attempt < retries - 1:
                st.warning(f"Rate limited. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                st.error("OpenAI rate limit hit. Try again later.")
                return []
        except Exception as e:
            st.error(f"Trivia generation failed: {e}")
            return []

@st.cache_data(ttl=86400)
def get_teams_cached():
    return fetch_nfl_teams()

def main():
    st.title("🏈 NFL Trivia Game Powered by API-Football & OpenAI")

    teams_data = get_teams_cached()
    if not teams_data:
        st.warning("Could not get NFL team data.")
        return

    st.info("Generating trivia questions, please wait...")
    questions = generate_trivia_questions_with_retry(teams_data)
    if not questions:
        st.warning("Trivia generation failed.")
        return

    st.markdown("### Today's NFL Trivia Questions")
    user_answers = []

    for idx, q in enumerate(questions, 1):
        st.write(f"**Q{idx}:** {q['question']}")
        choice = st.radio("Your answer:", q['choices'], key=f"q{idx}")
        user_answers.append(choice)
        st.write("---")

    if st.button("Submit Answers"):
        score = sum(1 for q, a in zip(questions, user_answers) if a == q['answer'])
        st.success(f"You scored {score} / {len(questions)}!")
        for i, q in enumerate(questions, 1):
            st.markdown(f"**Q{i} Answer:** {q['answer']}")

if __name__ == "__main__":
    main()
