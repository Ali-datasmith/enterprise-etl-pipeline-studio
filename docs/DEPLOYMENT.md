# Deployment Guide

## Streamlit Community Cloud Deployment

1. Fork or push this repository to GitHub under your account.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io).
3. Click **New app**, select your repository, branch (`main`), and set the main file path to `app.py`.
4. (Optional) Set Secrets in Streamlit Community Cloud:
   - Go to App Settings -> Secrets.
   - Add your Google Gemini API key:
     ```toml
     GOOGLE_API_KEY = "AIzaSy..."
     GEMINI_MODEL = "gemini-2.5-flash"
     ```
5. Click **Deploy!**

> **Note:** The application will boot successfully even if `GOOGLE_API_KEY` is absent. Core non-AI ETL pipeline features remain fully functional.

## Local Development Deployment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
streamlit run app.py
```
