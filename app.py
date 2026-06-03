import os
import random
import time
import requests
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import db

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "ollama"

#ollama configurations
def call_ollama(prompt):
    payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 500
            }
        }
    try: 
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        print(f"Ollama Error: {e}")
        raise e


# ─── CURRICULUM CONFIG ─────

PILLARS = {
    "personal finance": {
        "title": "Personal Finance",
        "subtitle": "Your money, your life",
        "subtopics": [
            "budgeting methods like the 50/30/20 rule, needs vs wants, paying yourself first",
            "checking vs savings accounts, high-yield savings accounts, how banks make money",
            "credit scores, APR, revolving vs installment debt, good debt vs bad debt",
            "health insurance, life insurance, auto insurance — how they work and what to look for",
            "building an emergency fund, why 3-6 months expenses is the target",
            "compound interest and why starting early matters so much",
        ]
    },
    "investing & markets": {
        "title": "Investing & Markets",
        "subtitle": "Making your money work",
        "subtopics": [
            "stocks and equities — what you actually own when you buy a share",
            "bonds and fixed income — how lending to governments and companies works",
            "index funds and ETFs — why most investors should start here",
            "mutual funds and target date funds — how they differ from ETFs",
            "how IPOs work, what market cap means, P/E ratios and basic valuation",
            "dividends — what they are and how dividend investing works",
            "401k, IRA, Roth vs Traditional, HSA — the alphabet soup of retirement accounts",
            "dollar cost averaging, rebalancing, and long-term investing strategy",
        ]
    },
    "macro": {
        "title": "Macroeconomics",
        "subtitle": "The weather of money",
        "subtopics": [
            "the Federal Reserve — what it is, what it does, and why it matters",
            "interest rate hikes and cuts — how they ripple through the economy",
            "inflation and CPI — why prices rise and how it's measured",
            "quantitative easing and money supply — what money printing actually means",
            "GDP growth and what it tells us about economic health",
            "unemployment rates and why the Fed watches them so closely",
            "recessions and depressions — how they start and how they end",
            "bull markets and bear markets — cycles, sentiment, and what drives them",
            "fiscal policy vs monetary policy — government spending vs Fed action",
        ]
    },
    "alternative assets": {
        "title": "Alternative Assets",
        "subtitle": "The frontier",
        "subtopics": [
            "Bitcoin and Ethereum — what they actually are beyond the hype",
            "DeFi (decentralized finance) — lending, borrowing, and yield without banks",
            "stablecoins — how they work and why they matter in crypto",
            "NFTs and digital ownership — the idea behind them stripped of the noise",
            "venture capital — how startups get funded from seed to IPO",
            "options contracts — calls, puts, and what people mean by options trading",
            "futures contracts — how commodities and hedging actually work",
            "short selling — borrowing shares to bet against a company",
            "real estate investing — REITs, rental properties, and leverage",
            "commodities — gold, oil, and why people hold them",
        ]
    },
    "wealth strategy": {
        "title": "Wealth Strategy",
        "subtitle": "Not what you make — what you keep",
        "subtopics": [
            "short-term vs long-term capital gains — why holding longer saves you money",
            "tax loss harvesting — selling losers to offset winners",
            "tax-advantaged accounts and how to use them to minimize your bill",
            "deductions — what ordinary people can actually write off",
            "wills and why everyone needs one regardless of wealth",
            "trusts — what they are and when they make sense",
            "estate planning — how wealth passes between generations",
            "salary negotiation — the one skill that compounds for your entire career",
            "side income and how the IRS treats it differently",
            "net worth tracking — assets minus liabilities and why it's the real number",
        ]
    }
}

CATEGORIES = list(PILLARS.keys())

# ─── HELPERS ────

def generate_lesson(category):
    """Call ollama to generate a fresh lesson, avoiding recently seen topics."""

    pillar = PILLARS[category]
    subtopic = random.choice(pillar["subtopics"])
    recent_titles = db.get_recent_titles(category, limit=20)

    avoid_section = ""

    if recent_titles:
        avoid_section = "ALREADY TAUGHT (do not repeat these or closely related topics):\n"
        avoid_section += "\n".join(f"- {t}" for t in recent_titles)
        

    prompt = f"""You are MoneyBuddy - a friendly, sharp finance educator.

    Teach one specific concept from this area: {subtopic}

    {avoid_section}

    Rules:
    - Pick ONE focused idea, term, or insight from that area
    - Must be genuinely different from anything in the already-taught list above
    - Write for someone smart but new to finance
    - Use one concrete real-world example
    - Sound like a knowledgeable friend, not a textbook
    - No jargon without a quick explanation

    Format your response EXACTLY like this with no extra text:

    TITLE: [punchy title, max 8 words]
    CONTENT: [3-5 sentences. clear, engaging, one real example.]"""

    raw_text = call_ollama(prompt)

    #creating basic 
    title = "Finance Insight"
    content = raw_text

    if "TITLE:" in raw_text:
        parts = raw_text.split("TITLE:")[-1].split("CONTENT:")
        if len(parts) == 2:
            title = parts[0].strip()
            content = parts[1].strip()
    title = title.replace("**", "")

    return {"title": title, "content": content}


def parse_quiz(raw):
    """Parse Gemini's structured quiz response into a clean dict."""
    quiz = {"a": "", "b": "", "c": "", "d": "", "question": "", "answer": "a"}
    for line in raw.strip().split("\n"):
        if line.startswith("QUESTION:"):
            quiz["question"] = line.split(":", 1)[1].strip()
        elif line.startswith("A:"):
            quiz["a"] = line.replace("A:", "").strip()
        elif line.startswith("B:"):
            quiz["b"] = line.replace("B:", "").strip()
        elif line.startswith("C:"):
            quiz["c"] = line.replace("C:", "").strip()
        elif line.startswith("D:"):
            quiz["d"] = line.replace("D:", "").strip()
        elif line.startswith("ANSWER:"):
            quiz["answer"] = line.split(":", 1)[1].strip().lower()
    return quiz


# ─── ROUTES ───────

@app.route("/api/pillars", methods=["GET"])
def get_pillars():
    """Return pillar metadata for the frontend nav.
    Subtopics stay server-side — they're prompt config, not UI data."""
    return jsonify({
        key: {"label": val["title"], "subtitle": val["subtitle"]}
        for key, val in PILLARS.items()
    })


@app.route("/api/lesson", methods=["GET"])
def get_lesson():
    """Generate and save a new lesson.
    Query param: ?category=macro  (defaults to personal finance)"""

    category = request.args.get("category", "personal finance")

    if category not in CATEGORIES:
        return jsonify({"error": f"Unknown category '{category}'."}), 400

    try:
        lesson = generate_lesson(category)
        lesson_id = db.save_lesson(category, lesson["title"], lesson["content"])
        streak = db.update_streak()

        return jsonify({
            "id": lesson_id,
            "category": category,
            "pillar_label": PILLARS[category]["title"],
            "pillar_subtitle": PILLARS[category]["subtitle"],
            "title": lesson["title"],
            "content": lesson["content"],
            "streak": streak
        })
    except Exception as e:
        return jsonify({"error": "API error", "details": str(e)}), 500


@app.route("/api/explain", methods=["POST"])
def explain_more():
    """Go deeper on a lesson the user is currently viewing.
    Body: { "title": "...", "content": "..." }"""
    
    try:
        data = request.get_json()
        title = data.get("title", "")
        content = data.get("content", "")

        prompt = f"""You are MoneyBuddy. The user just read this lesson:

        Topic: {title}
        Content: {content}

        Go deeper. Give more context, a vivid real-world example, and explain why this matters to an everyday person.
        Keep it conversational, under 150 words, no bullet points."""

        explanation = call_ollama(prompt)

        return jsonify({"explanation": explanation})
    except Exception as e:
        return jsonify({"error": "API error", "details": str(e)}), 500


@app.route("/api/ask", methods=["POST"])
def ask():
    """Generic prompt -> AI response endpoint used by the simple frontend.
    Body: { "prompt": "..." }
    If the Ollama call fails, return a lightweight mock response so the UI still works.
    """
    try:
        data = request.get_json() or {}
        prompt = data.get("prompt", "").strip()

        if not prompt:
            return jsonify({"error": "prompt is required"}), 400

        try:
            ai_resp = call_ollama(prompt)
        except Exception as e:
            # Fallback mock response when Ollama isn't available
            ai_resp = f"(mock) I received your prompt: {prompt[:200]}"

        return jsonify({"response": ai_resp})
    except Exception as e:
        return jsonify({"error": "API error", "details": str(e)}), 500


@app.route("/", methods=["GET"])
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/quiz", methods=["POST"])
def quiz():
    """Generate a multiple choice quiz question from a lesson.
    Body: { "title": "...", "content": "..." }"""
    
    try:
        data = request.get_json()
        title = data.get("title", "")
        content = data.get("content", "")

        prompt = f"""Based on this finance lesson:

        Topic: {title}
        Content: {content}

        Write one multiple choice question that tests real understanding, not just memorization.
        Format EXACTLY like this with no extra text:

        QUESTION: [the question]
        A: [option]
        B: [option]
        C: [option]
        D: [option]
        ANSWER: [just the letter, e.g. B]"""

        raw_quiz = call_ollama(prompt)

        return jsonify(parse_quiz(raw_quiz))
    except Exception as e:
        return jsonify({"error": "API error", "details": str(e)}), 500


@app.route("/api/bookmark", methods=["POST"])
def bookmark():
    """Toggle bookmark on a lesson.
    Body: { "lesson_id": 42 }"""

    data = request.get_json()
    lesson_id = data.get("lesson_id")

    if not lesson_id:
        return jsonify({"error": "lesson_id is required"}), 400

    is_bookmarked = db.toggle_bookmark(lesson_id)
    return jsonify({"bookmarked": is_bookmarked, "lesson_id": lesson_id})


@app.route("/api/bookmarks", methods=["GET"])
def get_bookmarks():
    """Return all bookmarked lessons."""
    return jsonify(db.get_bookmarks())


@app.route("/api/history", methods=["GET"])
def get_history():
    """Return recent lessons, optionally filtered by category.
    Query param: ?category=macro"""
    category = request.args.get("category")
    return jsonify(db.get_lessons(category=category))


# ─── START ─────

if __name__ == "__main__":
    db.init_db()
    app.run(debug=True, port=8080, host="127.0.0.1")