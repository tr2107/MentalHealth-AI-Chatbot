"""
ai_engine.py
------------
Conversational engine for MindCare AI.

Design:
- A lightweight, keyword-driven intent classifier with short-term context
  tracking (so follow-up messages like "mostly the amount of work" are
  understood relative to the previously discussed topic).
- Works fully offline / with zero configuration (no API key required).
- If OPENAI_API_KEY is set in the environment, chat requests are instead
  sent to OpenAI with a strict system prompt encoding MindCare AI's persona,
  scope, and boundaries. If that call fails for any reason (missing package,
  network error, invalid key, rate limit, etc.) the code falls back to the
  rule-based engine automatically so the app never crashes or hangs.

Safety note: this module is NEVER called for a message that safety.py has
flagged as high-risk. That check happens earlier, in app.py.
"""

import os
import random

SYSTEM_PROMPT = """You are MindCare AI, a warm, empathetic emotional-support chat companion \
for a student wellness app. You are NOT a therapist, psychologist, or doctor, and you must \
never claim to be one or imply you can diagnose anything.

Guidelines:
- Respond with warmth, validation, and curiosity. Ask at most one gentle follow-up question.
- Keep replies concise (2-5 sentences) and conversational, not clinical.
- Offer practical, low-risk coping suggestions when appropriate: breathing exercises, short \
breaks, journaling, organizing tasks, sleep/routine tips, grounding exercises, or talking to a \
trusted person.
- Never diagnose a condition or claim to replace professional care. If concerns sound serious, \
persistent, or are interfering with daily life, gently encourage professional support.
- Do not discuss self-harm methods under any circumstance.
- Maintain the thread of the conversation using the recent message history provided.
"""

# ---------------------------------------------------------------------------
# Intent keyword map. Order matters slightly for tie-breaking (first match
# with the most keyword hits wins).
# ---------------------------------------------------------------------------
INTENT_KEYWORDS = {
    "academic_pressure": ["exam", "exams", "study", "studies", "grades", "assignment",
                           "college", "university", "school", "gpa", "test", "class", "semester"],
    "work_pressure": ["my job", "my boss", "deadline", "at work", "office", "colleague",
                       "meeting", "career", "workload", "my manager", "my shift"],
    "overthinking": ["overthink", "overthinking", "can't stop thinking", "racing thoughts",
                      "spiraling", "spiralling", "ruminating"],
    "loneliness": ["lonely", "alone", "no friends", "isolated", "left out", "nobody understands"],
    "relationship": ["breakup", "boyfriend", "girlfriend", "partner", "relationship",
                      "friendship", "friend", "family fight", "argument with"],
    "low_mood": ["sad", "down", "depressed", "empty", "numb", "hopeless", "unmotivated",
                 "no energy", "tired of everything"],
    "stress": ["stress", "stressed", "overwhelmed", "anxious", "anxiety", "panic", "pressure",
               "burnt out", "burnout"],
}

FOLLOWUP_OPENERS = {
    "academic_pressure": [
        "That sounds like a lot to carry. Is it mainly the amount of work, the fear of the exams themselves, or something else weighing on you?",
        "Academic pressure can build up fast. What part of it feels heaviest right now \u2014 the workload, the expectations, or the uncertainty?",
    ],
    "work_pressure": [
        "Work stress has a way of following you home. Is it the workload itself, a specific situation, or the overall pace that's getting to you?",
        "That sounds draining. Is it more about the amount of work, or how you're being treated or supported there?",
    ],
    "overthinking": [
        "Overthinking can be exhausting \u2014 like your mind won't give you a break. What's the thought that keeps circling back the most?",
        "That racing-thoughts feeling is really tiring. Is there one specific worry driving most of it, or does it jump around a lot?",
    ],
    "loneliness": [
        "That sounds really hard to sit with. Has it felt this way for a while, or is it more recent?",
        "Feeling alone, even around other people sometimes, is genuinely painful. What does that loneliness feel like day to day for you?",
    ],
    "relationship": [
        "Relationship stuff can sit heavy on your chest. Do you want to tell me a bit more about what happened?",
        "That sounds tough. Is this something that just happened, or has it been building for a while?",
    ],
    "low_mood": [
        "I'm sorry you're feeling this way. Has it been a heavy day, or has this feeling been sticking around for a while?",
        "That sounds really draining to carry. When did you start noticing this feeling more?",
    ],
    "stress": [
        "That sounds like a lot to hold at once. What's feeling the most overwhelming right now?",
        "I hear you \u2014 stress like that can feel like it's everywhere at once. Is there one thing that's driving most of it?",
    ],
    "general": [
        "I'm here and I'm listening. Can you tell me a bit more about what's on your mind?",
        "Thanks for sharing that with me. What's been going on?",
    ],
}

COPING_SUGGESTIONS = {
    "academic_pressure": [
        "One thing that sometimes helps: breaking the work into small, timed chunks (like 25 minutes on, 5 minutes off) so it feels less like one giant mountain.",
        "It might help to write down everything on your plate and pick just the next single task \u2014 not the whole list, just the next one.",
    ],
    "work_pressure": [
        "A short 5-minute walk away from your desk can sometimes reset your head enough to tackle the next thing.",
        "Writing down tasks by priority \u2014 even roughly \u2014 can take some of the mental load off just carrying it all in your head.",
    ],
    "overthinking": [
        "A grounding trick that helps some people: name 5 things you can see, 4 you can hear, 3 you can touch, 2 you can smell, 1 you can taste. It pulls your mind back to the room.",
        "Sometimes writing the thought down on paper \u2014 just getting it out of your head \u2014 can loosen its grip a little.",
    ],
    "loneliness": [
        "Even a small bit of contact \u2014 texting one person, or sitting somewhere with people around \u2014 can sometimes soften that feeling, even briefly.",
        "Is there one person you trust who you could reach out to today, even just to say hi?",
    ],
    "relationship": [
        "It might help to write out what you'd actually want to say, even if you don't send it yet \u2014 sometimes that clarifies things.",
        "Taking a little space before responding, if you can, sometimes helps things feel less raw.",
    ],
    "low_mood": [
        "Small, gentle things can sometimes help \u2014 a short walk, some sunlight, or just changing rooms for a bit.",
        "Even a tiny routine \u2014 like getting up and making your bed \u2014 can sometimes give a small foothold on a heavy day.",
    ],
    "stress": [
        "A quick breathing exercise can help calm your body down in the moment \u2014 want to try one together?",
        "Sometimes writing down just the top 3 things that need attention (and letting the rest wait) can make it feel more manageable.",
    ],
    "general": [
        "Would it help to try a short breathing exercise together, or would you rather just keep talking it through?",
    ],
}

PROFESSIONAL_NUDGE = (
    " If this has been going on for a while, or it's starting to affect your sleep, "
    "work, or daily life, it could really help to talk to a counselor or mental-health "
    "professional \u2014 I can support the conversation, but I'm not a substitute for that."
)


def _detect_intent_with_score(message: str):
    text = message.lower()
    best_intent, best_score = None, 0
    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_intent, best_score = intent, score
    return best_intent, best_score


def _detect_intent(message: str):
    intent, _ = _detect_intent_with_score(message)
    return intent


def _is_vague_followup(message: str) -> bool:
    """Heuristic: short messages with only a weak/no new-topic signal are
    treated as elaborations of the previous topic rather than a new intent.
    A short message needs a fairly strong keyword match (score >= 2) to be
    considered a genuine topic switch rather than a continuation."""
    word_count = len(message.strip().split())
    if word_count > 8:
        return False
    _, score = _detect_intent_with_score(message)
    return score < 2


def _rule_based_response(message: str, context: dict) -> str:
    history_count = context.get("turn_count", 0)
    last_topic = context.get("last_topic")

    if last_topic and _is_vague_followup(message):
        intent = last_topic
        opener = random.choice(COPING_SUGGESTIONS.get(intent, COPING_SUGGESTIONS["general"]))
        reply = f"That makes sense \u2014 thank you for clarifying. {opener}"
    else:
        intent = _detect_intent(message) or "general"
        opener = random.choice(FOLLOWUP_OPENERS[intent])
        reply = opener

    context["last_topic"] = intent
    context["turn_count"] = history_count + 1

    # Every third-or-so turn on the same topic, add a gentle professional nudge
    if context["turn_count"] % 3 == 0 and intent != "general":
        reply += PROFESSIONAL_NUDGE

    return reply


def _try_openai_response(message: str, history: list, context: dict):
    """Attempts an OpenAI-backed response. Returns None on any failure so the
    caller can fall back to the rule-based engine."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for turn in history[-10:]:
            role = "assistant" if turn.get("role") == "assistant" else "user"
            messages.append({"role": role, "content": turn.get("content", "")})
        messages.append({"role": "user", "content": message})

        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=220,
            temperature=0.7,
        )
        text = completion.choices[0].message.content.strip()
        # Update lightweight context so a fallback later still has continuity
        context["last_topic"] = _detect_intent(message) or context.get("last_topic")
        context["turn_count"] = context.get("turn_count", 0) + 1
        return text
    except Exception:
        # Any failure (missing package, bad key, network, rate limit, etc.)
        # -> fall back to the rule-based engine. Never let this crash the app.
        return None


def generate_response(message: str, history: list, context: dict) -> str:
    """Main entry point used by app.py for non-crisis messages."""
    ai_text = _try_openai_response(message, history, context)
    if ai_text:
        return ai_text
    return _rule_based_response(message, context)
