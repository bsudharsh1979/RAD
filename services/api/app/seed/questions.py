"""Generate a large source-grounded question bank. Never LLM-batch '500 questions'."""

from __future__ import annotations

import hashlib
from typing import Any

from app.seed.concepts import CONCEPTS
from app.seed.misconceptions import MISCONCEPTIONS


def _qid(*parts: Any) -> str:
    return "q-" + hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()[:12]


def _q(**kwargs) -> dict:
    kwargs.setdefault("validated", True)
    kwargs.setdefault("integrity_flags", [])
    kwargs.setdefault("evidence_type", "COURSE_SOURCE")
    kwargs.setdefault("options", None)
    kwargs.setdefault("misconception_id", None)
    return kwargs


def _mc(stem, options, answer, **kw):
    return _q(qtype="mcq", stem=stem, options=options, answer=answer, **kw)


QUESTIONS: list[dict] = []


def _add(q: dict) -> None:
    QUESTIONS.append(q)


# ----- Hand-authored high-signal items -----
HAND = [
    _mc(
        "In notebook 1, which two objects does the course say a HuggingFace pipeline is largely comprised of?",
        ["optimizer and scheduler", "tokenizer and model", "GPU and CUDA graphs", "LangChain and LlamaIndex"],
        "tokenizer and model",
        bloom="recall", difficulty=1, concept_id="c-pipeline",
        source_file="01_llm_intro.ipynb", source_cell=14,
        explanation="Cell 14: tokenizer converts strings; model does tensor-to-tensor.",
    ),
    _mc(
        "What is the pipeline organization scheme given in notebook 1?",
        [
            "tokenize → retrieve → generate",
            "preprocess → forward → postprocess",
            "encode → quantize → decode",
            "plan → act → observe",
        ],
        "preprocess → forward → postprocess",
        bloom="recall", difficulty=1, concept_id="c-pipeline",
        source_file="01_llm_intro.ipynb", source_cell=14,
        explanation="preprocess is tokenizer; forward is model; postprocess is task-specific.",
    ),
    _mc(
        "BERT word embeddings in notebook 2 are described with which table shape intuition?",
        ["512 × 768", "30522 × 768", "12 × 64", "28 × 768"],
        "30522 × 768",
        bloom="recall", difficulty=2, concept_id="c-word-emb",
        source_file="02_llm_intake.ipynb", source_cell=10,
        explanation="Vocabulary 30,522 tokens, 768-d embeddings.",
    ),
    _mc(
        "How does notebook 2 say BERT combines word, position, and type embeddings?",
        ["concatenation to 2304-d", "addition in the embedding dimension", "cross-attention", "product of experts"],
        "addition in the embedding dimension",
        bloom="recall", difficulty=2, concept_id="c-emb-add",
        source_file="02_llm_intake.ipynb", source_cell=21,
        explanation="embed = Word + Pos + Type; HF source confirms addition.",
        misconception_id="m-concat-add",
    ),
    _mc(
        "BERT multi-head attention in notebook 2 uses how many heads of what width?",
        ["8 heads of 96", "12 heads of 64", "16 heads of 48", "32 heads of 24"],
        "12 heads of 64",
        bloom="recall", difficulty=2, concept_id="c-mha",
        source_file="02_llm_intake.ipynb", source_cell=27,
        explanation="768/12 = 64; concatenate back to 768.",
    ),
    _mc(
        "The BERT encoder MLP path listed in notebook 2 is:",
        ["768 → 3072 → 768", "768 → 768 → 3072 → 768", "512 → 768 → 512", "30522 → 768"],
        "768 → 768 → 3072 → 768",
        bloom="recall", difficulty=2, concept_id="c-encoder",
        source_file="02_llm_intake.ipynb", source_cell=27,
        explanation="BertSelfOutput → Intermediate → Output with 3072 hidden.",
    ),
    _mc(
        "Masked language modeling's training goal in notebook 3 is:",
        ["Translate English to French", "Recover the original tokens", "Generate unbounded chat", "Rank documents"],
        "Recover the original tokens",
        bloom="recall", difficulty=1, concept_id="c-mlm",
        source_file="03_encoder_task.ipynb", source_cell=7,
        explanation="MLM: replace some tokens with [MASK] / random; recover originals.",
    ),
    _mc(
        "For deepset/roberta-base-squad2, qa_outputs is described as:",
        ["Linear(768, 30522)", "Linear(768, 2)", "Linear(768, 28)", "Linear(512, 2)"],
        "Linear(768, 2)",
        bloom="recall", difficulty=2, concept_id="c-qa-span",
        source_file="03_encoder_task.ipynb", source_cell=9,
        explanation="Start logit and end logit per token.",
        misconception_id="m-qa-generate",
    ),
    _mc(
        "Why does notebook 3 say substring answers can be desirable?",
        ["They are always more fluent", "They limit the reasoning space of smaller models / add stability", "They use fewer GPUs", "They enable Python REPL"],
        "They limit the reasoning space of smaller models / add stability",
        bloom="explain", difficulty=3, concept_id="c-qa-span",
        source_file="03_encoder_task.ipynb", source_cell=7,
        explanation="Public-facing stability vs inability to converse.",
    ),
    _mc(
        "Next-sentence prediction is described as:",
        ["Universally required for all encoders", "Central like MLM", "Contested; RoBERTa drops it; ALBERT uses SOP", "The T5 prefix"],
        "Contested; RoBERTa drops it; ALBERT uses SOP",
        bloom="recall", difficulty=3, concept_id="c-nsp",
        source_file="03_encoder_task.ipynb", source_cell=11,
        explanation="MLM is central; NSP is optional/contested.",
    ),
    _mc(
        "Zero-shot inference as defined in notebook 3 means:",
        ["Weights are random", "The model predicts things it was never specifically trained to predict", "Exactly one gradient step", "Using GPTQ"],
        "The model predicts things it was never specifically trained to predict",
        bloom="recall", difficulty=2, concept_id="c-zeroshot",
        source_file="03_encoder_task.ipynb", source_cell=19,
        misconception_id="m-zeroshot-untrained",
        explanation="Few-shot: limited examples in train or context.",
    ),
    _mc(
        "A BERT-like encoder, per notebook 4, is NOT naturally generating:",
        ["Per-token class logits", "A span inside the input", "Novel response tokens", "Pooled sequence labels"],
        "Novel response tokens",
        bloom="explain", difficulty=3, concept_id="c-seq2seq",
        source_file="04_seq2seq.ipynb", source_cell=2,
        misconception_id="m-encoder-novel",
        explanation="Encoder yields insight, not a generated response sequence.",
    ),
    _mc(
        "Notebook 4 reports t5-base parameter count as:",
        ["73 million", "222,903,552", "13 billion", "70 billion"],
        "222,903,552",
        bloom="recall", difficulty=2, concept_id="c-t5",
        source_file="04_seq2seq.ipynb", source_cell=5,
        explanation="translator.model.num_parameters() comment.",
    ),
    _mc(
        "In the T5 generation listener observations, the encoder is:",
        ["Called once to build a static context", "Called every decoder token", "Never used", "Replaced by CLIP"],
        "Called once to build a static context",
        bloom="recall", difficulty=2, concept_id="c-t5",
        source_file="04_seq2seq.ipynb", source_cell=18,
        misconception_id="m-encoder-each-token",
        explanation="Avoids moving-target training; past_key_values grow on the decoder.",
    ),
    _mc(
        "Why does the course say pig latin is likely to fail even with few-shot Flan-T5?",
        ["Flan-T5 cannot tokenize French", "Letter-level semantically-unnatural reasoning vs typical tokenization", "Missing GPU RAM", "Cross-attention is disabled"],
        "Letter-level semantically-unnatural reasoning vs typical tokenization",
        bloom="diagnose", difficulty=4, concept_id="c-icl",
        source_file="04_seq2seq.ipynb", source_cell=33,
        explanation="Few-shot example in the notebook is expected to still fail.",
    ),
    _mc(
        "Flan-T5's ability to follow novel natural-language instructions is named:",
        ["Quantization-aware training", "In-context learning", "Next-sentence prediction", "GPTQ"],
        "In-context learning",
        bloom="recall", difficulty=2, concept_id="c-icl",
        source_file="04_seq2seq.ipynb", source_cell=28,
        explanation="Main enabler of prompt engineering in that notebook.",
    ),
    _mc(
        "Which is NOT listed as a prompt-engineering rule of thumb in notebook 4?",
        ["Format abiding", "Few-shot prompting", "Decoder priming", "Always increase temperature to 2.0"],
        "Always increase temperature to 2.0",
        bloom="recall", difficulty=2, concept_id="c-prompt-eng",
        source_file="04_seq2seq.ipynb", source_cell=28,
        explanation="Four bullets: format, few-shot, iterative, priming.",
    ),
    _mc(
        "High-level Whisper flow in notebook 5 starts by:",
        ["Byte-pair encoding the waveform samples directly as UTF-8", "Slicing audio into windows and making spectrograms", "Running BERT MLM on captions", "Quantizing Llama-2"],
        "Slicing audio into windows and making spectrograms",
        bloom="recall", difficulty=2, concept_id="c-whisper",
        source_file="05_multimodal.ipynb", source_cell=5,
        explanation="Then sequence the images, transformers, cross-attend a decoder.",
    ),
    _mc(
        "whisper-base is chosen in the notebook primarily because:",
        ["It is the only multilingual SOTA", "~73M params, faster, surprisingly serviceable", "It requires A100", "It is decoder-only GPT-2"],
        "~73M params, faster, surprisingly serviceable",
        bloom="apply", difficulty=3, concept_id="c-whisper",
        source_file="05_multimodal.ipynb", source_cell=8,
        explanation="large-v2 1.55B better hard multilingual cases.",
    ),
    _mc(
        "ViT treats images as sequences by:",
        ["Flattening every pixel into one token", "Dividing the image into patches (16×16 words paper)", "Using token_type_ids as RGB", "Running T5 on file paths"],
        "Dividing the image into patches (16×16 words paper)",
        bloom="recall", difficulty=2, concept_id="c-vit",
        source_file="05_multimodal.ipynb", source_cell=18,
        explanation="Then cross-attend a language decoder for captions.",
    ),
    _mc(
        "CLIP's training proposition in notebook 5 is:",
        ["Generate captions token-by-token", "Train language and image encoders so related pairs match", "Fill [MASK] in spectrograms", "Execute Python tools"],
        "Train language and image encoders so related pairs match",
        bloom="recall", difficulty=2, concept_id="c-clip",
        source_file="05_multimodal.ipynb", source_cell=35,
        misconception_id="m-clip-generative",
        explanation="Contrastive; embeddings semantically dense and synergized.",
    ),
    _mc(
        "Decoder-only models drop the encoder when:",
        ["You need bidirectional NSP", "Context and generation share a vocabulary / continue-the-passage", "You must caption images", "You need token classification"],
        "Context and generation share a vocabulary / continue-the-passage",
        bloom="explain", difficulty=3, concept_id="c-decoder-only",
        source_file="06_textgen.ipynb", source_cell=3,
        explanation="Passage fed directly into the decoder.",
    ),
    _mc(
        "Which is listed as a CodeGen pitfall?",
        ["It cannot emit comments", "Overgeneration after the requested function", "It only works on Java", "It requires Flan prefixes"],
        "Overgeneration after the requested function",
        bloom="recall", difficulty=2, concept_id="c-codegen",
        source_file="06_textgen.ipynb", source_cell=16,
        explanation="Also misinterpret, assume externals, go off track.",
    ),
    _mc(
        "Llama-2-70B is said to occupy roughly how much memory unquantized?",
        ["13 GB", "69 GB", "~135 GB", "2 GB"],
        "~135 GB",
        bloom="recall", difficulty=2, concept_id="c-quant",
        source_file="06_textgen.ipynb", source_cell=19,
        explanation="8-bit ~69GB; conversion does not delete the original from memory.",
    ),
    _mc(
        "GPTQ versus standard integer quantization in the primer:",
        ["GPTQ never needs a forward pass", "GPTQ adapts rounding using typical inputs and needs unquantized forwards", "GPTQ only works on encoders", "GPTQ increases parameter count"],
        "GPTQ adapts rounding using typical inputs and needs unquantized forwards",
        bloom="compare", difficulty=4, concept_id="c-quant",
        source_file="06_textgen.ipynb", source_cell=19,
        misconception_id="m-gptq-no-forward",
        explanation="bitsandbytes can load/quantize without that forward.",
    ),
    _mc(
        "The Llama-2 chat template wraps user instructions with:",
        ["### Human:", "<s>[INST] ... [/INST]", "<|im_start|>", "translate English to French:"],
        "<s>[INST] ... [/INST]",
        bloom="recall", difficulty=2, concept_id="c-llama2",
        source_file="06_textgen.ipynb", source_cell=25,
        misconception_id="m-raw-llama-chat",
        explanation="SYS block inside <<SYS>> ... <</SYS>>.",
    ),
    _mc(
        "LangChain Chain is analogized to:",
        ["A CUDA kernel", "nn.Module, but dict-in dict-out", "A tokenizer", "pgvector"],
        "nn.Module, but dict-in dict-out",
        bloom="recall", difficulty=2, concept_id="c-chain",
        source_file="07_stateful_models.ipynb", source_cell=7,
        explanation="Compose smaller chains into larger ones.",
    ),
    _mc(
        "Why does a plain LLMChain fail 'What did I just ask you?'",
        ["Temperature is 0", "No memory / history injection", "Missing GPU", "Wrong tokenizer"],
        "No memory / history injection",
        bloom="diagnose", difficulty=3, concept_id="c-memory",
        source_file="07_stateful_models.ipynb", source_cell=26,
        misconception_id="m-llmchain-memory",
        explanation="ConversationChain + history variable required.",
    ),
    _mc(
        "Notebook 7's precise definition of an agent is:",
        ["Any prompt with a system message", "LLM system(s) executing in an event loop accumulating context until the loop ends", "A vector database", "A quantized checkpoint"],
        "LLM system(s) executing in an event loop accumulating context until the loop ends",
        bloom="recall", difficulty=3, concept_id="c-agent",
        source_file="07_stateful_models.ipynb", source_cell=39,
        misconception_id="m-rag-agent",
        explanation="Loop may end at user-facing Final Action or span the whole dialog.",
    ),
    _mc(
        "The assessment requires implementing at least how many of the five features?",
        ["1", "2", "3", "5"],
        "3",
        bloom="recall", difficulty=1, concept_id="c-assess",
        source_file="08_assessment.ipynb", source_cell=22,
        explanation="3/5 test cases.",
    ),
    _mc(
        "nicholasKluge/ToxicityModel returns:",
        ["toxicity directly in [0,1] with 1 = toxic", "reward where reward = 1 - toxicity", "28 emotion logits", "start and end spans"],
        "reward where reward = 1 - toxicity",
        bloom="recall", difficulty=3, concept_id="c-toxicity-reward",
        source_file="08_assessment.ipynb", source_cell=23,
        misconception_id="m-toxicity-sign",
        explanation="Explicit WARNING in the assessment notebook.",
    ),
    _mc(
        "Images for the assessment agent are assumed to appear as:",
        ["base64 only", "backtick-wrapped path with png/jpg/jpeg", "CLIP tokens", "Whisper timestamps"],
        "backtick-wrapped path with png/jpg/jpeg",
        bloom="apply", difficulty=3, concept_id="c-assess",
        source_file="08_assessment.ipynb", source_cell=22,
        explanation="split('`') tip; BLIP caption then respond.",
    ),
    _mc(
        "Which HuggingFace pipeline task is used first in notebook 1?",
        ["text-generation", "fill-mask", "automatic-speech-recognition", "zero-shot-classification"],
        "fill-mask",
        bloom="recall", difficulty=1, concept_id="c-bert-base",
        source_file="01_llm_intro.ipynb", source_cell=9,
        explanation="unmasker = pipeline('fill-mask', model='bert-base-uncased').",
    ),
]
for h in HAND:
    h["id"] = _qid("hand", h["stem"][:80])
    _add(h)


BLOOMS_CYCLE = [
    "recall", "explain", "apply", "diagnose", "compare", "architecture", "code",
]


def _concept_variants(c: dict) -> None:
    file = c["notebook_file"]
    cell = c.get("cell_index")
    cid = c["id"]
    name = c["name"]
    definition = c["definition"]
    eng = c["engineer"]

    _add(_q(
        id=_qid("def", cid),
        qtype="short", bloom="recall", difficulty=1, concept_id=cid,
        stem=f"In one sentence, what does this course mean by **{name}**?",
        answer=definition, explanation=definition,
        source_file=file, source_cell=cell,
    ))
    _add(_q(
        id=_qid("eng", cid),
        qtype="free", bloom="explain", difficulty=3, concept_id=cid,
        stem=f"Explain **{name}** as an engineer implementing the notebook (APIs, shapes, or failure modes).",
        answer=eng, explanation=eng,
        source_file=file, source_cell=cell,
    ))
    _add(_q(
        id=_qid("school", cid),
        qtype="free", bloom="explain", difficulty=2, concept_id=cid,
        stem=f"Give a Grade-12 analogy for **{name}** that stays faithful to the NVIDIA notebook.",
        answer=c["school"], explanation=c["school"],
        source_file=file, source_cell=cell,
    ))
    _add(_q(
        id=_qid("pred", cid),
        qtype="prediction", bloom="predict", difficulty=3, concept_id=cid,
        stem=(
            f"Before running a twin, predict one observable if **{name}** is mis-applied "
            f"(wrong head, wrong template, or wrong memory)."
        ),
        answer="Learner-specific; compare to twin SIMULATED_RESULT after locking prediction.",
        explanation="Active lesson: predictions are stored before reveal.",
        source_file=file, source_cell=cell,
    ))
    distractors = [x["name"] for x in CONCEPTS if x["id"] != cid][:3]
    while len(distractors) < 3:
        distractors.append("KEDA autoscaling")
    _add(_mc(
        f"Which concept is defined as: “{definition[:180]}”?",
        [name] + distractors,
        name,
        bloom="recall", difficulty=2, concept_id=cid,
        source_file=file, source_cell=cell,
        explanation=definition,
        id=_qid("which", cid),
    ))
    _add(_q(
        id=_qid("code", cid),
        qtype="code", bloom="code", difficulty=3, concept_id=cid,
        stem=(
            f"You open `{file}` around cell {cell}. Which API or tensor would you inspect to verify **{name}**? "
            "Do not execute the cell."
        ),
        answer=eng,
        explanation="Notebook code is educational content; academy never auto-executes it.",
        source_file=file, source_cell=cell,
    ))
    _add(_q(
        id=_qid("arch", cid),
        qtype="architecture", bloom="architecture", difficulty=4, concept_id=cid,
        stem=f"Place **{name}** in the data path (pipeline, encoder, decoder, multimodal, or orchestration). Justify from `{file}`.",
        answer=c["cluster"] + " — " + eng,
        explanation=c["research"],
        source_file=file, source_cell=cell,
    ))
    _add(_q(
        id=_qid("trouble", cid),
        qtype="troubleshooting", bloom="diagnose", difficulty=4, concept_id=cid,
        stem=f"A teammate’s system misbehaves around **{name}**. What distinction from `{file}` would you check first?",
        answer=c.get("research") or eng,
        explanation="Diagnose using course distinctions, not internet rumors.",
        source_file=file, source_cell=cell,
    ))
    _add(_q(
        id=_qid("apply", cid),
        qtype="free", bloom="apply", difficulty=3, concept_id=cid,
        stem=f"Name a product behavior you would implement with **{name}** using only tools introduced by `{file}`.",
        answer=eng,
        explanation="Application credit requires a concrete mapping, not a slogan.",
        source_file=file, source_cell=cell,
    ))


for c in CONCEPTS:
    _concept_variants(c)


for m in MISCONCEPTIONS:
    _add(_q(
        id=_qid("misc", m["id"]),
        qtype="compare", bloom="compare", difficulty=3,
        concept_id=None, misconception_id=m["id"],
        stem=f"Contrast **{m['left']}** vs **{m['right']}**: {m['title']}. What do people mix up, and what is the missing distinction?",
        answer=m["distinction"],
        explanation=m["confusion"] + " → " + m["distinction"],
        source_file=m["source_file"], source_cell=m.get("source_cell"),
    ))
    _add(_mc(
        f"What is the missing distinction for: {m['title']}?",
        [m["distinction"], m["confusion"], "They are identical in this course", "Neither appears in the notebooks"],
        m["distinction"],
        bloom="diagnose", difficulty=3, misconception_id=m["id"],
        source_file=m["source_file"], source_cell=m.get("source_cell"),
        explanation=m["remediation"],
        id=_qid("misc-mc", m["id"]),
    ))
    _add(_q(
        id=_qid("whywrong", m["id"]),
        qtype="explain_back", bloom="explain", difficulty=4, misconception_id=m["id"],
        stem=f"A learner answered as if {m['confusion']} Teach back the correction using `{m['source_file']}`.",
        answer=m["distinction"],
        explanation=m["remediation"],
        source_file=m["source_file"], source_cell=m.get("source_cell"),
    ))


CODE_SNIPPETS = [
    ("01_llm_intro.ipynb", 9, "fill-mask", "pipeline('fill-mask', model='bert-base-uncased')",
     "Loads BERT MLM as a string-in human-out unmasker."),
    ("01_llm_intro.ipynb", 13, "MyMlmPipeline", "class MyMlmPipeline(FillMaskPipeline)",
     "Subclass to print preprocess/forward tensors."),
    ("02_llm_intake.ipynb", 4, "preprocess", "inputs = self.tokenizer(string, return_tensors='pt')",
     "Tokenizer produces the tensor dict."),
    ("02_llm_intake.ipynb", 12, "word-emb", "model.bert.embeddings.word_embeddings(tokens)",
     "Lookup 768-d word vectors; course drops CLS/SEP for illustration."),
    ("02_llm_intake.ipynb", 18, "pos", "position_embeddings(torch.arange(len(tokens)))",
     "Positions are indices, not token ids."),
    ("03_encoder_task.ipynb", 8, "qa", "pipeline('question-answering', model='deepset/roberta-base-squad2')",
     "Extractive span QA."),
    ("03_encoder_task.ipynb", 12, "emo", "pipeline('sentiment-analysis', 'SamLowe/roberta-base-go_emotions')",
     "Sequence classification with 28 emotion labels."),
    ("04_seq2seq.ipynb", 4, "t5", "pipeline('translation_en_to_fr', model='t5-base')",
     "Seq2seq translation pipeline."),
    ("04_seq2seq.ipynb", 14, "t2t", "pipeline('text2text-generation', model='t5-base')",
     "Exposes the instruction prefix."),
    ("04_seq2seq.ipynb", 26, "flan", "pipeline('text2text-generation', model='google/flan-t5-large')",
     "Instruction-tuned T5."),
    ("05_multimodal.ipynb", 9, "asr", "pipeline('automatic-speech-recognition', model=model_name)",
     "Whisper ASR pipeline."),
    ("05_multimodal.ipynb", 23, "vit", "pipeline('image-to-text', model='nlpconnect/vit-gpt2-image-captioning')",
     "ViT encoder + GPT-2 decoder captions."),
    ("05_multimodal.ipynb", 36, "clip", "model.get_text_features / get_image_features",
     "Dual-encoder CLIP features."),
    ("06_textgen.ipynb", 6, "gpt2", "pipeline('text-generation', model='gpt2')",
     "Decoder-only generation."),
    ("06_textgen.ipynb", 20, "llama", "TheBloke/Llama-2-13B-chat-GPTQ",
     "Prequantized chat Llama for consumer GPUs."),
    ("07_stateful_models.ipynb", 8, "tchain", "TransformChain / SequentialChain",
     "Dict-in dict-out composition."),
    ("07_stateful_models.ipynb", 19, "prompt", "PromptTemplate.from_template(... INST ...)",
     "Llama-2 chat template as an f-string analog."),
    ("07_stateful_models.ipynb", 45, "agent", "initialize_agent(..., agent='zero-shot-react-description')",
     "ReAct zero-shot agent with tool descriptions."),
    ("08_assessment.ipynb", 9, "setparams", "class SetParams",
     "Context manager to tweak pipeline _forward_params."),
    ("08_assessment.ipynb", 23, "pipes", "img_pipe / emo_pipe / zsc_pipe / tox_pipe",
     "Assessment helper models including inverted toxicity."),
]
for file, cell, tag, snippet, why in CODE_SNIPPETS:
    _add(_q(
        id=_qid("snip", tag),
        qtype="code", bloom="code", difficulty=3,
        stem=f"In `{file}` you see `{snippet}`. Why does this exist?",
        answer=why, explanation=why, source_file=file, source_cell=cell,
    ))
    _add(_q(
        id=_qid("fixme", tag),
        qtype="fill_fixme", bloom="apply", difficulty=4,
        stem=f"FIXME: a learner writes this without the course’s safety/template caveats: `{snippet}`. What should they double-check?",
        answer=why, explanation="Fill-the-FIXME from source, not from blogs.",
        source_file=file, source_cell=cell,
    ))
    _add(_q(
        id=_qid("seq", tag),
        qtype="sequence", bloom="architecture", difficulty=3,
        stem=f"Order the steps surrounding `{snippet}` in `{file}` (intake → compute → output or wrap).",
        answer=why, explanation=why, source_file=file, source_cell=cell,
    ))


ASSESS = [
    "Maintain a conversation buffer that at least tracks the speaker's name.",
    "If the message contains an image path in backticks, caption with BLIP and respond.",
    "If the message contains a triple backtick, generate code without emitting fences.",
    "Track user_toxicity from ToxicityModel remembering reward = 1 - toxicity.",
    "Track user_emotion via go_emotions (or similar) as a string state.",
]
for i, feat in enumerate(ASSESS, start=1):
    _add(_q(
        id=_qid("assess", i),
        qtype="architecture", bloom="design", difficulty=5, concept_id="c-assess",
        stem=f"Assessment feature {i}/5: {feat} Where in MyAgent.plan would you implement it, and which pipeline?",
        answer=feat, explanation="Pass 3/5; 13B GPTQ assumed by grader.",
        source_file="08_assessment.ipynb", source_cell=22,
    ))
    _add(_q(
        id=_qid("defend", i),
        qtype="free", bloom="defend", difficulty=6, concept_id="c-assess",
        stem=f"Defend including or skipping this feature under a 13B latency budget: {feat}",
        answer="Prefer cheap classifiers (emotion/toxicity) before extra large generations.",
        explanation="Notebook tip: limit generation; use preloaded HF models.",
        source_file="08_assessment.ipynb", source_cell=22,
    ))


# Extra application / metric-style items tied to twins (still course-grounded)
TWIN_Q = [
    ("pipeline-flow", "01_llm_intro.ipynb", 14, "If verbose preprocess prints input_ids, which evidence type is that print if you only imagined it?",
     "EXPECTED_RESULT until you import an ACTUAL_RUN"),
    ("quantization-memory", "06_textgen.ipynb", 19, "Self-quantizing 70B to 8-bit: why can peak RAM exceed the 69GB int8 footprint?",
     "Conversion does not delete the original from memory."),
    ("seq2seq-t5", "04_seq2seq.ipynb", 18, "Decoder receives one new word at a time. What stored structure grows?",
     "past_key_values"),
    ("rag-agent", "07_stateful_models.ipynb", 39, "VectorStoreRetrieverMemory is closer to RAG or to a ReAct agent loop?",
     "RAG-like retrieval into context; not automatically an agent loop."),
    ("langchain-memory", "07_stateful_models.ipynb", 28, "ConversationChain ignores prompt partials. What must be in input_variables?",
     "history (and input)"),
]
for twin, file, cell, stem, ans in TWIN_Q:
    _add(_q(
        id=_qid("twinq", twin, stem[:40]),
        qtype="troubleshooting", bloom="diagnose", difficulty=4,
        stem=stem + f" (twin `{twin}`)",
        answer=ans, explanation=ans, source_file=file, source_cell=cell,
    ))


# Interleave comparison pairs from related concepts
PAIRS = [
    ("c-t5", "c-flan"), ("c-t5", "c-decoder-only"), ("c-mlm", "c-qa-span"),
    ("c-qa-span", "c-seq-cls"), ("c-rag", "c-agent"), ("c-whisper", "c-clip"),
    ("c-vit", "c-blip"), ("c-quant", "c-llama2"), ("c-chain", "c-memory"),
    ("c-self-attention" if False else "c-attention", "c-cross-attn"),
    ("c-pipeline", "c-chain"), ("c-zeroshot", "c-icl"),
]
cmap = {c["id"]: c for c in CONCEPTS}
for a, b in PAIRS:
    if a not in cmap or b not in cmap:
        continue
    ca, cb = cmap[a], cmap[b]
    _add(_q(
        id=_qid("pair", a, b),
        qtype="compare", bloom="compare", difficulty=4,
        concept_id=a,
        stem=f"Compare **{ca['name']}** and **{cb['name']}** using only claims in `{ca['notebook_file']}` / `{cb['notebook_file']}`.",
        answer=f"{ca['engineer']} vs {cb['engineer']}",
        explanation="Do not import inference-at-scale vocabulary.",
        source_file=ca["notebook_file"], source_cell=ca.get("cell_index"),
    ))


def all_questions() -> list[dict]:
    # Dedup near-identical stems
    seen: set[str] = set()
    out: list[dict] = []
    for q in QUESTIONS:
        key = q["stem"].strip().lower()[:240]
        if key in seen:
            continue
        seen.add(key)
        if "id" not in q:
            q["id"] = _qid("auto", key)
        out.append(q)
    return out
