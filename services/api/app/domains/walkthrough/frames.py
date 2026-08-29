"""Curated lecture frames in our own words. Not NVIDIA-affiliated copy."""

from __future__ import annotations

# Each notebook: big_idea, simple_model, expert_model, game_plan, one_thing,
# concepts[{id,name}], stages[{title, start, end, crux_simple, crux_expert}]
# Stages MUST cover 0..n_cells-1 via ranges.

FRAMES: dict[str, dict] = {
    "01_llm_intro.ipynb": {
        "title": "Getting started with large language models",
        "n_cells": 25,
        "big_idea": {
            "hook": "A HuggingFace pipeline feels like magic: type a sentence, get a filled blank.",
            "stake": "If you treat that magic as the model, you cannot debug RAM, licenses, or wrong outputs in production.",
        },
        "simple_model": (
            "Think of a restaurant. You speak a sentence. A waiter writes a ticket. The kitchen cooks. "
            "A plate comes back in words you can eat. The waiter plus kitchen plus plating is the pipeline. "
            "The kitchen alone is the model. BERT is just the first kitchen we visit."
        ),
        "expert_model": (
            "FillMaskPipeline is preprocess via tokenizer, a forward pass of bert-base-uncased, then task-specific "
            "postprocess. Tensors never surface to the typical caller. GPU RAM, not host RAM, must hold weights "
            "for accelerated inference. This academy never executes those loads."
        ),
        "game_plan": "Meet HuggingFace, peel a fill-mask pipeline, then ask why GPU memory still matters.",
        "one_thing": "A pipeline is tokenizer plus model plus postprocess — not the neural net itself.",
        "concepts": ["c-pipeline", "c-tokenizer", "c-bert-base", "c-gpu-ram"],
        "stages": [
            {"title": "Why language models now", "start": 0, "end": 6, "crux_simple": "Vision already reused big pretrained nets. Language is the next messy input.", "crux_expert": "The notebook frames language combinatorics like a 200 by 200 by 3 image and defers tractability to pretrained LLMs."},
            {"title": "HuggingFace and transformers", "start": 7, "end": 12, "crux_simple": "HuggingFace is the library of ready-made language models.", "crux_expert": "transformers is the package; HuggingFace is the catalog plus community. Licenses live in a missing extras notebook."},
            {"title": "Peel the fill-mask pipeline", "start": 13, "end": 18, "crux_simple": "Type a sentence with a blank. The pipeline hides the math.", "crux_expert": "FillMaskPipeline equals tokenizer preprocess, model forward, task postprocess."},
            {"title": "Compute and wrap-up", "start": 19, "end": 24, "crux_simple": "The graphics card has its own suitcase of memory.", "crux_expert": "Host RAM can hold a huge checkpoint; GPU RAM must hold weights for CUDA acceleration."},
        ],
    },
    "02_llm_intake.ipynb": {
        "title": "How a model takes in language",
        "n_cells": 36,
        "big_idea": {
            "hook": "Before attention, there are only ID numbers and three lookup tables.",
            "stake": "If you concatenate those tables instead of adding them, every later shape is wrong.",
        },
        "simple_model": (
            "Each word-brick gets a personality vector. Each seat in the sentence gets a position vector. "
            "If there are two sentences, each brick gets a team sticker. BERT adds those three lists — it does not glue them end to end."
        ),
        "expert_model": (
            "input_ids index Embedding of 30522 by 768. Positions are a learned Embedding of 512 by 768, not sinusoids. "
            "token_type_ids mark sentence A versus B. The three vectors add in 768-d, then LayerNorm. "
            "Self-attention is 12 heads of 64-d, Q K V from the same sequence."
        ),
        "game_plan": "Tokens, then the three embeddings, then multi-head self-attention.",
        "one_thing": "BERT combines word, position, and type by addition in 768 dimensions.",
        "concepts": ["c-token", "c-word-emb", "c-pos-emb", "c-attention"],
        "stages": [
            {"title": "Tokens and IDs", "start": 0, "end": 8, "crux_simple": "A token is a brick, not always a whole English word.", "crux_expert": "input_ids are the primary intake; token_type_ids and attention_mask are extra flags."},
            {"title": "Three embedding tables", "start": 9, "end": 20, "crux_simple": "Meaning, seat number, and team sticker each have a table.", "crux_expert": "Word table 30522 by 768; positions 512 learned slots; types two rows."},
            {"title": "Add, do not concat", "start": 21, "end": 26, "crux_simple": "The three vectors are poured into the same 768 cup.", "crux_expert": "HuggingFace BERT embeddings forward adds then LayerNorm. Concatenation to 2304 is the common bug."},
            {"title": "Self-attention", "start": 27, "end": 35, "crux_simple": "Each brick looks at the others and decides who matters.", "crux_expert": "Softmax of Q K transpose over square root d_k, times V. Residuals keep token identity."},
        ],
    },
    "03_encoder_task.ipynb": {
        "title": "What you attach on top of an encoder",
        "n_cells": 26,
        "big_idea": {
            "hook": "The encoder body is reused. The head changes the job.",
            "stake": "Pick the wrong head and you ask BERT to write a novel it cannot write.",
        },
        "simple_model": (
            "The encoder is a reader. A fill-in-the-blank hat predicts a missing brick. "
            "A quiz hat points at a span already in the paragraph. A mood hat reads the first seat. "
            "Zero-shot asks the same reader the same question once per candidate label."
        ),
        "expert_model": (
            "MLM is n to vocab. Span QA is start and end logits over the context — answers must be substrings. "
            "Sequence classification typically pools index 0. Zero-shot MNLI-style models issue one entailment query per label."
        ),
        "game_plan": "Walk MLM, extractive QA, sequence class, then multi-query zero-shot.",
        "one_thing": "Encoders produce insights. Novel tokens need a decoder or a multi-query trick.",
        "concepts": ["c-mlm", "c-qa-span", "c-zeroshot"],
        "stages": [
            {"title": "Masked language modeling", "start": 0, "end": 6, "crux_simple": "Cover a brick, guess the brick.", "crux_expert": "Fill-mask still cannot emit tokens that are not in the vocabulary slot it scores."},
            {"title": "Span question answering", "start": 7, "end": 12, "crux_simple": "The answer must already be written in the paragraph.", "crux_expert": "deepset or roberta-base-squad2 start and end logits. Absent answers fail closed."},
            {"title": "Sequence classification", "start": 13, "end": 18, "crux_simple": "Read the first seat, name the mood.", "crux_expert": "go_emotions uses a pooled position, not a label per token."},
            {"title": "Zero-shot queries", "start": 19, "end": 25, "crux_simple": "Ask once per possible label.", "crux_expert": "Zero-shot means the label set was not fixed at train time, not that weights are random."},
        ],
    },
    "04_seq2seq.ipynb": {
        "title": "Encoder then decoder",
        "n_cells": 41,
        "big_idea": {
            "hook": "Readers cannot write new sentences. Writers can — one brick at a time.",
            "stake": "If you call vanilla T5 like a chatbot, you will blame the GPU for a training-recipe problem.",
        },
        "simple_model": (
            "First a librarian reads the whole request once and files notes. "
            "Then a writer looks at those notes and says the next word, then the next, until a stop sign. "
            "Flan is the writer who practiced following instructions. Vanilla T5 mostly practiced a short list of homework prefixes."
        ),
        "expert_model": (
            "T5 encoder runs once. Decoder steps equal output length. Cross-attention is n by m: queries from the decoder, keys and values from the encoder. "
            "past_key_values grow. Pig Latin is an expected fail from tokenization and semantics — the course says so. "
            "Instruction following is a Flan training result, not a guaranteed scale result."
        ),
        "game_plan": "See why encoders stall, meet T5, then compare Flan prompts.",
        "one_thing": "Encoder once, decoder many. Flan follows instructions; T5 memorizes prefixes.",
        "concepts": ["c-t5", "c-cross-attn", "c-flan"],
        "stages": [
            {"title": "Why we need a decoder", "start": 0, "end": 8, "crux_simple": "A reader cannot invent a sentence that was never there.", "crux_expert": "Encoder tasks stay extractive or classificatory unless you add a generative head."},
            {"title": "T5 machinery", "start": 9, "end": 20, "crux_simple": "Read once, write many times, stop at the end mark.", "crux_expert": "Cross-attention lets output length differ from input length. First decoder step often starts from pad."},
            {"title": "Flan versus vanilla T5", "start": 21, "end": 30, "crux_simple": "Flan went to instruction school.", "crux_expert": "Larger T5 does not suddenly become a general chatbot. The notebook says the recipe is too shallow."},
            {"title": "Prompt experiments", "start": 31, "end": 40, "crux_simple": "How you ask changes the homework the model thinks it is doing.", "crux_expert": "Prefix-style prompts match T5 pretraining more than open chat turns."},
        ],
    },
    "05_multimodal.ipynb": {
        "title": "Sound and pictures as sequences",
        "n_cells": 43,
        "big_idea": {
            "hook": "If you can turn a wave or a photo into a line of bricks, the same writer can talk about it.",
            "stake": "Confusing CLIP with a captioner ships a retrieval model into a generation slot.",
        },
        "simple_model": (
            "Whisper turns sound into a picture of frequencies, then into bricks, then into words. "
            "Caption models cut a photo into patches like tiles on a floor. "
            "CLIP keeps two libraries — pictures and sentences — and checks whether they point at the same idea. CLIP does not write the caption."
        ),
        "expert_model": (
            "ASR stages: window, spectrogram, sequence, then cross-attend into a text decoder. "
            "ViT patchify is the 16 by 16 words paper. BLIP or ViT-GPT2 generate tokens. "
            "CLIP trains dual encoders so related image and text embeddings agree. Softmax over candidates is retrieval or zero-shot class, not generation."
        ),
        "game_plan": "Audio intake, image patches, then dual-encoder retrieval.",
        "one_thing": "Sequence-ify the modality, then either generate with cross-attention or align with CLIP.",
        "concepts": ["c-whisper", "c-clip"],
        "stages": [
            {"title": "Whisper intake", "start": 0, "end": 12, "crux_simple": "Sound becomes a comic strip of frequencies, then words.", "crux_expert": "Whisper-base is tens of millions of parameters; large-v2 is far larger. This repo stores no run outputs."},
            {"title": "Patches to captions", "start": 13, "end": 26, "crux_simple": "Cut the photo into tiles and let a writer describe them.", "crux_expert": "An image is worth 16 by 16 words. ViT-GPT2 is weaker than BLIP in the course's qualitative story."},
            {"title": "CLIP alignment", "start": 27, "end": 42, "crux_simple": "Two libraries, one idea. No new sentence is written.", "crux_expert": "Dual encoders plus a similarity head. Do not call this captioning."},
        ],
    },
    "06_textgen.ipynb": {
        "title": "Decoder-only chat and memory pressure",
        "n_cells": 45,
        "big_idea": {
            "hook": "When the prompt and the answer share a vocabulary, you can drop the librarian.",
            "stake": "A 70 billion parameter chat model in 16-bit needs on the order of 135 gigabytes. That is a data-center suitcase.",
        },
        "simple_model": (
            "GPT only looks left. It writes the next brick using what it already said. "
            "Temperature is how adventurous the dice are. "
            "Quantization packs the suitcase tighter. Smaller suitcases can still wrinkle the clothes. "
            "Llama chat expects a very specific greeting card, not a raw GPT-2 prompt."
        ),
        "expert_model": (
            "Causal decoder. Temperature and do_sample trade diversity for coherence qualitatively. "
            "Course numbers: 70B about 135 GB in FP16, about 69 GB in 8-bit. GPTQ needs an unquantized forward to produce; TheBloke checkpoints skip self-quantization. "
            "Llama-2-chat wants the INST SYS template. Assessment uses 13B GPTQ, not 70B."
        ),
        "game_plan": "Unidirectional generation, codegen failure modes, then quantization and chat templates.",
        "one_thing": "Decoder-only plus the right template, and bits are a memory trade — not a free quality win.",
        "concepts": ["c-decoder-only", "c-quant", "c-llama2"],
        "stages": [
            {"title": "GPT-style generation", "start": 0, "end": 10, "crux_simple": "The model only looks backward, then rolls the next word.", "crux_expert": "Unidirectional attention. Seed and temperature are sampling knobs, not measurements of a GPU here."},
            {"title": "Code models go off-track", "start": 11, "end": 18, "crux_simple": "A coding helper can keep talking after the function is done.", "crux_expert": "CodeGen overgenerates because training files did. Copilot is an API of several models, not one checkpoint."},
            {"title": "Quantization", "start": 19, "end": 30, "crux_simple": "Pack the weights smaller so they fit. Expect some wrinkles.", "crux_expert": "GPTQ versus bitsandbytes. Never claim 4-bit always wins accuracy."},
            {"title": "Llama chat template", "start": 31, "end": 44, "crux_simple": "This model expects a formal letter, not a sticky note.", "crux_expert": "s INST SYS format is part of the fine-tune. Raw completion is misuse."},
        ],
    },
    "07_stateful_models.ipynb": {
        "title": "Memory, retrieval, and agent loops",
        "n_cells": 56,
        "big_idea": {
            "hook": "A bare LLM forgets the last turn the moment the HTTP call ends.",
            "stake": "If you hand it a Python terminal, you handed it the keys to the building.",
        },
        "simple_model": (
            "A chain is a recipe card. Memory is a notepad you staple onto the next card. "
            "Retrieval is looking up a binder and pasting a page into the prompt. "
            "An agent is a fidgety intern who thinks, acts, looks, and repeats until they say they are done. "
            "Talking to the user can be one of those actions."
        ),
        "expert_model": (
            "LLMChain has no memory. ConversationBuffer injects history; summary memory is lossy. "
            "History must be in input_variables — partials on PromptTemplate can be invisible to ConversationChain. "
            "RAG injects environment text. Agents are event loops with a scratchpad. Python REPL is flagged dangerous. "
            "The assessment loop is dialog-spanning via Ask-For-Input."
        ),
        "game_plan": "Stateless chains, memory types, then RAG versus ReAct.",
        "one_thing": "Memory is not an agent. Retrieval is not an agent. An agent is the loop.",
        "concepts": ["c-memory", "c-rag", "c-agent"],
        "stages": [
            {"title": "Stateless chains", "start": 0, "end": 15, "crux_simple": "Two calls, two strangers, unless you keep a notepad.", "crux_expert": "LLMChain will not remember the first utterance."},
            {"title": "Memory modules", "start": 16, "end": 32, "crux_simple": "A buffer keeps everything. A summary forgets on purpose.", "crux_expert": "Put history in input_variables. Summary-buffer trades faithfulness for length."},
            {"title": "RAG versus agents", "start": 33, "end": 47, "crux_simple": "Looking up a page is not the same as deciding which tool to grab.", "crux_expert": "RAG injects text. ReAct grows a scratchpad until a final action."},
            {"title": "Dangerous tools", "start": 48, "end": 55, "crux_simple": "Do not give the intern a live Python terminal.", "crux_expert": "Notebook: Python REPL is a bad idea in practice. Prefer Ask-For-Input."},
        ],
    },
    "08_assessment.ipynb": {
        "title": "Build an agent that talks to the user",
        "n_cells": 34,
        "big_idea": {
            "hook": "The exam is not a quiz. It is a small product with a pass line of three features out of five.",
            "stake": "Using 70B or leaking a solution notebook misses the point — and the grader.",
        },
        "simple_model": (
            "You build a helper that can remember, see a picture, read a code fence, score rudeness, and name a feeling. "
            "You need any three. The rudeness meter is upside down: a high reward means low rudeness. "
            "The helper talks to you as if you were a tool."
        ),
        "expert_model": (
            "Pass when at least three of memory, image, code, toxicity, emotion work. "
            "Image trigger is a path in backticks. Code trigger is a fence. "
            "nicholasKluge ToxicityModel returns reward equals one minus toxicity. "
            "Grader assumes TheBloke Llama-2-13B-chat-GPTQ. This platform does not leak a completed solution."
        ),
        "game_plan": "Read the pass rule, pick features, defend the inverted reward and the 13B grader.",
        "one_thing": "Three of five features, reward equals one minus toxicity, 13B GPTQ, user as a tool.",
        "concepts": ["c-assess"],
        "stages": [
            {"title": "Rules and model pick", "start": 0, "end": 8, "crux_simple": "Thirteen billion is enough for the exam. Seventy is optional fun.", "crux_expert": "Section 8.1.1: use 13B GPTQ. Do not assume 70B."},
            {"title": "The five features", "start": 9, "end": 20, "crux_simple": "Memory, picture, code, rudeness, feeling — pick three.", "crux_expert": "Image syntax path.png in backticks. Code fence triple backtick."},
            {"title": "The event loop", "start": 21, "end": 33, "crux_simple": "The user is a tool the agent can ask.", "crux_expert": "Ask-For-Input Tool. ToxicityModel reward is inverted. No leaked solution here."},
        ],
    },
}


def frame_for(filename: str) -> dict | None:
    return FRAMES.get(filename)
