# MindCare AI 🌿 — Mental Wellness Chatbot

A privacy-first, session-only mental wellness chatbot that helps people talk through everyday
stress, academic and work pressure, overthinking, loneliness, and low mood — with a built-in
safety layer for crisis situations. Built as a student project with a clean Flask backend and a
calming, accessible chat interface.

> ⚠️ **MindCare AI provides general emotional support and is not a replacement for professional
> mental-health care.** It does not diagnose, treat, or provide emergency intervention.

---

## Project description (for GitHub)

**MindCare AI** is a full-stack web application that combines a rule-based/AI-assisted
conversational engine with a dedicated safety layer to provide empathetic, context-aware emotional
support. The app maintains short-term conversational context within a single session only —
no conversations, messages, or personal information are ever written to a database or disk. A
pattern-based crisis-detection system runs on every message *before* any conversational logic,
ensuring that expressions of suicidal ideation, self-harm, or intent to harm others are always
met with a calm, compassionate, resource-focused response rather than being answered by the
general chat engine. The project demonstrates practical skills in Flask API design, session
management, prompt engineering, front-end UX for sensitive contexts, and responsible AI safety
design.

---

## Architecture overview

```
Browser (chat UI)
   │  fetch('/api/chat', { message })
   ▼
Flask app.py
   │
   ├─► safety.py  ── ALWAYS checked first
   │     • assess_risk(message) → 'high' | 'none'
   │     • if high risk → crisis card + safety question (never reaches AI engine)
   │     • if answering a pending safety question → yes/no handling
   │
   └─► ai_engine.py  ── only reached for non-crisis messages
         • rule-based contextual engine (keyword intent detection +
           short-term topic memory), works with zero configuration
         • OPTIONAL: if OPENAI_API_KEY is set, calls OpenAI instead,
           with automatic fallback to the rule-based engine on any error
   │
   ▼
Response JSON { type, text, buttons? }
   │
   ▼
Session (signed cookie) stores only:
   • last N messages (for context)
   • current topic
   • whether we're mid-safety-check
   → cleared on "Clear chat" or when the browser session ends
   → NEVER written to a database or log file
```

**Why safety runs first:** the crisis check in `safety.py` is a hard gate in `app.py` — a
high-risk message is intercepted before it ever reaches the conversational engine (rule-based or
OpenAI). This means the safety response can never be "argued past" by prompt injection or
unusual phrasing that an LLM might otherwise respond to conversationally.

---

## Features

- 💬 Context-aware chat that remembers the current session's topic (e.g. understands that "mostly
  the amount of work" refers to previously-mentioned exam stress)
- 🧠 Rule-based conversational engine that works fully offline, with optional OpenAI enhancement
- 🛟 Crisis/self-harm detection layer with a dedicated emergency-support card, click-to-call
  buttons, and a follow-up safety question
- 🔒 Zero persistent storage — no database, no chat logs, no analytics
- ⚡ Quick Support buttons for common feelings
- 🫁 Guided breathing exercise
- ⌨️ Enter-to-send, typing indicator, clear-chat button
- 📱 Responsive, accessible, calming UI

---

## Tech stack

- **Backend:** Python, Flask
- **Frontend:** HTML5, CSS3, vanilla JavaScript (no framework/build step)
- **AI:** Lightweight rule-based contextual engine; optional OpenAI API integration
- **Session storage:** Flask signed session cookies (client-side, ephemeral, no database)
- **Config:** `python-dotenv` + environment variables (no hard-coded secrets)

---

## Project structure

```
mindcare-ai/
│
├── app.py                 # Flask routes, session handling, safety gate
├── safety.py               # Crisis/self-harm detection + crisis response content
├── ai_engine.py             # Rule-based + optional OpenAI conversational engine
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── templates/
│   └── index.html
│
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── script.js
```

---

## Getting started

### 1. Clone and set up a virtual environment

```bash
git clone https://github.com/<your-username>/mindcare-ai.git
cd mindcare-ai
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Generate a real secret key and put it in `.env`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

`OPENAI_API_KEY` is **optional**. Leave it blank to run entirely offline with the built-in
rule-based engine — this is the recommended setup for local demos and grading, since it requires
no external account or cost.

### 4. Run the app

```bash
python app.py
```

Visit **http://localhost:5000** in your browser.

---

## Privacy & data handling

- No database of any kind is used.
- Conversation history lives only in the browser's signed session cookie, capped at the last 20
  messages, and is never written to disk or logged.
- The "Clear chat" button immediately wipes the session server-side.
- No names, emails, phone numbers, or other identifying information are requested or stored.
- No analytics or third-party tracking scripts are included.
- If you enable the optional OpenAI integration, be aware that message content for that request
  is sent to OpenAI's API per their standard terms — review OpenAI's data usage policy before
  enabling this in any deployment involving real users.

---

## Safety design notes

- Detection in `safety.py` uses transparent, auditable regular expressions rather than an opaque
  model, so its behavior can be reviewed and tested directly (see the patterns in that file).
- It is intentionally tuned to prefer false positives over false negatives — it's safer to
  occasionally show crisis resources to someone who isn't in crisis than to miss someone who is.
- Ordinary statements like "I'm stressed about my exams" or "I feel sad today" are **not**
  flagged — only explicit or strongly contextual indicators of suicidal ideation, self-harm, or
  intent to harm others trigger the crisis flow.
- On a high-risk message, the app **never** calls the AI engine (rule-based or OpenAI) — it
  responds directly with a fixed, reviewed crisis message, click-to-call resources, and a direct
  safety question, then branches based on a yes/no answer.
- This is a basic safety net appropriate for a student/demo project, **not** a substitute for a
  clinically validated risk-assessment system. Any real-world deployment should be reviewed by
  mental-health professionals and should provide region-appropriate helpline numbers (this
  project ships with Indian helplines — Tele-MANAS 14416 and emergency number 112 — as an
  example; update these for your target region).

---

## Resume bullet points

- Designed and built **MindCare AI**, a full-stack Flask mental-wellness chatbot with a
  privacy-first architecture that stores zero conversation data persistently, using signed
  session cookies for ephemeral, context-aware conversation memory.
- Implemented a pattern-based crisis-detection safety layer that intercepts high-risk messages
  (suicidal ideation, self-harm intent) before they reach the conversational engine, surfacing
  region-specific crisis resources and a structured safety-check flow.
- Built a context-aware conversational engine with intent classification and short-term topic
  memory, plus an optional OpenAI integration with automatic graceful fallback on API failure.
- Designed a responsive, accessible chat UI (HTML/CSS/JS) featuring live typing indicators, quick
  -support shortcuts, and an interactive guided-breathing exercise.

## Suggested technologies to list

`Python` · `Flask` · `JavaScript` · `HTML5` · `CSS3` · `REST API design` · `Session management`
· `OpenAI API (optional)` · `python-dotenv` · `Responsible AI / safety design`

---

## Disclaimer

MindCare AI is a student/portfolio project. It is not a licensed medical, psychological, or
crisis-intervention service. If you or someone you know is in immediate danger, please contact
local emergency services immediately.

## License

MIT
