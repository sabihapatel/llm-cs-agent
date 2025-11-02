import re
from dataclasses import dataclass
from typing import Optional, Dict

ORDER_ID_RE = re.compile(r"\b([A-Z]\-?\d{3,6})\b", re.IGNORECASE)

@dataclass
class Route:
    intent: str
    slots: Dict[str, str]
    reason: str

KEYWORDS = {
    "order_status": ["status", "track", "tracking", "order"],
    "create_ticket": ["ticket", "issue", "problem", "support", "help"],
    "faq": ["refund", "return", "warranty", "shipping", "policy", "faq"],
}

OUT_OF_SCOPE_HINTS = ["joke", "weather", "stock", "translate", "music"]

def extract_order_id(text: str) -> Optional[str]:
    m = ORDER_ID_RE.search(text)
    if m:
        oid = m.group(1).upper().replace("-", "")
        return oid
    return None

def route(text: str) -> Route:
    low = text.lower()
    if any(w in low for w in OUT_OF_SCOPE_HINTS):
        return Route("out_of_scope", {}, "content unrelated to support domain")

    oid = extract_order_id(text)

    scores = {k: 0 for k in KEYWORDS}
    for intent, kws in KEYWORDS.items():
        for kw in kws:
            if kw in low:
                scores[intent] += 1

    intent = max(scores, key=scores.get)
    if oid:
        intent = "order_status"
    if all(v == 0 for v in scores.values()) and not oid:
        intent = "faq"

    slots = {}
    if oid:
        slots["order_id"] = oid

    return Route(intent=intent, slots=slots, reason=f"scores={scores}, oid={oid}")

