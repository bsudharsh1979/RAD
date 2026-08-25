"use client";

import type { ReactNode } from "react";

type Props = { scenario: string; params: Record<string, any>; state: any };

export function TwinViz({ scenario, params, state }: Props) {
  return (
    <div className="panel p-4" role="img" aria-label={`Digital twin ${scenario}`}>
      {scenario === "pipeline-flow" && <PipelineViz params={params} state={state} />}
      {scenario === "tokenizer-embeddings" && <EmbedViz params={params} state={state} />}
      {scenario === "attention-encoder" && <AttnViz params={params} state={state} />}
      {scenario === "encoder-heads" && <HeadsViz params={params} state={state} />}
      {scenario === "seq2seq-t5" && <T5Viz params={params} state={state} />}
      {scenario === "multimodal" && <MultiViz params={params} state={state} />}
      {scenario === "decoder-sampling" && <DecViz params={params} state={state} />}
      {scenario === "quantization-memory" && <QuantViz params={params} state={state} />}
      {scenario === "langchain-memory" && <MemViz params={params} state={state} />}
      {scenario === "rag-agent" && <RagViz params={params} state={state} />}
      {scenario === "assessment-agent" && <AssessViz params={params} state={state} />}
      {!KNOWN.has(scenario) && <Generic stages={state?.stages || ["input", "model", "output"]} />}
      <p className="mt-2 text-xs text-[color:var(--muted)]">
        Educational animation of {scenario}. Not a GPU measurement. Evidence: SIMULATED_RESULT until you import an
        ACTUAL_RUN.
      </p>
    </div>
  );
}

const KNOWN = new Set([
  "pipeline-flow",
  "tokenizer-embeddings",
  "attention-encoder",
  "encoder-heads",
  "seq2seq-t5",
  "multimodal",
  "decoder-sampling",
  "quantization-memory",
  "langchain-memory",
  "rag-agent",
  "assessment-agent",
]);

function Box({ x, y, w, h, label, fill = "#1c2618", accent = false }: any) {
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx="8" fill={fill} stroke={accent ? "#76b900" : "#4a5a48"} strokeWidth={accent ? 2 : 1} />
      <text x={x + w / 2} y={y + h / 2 + 4} textAnchor="middle" fill="#e8eee6" fontSize="11">
        {label}
      </text>
    </g>
  );
}

function Arrow({ x1, y1, x2, y2 }: { x1: number; y1: number; x2: number; y2: number }) {
  return <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#76b900" strokeWidth="2" markerEnd="url(#arrow)" />;
}

function Svg({ children, h = 220 }: { children: ReactNode; h?: number }) {
  return (
    <svg viewBox={`0 0 720 ${h}`} className="w-full" style={{ height: h }} aria-hidden="true">
      <defs>
        <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 Z" fill="#76b900" />
        </marker>
      </defs>
      {children}
    </svg>
  );
}

function Generic({ stages }: { stages: string[] }) {
  return (
    <Svg>
      {stages.map((s, i) => {
        const x = 30 + i * (680 / Math.max(stages.length, 1));
        return (
          <g key={s}>
            {i < stages.length - 1 && <Arrow x1={x + 70} y1={90} x2={x + 680 / stages.length - 10} y2={90} />}
            <Box x={x} y={55} w={90} h={70} label={String(s).slice(0, 14)} accent />
          </g>
        );
      })}
    </Svg>
  );
}

function PipelineViz({ params, state }: any) {
  const active = state ? ["human_string", "preprocess", "forward", "postprocess", "human_output"] : ["human_string"];
  const mask = String(params.text || "").includes("[MASK]");
  return (
    <div>
      <Svg>
        <Box x={10} y={50} w={110} h={70} label="string" accent={active.includes("human_string")} />
        <Arrow x1={125} y1={85} x2={155} y2={85} />
        <Box x={160} y={50} w={110} h={70} label="tokenizer" accent={active.includes("preprocess")} />
        <Arrow x1={275} y1={85} x2={305} y2={85} />
        <Box x={310} y={50} w={110} h={70} label="model" accent={active.includes("forward")} />
        <Arrow x1={425} y1={85} x2={455} y2={85} />
        <Box x={460} y={50} w={110} h={70} label="postprocess" accent={active.includes("postprocess")} />
        <Arrow x1={575} y1={85} x2={605} y2={85} />
        <Box x={610} y={50} w={100} h={70} label="output" accent={!!state} />
        <text x={360} y={160} textAnchor="middle" fill="#9aa89a" fontSize="12">
          FillMaskPipeline · tensors stay hidden · MASK {mask ? "present" : "missing"}
        </text>
        {state && (
          <text x={360} y={185} textAnchor="middle" fill="#76b900" fontSize="12">
            {state.preprocess_ms} + {state.forward_ms} + {state.postprocess_ms} ms (simulated)
          </text>
        )}
      </Svg>
    </div>
  );
}

function EmbedViz({ params, state }: any) {
  const seq = Number(params.seq_len || 12);
  const n = Math.min(12, seq);
  return (
    <Svg h={240}>
      {Array.from({ length: n }).map((_, i) => (
        <rect key={i} x={20 + i * 55} y={30} width={48} height={28} rx="4" fill="#1c2618" stroke="#76b900" />
      ))}
      <text x={20} y={78} fill="#9aa89a" fontSize="11">
        input_ids ({seq}) {seq > 512 ? "— over BERT 512 position table" : ""}
      </text>
      <Box x={40} y={100} w={180} h={50} label="Word 30522×768" accent />
      <Box x={270} y={100} w={180} h={50} label="Pos 512×768" accent />
      <Box x={500} y={100} w={180} h={50} label="Type 2×768" accent={!!params.sentence_pair} />
      <text x={360} y={180} textAnchor="middle" fill="#e8eee6" fontSize="12">
        embed = Word + Pos + Type (addition, not concat)
      </text>
      {state && (
        <text x={360} y={205} textAnchor="middle" fill="#76b900" fontSize="12">
          ~{state.embedding_bytes_f32} bytes f32 for this sequence (simulated)
        </text>
      )}
    </Svg>
  );
}

function AttnViz({ params, state }: any) {
  const seq = Math.min(12, Number(params.seq_len || 10));
  const residual = params.residual !== false;
  return (
    <Svg h={250}>
      <text x={20} y={24} fill="#9aa89a" fontSize="12">
        Q, K, V from the same sequence · 12 heads × 64-d → 768
      </text>
      {Array.from({ length: seq }).map((_, i) =>
        Array.from({ length: seq }).map((_, j) => (
          <rect
            key={`${i}-${j}`}
            x={40 + j * 14}
            y={40 + i * 10}
            width={12}
            height={8}
            fill={`rgba(118,185,0,${0.15 + ((i * 3 + j) % 7) / 14})`}
          />
        )),
      )}
      <Box x={280} y={50} w={90} h={40} label="Q" />
      <Box x={400} y={50} w={90} h={40} label="K" />
      <Box x={520} y={50} w={90} h={40} label="V" />
      <Box x={340} y={120} w={220} h={44} label="softmax(QKᵀ/√d) V" accent />
      <Box x={340} y={180} w={220} h={40} label={residual ? "residual + MLP 3072" : "no residual"} accent={residual} />
      {state && (
        <text x={40} y={200} fill="#76b900" fontSize="11">
          attn elems {state.attn_elems} · layers {state.layers}
        </text>
      )}
    </Svg>
  );
}

function HeadsViz({ params, state }: any) {
  const mode = String(params.mode || "mlm");
  const labels: Record<string, string[]> = {
    mlm: ["n tokens", "n × vocab"],
    qa: ["n tokens", "start/end logits"],
    sequence: ["CLS / pool", "n_classes"],
    zero_shot: ["n queries", "entailment each"],
  };
  const [a, b] = labels[mode] || labels.mlm;
  return (
    <Svg>
      <Box x={40} y={60} w={160} h={70} label="encoder n→n" accent />
      <Arrow x1={210} y1={95} x2={250} y2={95} />
      <Box x={260} y={60} w={160} h={70} label={a} />
      <Arrow x1={430} y1={95} x2={470} y2={95} />
      <Box x={480} y={60} w={180} h={70} label={b} accent />
      <text x={360} y={170} textAnchor="middle" fill="#9aa89a" fontSize="12">
        {state?.restriction || "Head changes granularity; body is reused."}
      </text>
      {mode === "qa" && (
        <text x={360} y={195} textAnchor="middle" fill="#76b900" fontSize="12">
          Answer must be a substring of context
        </text>
      )}
    </Svg>
  );
}

function T5Viz({ params, state }: any) {
  const osl = Number(params.output_tokens || 8);
  const model = String(params.model || "t5-base");
  const dots = Math.min(10, osl);
  return (
    <Svg h={240}>
      <Box x={40} y={40} w={200} h={70} label={`encoder ×1`} accent />
      <text x={140} y={130} textAnchor="middle" fill="#9aa89a" fontSize="11">
        ISL {params.input_tokens || 12}
      </text>
      <Arrow x1={250} y1={75} x2={310} y2={75} />
      <text x={270} y={60} fill="#76b900" fontSize="10">
        cross-attn
      </text>
      {Array.from({ length: dots }).map((_, i) => (
        <rect key={i} x={320 + i * 36} y={50} width={30} height={50} rx="4" fill="#1c2618" stroke="#76b900" />
      ))}
      <text x={500} y={130} fill="#9aa89a" fontSize="11">
        decoder × OSL ({osl}) then &lt;/s&gt;
      </text>
      <text x={360} y={170} textAnchor="middle" fill="#e8eee6" fontSize="12">
        {model} · Flan follows instructions; vanilla T5 is prefix-style
      </text>
      {state && (
        <text x={360} y={200} textAnchor="middle" fill="#76b900" fontSize="12">
          encoder_calls={state.encoder_calls} decoder_calls={state.decoder_calls} · pig latin expected fail
        </text>
      )}
    </Svg>
  );
}

function MultiViz({ params, state }: any) {
  const kind = String(params.kind || "whisper");
  return (
    <Svg>
      <Box x={30} y={50} w={140} h={70} label={kind === "whisper" ? "audio" : kind === "clip" ? "image|text" : "image"} accent />
      <Arrow x1={180} y1={85} x2={220} y2={85} />
      <Box x={230} y={50} w={160} h={70} label={kind === "clip" ? "dual encoders" : "seq encoder"} />
      <Arrow x1={400} y1={85} x2={440} y2={85} />
      <Box x={450} y={50} w={220} h={70} label={kind === "clip" ? "cosine / softmax" : "text decoder"} accent />
      <text x={360} y={160} textAnchor="middle" fill="#9aa89a" fontSize="12">
        {kind === "whisper"
          ? "Spectrogram frames → tokens (notebook Whisper)"
          : kind === "clip"
            ? "Related image/text embeddings agree"
            : "16×16 patches become tokens"}
      </text>
      {state && kind === "whisper" && (
        <text x={360} y={190} textAnchor="middle" fill="#76b900" fontSize="12">
          ~{state.spectrogram_frames} frames (simulated)
        </text>
      )}
    </Svg>
  );
}

function DecViz({ params, state }: any) {
  const temp = Number(params.temperature || 0.6);
  const w = Math.min(640, 80 + temp * 280);
  return (
    <Svg>
      <Box x={30} y={40} w={180} h={60} label="unidirectional" accent />
      <Arrow x1={220} y1={70} x2={260} y2={70} />
      <Box x={270} y={40} w={180} h={60} label={params.do_sample ? "sample" : "greedy"} />
      <Arrow x1={460} y1={70} x2={500} y2={70} />
      <Box x={510} y={40} w={180} h={60} label={params.chat_template ? "INST/SYS" : "raw GPT"} />
      <rect x={40} y={130} width={w} height={16} fill="#76b900" />
      <text x={40} y={170} fill="#9aa89a" fontSize="12">
        temperature {temp} · diversity vs coherence (qualitative bar, not measured)
      </text>
      {state && (
        <text x={40} y={195} fill="#76b900" fontSize="12">
          diversity {state.diversity_qualitative} · coherence {state.coherence_qualitative}
        </text>
      )}
    </Svg>
  );
}

function QuantViz({ params, state }: any) {
  const bits = Number(params.bits || 4);
  const gb = state?.approx_weight_gb || (Number(params.params_billion || 13) * bits) / 8;
  const w = Math.min(640, (gb / 140) * 640);
  return (
    <Svg h={230}>
      <text x={20} y={28} fill="#9aa89a" fontSize="12">
        Weight memory ≈ params × bytes/param (educational). Course: 70B FP16 ≈ 135 GB.
      </text>
      <rect x={20} y={50} width={640} height={28} fill="#1c2618" stroke="#2a322c" />
      <rect x={20} y={50} width={w} height={28} fill="#76b900" />
      <text x={20} y={100} fill="#e8eee6" fontSize="12">
        {bits}-bit · ~{Number(gb).toFixed(1)} GB simulated · GPU hint: {state?.suggested_gpu || "run to see"}
      </text>
      <Box x={20} y={120} w={200} h={50} label="naive quant" />
      <Box x={250} y={120} w={200} h={50} label="GPTQ (+forward)" accent={params.method === "gptq"} />
      <Box x={480} y={120} w={200} h={50} label="TheBloke GPTQ" accent />
      <text x={20} y={200} fill="#9aa89a" fontSize="12">
        Lower bits do not universally win accuracy.
      </text>
    </Svg>
  );
}

function MemViz({ params, state }: any) {
  const stored = Number(state?.stored_tokens || params.turns * params.tokens_per_turn || 320);
  const limit = Number(params.context_limit || 1024);
  const w = Math.min(640, (stored / Math.max(limit, 1)) * 640);
  return (
    <Svg>
      <Box x={20} y={40} w={140} h={50} label="LLMChain" />
      <Arrow x1={170} y1={65} x2={210} y2={65} />
      <Box x={220} y={40} w={160} h={50} label={String(params.mode || "buffer")} accent />
      <Arrow x1={390} y1={65} x2={430} y2={65} />
      <Box x={440} y={40} w={240} h={50} label={state?.overflow ? "OVERFLOW" : "fits"} accent={!!state?.overflow} />
      <rect x={20} y={120} width={640} height={18} fill="#1c2618" stroke="#2a322c" />
      <rect x={20} y={120} width={w} height={18} fill={state?.overflow ? "#e8b86d" : "#76b900"} />
      <text x={20} y={165} fill="#9aa89a" fontSize="12">
        stored {stored} / limit {limit}
        {state?.lossy ? " · summary is lossy" : ""}
      </text>
      <text x={20} y={190} fill="#e8eee6" fontSize="11">
        History must be in input_variables (notebook 7 gotcha)
      </text>
    </Svg>
  );
}

function RagViz({ params, state }: any) {
  const steps = Number(params.steps || 3);
  const danger = String(params.tool || "").toLowerCase().includes("python");
  return (
    <Svg h={240}>
      <Box x={20} y={40} w={120} h={50} label="thought" accent />
      <Arrow x1={145} y1={65} x2={175} y2={65} />
      <Box x={180} y={40} w={140} h={50} label={danger ? "Python REPL" : "tool"} fill={danger ? "#3a1c1c" : "#1c2618"} accent />
      <Arrow x1={325} y1={65} x2={355} y2={65} />
      <Box x={360} y={40} w={140} h={50} label="observation" />
      <Arrow x1={505} y1={65} x2={535} y2={65} />
      <Box x={540} y={40} w={150} h={50} label={params.loop === "dialog" ? "ask user" : "final"} accent />
      <text x={20} y={130} fill="#9aa89a" fontSize="12">
        ReAct scratchpad grows · {steps} steps · retrieved chunks {params.retrieved_chunks}
      </text>
      {danger && (
        <text x={20} y={160} fill="#e8b86d" fontSize="12">
          Course: Python REPL is a bad idea in practice
        </text>
      )}
      {state && (
        <text x={20} y={190} fill="#76b900" fontSize="12">
          grounded={String(state.grounded)} · assessment loop={String(state.assessment_loop)}
        </text>
      )}
    </Svg>
  );
}

function AssessViz({ params, state }: any) {
  const feats = ["memory", "image", "code", "toxicity", "emotion"];
  const n = feats.filter((f) => params[f]).length;
  const reward = state ? state.toxicity_reward : 1 - Number(params.user_toxicity || 0);
  return (
    <Svg h={240}>
      {feats.map((f, i) => (
        <Box key={f} x={20 + i * 140} y={40} w={130} h={50} label={f} accent={!!params[f]} />
      ))}
      <text x={20} y={120} fill="#e8eee6" fontSize="13">
        Implemented {state?.implemented_count ?? n} / 5 · pass ≥ 3 {state ? (state.passed ? "PASS (sim)" : "not yet") : ""}
      </text>
      <text x={20} y={150} fill="#9aa89a" fontSize="12">
        ToxicityModel reward = 1 − toxicity → {Number(reward).toFixed(2)} (simulated from slider)
      </text>
      <text x={20} y={180} fill="#9aa89a" fontSize="12">
        Grader: TheBloke/Llama-2-13B-chat-GPTQ · image syntax `path.png` · code fence ```
      </text>
    </Svg>
  );
}
