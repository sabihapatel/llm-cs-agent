# backend/app/main.py
from typing import Dict, Any, List, Optional
from fastapi import FastAPI
from pydantic import BaseModel

from app import guards, router
from app.rag import retrieve, top_confidence
from app.tools import get_order_status, create_ticket
from app.handoff import escalate
from app.metrics import METRICS, timed
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="LLM Customer Service Agent (MVP)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatTurn(BaseModel):
    session_id: str
    message: str

@app.post("/answer")
async def answer(turn: ChatTurn) -> Dict[str, Any]:
    # ---- Metrics: start ----
    from time import perf_counter
    t0 = perf_counter()
    METRICS.inc("calls_total")

    # ---- Guardrails ----
    g = guards.apply(turn.message)
    text = g.safe_text
    if g.redacted:
        METRICS.inc("redactions")

    if not g.domain_ok:
        METRICS.inc("refusals")
        out = {
            "intent": "out_of_scope",
            "text": "I can help with orders, returns, refunds, shipping, and tickets. What would you like to do?",
            "tool_result": None,
            "sources": [],
            "metrics": {"latency_ms": 0, "redacted": g.redacted},
        }
        # finalize metrics & return
        METRICS.observe_latency("answer", (perf_counter() - t0) * 1000.0)
        return out

    if g.risky:
        METRICS.inc("refusals")
        out = {
            "intent": "refusal",
            "text": "For your security, I can’t help with passwords or sensitive financial details. Would you like to open a support ticket instead?",
            "tool_result": None,
            "sources": [],
            "metrics": {"latency_ms": 0, "redacted": g.redacted},
        }
        METRICS.observe_latency("answer", (perf_counter() - t0) * 1000.0)
        return out

    # ---- Route intent ----
    r = router.route(text)
    intent = r.intent
    METRICS.inc(intent)

    sources: List[Dict[str, Any]] = []
    tool_result: Optional[Dict[str, Any]] = None
    reply: str = ""

    # ---- Tool path: order status ----
    if intent == "order_status":
        order_id = r.slots.get("order_id")
        if not order_id:
            out = {
                "intent": intent,
                "text": "Could you share your order ID (e.g., A1234)?",
                "tool_result": None,
                "sources": [],
                "metrics": {"latency_ms": 0},
            }
            METRICS.observe_latency("answer", (perf_counter() - t0) * 1000.0)
            return out

        tool_result = get_order_status(order_id)
        if tool_result.get("found"):
            METRICS.inc("tool_success")
            reply = f"Order {order_id}: {tool_result['status']}. ETA {tool_result['eta_days']} day(s)."
        else:
            METRICS.inc("tool_fail")
            # escalate instead of dead end
            METRICS.inc("handoffs")
            hand = escalate(turn.session_id, text, {"intent": "order_status", "order_id": order_id})
            out = {
                "intent": "handoff",
                "text": "I couldn’t find that order. I’ve escalated this to a human—expect a follow-up shortly.",
                "tool_result": hand,
                "sources": [],
                "metrics": {"latency_ms": 0},
            }
            METRICS.observe_latency("answer", (perf_counter() - t0) * 1000.0)
            return out

    # ---- Tool path: create ticket ----
    elif intent == "create_ticket":
        tool_result = create_ticket("Customer Support", text)
        reply = f"I've created ticket {tool_result['ticket_id']}. Our team will follow up via email."

    # ---- Out-of-scope (defensive) ----
    elif intent == "out_of_scope":
        reply = "I can help with orders, returns, refunds, shipping, and tickets. What would you like to do?"

    # ---- FAQ (RAG) path ----
    else:
        with timed("rag"):
            hits = retrieve(text, k=3)
        conf = top_confidence(hits)
        from app.metrics import METRICS as M  # avoid shadowing
        M.observe_conf(conf)

        if conf < 0.60:
            METRICS.inc("handoffs")
            hand = escalate(turn.session_id, text, {"intent": "faq", "hits": len(hits), "conf": conf})
            out = {
                "intent": "handoff",
                "text": "I’m not fully confident. I’ve escalated this to our human support team and they’ll follow up shortly.",
                "tool_result": hand,
                "sources": [],
                "metrics": {"latency_ms": 0, "confidence": conf},
            }
            METRICS.observe_latency("answer", (perf_counter() - t0) * 1000.0)
            return out

        # build sources + concise answer
        for i, (title, chunk, score, src) in enumerate(hits, start=1):
            sources.append({"id": i, "title": title, "source": src, "score": score, "snippet": chunk})

        if hits:
            lines = [ln.strip() for ln in hits[0][1].splitlines() if ln.strip()]
            answer_line = next((ln[2:].strip() for ln in lines if ln.lower().startswith("a:")), lines[0])
            reply = f"{answer_line} [1]"
        else:
            reply = "I'm not fully sure. Would you like me to escalate to a human?"

    # ---- Final unified return (always returns a dict) ----
    out = {
        "intent": intent,
        "text": reply,
        "tool_result": tool_result,
        "sources": sources,
        "metrics": {},  # latency added below
    }
    from time import perf_counter as _pc
    METRICS.observe_latency("answer", (_pc() - t0) * 1000.0)
    return out

@app.get("/metrics")
async def metrics():
    return METRICS.snapshot()
