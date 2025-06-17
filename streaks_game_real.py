import streamlit as st
import openai
import json

# Set your OpenAI API key in Streamlit Secrets or directly here
openai.api_key = st.secrets["openai_api_key"]

# Hardcoded NFL teams (32 teams)
NFL_TEAMS = [
    "Arizona Cardinals", "Atlanta Falcons", "Baltimore Ravens", "Buffalo Bills",
    "Carolina Panthers", "Chicago Bears", "Cincinnati Bengals", "Cleveland Browns",
    "Dallas Cowboys", "Denver Broncos", "Detroit Lions", "Green Bay Packers",
    "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars", "Kansas City Chiefs",
    "Las Vegas Raiders", "Los Angeles Chargers", "Los Angeles Rams", "Miami Dolphins",
    "Minnesota Vikings", "New England Patriots", "New Orleans Saints", "New York Giants",
    "New York Jets", "Philadelphia Eagles", "Pittsburgh Steelers", "San Francisco 49ers",
    "Seattle Seahawks", "Tampa Bay Buccaneers", "Tennessee Titans", "Washington Commanders"
]

def extract_json_from_response(text):
    try:
        start = text.index("[")
        end = text.rindex("]") + 1
        return text[start:end]
    except Exception:
        return "[]"

def generate_trivia_questions(teams):
    prompt = (
        "Generate 3 unique NFL trivia questions using only the following team names: "
        f"{', '.join(teams)}.\n"
        "Each question should be a dictionary with keys: 'question' (string), 'choices' (list of 4 strings), and 'answer' (string).\n"
        "Make sure the correct answer is in the choices."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=600
        )
        raw_text = response.choices[0].message.content
        json_text = extract_json_from_response(raw_text)
        questions = json.loads(json_text)
        return questions
    except Exception as e:
        st.error(f"Error generating trivia questions: {e}")
        return []

def main():
    st.title("NFL Trivia Game Powered by OpenAI")
    st.write("Test your NFL knowledge with AI-generated trivia questions!")

    st.info("[DEBUG] Using hardcoded NFL teams list")
    st.info(f"Using {len(NFL_TEAMS)} NFL teams for trivia generation.")

    st.info("Generating 3 trivia questions, please wait...")
    questions = generate_trivia_questions(NFL_TEAMS)

    if not questions:
        st.error("No trivia questions available. Try again later.")
        return

    user_answers = []

    for idx, q in enumerate(questions, 1):
        question_text = q.get("question", f"Question {idx} missing")
        choices = q.get("choices", [])
        if not isinstance(choices, list) or len(choices) != 4:
            st.error(f"Invalid choices for question {idx}")
            return
        st.write(f"**Q{idx}:** {question_text}")
        choice = st.radio(f"Select your answer for Q{idx}:", choices, key=f"q{idx}")
        user_answers.append(choice)
        st.write("---")

    if st.button("Submit Answers"):
        score = 0
        for i, (q, answer) in enumerate(zip(questions, user_answers), 1):
            correct_answer = q.get("answer")
            if answer == correct_answer:
                score += 1
            st.markdown(f"**Q{i} Answer:** {correct_answer}")
        st.success(f"Your score: {score} / {len(questions)}")

if __name__ == "__main__":
    main()
