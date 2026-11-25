# ResumePilot – Free Starter

A local Streamlit MVP for uploading a master resume, adding job descriptions, estimating keyword overlap, generating an AI-tailored draft with Gemini, and downloading a DOCX.

## Requirements
- Python 3.10+
- Internet connection only for installing packages and optional Gemini API calls

## Windows setup
1. Extract the ZIP.
2. Open the extracted `ResumePilot_Free_Starter` folder in VS Code.
3. Open Terminal > New Terminal.
4. Run:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

5. The website opens in your browser at `http://localhost:8501`.

## Optional Gemini API
- Create a key in Google AI Studio: https://aistudio.google.com/app/apikey
- In the app sidebar, paste the key. Or copy `.env.example` to `.env` and set `GEMINI_API_KEY`.
- Never commit your API key or share it.
- Gemini free-tier availability, model names, limits and data terms can change. Do not send personal resume information unless you have reviewed the provider's terms and have appropriate consent.

## Important limitations
- This is a local MVP, not yet a public multi-user SaaS.
- Match score is a basic keyword-overlap estimate, not a guaranteed ATS score or hiring probability.
- The app does not automatically submit applications. Apply opens the employer's job URL.
- AI tailoring is optional and requires an API key and available quota.
- Always review generated resumes. The app instructs the AI not to invent experience, but human verification is essential.
- Scanned/image-only PDFs may not extract text correctly.
- No account system or cloud resume storage is included in this starter.
