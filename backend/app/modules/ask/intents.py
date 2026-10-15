"""Ask-your-record intent matching (contract only, no logic yet).

Rule-based intent matching, no LLM. Each locale has a self-written lexicon
of trigger phrases. The hi, ta and ml lexicons are unreviewed by native
speakers (see docs/locale-review.md) and must not be treated as final copy.

Fuzzy matching uses stdlib difflib, so typos and romanised spelling
variants still land on an intent without a model in the loop.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import StrEnum
from typing import Literal


class AskIntent(StrEnum):
    LATEST_LAB = "LATEST_LAB"
    LAB_TREND = "LAB_TREND"
    MEDICATIONS = "MEDICATIONS"
    ALLERGIES = "ALLERGIES"
    CONDITIONS = "CONDITIONS"
    WHAT_CHANGED = "WHAT_CHANGED"
    WHO_ACCESSED = "WHO_ACCESSED"
    EMERGENCY_PREVIEW = "EMERGENCY_PREVIEW"
    UNMATCHED = "UNMATCHED"


Locale = Literal["en", "hi", "ta", "ml"]


@dataclass(frozen=True)
class IntentMatch:
    intent: AskIntent
    entity: str | None = None
    window_days: int | None = None


_LEXICONS: dict[str, dict[AskIntent, tuple[str, ...]]] = {
    "en": {
        AskIntent.WHO_ACCESSED: (
            "who accessed",
            "who viewed",
            "who looked",
            "who saw",
            "who has seen",
            "who opened",
            "who read",
            "who checked",
            "access log",
            "who has access",
        ),
        AskIntent.EMERGENCY_PREVIEW: (
            "paramedic",
            "emergency card",
            "emergency",
            "first responder",
            "ambulance",
            "qr",
        ),
        AskIntent.WHAT_CHANGED: (
            "what changed",
            "whats new",
            "what is new",
            "anything new",
            "new since",
            "recent changes",
            "what was added",
            "what has changed",
            "since my last visit",
        ),
        AskIntent.ALLERGIES: ("allergy", "allergies", "allergic"),
        AskIntent.MEDICATIONS: (
            "medication",
            "medications",
            "medicine",
            "medicines",
            "drugs",
            "tablets",
            "pills",
            "prescription",
            "prescriptions",
            "what am i taking",
        ),
        AskIntent.CONDITIONS: (
            "condition",
            "conditions",
            "diagnosis",
            "diagnoses",
            "diagnosed",
            "illness",
            "disease",
            "what do i have",
        ),
        AskIntent.LAB_TREND: (
            "trend",
            "over time",
            "history",
            "going up",
            "going down",
            "changing",
            "progress",
            "graph",
            "chart",
            "improving",
        ),
        AskIntent.LATEST_LAB: (
            "latest",
            "last",
            "recent",
            "current",
            "result",
            "results",
            "level",
            "levels",
            "what is my",
            "whats my",
            "how much",
        ),
    },
    "hi": {
        AskIntent.WHO_ACCESSED: ("किसने देखा", "किसने देखी", "किसने खोला", "कौन देख", "किसने पढ़ा"),
        AskIntent.EMERGENCY_PREVIEW: ("आपातकालीन", "इमरजेंसी", "पैरामेडिक", "एम्बुलेंस"),
        AskIntent.WHAT_CHANGED: ("क्या बदला", "क्या नया", "नया क्या", "बदलाव"),
        AskIntent.ALLERGIES: ("एलर्जी",),
        AskIntent.MEDICATIONS: ("दवा", "दवाई", "दवाएं", "दवाइयां", "गोली", "गोलियां"),
        AskIntent.CONDITIONS: ("बीमारी", "बीमारियां", "निदान", "रोग"),
        AskIntent.LAB_TREND: ("रुझान", "ट्रेंड", "समय के साथ", "बढ़ रहा", "घट रहा", "इतिहास"),
        AskIntent.LATEST_LAB: ("ताज़ा", "ताजा", "पिछला", "नवीनतम", "स्तर", "कितना"),
    },
    "ta": {
        AskIntent.WHO_ACCESSED: ("யார் பார்த்தது", "யார் பார்த்தார்", "யார் அணுகினார்", "யார் திறந்தார்"),
        AskIntent.EMERGENCY_PREVIEW: ("அவசர", "ஆம்புலன்ஸ்", "துணை மருத்துவர்"),
        AskIntent.WHAT_CHANGED: ("என்ன மாறியது", "புதிதாக என்ன", "மாற்றங்கள்"),
        AskIntent.ALLERGIES: ("ஒவ்வாமை",),
        AskIntent.MEDICATIONS: ("மருந்து", "மருந்துகள்", "மாத்திரை", "மாத்திரைகள்"),
        AskIntent.CONDITIONS: ("நோய்", "நோய்கள்", "கண்டறிதல்"),
        AskIntent.LAB_TREND: ("போக்கு", "காலப்போக்கில்", "அதிகரிக்கிறது", "குறைகிறது", "வரலாறு"),
        AskIntent.LATEST_LAB: ("சமீபத்திய", "கடைசி", "தற்போதைய", "முடிவு", "அளவு"),
    },
    "ml": {
        AskIntent.WHO_ACCESSED: ("ആരാണ് കണ്ടത്", "ആര് കണ്ടു", "ആരാണ് നോക്കിയത്", "ആര് തുറന്നു"),
        AskIntent.EMERGENCY_PREVIEW: ("അടിയന്തര", "ആംബുലൻസ്", "പാരാമെഡിക്"),
        AskIntent.WHAT_CHANGED: ("എന്താണ് മാറിയത്", "പുതിയത് എന്ത്", "മാറ്റങ്ങൾ"),
        AskIntent.ALLERGIES: ("അലർജി",),
        AskIntent.MEDICATIONS: ("മരുന്ന്", "മരുന്നുകൾ", "ഗുളിക", "ഗുളികകൾ"),
        AskIntent.CONDITIONS: ("രോഗം", "രോഗങ്ങൾ", "അസുഖം", "രോഗനിർണയം"),
        AskIntent.LAB_TREND: ("ട്രെൻഡ്", "കാലക്രമേണ", "കൂടുന്നു", "കുറയുന്നു", "ചരിത്രം"),
        AskIntent.LATEST_LAB: ("ഏറ്റവും പുതിയ", "അവസാന", "നിലവിലെ", "ഫലം", "അളവ്"),
    },
}

# Tie-break order when two intents score equally: the more specific wins.
_PRIORITY = (
    AskIntent.WHO_ACCESSED,
    AskIntent.EMERGENCY_PREVIEW,
    AskIntent.WHAT_CHANGED,
    AskIntent.ALLERGIES,
    AskIntent.MEDICATIONS,
    AskIntent.CONDITIONS,
    AskIntent.LAB_TREND,
    AskIntent.LATEST_LAB,
)
_FUZZY = 0.85
_WEEK = ("week", "weeks", "हफ्ते", "हफ्ता", "सप्ताह", "வாரம்", "ആഴ്ച")
_MONTH = ("month", "months", "महीने", "महीना", "மாதம்", "மாசம்", "മാസം")


def normalize(text: str) -> str:
    """NFC, lower-cased, punctuation to spaces; combining marks are kept so
    Indic scripts survive."""
    text = unicodedata.normalize("NFC", text).lower()
    kept = (c if c.isalnum() or unicodedata.category(c) in ("Mn", "Mc") else " " for c in text)
    return " ".join("".join(kept).split())


def _token_match(phrase_token: str, token: str) -> float:
    if token == phrase_token:
        return 1.0
    # Prefix match absorbs plurals and Dravidian case suffixes.
    if len(phrase_token) >= 4 and token.startswith(phrase_token):
        return 1.0
    return SequenceMatcher(None, phrase_token, token).ratio()


def _phrase_score(phrase: list[str], tokens: list[str]) -> float:
    """Phrase tokens must match question tokens in order, with at most two
    stray words between them ("किसने मेरा रिकॉर्ड देखा" still hits "किसने देखा")."""
    n = len(phrase)
    best = 0.0
    for start in range(len(tokens)):
        pos, scores = start, []
        for p in phrase:
            for j in range(pos, min(pos + 3, len(tokens))):
                score = _token_match(p, tokens[j])
                if score >= _FUZZY:
                    scores.append(score)
                    pos = j + 1
                    break
            else:
                break
        if len(scores) == n:
            best = max(best, sum(scores) / n)
    # Longer phrases are more specific; a 2-word hit beats a 1-word hit.
    return best * (1 + 0.1 * n)


def _window(tokens: list[str]) -> int | None:
    def has(words: tuple[str, ...]) -> bool:
        return any(_token_match(w, t) >= _FUZZY for t in tokens for w in words)

    if "90" in tokens or "quarter" in tokens:
        return 90
    if "3" in tokens and has(_MONTH):
        return 90
    if "30" in tokens or has(_MONTH):
        return 30
    if "7" in tokens or has(_WEEK):
        return 7
    return None


def match_entity(names: Sequence[str], text: str) -> str | None:
    """Best of `names` mentioned in `text`, or None. A name token matches a
    question token on equality, containment (min 3 chars: "a1c" in "hba1c")
    or fuzzy ratio; at least half the name's tokens must match."""
    tokens = normalize(text).split()
    best: tuple[float, int, str] | None = None
    for name in names:
        name_tokens = [t for t in normalize(name).split() if len(t) >= 2]
        if not name_tokens:
            continue
        hits = sum(
            any(
                t == q
                or (min(len(t), len(q)) >= 3 and (t in q or q in t))
                or _token_match(t, q) >= _FUZZY
                for q in tokens
            )
            for t in name_tokens
        )
        ratio = hits / len(name_tokens)
        if ratio >= 0.5 and (best is None or (ratio, hits) > best[:2]):
            best = (ratio, hits, name)
    return best[2] if best else None


def match_intent(question: str, locale: Locale) -> IntentMatch:
    """Pure and deterministic: same question and locale, same match.

    Fuzzy matching via stdlib difflib. A question that matches no lexicon
    entry returns UNMATCHED rather than guessing an intent. The English
    lexicon always applies as well, since people mix scripts. `entity` is
    the normalised question for lab intents, for the caller to match
    against the patient's own test names.
    """
    text = normalize(question)
    tokens = text.split()
    best_intent, best_score = AskIntent.UNMATCHED, 0.0
    for intent in _PRIORITY:
        phrases = _LEXICONS["en"].get(intent, ()) + _LEXICONS[locale].get(intent, ())
        score = max((_phrase_score(p.split(), tokens) for p in map(normalize, phrases)), default=0)
        if score > best_score:
            best_intent, best_score = intent, score
    if best_score == 0.0:
        return IntentMatch(AskIntent.UNMATCHED)
    labs = best_intent in (AskIntent.LATEST_LAB, AskIntent.LAB_TREND)
    return IntentMatch(best_intent, entity=text if labs else None, window_days=_window(tokens))


SUGGESTED_INTENTS: tuple[AskIntent, ...] = tuple(
    intent for intent in AskIntent if intent is not AskIntent.UNMATCHED
)

__all__ = [
    "SUGGESTED_INTENTS",
    "AskIntent",
    "IntentMatch",
    "Locale",
    "match_entity",
    "match_intent",
    "normalize",
]
