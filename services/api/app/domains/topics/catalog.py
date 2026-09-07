"""Curated topic tracks for NVIDIA DLI RAD-LLM. Stories, not a concept dump."""

from __future__ import annotations

TOPICS: list[dict] = [
    {
        "id": "the-black-box",
        "order": 1,
        "title": "The model that hides its homework",
        "hook": "You type a sentence. A blank fills in. The tensors never appear. That disappearing act is the whole point of a HuggingFace pipeline — and the first thing this course wants you to undo.",
        "promise": "Peel a fill-mask pipeline into tokenizer → model → postprocess and say what each stage is actually doing.",
        "minutes": 15,
        "notebook": "01_llm_intro.ipynb",
        "twin": "pipeline-flow",
        "concept_ids": ["c-pipeline", "c-preprocess", "c-forward", "c-postprocess", "c-tokenizer"],
        "ask": "What actually happens between the sentence I type and the [MASK] guess?",
        "cluster": "fundamentals",
    },
    {
        "id": "lego-language",
        "order": 2,
        "title": "Sentences become brick numbers",
        "hook": "Models do not read English. They look up brick numbers in a 30,522-row table, then add a second table that only cares about position. Mix those two vectors and you have the real input.",
        "promise": "Explain input_ids, the 768-d word table, and why position embeddings exist.",
        "minutes": 15,
        "notebook": "02_llm_intake.ipynb",
        "twin": "tokenizer-embeddings",
        "concept_ids": ["c-token", "c-input-ids", "c-word-emb", "c-pos-emb", "c-emb-add"],
        "ask": "Why does BERT need a second embedding table just for position?",
        "cluster": "intake",
    },
    {
        "id": "who-looks-at-whom",
        "order": 3,
        "title": "Every word looks at every word",
        "hook": "Attention is not 'the model focusing.' It is a scored meeting: query asks, keys answer, values speak. Softmax turns the meeting into a weighted average.",
        "promise": "Name Q, K, and V, and say what the softmax weights are averaging.",
        "minutes": 18,
        "notebook": "03_encoder_task.ipynb",
        "twin": "attention-encoder",
        "concept_ids": ["c-attention", "c-qk-v", "c-scaled-dot", "c-mha", "c-residual"],
        "ask": "What are Q, K, and V actually doing in one attention head?",
        "cluster": "attention",
    },
    {
        "id": "one-encoder-many-hats",
        "order": 4,
        "title": "Same brain, different hats",
        "hook": "The encoder is reusable. Swap the last layer and the same BERT becomes a blank-filler, a named-entity tagger, a span finder, or a zero-shot classifier. The body stays; the hat changes.",
        "promise": "Match MLM, token classification, span QA, and zero-shot MNLI to the head each one needs.",
        "minutes": 16,
        "notebook": "03_encoder_task.ipynb",
        "twin": "encoder-heads",
        "concept_ids": ["c-mlm", "c-token-cls", "c-qa-span", "c-seq-cls", "c-zeroshot"],
        "ask": "Why can one encoder do fill-mask and extractive QA without becoming a new model?",
        "cluster": "encoder-tasks",
    },
    {
        "id": "writer-plus-reader",
        "order": 5,
        "title": "The intern who writes after reading",
        "hook": "T5 is not a chatbot. The encoder reads the whole prompt once. The decoder writes one new token at a time, peeking back at that encoding through cross-attention. Flan is the intern who practiced following instructions.",
        "promise": "Say why the encoder runs once, what cross-attention is for, and why vanilla T5 fails Pig Latin.",
        "minutes": 16,
        "notebook": "04_seq2seq.ipynb",
        "twin": "seq2seq-t5",
        "concept_ids": ["c-seq2seq", "c-t5", "c-cross-attn", "c-flan", "c-t5-prefix"],
        "ask": "Why does T5's encoder run once while the decoder loops?",
        "cluster": "seq2seq",
    },
    {
        "id": "ears-and-eyes",
        "order": 6,
        "title": "When language is not enough",
        "hook": "Whisper hears a spectrogram. ViT sees image patches. CLIP keeps two encoders that never fuse until a similarity score. Captioning is a different job: one side must generate words.",
        "promise": "Tell Whisper, ViT, BLIP, and CLIP apart by what they take in and what they emit.",
        "minutes": 14,
        "notebook": "05_multimodal.ipynb",
        "twin": "multimodal",
        "concept_ids": ["c-modality", "c-whisper", "c-vit", "c-blip", "c-clip"],
        "ask": "How is CLIP's dual encoder different from a captioning model?",
        "cluster": "multimodal",
    },
    {
        "id": "next-token-factory",
        "order": 7,
        "title": "Guess the next brick, again",
        "hook": "A decoder-only model is a next-token factory with a one-way mirror: it may look left, never right. Temperature and do_sample decide whether it picks the safest brick or rolls the dice.",
        "promise": "Explain causal masking, greedy vs sampling, and why Llama-2 chat needs INST/SYS wrappers.",
        "minutes": 16,
        "notebook": "06_textgen.ipynb",
        "twin": "decoder-sampling",
        "concept_ids": ["c-decoder-only", "c-causal", "c-temp", "c-do-sample", "c-llama2"],
        "ask": "What does a causal mask prevent the decoder from seeing?",
        "cluster": "decoder",
    },
    {
        "id": "suitcase-too-small",
        "order": 8,
        "title": "The 70B elephant and the GPU suitcase",
        "hook": "Host RAM can hold a giant checkpoint. GPU RAM cannot. The course's 70B FP16 story is ~135 GB. GPTQ and bitsandbytes are how you fold the elephant so it fits.",
        "promise": "Separate system RAM from GPU RAM, and say what 4-bit / GPTQ is trading away.",
        "minutes": 14,
        "notebook": "06_textgen.ipynb",
        "twin": "quantization-memory",
        "concept_ids": ["c-gpu-ram", "c-quant", "c-70b-ram", "c-gptq", "c-bnb"],
        "ask": "Why can a 70B model sit in host RAM and still fail to run on the GPU?",
        "cluster": "decoder",
    },
    {
        "id": "does-it-remember",
        "order": 9,
        "title": "Why the chatbot forgot your name",
        "hook": "An LLMChain without memory is a goldfish. Second-turn amnesia is not a model bug — the last turn never entered the prompt. Commit a cause before the twin shows the ground truth.",
        "promise": "Name ConversationBuffer memory, why history must be an input variable, and diagnose second-turn amnesia.",
        "minutes": 16,
        "notebook": "07_stateful_models.ipynb",
        "twin": "incident-diagnosis",
        "concept_ids": ["c-memory", "c-llmchain", "c-buffer-mem", "c-history-var", "c-incident"],
        "ask": "Why does a second turn forget the first if I used LLMChain?",
        "cluster": "stateful",
    },
    {
        "id": "search-or-think",
        "order": 10,
        "title": "Library card versus intern with tools",
        "hook": "RAG fetches pages, then writes. An agent decides which tool to call, including asking you. The course treats a live Python REPL as a bad idea; Ask-For-Input is the safer loop.",
        "promise": "Contrast RAG with a ReAct agent, and say why the user-as-tool loop exists.",
        "minutes": 16,
        "notebook": "07_stateful_models.ipynb",
        "twin": "rag-agent",
        "concept_ids": ["c-rag", "c-agent", "c-tools", "c-react", "c-ask-input"],
        "ask": "When should I retrieve documents instead of handing the model a tool?",
        "cluster": "stateful",
    },
]


def list_topics() -> list[dict]:
    return [dict(t) for t in sorted(TOPICS, key=lambda x: x["order"])]


def get_topic(tid: str) -> dict | None:
    for t in TOPICS:
        if t["id"] == tid:
            return dict(t)
    return None


def topic_for_concept(concept_id: str) -> dict | None:
    for t in TOPICS:
        if concept_id in t["concept_ids"]:
            return dict(t)
    return None


def topic_for_notebook(filename: str) -> dict | None:
    for t in TOPICS:
        if t["notebook"] == filename:
            return dict(t)
    return None
