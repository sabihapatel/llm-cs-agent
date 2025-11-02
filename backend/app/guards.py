import re
from dataclasses import dataclass

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b")
CC_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")  # naive credit-card catch

OUT_OF_DOMAIN = ["weather", "sports", "stocks", "translate", "song", "joke"]
RISKY_KEYWORDS = ["password", "ssn", "social security", "credit card", "cvv"]

@dataclass
class GuardResult:
    safe_text: str
    redacted: bool
    domain_ok: bool
    risky: bool

def redact_pii(text: str) -> str:
    t = EMAIL_RE.sub("[EMAIL]", text)
    t = PHONE_RE.sub("[PHONE]", t)
    t = CC_RE.sub("[CARD]", t)
    return t

def is_in_domain(text: str) -> bool:
    low = text.lower()
    return not any(w in low for w in OUT_OF_DOMAIN)

def looks_risky(text: str) -> bool:
    low = text.lower()
    return any(w in low for w in RISKY_KEYWORDS)

def apply(text: str) -> GuardResult:
    safe = redact_pii(text)
    return GuardResult(
        safe_text=safe,
        redacted=(safe != text),
        domain_ok=is_in_domain(safe),
        risky=looks_risky(safe),
    )

