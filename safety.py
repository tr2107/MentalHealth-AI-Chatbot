"""
safety.py
---------
Crisis / self-harm / harm-to-others detection layer for MindCare AI.

This module is intentionally simple and pattern-based (not ML-based) so that
its behavior is transparent, auditable, and easy for a reviewer to verify.
It is checked BEFORE any conversational/AI logic runs, so a high-risk message
can never be "talked past" by the chatbot's normal conversation flow.

IMPORTANT: This is a basic safety net for a student project, not a clinical
risk-assessment tool. It should never be presented as a substitute for
professional crisis triage.
"""

import re

# ---------------------------------------------------------------------------
# High-risk patterns: explicit and contextual expressions of suicidal
# ideation, self-harm intent, or intent to harm someone else.
# Patterns are matched case-insensitively against the raw user message.
# ---------------------------------------------------------------------------
HIGH_RISK_PATTERNS = [
    # Explicit suicidal ideation
    r"\bkill(ing)?\s+myself\b",
    r"\bwant(ing)?\s+to\s+die\b",
    r"\bwant(ing)?\s+to\s+end\s+(my|this)\s+life\b",
    r"\bend(ing)?\s+(my|this)\s+life\b",
    r"\bdon'?t\s+want\s+to\s+live\b",
    r"\bnot\s+worth\s+living\b",
    r"\bno\s+point\s+(in\s+)?living\b",
    r"\bno\s+reason\s+to\s+(continue|live|go\s+on)\b",
    r"\bsuicid\w*\b",
    r"\bplan\s+to\s+end\s+(my|this)\s+life\b",
    r"\bi\s+want\s+to\s+die\b",

    # Self-harm intent
    r"\bhurt(ing)?\s+myself\b",
    r"\bharm(ing)?\s+myself\b",
    r"\bself[-\s]?harm\w*\b",
    r"\bcut(ting)?\s+myself\b",

    # Contextual / indirect expressions
    r"\bcan'?t\s+do\s+this\s+anymore\b",
    r"\bwish\s+i\s+(wasn'?t|weren'?t)\s+here\b",
    r"\bwish\s+i\s+(was|were)\s+never\s+born\b",
    r"\beveryone\s+(would\s+be\s+)?better\s+off\s+without\s+me\b",
    r"\bthey'?d\s+be\s+better\s+off\s+without\s+me\b",
    r"\bwant\s+everything\s+to\s+stop\b",
    r"\bi\s+don'?t\s+see\s+(a|the)\s+(reason|point)\s+(to|in)\s+continu\w*\b",
    r"\bnothing\s+matters\s+anymore\b",
    r"\bgiving\s+up\s+on\s+(life|everything)\b",

    # Harm to others
    r"\bhurt\s+(him|her|them|someone)\b",
    r"\bkill\s+(him|her|them|someone)\b",
    r"\bgoing\s+to\s+hurt\s+(myself|someone|him|her|them)\b",

    # Immediate danger
    r"\bi\s+have\s+a\s+plan\b",
    r"\bi'?m\s+in\s+(immediate\s+)?danger\b",
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in HIGH_RISK_PATTERNS]

# Words that, on their own in a short message, indicate an affirmative or
# negative answer to a direct safety-check question ("Are you in danger?").
_YES_WORDS = {"yes", "y", "yeah", "yep", "yup", "ya", "affirmative", "true"}
_NO_WORDS = {"no", "n", "nope", "nah", "not really", "false"}


def assess_risk(text: str) -> str:
    """
    Returns 'high' if the message matches a high-risk pattern, else 'none'.

    This is deliberately conservative in favor of false positives: it is
    far safer to occasionally show crisis resources to someone who is not
    in crisis than to miss someone who is.
    """
    if not text:
        return "none"
    for pattern in _COMPILED_PATTERNS:
        if pattern.search(text):
            return "high"
    return "none"


def parse_yes_no(text: str):
    """
    Parses a short yes/no style answer to the safety-check question.
    Returns True, False, or None if it can't be confidently determined.
    """
    t = text.strip().lower().rstrip(".!?")
    if t in _YES_WORDS:
        return True
    if t in _NO_WORDS:
        return False
    # Looser matching for short phrases
    if re.search(r"\b(yes|yeah|yep|i (am|have))\b", t):
        return True
    if re.search(r"\b(no|not|i'?m not|i haven'?t)\b", t):
        return False
    return None


def crisis_card_text() -> str:
    return (
        "\U0001F499 You don't have to handle this alone.\n\n"
        "I'm really sorry you're going through this. I can't provide emergency help, "
        "but you can speak with a trained mental-health professional right now.\n\n"
        "\U0001F1EE\U0001F1F3 Tele-MANAS \u2014 24/7 Mental Health Support\n"
        "\U0001F4DE 14416\n"
        "\U0001F4DE 1800-89-14416\n\n"
        "If you are in immediate danger or may hurt yourself, please call emergency "
        "services (112 in India) or go to the nearest emergency department.\n\n"
        "You can also contact someone you trust and ask them to stay with you."
    )


CRISIS_BUTTONS = [
    {"label": "\U0001F4DE Call Tele-MANAS \u2013 14416", "action": "tel:14416"},
    {"label": "\U0001F4DE Call Emergency Services \u2013 112", "action": "tel:112"},
    {"label": "\u2764\uFE0F Contact Someone I Trust", "action": "trusted_contact"},
]

SAFETY_QUESTION = "Are you in immediate danger right now, or have you already hurt yourself?"


def danger_followup_yes_text() -> str:
    return (
        "Thank you for telling me \u2014 that took courage. Please call emergency "
        "services (112 in India) right now, or Tele-MANAS at 14416.\n\n"
        "If you can, stay with someone you trust and move away from anything you "
        "could use to hurt yourself. You don't need to face this by yourself \u2014 "
        "reaching a real person right now matters more than anything I can say here."
    )


def danger_followup_no_text() -> str:
    return (
        "I'm glad you're not in immediate danger. I'm still here to listen, and it "
        "may really help to talk to a mental-health professional about how you've "
        "been feeling \u2014 Tele-MANAS (14416) is free and available 24/7 if you ever "
        "want to talk it through with someone. What's been weighing on you the most?"
    )


def danger_followup_unclear_text() -> str:
    return (
        "I just want to make sure I understand \u2014 could you answer with a simple "
        "yes or no: are you in immediate danger right now, or have you already hurt "
        "yourself?"
    )
