import streamlit as st
import openai
import json

# Set your OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["openai_api_key"]

# Hardcoded NFL teams list
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

def generate_trivia_questions(teams):
    prompt = (
        "Generate 3 unique NFL trivia questions using only these teams: "
        + ", ".join(teams)
        + ". Each question should be a JSON dictionary with 'question', 'choices' (list of 4), and 'answer'. "
        "Return a JSON list of these question dictionaries only."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"OpenAI API error: {e}")
        return None

def main():
    st.title("NFL Trivia Game Powered by OpenAI")
    st.write("Test your NFL knowledge with AI-generated trivia questions!")

    st.info("[DEBUG] Using hardcoded NFL teams list")
    st.info(f"Using {len(NFL_TEAMS)} NFL teams for trivia generation.")

    if st.button("Generate Trivia Questions"):
        st.info("Generating 3 trivia questions, please wait...")
        questions_json = generate_trivia_questions(NFL_TEAMS)

        if questions_json:
            st.write("### Generated Questions (raw JSON):")
            st.text(questions_json)

            try:
                questions = json.loads(questions_json)
                st.write("### Questions Preview:")
                for i, q in enumerate(questions, 1):
                    st.markdown(f"**Q{i}:** {q.get('question', 'N/A')}")
                    choices = q.get('choices', [])
                    if isinstance(choices, list):
                        for choice in choices:
                            st.write(f"- {choice}")
                    st.write(f"**Answer:** {q.get('answer', 'N/A')}")
                    st.write("---")
            except json.JSONDecodeError as je:
                st.error(f"Error decoding JSON: {je}")

if __name__ == "__main__":
    main()
