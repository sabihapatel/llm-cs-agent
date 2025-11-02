from sqlalchemy import text
from app.models import get_engine, init_db
from app.embedding import embed

def upsert_doc(title: str, body: str, source: str):
    emb = embed(f"{title}\n{body}")  # fixed f-string with newline
    eng = get_engine()
    with eng.begin() as con:
        con.execute(
            text("""
            INSERT INTO kb_docs (title, body, source, embedding)
            VALUES (:title, :body, :source, :embedding)
            """),
            {
                "title": title,
                "body": body,
                "source": source,
                "embedding": emb.tolist(),
            },
        )

def main():
    init_db()
    # Seed sample docs
    try:
        with open("/app/data/kb/sample_faq.md", "r", encoding="utf-8") as f:
            body = f.read()
    except FileNotFoundError:
        body = "Returns accepted within 30 days with receipt."
    upsert_doc("FAQ: Returns & Refunds", body, "data/kb/sample_faq.md")
    upsert_doc("Shipping", "Standard shipping takes 3–5 business days.", "seed:shipping")
    upsert_doc("Return Policy", "You can return items within 30 days with receipt.", "seed:return")
    print("✅ Seeded sample docs with embeddings.")

if __name__ == "__main__":
    main()
