# backend/app/rag.py
from typing import List, Tuple
from sqlalchemy import text
from app.models import get_engine
from app.embedding import embed

# Returns: (title, chunk/body, score, source)
def retrieve(query: str, k: int = 5) -> List[Tuple[str, str, float, str]]:
    q = embed(query)
    qv_str = "[" + ",".join(f"{x:.6f}" for x in q.tolist()) + "]"

    eng = get_engine()
    sql_sim = text("""
        SELECT title, body, source,
               1 - (embedding <=> CAST(:qv AS vector)) AS score
        FROM kb_docs
        ORDER BY embedding <=> CAST(:qv AS vector)
        LIMIT :k
    """)

    rows: List[Tuple[str, str, float, str]] = []
    with eng.begin() as con:
        rows = [(r.title, r.body, float(r.score), r.source)
                for r in con.execute(sql_sim, {"qv": qv_str, "k": int(k)})]

        if not rows:
            # Fallback 1: simple keyword search (case-insensitive)
            kw = query.strip().split()
            kw = [w for w in kw if len(w) >= 4] or [query]  # avoid tiny stopwords
            like = "%" + kw[0].lower() + "%"
            sql_kw = text("""
                SELECT title, body, source, 1.0 AS score
                FROM kb_docs
                WHERE LOWER(body) LIKE :like OR LOWER(title) LIKE :like
                LIMIT :k
            """)
            rows = [(r.title, r.body, float(r.score), r.source)
                    for r in con.execute(sql_kw, {"like": like, "k": int(k)})]

        if not rows:
            # Fallback 2: return any docs so the app never responds empty
            sql_any = text("SELECT title, body, source, 0.0 AS score FROM kb_docs ORDER BY id LIMIT :k")
            rows = [(r.title, r.body, float(r.score), r.source)
                    for r in con.execute(sql_any, {"k": int(k)})]

    return rows

def top_confidence(hits) -> float:
    return float(hits[0][2]) if hits else 0.0

