"""
app.py
------
MindCare AI - Flask backend.

Privacy / storage policy (please read before deploying):
- No database. No file-based conversation logs.
- Conversation state lives ONLY in the signed Flask session cookie held by
  the user's browser, and only for the current browser session
  (`SESSION_PERMANENT = False`, no `PERMANENT_SESSION_LIFETIME` set, and no
  "remember me" cookie is issued).
- The session cookie is signed (not encrypted) - it contains no personal
  identifiers, names, emails, or phone numbers, only short conversational
  text needed for context continuity.
- "Clear chat" wipes the session server-side reference immediately.
- No analytics, tracking, or logging of message content is performed.
"""

import os
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv

import safety
import ai_engine

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-insecure-key-change-me")

# Ensure the session cookie is a true "session" cookie (cleared when the
# browser closes) rather than a persistent one.
app.config["SESSION_PERMANENT"] = False

MAX_HISTORY_TURNS = 20  # messages (user + assistant combined), not pairs


def _reset_session_state():
    session["history"] = []
    session["context"] = {}
    session["awaiting_danger_check"] = False
    session.modified = True


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400
    if len(user_message) > 2000:
        return jsonify({"error": "Message is too long."}), 400

    session.setdefault("history", [])
    session.setdefault("context", {})
    session.setdefault("awaiting_danger_check", False)

    try:
        # --- Branch 1: we previously asked the safety question and are
        # waiting on a yes/no answer. This takes priority over everything.
        if session.get("awaiting_danger_check"):
            answer = safety.parse_yes_no(user_message)
            if answer is True:
                reply_text = safety.danger_followup_yes_text()
                session["awaiting_danger_check"] = False
                response = {
                    "type": "danger_yes",
                    "text": reply_text,
                    "buttons": safety.CRISIS_BUTTONS,
                }
            elif answer is False:
                reply_text = safety.danger_followup_no_text()
                session["awaiting_danger_check"] = False
                response = {"type": "danger_no", "text": reply_text}
            else:
                reply_text = safety.danger_followup_unclear_text()
                # stay in awaiting state until we get a clear answer
                response = {"type": "danger_unclear", "text": reply_text}

        # --- Branch 2: fresh high-risk message detected right now.
        elif safety.assess_risk(user_message) == "high":
            reply_text = safety.crisis_card_text() + "\n\n" + safety.SAFETY_QUESTION
            session["awaiting_danger_check"] = True
            response = {
                "type": "crisis",
                "text": reply_text,
                "buttons": safety.CRISIS_BUTTONS,
            }

        # --- Branch 3: ordinary supportive conversation.
        else:
            reply_text = ai_engine.generate_response(
                user_message, session["history"], session["context"]
            )
            response = {"type": "normal", "text": reply_text}

    except Exception:
        # Graceful degradation: never expose a stack trace or crash the chat.
        response = {
            "type": "error",
            "text": (
                "I'm having trouble responding right now. Please try again in a "
                "moment. If you're in crisis, please contact Tele-MANAS at 14416 "
                "or emergency services at 112."
            ),
        }

    # Update short-term, in-session-only history (never persisted to disk).
    session["history"].append({"role": "user", "content": user_message})
    session["history"].append({"role": "assistant", "content": response["text"]})
    session["history"] = session["history"][-MAX_HISTORY_TURNS:]
    session.modified = True

    return jsonify(response)


@app.route("/api/clear", methods=["POST"])
def clear_chat():
    _reset_session_state()
    return jsonify({"status": "cleared"})


@app.errorhandler(404)
def not_found(_e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(_e):
    return jsonify({"error": "Something went wrong. Please try again."}), 500


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    app.run(debug=debug_mode, port=int(os.environ.get("PORT", 5000)))
