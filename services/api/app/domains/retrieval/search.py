from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Concept, SourceSpan
from app.domains.retrieval.embeddings import cosine, hash_embedding, lexical_score


FILE_ALIASES = {
    "01_llm_intro.ipynb": "pipeline huggingface fill-mask tokenizer model preprocess postprocess",
    "02_llm_intake.ipynb": "token embedding attention q k v bert position type",
    "03_encoder_task.ipynb": "mlm qa span sequence classification zero-shot",
    "04_seq2seq.ipynb": "t5 flan encoder-decoder cross-attention",
    "05_multimodal.ipynb": "whisper vit blip clip spectrogram caption",
    "06_textgen.ipynb": "gpt decoder llama quantization gptq codegen",
    "07_stateful_models.ipynb": "langchain memory rag agent react",
    "08_assessment.ipynb": "assessment toxicity emotion agent",
}


def hybrid_search(
    db: Session,
    query: str,
    *,
    limit: int = 8,
    source_type: str | None = None,
    filename: str | None = None,
) -> list[dict]:
    q = db.query(SourceSpan)
    if source_type:
        q = q.filter(SourceSpan.source_type == source_type)
    if filename:
        q = q.filter(SourceSpan.file == filename)
    spans = q.all()
    qvec = hash_embedding(query)
    scored: list[tuple[float, SourceSpan]] = []
    qlow = query.lower()
    for sp in spans:
        aliases = FILE_ALIASES.get(sp.file or "", "")
        body = " ".join(
            x
            for x in [sp.file, aliases, sp.heading, sp.body, sp.code or "", sp.stored_output or ""]
            if x
        )
        if not body.strip():
            continue
        lex = lexical_score(query, body)
        sem = cosine(qvec, sp.embedding or []) if sp.embedding else 0.0
        score = 0.62 * lex + 0.38 * sem
        if aliases and any(tok in qlow for tok in aliases.split() if len(tok) > 3):
            score += 0.08
        if score > 0:
            scored.append((score, sp))
    scored.sort(key=lambda t: t[0], reverse=True)
    out = []
    for score, sp in scored[:limit]:
        out.append(
            {
                "score": round(score, 4),
                "span_id": sp.id,
                "source_type": sp.source_type,
                "file": sp.file,
                "cell_index": sp.cell_index,
                "page": sp.page,
                "slide": sp.slide,
                "heading": sp.heading,
                "excerpt": (sp.body or sp.code or "")[:900],
                "evidence_type": sp.evidence_type,
                "has_stored_output": bool(sp.stored_output),
            }
        )
    return out


def match_concepts(db: Session, query: str, limit: int = 5) -> list[Concept]:
    qvec = hash_embedding(query)
    qlow = query.lower()
    ranked: list[tuple[float, Concept]] = []
    for c in db.query(Concept).all():
        blob = " ".join([c.name, c.definition, c.engineer, c.analogy or "", c.slug.replace("-", " ")])
        s = 0.7 * lexical_score(query, blob) + 0.3 * cosine(qvec, hash_embedding(blob))
        name = (c.name or "").lower()
        slug = (c.slug or "").replace("-", " ")
        if name and name in qlow:
            s += 0.5
        elif slug and slug in qlow:
            s += 0.35
        else:
            words = [w for w in name.split() if len(w) > 3]
            if words and all(w in qlow for w in words):
                s += 0.25
        ranked.append((s, c))
    ranked.sort(key=lambda t: t[0], reverse=True)
    return [c for s, c in ranked[:limit] if s > 0.02]
