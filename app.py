from fastapi import FastAPI, Request, Form, Response, Depends, BackgroundTasks, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os
import sqlite3
import base64
from datetime import datetime
from dotenv import load_dotenv
from utils.reddit_scraper import fetch_subreddit_content
from utils.ai_summarizer import summarize_sentiment
from utils.downloader import download_video

load_dotenv()

# App initialization
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv(
    "SESSION_SECRET", "supersecret"))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Ensure DB exists


def init_db():
    conn = sqlite3.connect("database/logs.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool TEXT,
            ip TEXT,
            timestamp TEXT,
            user_agent TEXT
        )
    ''')
    conn.commit()
    conn.close()


init_db()

# Activity Logger


def log_activity(request: Request, tool_name: str):
    ip = request.client.host
    ua = request.headers.get("user-agent", "unknown")
    timestamp = datetime.utcnow().isoformat()
    conn = sqlite3.connect("database/logs.db")
    c = conn.cursor()
    c.execute("INSERT INTO logs (tool, ip, timestamp, user_agent) VALUES (?, ?, ?, ?)",
              (tool_name, ip, timestamp, ua))
    conn.commit()
    conn.close()

# Admin session check


def get_admin_user(request: Request):
    return request.session.get("admin") == "true"


# Presets for dropdown
DROPDOWN_PRESETS = {
    "crypto": ["bitcoin", "ethereum", "cryptocurrency"],
    "gaming": ["gaming", "pcgaming", "xbox"],
    "tech": ["technology", "gadgets", "programming"],
    "politics": ["politics", "conservative", "liberal"],
    "memes": ["memes", "dankmemes", "wholesomememes"]
}

# ------------------- Home -------------------


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ------------------- Downloader -------------------


@app.get("/downloader", response_class=HTMLResponse)
def downloader_form(request: Request):
    return templates.TemplateResponse("tools/downloader.html", {"request": request, "result": None})


@app.post("/downloader")
def downloader_submit(
    request: Request,
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    format: str = Form("mp4")
):
    log_activity(request, "downloader")
    try:
        return download_video(url, format, background_tasks)
    except Exception as e:
        return templates.TemplateResponse("tools/downloader.html", {
            "request": request,
            "result": f"Error: {str(e)}"
        })

# ------------------- Sentiment -------------------


@app.get("/sentiment", response_class=HTMLResponse)
def sentiment_form(request: Request):
    return templates.TemplateResponse("tools/sentiment.html", {
        "request": request,
        "results": None,
        "subreddits": "",
        "preset": "",
        "dropdown_presets": DROPDOWN_PRESETS
    })


@app.post("/sentiment", response_class=HTMLResponse)
def sentiment_submit(request: Request, subreddits: str = Form(""), preset: str = Form("")):
    log_activity(request, "sentiment")

    if preset and not subreddits.strip():
        subreddits = ",".join(DROPDOWN_PRESETS.get(preset, []))

    subreddit_list = [
        sub.strip().lower().replace("r/", "").replace(" ", "")
        for sub in subreddits.split(",") if sub.strip()
    ]

    results = {}

    if not subreddit_list:
        return templates.TemplateResponse("tools/sentiment.html", {
            "request": request,
            "results": {"Error": "Please enter a subreddit or choose a preset."},
            "subreddits": subreddits,
            "preset": preset,
            "dropdown_presets": DROPDOWN_PRESETS
        })

    for sub in subreddit_list:
        try:
            content = fetch_subreddit_content(sub)
            summary = summarize_sentiment(content)
            results[f"r/{sub}"] = summary
        except Exception as e:
            results[f"r/{sub}"] = f"Error: {str(e)}"

    return templates.TemplateResponse("tools/sentiment.html", {
        "request": request,
        "results": results,
        "subreddits": subreddits,
        "preset": preset,
        "dropdown_presets": DROPDOWN_PRESETS
    })

# ------------------- Admin -------------------


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login")
def login(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    if username == os.getenv("ADMIN_USER", "admin") and password == os.getenv("ADMIN_PASS", "password"):
        request.session["admin"] = "true"
        return RedirectResponse("/admin", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    if not get_admin_user(request):
        return RedirectResponse("/login")

    conn = sqlite3.connect("database/logs.db")
    c = conn.cursor()
    c.execute(
        "SELECT tool, ip, timestamp, user_agent FROM logs ORDER BY id DESC LIMIT 100")
    logs = c.fetchall()
    conn.close()

    return templates.TemplateResponse("admin.html", {"request": request, "logs": logs})


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)
