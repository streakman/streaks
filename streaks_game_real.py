import streamlit as st
import requests
import os

SPORTSDB_API_KEY = st.secrets.get("SPORTSDB_API_KEY") or os.getenv("SPORTSDB_API_KEY")

if not SPORTSDB_API_KEY:
    st.error("Set your SPORTSDB_API_KEY in Streamlit secrets or environment variables.")
    st.stop()

url = f"https://www.thesportsdb.com/api/v1/json/{SPORTSDB_API_KEY}/lookuptable.php?l=4387&s=2023-2024"

st.write(f"Requesting URL: {url}")

try:
    res = requests.get(url, timeout=10)
    st.write(f"Status code: {res.status_code}")
    st.write(f"Response text:\n{res.text}")

    res.raise_for_status()  # Raises error on HTTP 4xx/5xx

    data = res.json()
    st.write("Parsed JSON data:")
    st.json(data)

except requests.exceptions.HTTPError as http_err:
    st.error(f"HTTP error occurred: {http_err}")
except requests.exceptions.RequestException as req_err:
    st.error(f"Request exception occurred: {req_err}")
except ValueError as json_err:
    st.error(f"JSON decode error: {json_err}")
