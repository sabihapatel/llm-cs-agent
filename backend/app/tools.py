from dataclasses import dataclass

@dataclass
class Order:
    id: str
    status: str
    eta_days: int

FAKE_DB = {
    "A123": Order("A123", "Shipped", 2),
    "B456": Order("B456", "Processing", 5),
    "C789": Order("C789", "Delivered", 0),
}

_ticket_counter = 1000

def get_order_status(order_id: str) -> dict:
    o = FAKE_DB.get(order_id)
    if not o:
        return {"found": False}
    return {"found": True, "id": o.id, "status": o.status, "eta_days": o.eta_days}

def create_ticket(subject: str, desc: str) -> dict:
    global _ticket_counter
    _ticket_counter += 1
    return {"ticket_id": f"T{_ticket_counter}", "subject": subject, "desc": desc}
