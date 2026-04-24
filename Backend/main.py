from fastapi import FastAPI, Form, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI
import csv
import io
import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from PyPDF2 import PdfReader


# LangChain
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# -----------------------------
# APP
# -----------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# OPENROUTER
# -----------------------------
OPENROUTER_API_KEY = "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"

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# -----------------------------
# DATABASE
# -----------------------------
conn = sqlite3.connect("chatbot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    phone TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    sender TEXT,
    message TEXT,
    needs_human INTEGER DEFAULT 0
)
""")

conn.commit()

# -----------------------------
# GLOBAL VECTOR DB
# -----------------------------
db = None

# -----------------------------
# AUTO WEBSITE CRAWLER
# -----------------------------
def crawl_website(base_url):
    visited = set()
    to_visit = [base_url]
    documents = []

    while to_visit and len(visited) < 10:
        url = to_visit.pop(0)

        if url in visited:
            continue

        try:
            res = requests.get(url, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")

            for tag in soup(["script", "style", "noscript"]):
                tag.extract()

            text = soup.get_text(" ")
            text = " ".join(text.split())

            print(f"✅ Crawled: {url}")

            documents.append(Document(page_content=text))
            visited.add(url)

            # collect internal links
            for link in soup.find_all("a", href=True):
                full_url = urljoin(base_url, link['href'])

                if base_url in full_url and full_url not in visited:
                    to_visit.append(full_url)

        except Exception as e:
            print("Error:", e)

    return documents

# -----------------------------
# LOAD RAG
# -----------------------------
def load_website():
    global db

    if db is not None:
        return

    print("Crawling website...")

    docs = crawl_website("https://softwalletinnovativetechnologies.cloud/")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )

    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    db = FAISS.from_documents(chunks, embeddings)

    print("✅ RAG READY")

# ========================================
# STARTUP EVENT - Load RAG on server start
# ========================================
@app.on_event("startup")
async def startup_event():
    """Load RAG database on server startup"""
    global db
    print("⏳ Loading RAG system on startup...")
    load_website()
    print("✅ RAG system loaded successfully!")

# -----------------------------
# LEAD API
# -----------------------------
@app.post("/lead")
def save_lead(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form("")
):
    cursor.execute(
        "INSERT INTO leads (name, email, phone) VALUES (?, ?, ?)",
        (name, email, phone)
    )
    conn.commit()
    return {"status": "saved"}

# -----------------------------
# CHAT API (SMART SALES BOT)
# -----------------------------
from fastapi import Form, Query

@app.post("/chat")
def chat(
    user_input: str = Form(None),
    user: str = Form(None),
    user_input_q: str = Query(None, alias="user_input"),
    user_q: str = Query(None, alias="user")
    
):
    global db

    # ✅ FIX
    user_input = user_input or user_input_q
    user = user or user_q
    
    user = user.strip().lower()


    if not user_input or not user:
        return {"error": "Missing parameters"}



    try:
        # RAG is now pre-loaded at startup, no need to load it here
        
        text = user_input.lower()
        keywords = ["human", "agent", "call", "support"]
        needs_human = 1 if any(k in text for k in keywords) else 0

        cursor.execute(
    		"INSERT INTO messages (user, sender, message, needs_human) VALUES (?, ?, ?, ?)",
    		(user, user, user_input, needs_human)
	    )

        text = user_input.lower()

        # 🔥 GREETING
        # 🔥 GREETING
        if text in ["hi", "hello", "hey"]:
            bot_reply = "Hello!, I am veda, How can I help you today?"
            cursor.execute(
        		"INSERT INTO messages (user, sender, message) VALUES (?, ?, ?)",
        		(user, "bot", bot_reply)
    		)
            conn.commit()
            return {"response": bot_reply}

# 🔥 USER INTEREST
        elif "project" in text:
            bot_reply = "That’s great!\n\nAre you looking for:\n- Website\n- Web App\n- Mobile App\n- Software Solution?"
            cursor.execute(
        	"INSERT INTO messages (user, sender, message) VALUES (?, ?, ?)",
        	(user, "bot", bot_reply)
    	)
            conn.commit()
            return {"response": bot_reply}

# 🔥 WEB APP FLOW
        elif "web app" in text:
            bot_reply = "Awesome!\n\nWe specialize in web app development.\n\nOur team will contact you shortly.\n\nMeanwhile, you can share:\n- Features you need\n- Budget\n- Timeline"

            cursor.execute(
        	"INSERT INTO messages (user, sender, message) VALUES (?, ?, ?)",
        	(user, "bot", bot_reply)
    	)

            conn.commit()

            return {"response": bot_reply}

# 🔥 MOBILE APP FLOW
        elif "mobile app" in text:

            bot_reply = "Great choice!\n\nWe build high-quality mobile apps.\n\nOur team will contact you soon.\n\nTell me:\n- Android / iOS?\n- Features?\n- Budget?"
            cursor.execute(
        		"INSERT INTO messages (user, sender, message) VALUES (?, ?, ?)",
        		(user, "bot", bot_reply)
    		)

            conn.commit()

            return {"response": bot_reply}

# 🔥 WEBSITE FLOW
        elif "website" in text:

            bot_reply = "Perfect! 🌐\n\nWe can build a modern website for you.\n\nCan you share:\n- Business type?\n- Pages needed?\n- Budget?"

            cursor.execute(
        		"INSERT INTO messages (user, sender, message) VALUES (?, ?, ?)",
        		(user, "bot", bot_reply)
    		)

            conn.commit()

            return {"response": bot_reply}

# 🔥 FALLBACK → AI

        # 🔍 RAG SEARCH
        docs = db.similarity_search(user_input, k=5)
        context = "\n\n".join([d.page_content for d in docs])

        print("\n------ CONTEXT ------")
        print(context[:500])
        print("---------------------\n")

        # 🔥 FALLBACK CONTEXT
        if len(context.strip()) < 50:
            context = """
SoftWallet is a technology company offering:
- Website Development
- Software Solutions
- IT Services
"""

        # 🔥 SALES PROMPT
        prompt = f"""
You are a professional AI sales assistant for SoftWallet.

GOALS:
- Help the user
- Suggest services
- Convert them into a potential client
- Ask follow-up questions

STYLE:
- Friendly
- Professional
- Confident

Context:
{context}

User:
{user_input}
"""

        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        bot_reply = response.choices[0].message.content

        cursor.execute(
    		"INSERT INTO messages (user, sender, message) VALUES (?, ?, ?)",
    		(user, "bot", bot_reply)
	)

        conn.commit()

        return {"response": bot_reply}

    except Exception as e:
        print("ERROR:", e)
        return {"error": str(e)}

# -----------------------------
# ADMIN DATA
# -----------------------------
@app.get("/admin-data")
def admin_data():
    cursor.execute("""
        SELECT user,
               COUNT(*) as msg_count,
               MAX(needs_human)
        FROM messages
        WHERE sender != 'bot'
        GROUP BY user
    """)

    users = cursor.fetchall()

    return {
        "users": [
            {
                "name": u[0],
                "messages": u[1],
                "needs_human": u[2]
            }
            for u in users
        ]
    }

@app.get("/chat-history")
def chat_history(user: str):
    print("API HIT FOR USER:", user)   # 👈 debug

    cursor.execute(
    	"SELECT sender, message FROM messages WHERE LOWER(user)=?",
    	(user.lower(),)
    )

    chats = cursor.fetchall()

    print("DATA FOUND:", chats)  # 👈 debug

    return {
        "chats": [
            {"sender": c[0], "message": c[1]}
            for c in chats
        ]
    }

@app.get("/leads")
def get_leads():
    cursor.execute("SELECT name, email, phone FROM leads")
    data = cursor.fetchall()

    return {
        "leads": [
            {"name": d[0], "email": d[1], "phone": d[2]}
            for d in data
        ]
    }

@app.get("/download-leads")
def download_leads():
    cursor.execute("SELECT name, email, phone FROM leads")
    rows = cursor.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Email", "Phone"])
    writer.writerows(rows)
    output.seek(0)

    response = StreamingResponse(io.StringIO(output.getvalue()), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=leads.csv"
    return response

@app.get("/download-chat")
def download_chat(user: str):
    cursor.execute(
        "SELECT sender, message FROM messages WHERE LOWER(user)=?",
        (user.lower(),)
    )
    chats = cursor.fetchall()

    if not chats:
        return {"detail": "No chat history found"}

    lines = []
    for sender, message in chats:
        prefix = "Bot" if sender == "bot" else "User"
        lines.append(f"{prefix}: {message}")

    text = "\n".join(lines)
    buffer = io.StringIO(text)
    response = StreamingResponse(buffer, media_type="text/plain")
    response.headers["Content-Disposition"] = f"attachment; filename={user}_chat.txt"
    return response




@app.get("/scrape")
def scrape(url: str):
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")

        service = Service("chromedriver.exe")
        driver = webdriver.Chrome(service=service, options=options)

        driver.get(url)

        html = driver.page_source
        driver.quit()

        soup = BeautifulSoup(html, "html.parser")

        text = soup.get_text(" ")
        text = " ".join(text.split())

        if len(text) < 50:
            return {"content": "No useful content"}

        return {"content": text[:2000]}

    except Exception as e:
        return {"content": str(e)}