"""
stich_agent.py - Groq Llama AI Companion Engine ("Stitch")
Handles natural language reasoning, tool recommendations, command routing,
and synchronization with needs.json and appset.json.
"""

import os
import json
import datetime
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Backend utilities
from getting_data import get_live_desktop_summary, launch_application, get_installed_applications

# Groq Client Initialization
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

try:
    from groq import Groq
    groq_client = Groq(api_key=GROQ_API_KEY)
except Exception:
    groq_client = None

NEEDS_FILE = Path(__file__).parent / "needs.json"
APPSET_FILE = Path(__file__).parent / "appset.json"
PROMPT_FILE = Path(__file__).parent / "prompt.txt"


def load_system_prompt() -> str:
    """Reads persona and instructions from prompt.txt."""
    if PROMPT_FILE.exists():
        try:
            with open(PROMPT_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return (
        "You are Stitch, the intelligent desktop agent and workspace assistant for thelifeofpablo. "
        "Recommend apps and websites that solve user issues, maintain needs.json, and keep appset.json updated."
    )


def load_needs_data() -> Dict[str, Any]:
    """Reads needs.json."""
    if NEEDS_FILE.exists():
        try:
            with open(NEEDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_updated": str(datetime.datetime.now()), "problems": []}


def save_needs_data(data: Dict[str, Any]):
    """Saves to needs.json."""
    try:
        data["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(NEEDS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving needs.json: {e}")


def log_user_need(title: str, category: str = "General", description: str = "", recommended_apps: Optional[List[str]] = None):
    """Adds a new user problem/need entry into needs.json."""
    data = load_needs_data()
    problems = data.get("problems", [])
    need_id = f"need_{len(problems) + 1}"
    entry = {
        "id": need_id,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "category": category,
        "title": title,
        "description": description or title,
        "status": "logged",
        "recommended_apps": recommended_apps or []
    }
    problems.append(entry)
    data["problems"] = problems
    save_needs_data(data)


def load_appset_data() -> Dict[str, Any]:
    """Reads appset.json."""
    if APPSET_FILE.exists():
        try:
            with open(APPSET_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_updated": str(datetime.datetime.now()), "categories": [], "recommendations": []}


def save_appset_data(data: Dict[str, Any]):
    """Saves to appset.json."""
    try:
        data["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(APPSET_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving appset.json: {e}")


def add_appset_recommendation(name: str, category: str, target: str, description: str, tags: Optional[List[str]] = None):
    """Adds or updates a recommendation in appset.json."""
    data = load_appset_data()
    recs = data.get("recommendations", [])
    # Check if already exists
    for r in recs:
        if r.get("name", "").lower() == name.lower():
            r["category"] = category
            r["target"] = target
            r["description"] = description
            if tags:
                r["tags"] = tags
            save_appset_data(data)
            return

    recs.append({
        "name": name,
        "category": category,
        "target": target,
        "description": description,
        "type": "web" if target.startswith("http") else "app",
        "is_preset": False,
        "tags": tags or [name.lower()]
    })
    data["recommendations"] = recs
    save_appset_data(data)


def generate_text(user_input: str) -> str:
    """
    Main processing entry point.
    Handles command shortcuts, live desktop context injection, Groq LLM queries,
    and automatic needs/appset persistence.
    """
    clean_input = user_input.strip()
    if not clean_input:
        return "Hey there! I'm Stitch 🐻. What app or task are we working on today?"

    lower_input = clean_input.lower()

    # 1. Quick Command: Search Web
    if lower_input.startswith(("search ", "find ", "look up ", "google ")):
        query = clean_input.split(" ", 1)[1]
        webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
        return f"🔍 Opened web search for: **{query}**"

    # 2. Quick Command: Launch or Open App
    if lower_input.startswith(("open ", "launch ", "start ")):
        target_name = clean_input.split(" ", 1)[1].strip()
        all_apps = get_installed_applications()
        for app in all_apps:
            if target_name.lower() in app["name"].lower():
                launch_application(app["target"])
                return f"🚀 Launching **{app['name']}** for you!"

    # 3. Build Rich Context for Groq LLM
    live_desktop = get_live_desktop_summary()
    base_prompt = load_system_prompt()

    # Read current needs log summary
    needs_data = load_needs_data()
    problems = needs_data.get("problems", [])
    recent_needs_summary = ", ".join([p.get("title", "") for p in problems[-3:]]) if problems else "None"

    system_instruction = (
        f"{base_prompt}\n\n"
        f"--- LIVE RUNTIME ENVIRONMENT ---\n"
        f"[Currently Active Windows & Processes]:\n{live_desktop}\n\n"
        f"[Recent Needs Logged]: {recent_needs_summary}\n"
        f"Format your response nicely with clear bullet points for recommended apps and concise explanations."
    )

    if not groq_client:
        return "🐻 Stitch: Groq client is not initialized. Please ensure `GROQ_API_KEY` is configured."

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": clean_input}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.6,
            max_tokens=600,
        )
        reply = chat_completion.choices[0].message.content

        # Background auto-log if user mentions an issue/problem
        if any(w in lower_input for w in ("need", "want", "help with", "problem", "struggling", "anxious", "track", "organize", "automate", "issue")):
            log_user_need(title=clean_input[:60], category="Workspace Assistance", description=clean_input)

        return reply
    except Exception as e:
        return f"🐻 Stitch encountered an error communicating with Groq: {e}"