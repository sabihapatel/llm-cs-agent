import os, json, time
import urllib.request

WEBHOOK_URL = os.getenv("HANDOFF_WEBHOOK_URL", "")

def escalate(session_id: str, user_text: str, context):
    if not WEBHOOK_URL:
        return {"sent": False, "reason": "no webhook configured"}
    payload = {
        "session_id": session_id,
        "user_text": user_text,
        "context": context,
        "ts": int(time.time()),
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(WEBHOOK_URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return {"sent": True, "status": resp.status}
    except Exception as e:
        return {"sent": False, "error": str(e)}

