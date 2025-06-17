import streamlit as st
import openai

openai.api_key = st.secrets["openai_api_key"]

st.title("Test OpenAI")

if st.button("Generate"):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say hello"}]
    )
    st.write(response.choices[0].message.content)
