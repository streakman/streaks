import streamlit as st
import requests
import openai
import json
import time
from openai.error import RateLimitError

# API key used for all sports APIs (including hockey)
API_KEY = st.secrets["api_football_key"]
openai.api_key = st.secrets["openai_api_key"]

@st.cache_data(ttl=86400)
def fetch_hockey_teams():
    st.info("[DEBUG] Fetching Hockey teams from API-Hockey")
    url = "https://v3.icehockey.api-sports.io/teams?league=57&season=2023"
    headers = {"x-apisports-key": API_KEY}
    response = requests.get(url, headers=headers)
    st.info(f"[DEBUG] API response status: {response.status_code}")
    if response.status_code != 200:
        raise Exception("Failed to fetch Hockey teams.")
    teams = response.json().get("response", [])
    team_names = [team["team"]["name"] for team in teams]
    st.info(f"[DEBUG] Retrieved {len(team_names)} teams")
    return team_names

def extract_json(response_text):
    st.info("[DEBUG] Extracting JSON from OpenAI response")
    try:
        start = response_text.index("[")
        end = response_text.rindex("]") + 1
        return response_text[start:end]
    except ValueError as ve:
        st.error(f"[DEBUG] JSON extraction error: {ve}")
        return "[]"

def generate_trivia_questions(teams_data):
    st.info("[DEBUG] Generating 3 Hockey trivia questions with OpenAI")
    prompt = (
        "Generate 3 unique hockey trivia questions using only the following team names: "
        f"{', '.join(teams_data)}. Each question should be a dictionary with keys: "
        "'question', 'choices' (4 options), and 'answer'. Make sure answers are accurate."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000,
        )
        raw_text = response.choices[0].message.content
        st.info(f"[DEBUG] OpenAI raw response snippet: {raw_text[:200]}...")
        questions_json = extract_json(raw_text)
        questions = json.loads(questions_json)
        st.info(f"[DEBUG] Parsed {len(questions)} questions")
        return questions
    except RateLimitError:
        st.warning("[DEBUG] RateLimitError caught, please try later.")
        raise
    except json.JSONDecodeError as jde:
        st.error(f"[DEBUG] JSON decoding error: {jde}")
        return []
    except Exception as e:
        st.error(f"[DEBUG] Error generating questions: {e}")
        return []

@st.cache_data(ttl=86400)
def get_daily_questions(teams_data):
    retries = 3
    for attempt in range(retries):
        try:
            questions = generate_trivia_questions(teams_data)
            if questions:
                return questions
            else:
                st.warning("[DEBUG] No questions generated, retrying...")
        except RateLimitError:
            wait = 5 + attempt * 5
            st.warning(f"Rate limited. Retrying in {wait} seconds...")
            time.sleep(wait)
        except Exception as e:
            st.error(f"[DEBUG] Exception on attempt {attempt + 1}: {e}")
            return []
    return []

def main():
    st.title("Hockey Trivia Game Powered by API-Hockey & OpenAI")

    st.info("Fetching Hockey teams data from API-Hockey...")
    try:
        teams = fetch_hockey_teams()
    except Exception as e:
        st.error(f"Error fetching hockey teams: {e}")
        return

    st.info("Generating trivia questions, please wait...")
    questions = get_daily_questions(teams)

    if not questions:
        st.error("No trivia questions available right now. Please try again later.")
        return

    st.markdown("### Today's Hockey Trivia Questions")
    user_answers = []

    for idx, q in enumerate(questions, 1):
        question_text = q.get("question", f"Missing question {idx}")
        choices = q.get("choices", [])
        if not isinstance(choices, list) or len(choices) != 4:
            st.error(f"Invalid choices format for question {idx}")
            continue

        st.write(f"**Q{idx}:** {question_text}")
        choice = st.radio("Your answer:", choices, key=f"q{idx}")
        user_answers.append(choice)
        st.write("---")

    if st.button("Submit Answers"):
        score = 0
        for i, (q, a) in enumerate(zip(questions, user_answers), 1):
            correct = q.get("answer")
            if a == correct:
                score += 1
            st.markdown(f"**Q{i} Answer:** {correct}")
        st.success(f"You scored {score} / {len(questions)}!")

if __name__ == "__main__":
    main()
