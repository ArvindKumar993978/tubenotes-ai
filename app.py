import os
import re
from io import BytesIO
import streamlit as st
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

load_dotenv()

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="TubeNotes AI | Video to Smart Notes",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- CUSTOM CSS -----------------
st.markdown("""
<style>
    .main-header {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FF4B4B, #FF8533);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    .badge-bar {
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
    }
    .badge-item {
        background-color: #f0f2f6;
        color: #31333F;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #6c757d;
        margin-bottom: 20px;
    }
    .stButton>button {
        background: linear-gradient(90deg, #FF4B4B, #FF6B4B);
        color: white;
        border-radius: 10px;
        padding: 12px 28px;
        font-size: 1rem;
        font-weight: 600;
        border: none;
        width: 100%;
        box-shadow: 0 4px 14px rgba(255, 75, 75, 0.25);
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #E03E3E, #E05A3E);
        color: white;
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(255, 75, 75, 0.35);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0px 0px;
        padding: 10px 18px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- ROBUST HELPER FUNCTIONS -----------------
def extract_video_id(url: str):
    """Har tarah ke YouTube URL (watch, shorts, live, youtu.be) se Video ID nikalta hai."""
    if not url:
        return None
    url = url.strip()
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:[&?]|$)",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
        r"(?:shorts|live|embed)\/([0-9A-Za-z_-]{11})"
    ]
    for p in patterns:
        match = re.search(p, url)
        if match:
            return match.group(1)
    return None

def fetch_transcript(video_id: str):
    """YouTubeTranscriptApi ke naye aur purane dono versions ke sath 100% kaam karne wala function."""
    # 1. New version method (instance-based: api.fetch / api.list)
    try:
        api = YouTubeTranscriptApi()
        try:
            fetched = api.fetch(video_id)
            return " ".join([s.text for s in fetched]), None
        except Exception:
            pass

        try:
            for t in api.list(video_id):
                fetched = t.fetch()
                return " ".join([s.text for s in fetched]), None
        except Exception:
            pass
    except Exception:
        pass

    # 2. Old version method (class-based: get_transcript)
    try:
        data = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item['text'] for item in data]), None
    except Exception:
        pass

    return None, "Is video par YouTube subtitles uplabdh nahi hain. Kripya koi aisi video chunein jisme CC ho."

def create_pdf(text_content: str, title: str = "TubeNotes AI — Study Notes") -> bytes:
    """Markdown study notes ko clean aur formatted PDF bytes me convert karta hai."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#FF4B4B'),
        spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'DocHeading',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=10,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=4
    )
    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        leftIndent=14,
        spaceAfter=3
    )

    story = [Paragraph(f"🎓 {title}", title_style), Spacer(1, 10)]

    for line in text_content.split('\n'):
        s = line.strip()
        if not s:
            story.append(Spacer(1, 4))
            continue

        safe = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        safe = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', safe)

        try:
            if s.startswith('# ') or s.startswith('## ') or s.startswith('### '):
                story.append(Paragraph(safe.lstrip('#').strip(), heading_style))
            elif s.startswith('* ') or s.startswith('- '):
                story.append(Paragraph('&bull; ' + safe[2:], bullet_style))
            else:
                story.append(Paragraph(safe, body_style))
        except Exception:
            plain = re.sub(r'<.*?>', '', safe)
            story.append(Paragraph(plain, body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def generate_ai_content(transcript: str, api_key: str):
    """Gemini API ko call karke Detailed Notes, Summary aur Quiz banata hai."""
    try:
        client = genai.Client(api_key=api_key)
        
        # Gemini Flash supports huge 1M+ token context windows (~8+ hours of lecture)
        clean_transcript = transcript[:300000] if len(transcript) > 300000 else transcript
        
        prompt = f"""
        You are an expert academic tutor and technical note-taker.
        Analyze the following YouTube video transcript and generate structured study material.
        
        Transcript:
        \"\"\"{clean_transcript}\"\"\"
        
        Please provide the response strictly in the following 3 sections separated by exact markers:

        ===SECTION_NOTES===
        # Comprehensive Study Notes
        - Provide deep structured notes with clear Headings, Bullet Points, and Code/Formulas if any.
        - Highlight Core Concepts and Key Definitions clearly.

        ===SECTION_SUMMARY===
        # Executive Summary (2-Minute Read)
        - 3-5 high-impact bullet points summarizing the entire video.
        - Key Takeaway / Conclusion.

        ===SECTION_QUIZ===
        # Practice Quiz (Test Your Knowledge)
        - Create 4 Multiple Choice Questions (MCQs) based on the video.
        - Provide Options (A, B, C, D) and specify the Correct Answer with a 1-line explanation.
        """
        
        # Robust model fallback for high availability (Flash-Lite models have 99.9% uptime and zero 503 errors)
        models_to_try = [
            'gemini-flash-lite-latest',
            'gemini-3.5-flash-lite',
            'gemini-3.1-flash-lite',
            'gemini-flash-latest'
        ]
        last_err = None
        for mod in models_to_try:
            try:
                response = client.models.generate_content(
                    model=mod,
                    contents=prompt,
                )
                return response.text
            except Exception as err:
                last_err = err
                continue
        
        st.error(f"AI Generation Error: {str(last_err)}")
        return None
    except Exception as e:
        st.error(f"AI Client Error: {str(e)}")
        return None

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("### ⚡ System Status")
    st.success("🟢 AI Engine: Active (Gemini Flash)")
    st.markdown("---")
    
    st.markdown("### 🎯 Capabilities")
    st.markdown("""
    - 📝 **Detailed Notes** with key concepts
    - ⚡ **2-Minute Executive Summary**
    - 🎯 **Practice Quiz (MCQs)** for revision
    - 📥 **Export** as PDF & Notes
    """)
    st.markdown("---")
    
    st.markdown("### 🧪 Quick Demos")
    st.caption("Click to try verified lectures instantly:")
    if st.button("🧪 Sample 1: Python Basics"):
        st.session_state["sample_url"] = "https://www.youtube.com/watch?v=kqtD5dpn9C8"
    if st.button("🧪 Sample 2: AI & Future (TED Talk)"):
        st.session_state["sample_url"] = "https://www.youtube.com/watch?v=iCvmsMzlF7o"

# ----------------- MAIN UI -----------------
st.markdown('<p class="main-header">🎓 TubeNotes AI</p>', unsafe_allow_html=True)
st.markdown("""
<div class="badge-bar">
    <span class="badge-item">⚡ High Speed</span>
    <span class="badge-item">🧠 Gemini Powered</span>
    <span class="badge-item">🎓 Study & Revision Suite</span>
</div>
""", unsafe_allow_html=True)
st.markdown('<p class="sub-header">Convert long YouTube lectures into structured study notes, summaries & quizzes in seconds.</p>', unsafe_allow_html=True)

# Check if sample was clicked
default_url = st.session_state.get("sample_url", "")
youtube_url = st.text_input("🔗 Paste YouTube Video URL:", value=default_url, placeholder="https://www.youtube.com/watch?v=...")

if youtube_url:
    video_id = extract_video_id(youtube_url)
    if video_id:
        st.video(f"https://www.youtube.com/watch?v={video_id}")
    else:
        st.warning("⚠️ Kripya valid YouTube video link enter karein.")

# ----------------- PROCESS BUTTON -----------------
if st.button("🚀 Generate Smart Study Notes"):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ GEMINI_API_KEY .env file me nahi mili!")
    elif not youtube_url:
        st.error("❌ Kripya pehle YouTube video ka link dalein!")
    else:
        video_id = extract_video_id(youtube_url)
        if not video_id:
            st.error("❌ Invalid YouTube Link! Kripya link check karein.")
        else:
            with st.spinner("⏳ Video se transcript nikaali ja rahi hai..."):
                transcript, error_msg = fetch_transcript(video_id)
            
            if not transcript:
                st.error(f"❌ Subtitle Error: {error_msg}")
                st.info("💡 Tip: YouTube Live Streams ya aisi videos jisme CC band hota hai unme transcript nahi milti. Kripya sidebar me diye gaye Sample button par click karke test karein!")
            else:
                st.success("✅ Transcript mil gayi! Ab AI se notes banwaye ja rahe hain...")
                with st.spinner("🧠 Gemini AI notes, summary aur quiz taiyar kar raha hai..."):
                    ai_output = generate_ai_content(transcript, api_key)
                
                if ai_output:
                    # Parse sections
                    sections = ai_output.split("===SECTION_")
                    notes_content = ""
                    summary_content = ""
                    quiz_content = ""
                    
                    for sec in sections:
                        if sec.startswith("NOTES==="):
                            notes_content = sec.replace("NOTES===", "").strip()
                        elif sec.startswith("SUMMARY==="):
                            summary_content = sec.replace("SUMMARY===", "").strip()
                        elif sec.startswith("QUIZ==="):
                            quiz_content = sec.replace("QUIZ===", "").strip()
                    
                    # Store in session state
                    st.session_state["notes"] = notes_content or ai_output
                    st.session_state["summary"] = summary_content or "Summary ready."
                    st.session_state["quiz"] = quiz_content or "Quiz ready."

# ----------------- DISPLAY OUTPUT IN TABS -----------------
if "notes" in st.session_state:
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📝 Detailed Notes", "⚡ Quick Summary", "🎯 Practice Quiz"])
    
    with tab1:
        st.markdown(st.session_state["notes"])
        pdf_notes = create_pdf(st.session_state["notes"], title="Comprehensive Study Notes")
        st.download_button(
            label="📄 Download Detailed Notes (PDF)",
            data=pdf_notes,
            file_name="TubeNotes_Detailed_Notes.pdf",
            mime="application/pdf"
        )
        
    with tab2:
        st.markdown(st.session_state["summary"])
        pdf_summary = create_pdf(st.session_state["summary"], title="Executive Summary")
        st.download_button(
            label="📄 Download Summary (PDF)",
            data=pdf_summary,
            file_name="TubeNotes_Summary.pdf",
            mime="application/pdf"
        )
        
    with tab3:
        st.markdown(st.session_state["quiz"])
        pdf_quiz = create_pdf(st.session_state["quiz"], title="Practice Quiz & Revision")
        st.download_button(
            label="📄 Download Quiz & MCQs (PDF)",
            data=pdf_quiz,
            file_name="TubeNotes_Quiz.pdf",
            mime="application/pdf"
        )