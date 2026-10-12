import io
import re
from typing import List, TypedDict

import PyPDF2
import streamlit as st
from google import genai
from google.genai import types

MODEL_NAME = "gemini-3.8-flash"
MAX_CONTEXT_CHARS = 12000
STOP_WORDS = {
    "a", "an", "and", "about", "for", "from", "how", "in", "is", "of", "on",
    "or", "the", "to", "what", "when", "where", "who", "does", "do", "this",
    "that", "with",
}

EXAMPLE_QUESTIONS = [
    "Who is the lecturer and what is the course code?",
    "What is the attendance policy?",
    "When is the midterm exam?",
    "What is the Wi-Fi password for the student lounge?",
]


class PdfPage(TypedDict):
    page: int
    text: str


st.set_page_config(page_title="Campus Document Assistant", page_icon="📚", layout="centered")

st.title("📚 Campus AI Document Q&A Assistant")
st.caption(f"Answers only from your uploaded PDF · {MODEL_NAME} · GDG on Campus demo")

with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Gemini API key", type="password", help="Use a Google AI Studio key. Do not screenshot this.")
    uploaded_file = st.file_uploader("Upload a PDF (syllabus, guidelines, FAQ)", type=["pdf"])
    st.caption("Try `sample_syllabus.pdf` in this folder if you need a demo file.")


@st.cache_data(show_spinner=False)
def extract_pages(file_bytes: bytes) -> List[PdfPage]:
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    pages: List[PdfPage] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append({"page": index, "text": text.strip()})
    return pages


def select_pages(pages: List[PdfPage], query: str, max_chars: int = MAX_CONTEXT_CHARS) -> List[PdfPage]:
    total = sum(len(page["text"]) for page in pages)
    if total <= max_chars:
        return pages

    tokens = [
        token.lower()
        for token in re.findall(r"[a-zA-Z0-9]+", query)
        if token.lower() not in STOP_WORDS and len(token) > 1
    ]

    def score(page: PdfPage) -> int:
        blob = page["text"].lower()
        if not tokens:
            return 0
        return sum(blob.count(token) for token in tokens)

    ranked = sorted(pages, key=lambda page: (-score(page), page["page"]))
    chosen: List[PdfPage] = []
    used = 0
    seen = set()

    for page in [pages[0], *ranked]:
        if page["page"] in seen:
            continue
        chunk_len = len(page["text"]) + 24
        if chosen and used + chunk_len > max_chars:
            continue
        chosen.append(page)
        seen.add(page["page"])
        used += chunk_len

    return sorted(chosen, key=lambda page: page["page"])


def build_context(pages: List[PdfPage]) -> str:
    return "\n".join(f"--- Page {page['page']} ---\n{page['text']}" for page in pages)


def ask_document(api_key: str, context: str, question: str) -> str:
    client = genai.Client(api_key=api_key)
    prompt = f"""You are a campus document assistant.
Answer the student's question using ONLY the document context below.
If the answer is not in the context, say that the information is not in the uploaded document.
Do not invent policies, dates, names, or contact details.
Quote or paraphrase briefly and mention the page number when you can.

DOCUMENT CONTEXT:
{context}

STUDENT QUESTION:
{question}
"""
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=500),
    )
    return (response.text or "").strip() or "The model returned an empty answer. Try again."


if uploaded_file and api_key:
    pages = extract_pages(uploaded_file.getvalue())
    page_count = len(pages)
    extracted_chars = sum(len(page["text"]) for page in pages)
    empty_pages = sum(1 for page in pages if not page["text"])

    st.success(f"Loaded **{uploaded_file.name}** · {page_count} page(s) · {extracted_chars:,} characters extracted")

    if extracted_chars < 40:
        st.warning(
            "Almost no text was extracted. This PDF may be scanned or image-only. "
            "Try a text-based PDF such as `sample_syllabus.pdf`."
        )
    elif empty_pages:
        st.info(f"{empty_pages} page(s) had no extractable text and will be skipped.")

    st.subheader("Ask a question")
    st.caption("Start with an example, then try your own.")

    if "query" not in st.session_state:
        st.session_state.query = ""

    cols = st.columns(2)
    for index, example in enumerate(EXAMPLE_QUESTIONS):
        if cols[index % 2].button(example, use_container_width=True):
            st.session_state.query = example

    query = st.text_input("Your question", key="query")

    if st.button("Get answer", type="primary") and query.strip():
        if extracted_chars < 40:
            st.error("There is not enough extracted text to answer from. Upload a different PDF.")
        else:
            selected = select_pages(pages, query.strip())
            context = build_context(selected)
            with st.spinner("Reading the document with Gemini..."):
                try:
                    answer = ask_document(api_key, context, query.strip())
                    st.markdown("### Answer")
                    st.write(answer)
                    used_pages = ", ".join(str(page["page"]) for page in selected)
                    st.caption(f"Context sent from page(s): {used_pages}")
                except Exception as error:
                    st.error(
                        f"Could not get an answer ({error}). "
                        f"Check the API key and that `{MODEL_NAME}` is available for your account."
                    )

elif not api_key:
    st.info("Enter your Gemini API key in the sidebar to get started.")
elif not uploaded_file:
    st.info("Upload a PDF in the sidebar. You can use `sample_syllabus.pdf` for a rehearsal.")
