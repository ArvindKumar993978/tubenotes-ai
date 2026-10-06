import os
import sqlite3
import datetime
import json

# Try importing firebase_admin
FIREBASE_AVAILABLE = False
db_firestore = None

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    import streamlit as st

    cred = None
    cred_path = os.getenv("FIREBASE_KEY_PATH", "firebase_key.json")

    # 1. Local file on disk
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
    # 2. Streamlit Cloud Secrets [firebase] section
    elif hasattr(st, "secrets") and "firebase" in st.secrets:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
    # 3. Streamlit Cloud Secrets string FIREBASE_KEY_JSON
    elif hasattr(st, "secrets") and "FIREBASE_KEY_JSON" in st.secrets:
        key_dict = json.loads(st.secrets["FIREBASE_KEY_JSON"])
        cred = credentials.Certificate(key_dict)
    # 4. Environment variable
    elif os.getenv("FIREBASE_KEY_JSON"):
        key_dict = json.loads(os.getenv("FIREBASE_KEY_JSON"))
        cred = credentials.Certificate(key_dict)

    if cred:
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db_firestore = firestore.client()
        FIREBASE_AVAILABLE = True
except Exception as e:
    FIREBASE_AVAILABLE = False

# Local SQLite Fallback Setup
DB_FILE = "notes_history.db"

def init_sqlite():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT UNIQUE,
            url TEXT,
            notes TEXT,
            summary TEXT,
            quiz TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_sqlite()

def is_firebase_active() -> bool:
    """Returns True if live Firebase Firestore is connected."""
    return FIREBASE_AVAILABLE and (db_firestore is not None)

def save_note(video_id: str, url: str, notes: str, summary: str, quiz: str):
    """Saves note to Firebase Firestore if available, otherwise local SQLite database."""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Save to Firebase Firestore if connected
    if is_firebase_active():
        try:
            doc_ref = db_firestore.collection("tubenotes").document(video_id)
            doc_ref.set({
                "video_id": video_id,
                "url": url,
                "notes": notes,
                "summary": summary,
                "quiz": quiz,
                "created_at": now_str
            })
            return True
        except Exception:
            pass
            
    # 2. Local database fallback
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO notes (video_id, url, notes, summary, quiz, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (video_id, url, notes, summary, quiz, now_str))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("DB Save Error:", e)
        return False

def get_recent_notes(limit: int = 10):
    """Fetches recent saved lecture notes from Firebase or SQLite."""
    # 1. Fetch from Firebase if connected
    if is_firebase_active():
        try:
            docs = (
                db_firestore.collection("tubenotes")
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )
            results = []
            for d in docs:
                data = d.to_dict()
                results.append(data)
            if results:
                return results
        except Exception:
            pass

    # 2. Fetch from Local SQLite
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT video_id, url, notes, summary, quiz, created_at
            FROM notes
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for r in rows:
            results.append({
                "video_id": r[0],
                "url": r[1],
                "notes": r[2],
                "summary": r[3],
                "quiz": r[4],
                "created_at": r[5]
            })
        return results
    except Exception as e:
        print("DB Fetch Error:", e)
        return []
