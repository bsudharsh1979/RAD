from __future__ import annotations

import hashlib
import math
import re
from collections import Counter

from app.config import settings

_TOKEN = re.compile(r"[a-z0-9_#./+-]+", re.I)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text or "") if len(t) > 1]


def hash_embedding(text: str, dim: int | None = None) -> list[float]:
    """Deterministic offline embedding. Not a semantic model — labeled as such."""
    dim = dim or settings.embedding_dim
    vec = [0.0] * dim
    toks = tokenize(text)
    if not toks:
        return vec
    for tok in toks:
        h = hashlib.sha256(tok.encode("utf-8")).digest()
        idx = int.from_bytes(h[:4], "little") % dim
        sign = 1.0 if h[4] % 2 == 0 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    return sum(a[i] * b[i] for i in range(n))


def lexical_score(query: str, body: str) -> float:
    q = Counter(tokenize(query))
    d = Counter(tokenize(body))
    if not q or not d:
        return 0.0
    overlap = sum((q & d).values())
    return overlap / (sum(q.values()) ** 0.5 * sum(d.values()) ** 0.5)
