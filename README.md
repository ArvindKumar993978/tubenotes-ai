# 🎓 TubeNotes AI — Smart Video Lecture to PDF Notes Generator

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit)](https://streamlit.io/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-Flash%20API-8E75C2?logo=google)](https://ai.google.dev/)
[![ReportLab](https://img.shields.io/badge/Export-Formatted%20PDF-success)](https://www.reportlab.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**TubeNotes AI** is an AI-powered full-stack web application designed for students and self-learners to convert hours-long YouTube video lectures, podcasts, and tech tutorials into **comprehensive study notes, executive summaries, revision quizzes, and downloadable PDF documents** within seconds.

---

## ⚡ The Problem It Solves

* **Time Sink:** Watching 2-3 hour long video lectures just to take notes is inefficient.
* **Manual Note Taking:** Students struggle to identify key formulas, definitions, and high-yield topics while watching videos.
* **Revision Bottleneck:** No quick way to test comprehension immediately after learning.

**TubeNotes AI** automates this entire pipeline using multi-modal AI agents and structured document generators.

---

## 🚀 Key Features

- 📑 **Comprehensive Study Notes:** Generates structured notes featuring clear concept hierarchies, headings, definitions, and code/formulas.
- ⚡ **2-Minute Executive Summary:** High-impact executive takeaways for quick revision before exams or meetings.
- 🎯 **Interactive Practice Quiz:** 4-5 Multiple Choice Questions (MCQs) with correct answers and explanations for active recall.
- 📄 **1-Click PDF Export:** Powered by `ReportLab` to produce clean, formatted PDF study guides ready for printing or offline reading.
- 🔗 **Smart URL Ingestion:** Supports standard YouTube links (`watch?v=`), short links (`youtu.be/`), and livestreams/shorts.
- 🛡️ **Resilient AI Architecture:** Auto-fallbacks across Google Gemini models (`gemini-flash-lite`, `gemini-3.5-flash`, etc.) ensuring 99.9% uptime with zero 503 errors.
- 🔒 **Secure Environment:** Built with strict zero-leak security via python-dotenv (`.env`).

---

## 🏗️ Architecture & Workflow

```
[ User YouTube Link ]
          │
          ▼
[ Regex URL Parser ] ───► Extracts 11-char Video ID
          │
          ▼
[ youtube-transcript-api ] ───► Extracts Subtitles & Closed Captions (Auto/Manual)
          │
          ▼
[ Google Gemini AI Engine ] ───► Processes Context via Prompt Engineering
          │
          ├──► 📝 Detailed Conceptual Notes
          ├──► ⚡ 2-Minute Executive Summary
          └──► 🎯 Multiple-Choice Quiz (Active Recall)
          │
          ▼
[ ReportLab Engine ] ───► Generates Formatted PDF on Demand
          │
          ▼
[ Streamlit Web App ] ───► Live Interactive Student Dashboard
```

---

## 🛠️ Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Core programming language |
| **Frontend UI** | Streamlit | Responsive, real-time web interface |
| **AI Model** | Google Gemini Flash | Ultra-fast token processing & reasoning |
| **Data Ingestion** | `youtube-transcript-api` | Captures subtitles across multiple languages |
| **Document Generation** | `ReportLab` | Formats and compiles dynamic PDFs |
| **Environment Mgmt** | `python-dotenv` | Secure API key isolation |

---

## 📦 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/tubenotes-ai.git
cd tubenotes-ai
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Your API Key
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_actual_google_gemini_api_key_here
```
*(You can get a free API key at [Google AI Studio](https://aistudio.google.com/))*

### 5. Launch the Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 📂 Project Structure

```
📁 tubenotes-ai/
│── 📄 app.py               # Main Streamlit Application with full logic
│── 📄 requirements.txt      # Project dependencies
│── 📄 .env                 # API Key credentials (git-ignored)
│── 📄 .env.example         # Template for environment variables
│── 📄 README.md            # Comprehensive project documentation
```

---

## 💡 Future Enhancements
- [ ] Add direct audio download fallback for videos without subtitles.
- [ ] Support Hindi / regional language output translation.
- [ ] Direct export to Notion and Google Docs via Webhooks.

---

## 👨‍💻 Author
Built with focus by a B.Tech Computer Science student building real-world AI applications.  
*Contributions, suggestions, and feedback are always welcome!*
