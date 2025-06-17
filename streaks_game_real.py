import streamlit as st
import openai
import json
import random
import time
from openai.error import RateLimitError

# Set your OpenAI API key
OPENAI_API_KEY = st.secrets["openai_api_key"]
openai.api_key = OPENAI_API_KEY

# Static hockey teams list to avoid API limits
@st.cache_data(ttl=86400)
def fetch_hockey_teams():
    st.info("[DEBUG] Using static hockey teams data")
    return [
        "Boston Bruins",
        "Chicago Blackhawks",
        "Detroit Red Wings",
        "Montreal Canadiens",
        "New York Rangers",
        "Toronto Maple Leafs"
    ]

# Extract JSON array from OpenAI response
def extract_json(response_text):
    st.info("[DEBUG] Extracting JSON from OpenAI response")
    try:
        start = response_text.index("[")
        end = response_text.rindex("]") + 1
        json_str = response_text[start:end]
        st.info("[DEBUG] Successfully extracted JSON")
        return json_str
    except Exception as e:
        st.error(f"[DEBUG] JSON extraction error: {e}")
        return "[]"

# Generate trivia questions with OpenAI
def generate_trivia_questions(teams_data):
    st.info("[DEBUG] Generating trivia questions from OpenAI")
    prompt = (
        "Generate 3 unique hockey trivia questions using only the following teams: "
        f"{', '.join(teams_data)}. Each question should be a dictionary with keys: "
        "'question' (str), 'choices' (list of 4 strings), and 'answer' (one of the choices). "
        "Output only a JSON array of these questions."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800,
        )
        raw = response.choices[0].message.content
        st.info(f"[DEBUG] Raw OpenAI response snippet: {raw[:200]}...")
        clean_json = extract_json(raw)
        questions = json.loads(clean_json)
        st.info(f"[DEBUG] Parsed {len(questions)} questions successfully")
        return questions
    except RateLimitError:
        st.warning("[DEBUG] OpenAI RateLimitError: Please try again later.")
        return []
    except json.JSONDecodeError as e:
        st.error(f"[DEBUG] JSON decoding error: {e}")
        return []
    except Exception as e:
        st.error(f"[DEBUG] Unexpected error: {e}")
        return []

# Retry wrapper with caching
@st.cache_data(ttl=86400)
def get_daily_questions(teams_data):
    retries = 3
    for attempt in range(retries):
        st.info(f"[DEBUG] get_daily_questions attempt {attempt + 1}")
        questions = generate_trivia_questions(teams_data)
        if questions:
            return questions
        else:
            wait = 3 + attempt * 3
            st.info(f"[DEBUG] Waiting {wait}s before retry...")
            time.sleep(wait)
    return []

def main():
    st.title("Hockey Trivia Game Powered by OpenAI")
    st.write("Test your hockey knowledge with AI-generated trivia questions!")

    teams = fetch_hockey_teams()
    st.info(f"[DEBUG] Loaded {len(teams)} hockey teams")

    st.info("Generating 3 trivia questions, please wait...")
    questions = get_daily_questions(teams)

    if not questions:
        st.error("No trivia questions available right now. Please try again later.")
        return

    user_answers = []
    for i, q in enumerate(questions, 1):
        try:
            question = q.get("question", f"Missing question {i}")
            choices = q.get("choices", [])
            if not isinstance(choices, list) or len(choices) != 4:
                raise ValueError("Invalid choices format.")

            st.write(f"**Q{i}:** {question}")
            choice = st.radio(f"Your answer for Q{i}:", choices, key=f"q{i}")
            user_answers.append(choice)
            st.write("---")
        except Exception as e:
            st.error(f"Error displaying question {i}: {e}")
            user_answers.append(None)

    if st.button("Submit Answers"):
        score = 0
        for i, (q, a) in enumerate(zip(questions, user_answers), 1):
            correct = q.get("answer")
            if a == correct:
                score += 1
            st.markdown(f"**Q{i} answer:** {correct}")
        st.success(f"Your score: {score} out of {len(questions)}")

if __name__ == "__main__":
    main()
