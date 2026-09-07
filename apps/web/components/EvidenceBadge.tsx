const STYLES: Record<string, string> = {
  COURSE_SOURCE: "bg-sky-950 text-sky-200 border-sky-700",
  EXPECTED_RESULT: "bg-amber-950 text-amber-200 border-amber-700",
  SIMULATED_RESULT: "bg-violet-950 text-violet-200 border-violet-700",
  ACTUAL_RUN: "bg-emerald-950 text-emerald-200 border-emerald-700",
  TUTOR_INTERPRETATION: "bg-zinc-800 text-zinc-200 border-zinc-600",
  EXTERNAL_RESEARCH: "bg-orange-950 text-orange-200 border-orange-700",
};

const LABELS: Record<string, string> = {
  COURSE_SOURCE: "🔵 NVIDIA COURSE SOURCE",
  EXPECTED_RESULT: "🟡 EXPECTED RESULT",
  SIMULATED_RESULT: "🟣 SIMULATION",
  ACTUAL_RUN: "🟢 ACTUAL RUN",
  TUTOR_INTERPRETATION: "⚪ TUTOR INTERPRETATION",
  EXTERNAL_RESEARCH: "🟠 EXTERNAL RESEARCH",
};

export function EvidenceBadge({ type }: { type?: string }) {
  const t = type || "TUTOR_INTERPRETATION";
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium tracking-wide ${STYLES[t] || STYLES.TUTOR_INTERPRETATION}`}
    >
      {LABELS[t] || t}
    </span>
  );
}
