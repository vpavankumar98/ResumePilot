import os
import re
import io
import json
from datetime import datetime

import streamlit as st
import fitz
from docx import Document
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="ResumePilot | Free Edition", page_icon="📄", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 2rem; max-width: 1200px;}
.hero {padding: 1.5rem; border-radius: 16px; background: linear-gradient(120deg,#14213d,#2563eb); color:white;}
.job-card {padding: 1rem; border: 1px solid #d9deea; border-radius: 14px; margin-bottom: .8rem;}
.small-muted {color: #667085; font-size: .9rem;}
</style>
""", unsafe_allow_html=True)

if "jobs" not in st.session_state:
    st.session_state.jobs = []
if "master_text" not in st.session_state:
    st.session_state.master_text = ""
if "master_name" not in st.session_state:
    st.session_state.master_name = ""
if "tailored_docx" not in st.session_state:
    st.session_state.tailored_docx = None
if "tailored_text" not in st.session_state:
    st.session_state.tailored_text = ""

def extract_resume(uploaded_file):
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()
    if name.endswith(".pdf"):
        doc = fitz.open(stream=data, filetype="pdf")
        return "\n".join(page.get_text() for page in doc)
    if name.endswith(".docx"):
        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError("Please upload a PDF or DOCX file.")

def extract_jd(uploaded_file):
    if uploaded_file is None:
        return ""
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()
    if name.endswith(".pdf"):
        doc = fitz.open(stream=data, filetype="pdf")
        return "\n".join(page.get_text() for page in doc)
    if name.endswith(".docx"):
        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)
    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore")
    raise ValueError("JD file must be PDF, DOCX or TXT.")

def make_docx(text, title="Tailored Resume"):
    doc = Document()
    doc.add_heading(title, 0)
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if len(line) < 65 and (line.isupper() or line.endswith(":")):
            doc.add_heading(line.rstrip(":"), level=1)
        else:
            doc.add_paragraph(line)
    output = io.BytesIO()
    doc.save(output)
    return output.getvalue()

def keyword_score(resume, jd):
    words = lambda s: set(re.findall(r"[A-Za-z][A-Za-z0-9+#.-]{1,}", s.lower()))
    stop = {"with","from","that","this","will","have","your","their","about","into","years","work","team","role","job","using","good","strong","ability","experience","skills","required","preferred"}
    jd_terms = words(jd) - stop
    resume_terms = words(resume)
    if not jd_terms:
        return 0, []
    matched = sorted(jd_terms & resume_terms)
    score = round(100 * len(matched) / len(jd_terms))
    missing = sorted(jd_terms - resume_terms)
    return min(score, 100), missing[:25]

def ai_tailor(resume, jd, api_key):
    if not api_key:
        return None, "No Gemini API key supplied."
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        prompt = f"""
You are an ethical resume editor. Tailor the candidate's resume to the job description.
Rules:
- Never invent employers, job titles, dates, degrees, certifications, tools, achievements, metrics, or responsibilities.
- Use only facts present in the master resume.
- Reorder and clarify relevant existing information; identify missing requirements separately.
- Keep the resume ATS-friendly, plain text, professional, and concise.
- Return the complete revised resume, then a heading 'GAPS TO REVIEW' with requirements not evidenced in the resume.
MASTER RESUME:
{resume[:18000]}
JOB DESCRIPTION:
{jd[:12000]}
"""
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text, None
    except Exception as e:
        return None, f"AI request failed: {e}"

st.markdown('<div class="hero"><h1>📄 ResumePilot</h1><p>One master resume. Tailored applications for every opportunity.</p><b>Free starter edition · Runs on your computer</b></div>', unsafe_allow_html=True)
st.write("")

with st.sidebar:
    st.header("Settings")
    st.caption("Gemini API is optional. Without it, you can still calculate a basic keyword-match estimate and create a draft.")
    api_key = st.text_input("Gemini API key", value=os.getenv("GEMINI_API_KEY", ""), type="password", help="Get a key from Google AI Studio. Do not share it.")
    st.divider()
    st.caption("Privacy: files are processed by this running app. If you use Gemini, resume/JD text is sent to Google's API. Review its terms before using real personal data.")

tab1, tab2, tab3 = st.tabs(["① Master Resume", "② Add a Job", "③ Dashboard"])

with tab1:
    st.subheader("Upload your master resume")
    uploaded = st.file_uploader("Choose your master resume", type=["pdf", "docx"], key="master_upload")
    if uploaded:
        try:
            extracted = extract_resume(uploaded)
            if not extracted.strip():
                st.error("No text could be extracted. If this is a scanned PDF, run OCR first or upload a DOCX.")
            else:
                st.session_state.master_text = extracted
                st.session_state.master_name = uploaded.name
                st.success(f"Loaded {uploaded.name}")
        except Exception as e:
            st.error(str(e))
    if st.session_state.master_text:
        st.info(f"Master resume ready: {st.session_state.master_name}")
        with st.expander("Preview extracted resume text"):
            st.text(st.session_state.master_text[:8000])
        if st.button("Clear master resume"):
            st.session_state.master_text = ""
            st.session_state.master_name = ""
            st.rerun()
    else:
        st.warning("Upload a PDF or DOCX resume to get started.")

with tab2:
    st.subheader("Add a job opportunity")
    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input("Company", placeholder="e.g. Bentley Systems")
        role = st.text_input("Job title", placeholder="e.g. Applied AI Engineer")
        job_url = st.text_input("Job posting URL", placeholder="https://...")
    with col2:
        jd_file = st.file_uploader("Upload JD (PDF, DOCX or TXT)", type=["pdf", "docx", "txt"], key="jd_file")
        jd_pasted = st.text_area("Or paste the job description", height=180)
    if st.button("Add job and analyze", type="primary", use_container_width=True):
        if not st.session_state.master_text:
            st.error("Upload your master resume first.")
        elif not (jd_pasted.strip() or jd_file):
            st.error("Paste a job description or upload a JD file.")
        else:
            try:
                jd_text = jd_pasted.strip() or extract_jd(jd_file)
                score, missing = keyword_score(st.session_state.master_text, jd_text)
                st.session_state.jobs.append({
                    "company": company or "Company not specified",
                    "role": role or "Role not specified",
                    "url": job_url.strip(),
                    "jd": jd_text,
                    "score": score,
                    "missing": missing,
                    "created": datetime.now().strftime("%d %b %Y %H:%M")
                })
                st.success("Job added to your dashboard.")
                st.rerun()
            except Exception as e:
                st.error(str(e))

with tab3:
    st.subheader("Your job dashboard")
    if not st.session_state.master_text:
        st.info("Upload your master resume in the first tab to begin.")
    if not st.session_state.jobs:
        st.info("No jobs yet. Add your first job in the second tab.")
    for idx, job in enumerate(st.session_state.jobs):
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"### {job['role']}")
                st.write(job["company"])
                st.caption(f"Added {job['created']}")
            with c2:
                st.metric("Match estimate", f"{job['score']}%")
            b1, b2, b3, b4 = st.columns(4)
            with b1:
                if job["url"]:
                    st.link_button("View Job", job["url"], use_container_width=True)
                else:
                    st.button("View Job", key=f"view{idx}", disabled=True, use_container_width=True)
            with b2:
                if job["url"]:
                    st.link_button("Apply", job["url"], use_container_width=True)
                else:
                    st.button("Apply", key=f"apply{idx}", disabled=True, use_container_width=True)
            with b3:
                if st.button("Master Resume", key=f"master{idx}", use_container_width=True):
                    st.session_state["show_master"] = idx
            with b4:
                if st.button("Modify Resume", key=f"modify{idx}", type="primary", use_container_width=True):
                    st.session_state["selected_job"] = idx
            if st.session_state.get("show_master") == idx:
                with st.expander("Master resume text", expanded=True):
                    st.text(st.session_state.master_text[:8000])
            if st.session_state.get("selected_job") == idx:
                st.markdown("#### Tailor resume for this job")
                st.write("Missing/less-evident JD keywords (not proof that you lack these skills):")
                st.write(", ".join(job["missing"]) or "No obvious keyword gaps.")
                if st.button("Generate tailored resume", key=f"generate{idx}", type="primary"):
                    with st.spinner("Preparing tailored resume..."):
                        result, error = ai_tailor(st.session_state.master_text, job["jd"], api_key)
                    if result:
                        st.session_state.tailored_text = result
                        st.session_state.tailored_docx = make_docx(result, f"{job['role']} - Tailored Resume")
                        st.success("Draft generated. Review it carefully before applying.")
                    else:
                        st.error(error)
                        st.info("You can still copy your master resume into a tailored draft manually. Add a valid Gemini API key to enable AI tailoring.")
                if st.session_state.tailored_text:
                    st.text_area("Review and edit tailored resume", key="tailored_editor", value=st.session_state.tailored_text, height=320)
                    edited = st.session_state.get("tailored_editor", st.session_state.tailored_text)
                    st.download_button("Download Modified Resume (DOCX)", data=make_docx(edited, f"{job['role']} - Tailored Resume"), file_name="tailored_resume.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                    st.caption("Please verify every statement, date, skill and achievement before using this resume.")

st.divider()
st.caption("ResumePilot Free Starter · This local starter does not provide public accounts or cloud storage yet.")
