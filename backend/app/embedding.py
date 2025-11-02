# backend/app/embedding.py
import hashlib, re
import numpy as np

DIM = 1536

_WORD_RE = re.compile(r"\w+", flags=re.UNICODE)

def _tokenize(txt: str):
    # lowercase + keep only word characters (letters/digits/_)
    return _WORD_RE.findall(txt.lower())

def _bucket(token: str) -> int:
    h = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return int(h[:8], 16) % DIM

def embed(text: str) -> np.ndarray:
    v = np.zeros(DIM, dtype=np.float32)
    for tok in _tokenize(text):
        v[_bucket(tok)] += 1.0
    n = np.linalg.norm(v)
    if n > 0:
        v /= n
    return v

