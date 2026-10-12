# Campus Document Q&A

Streamlit demo that answers questions using **only** an uploaded campus PDF (syllabus, FAQ, or guidelines).

## Run

```powershell
cd "C:\Users\Marcus\Desktop\qna bot"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL Streamlit prints (usually http://localhost:8501).

## Demo (about 2 minutes)

1. Paste a Gemini API key in the sidebar. Do not show the key on screen or in a recording.
2. Upload `sample_syllabus.pdf`.
3. Ask **Who is the lecturer and what is the course code?**
4. Ask **What is the attendance policy?** and **When is the midterm exam?**
5. Ask **What is the Wi-Fi password for the student lounge?** — it should say that is not in the document.
6. Clear the key or PDF to show the empty-state messages.

Get a key from [Google AI Studio](https://aistudio.google.com/apikey).

If generation fails, edit `MODEL_NAME` at the top of `app.py` to a Gemini flash model your key supports.
