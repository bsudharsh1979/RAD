"use client";

export function TwinViz({ scenario, params, state }: { scenario: string; params: any; state: any }) {
  const util = Math.min(1, Number(state?.instruction_following_qualitative || state?.caption_quality_qualitative || state?.diversity_qualitative || params.seq_len / 128 || 0.4));
  const stages =
    state?.stages ||
    (scenario === "seq2seq-t5"
      ? ["encoder", "cross-attn", "decoder", "</s>"]
      : scenario === "rag-agent"
        ? ["thought", "action", "observation", "final"]
        : ["input", "reason", "output"]);
  return (
    <div className="panel p-4" role="img" aria-label={`Digital twin ${scenario}`}>
      <svg viewBox="0 0 640 200" className="h-48 w-full" aria-hidden="true">
        {stages.map((s: string, i: number) => {
          const x = 40 + i * (560 / Math.max(stages.length - 1, 1));
          return (
            <g key={s}>
              {i < stages.length - 1 && <line x1={x + 18} y1={90} x2={x + 560 / Math.max(stages.length - 1, 1) - 18} y2={90} stroke="#76b900" strokeWidth="2" />}
              <rect x={x - 30} y={60} width={60} height={60} rx="8" fill="#1c2618" stroke="#76b900" />
              <text x={x} y={94} textAnchor="middle" fill="#e8eee6" fontSize="10">
                {s.slice(0, 10)}
              </text>
            </g>
          );
        })}
        <rect x={40} y={150} width={560 * util} height={12} fill="#76b900" />
        <rect x={40} y={150} width={560} height={12} fill="none" stroke="#2a322c" />
      </svg>
      <p className="text-xs text-[#9aa89a]">
        Educational animation of {scenario}. Bar is a qualitative indicator, not a GPU measurement.
      </p>
    </div>
  );
}
