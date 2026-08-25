"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

function PracticeInner() {
  const sp = useSearchParams();
  const mode = sp.get("mode");
  const concept = sp.get("concept") || undefined;
  const [qs, setQs] = useState<any[]>([]);
  const [i, setI] = useState(0);
  const [given, setGiven] = useState("");
  const [fb, setFb] = useState<any>(null);

  useEffect(() => {
    const url = mode === "diagnostic" ? "/diagnostic" : `/questions?limit=15${concept ? `&concept_id=${concept}` : ""}`;
    api<any>(url).then((r) => setQs(r.questions || r));
  }, [mode, concept]);

  const q = qs[i];
  if (!q) return <p>Loading practice…</p>;

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <h1 className="text-3xl">{mode === "diagnostic" ? "Adaptive diagnostic" : "Practice"}</h1>
      <p className="text-sm text-[#9aa89a]">
        {i + 1} / {qs.length} · {q.bloom} · {q.qtype}
      </p>
      <EvidenceBadge type={q.evidence_type} />
      <p className="text-lg">{q.stem}</p>
      {q.options ? (
        <ul className="space-y-2">
          {q.options.map((o: string) => (
            <li key={o}>
              <button className={`w-full rounded border px-3 py-2 text-left ${given === o ? "border-[#76b900]" : "border-[#2a322c]"}`} onClick={() => setGiven(o)}>
                {o}
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <textarea className="w-full rounded bg-[#141816] p-2" value={given} onChange={(e) => setGiven(e.target.value)} />
      )}
      <button
        className="rounded bg-[#76b900] px-4 py-2 text-black"
        onClick={async () => {
          const r: any = await api("/questions/attempt", {
            method: "POST",
            body: JSON.stringify({ question_id: q.id, given }),
          });
          setFb(r.feedback);
          if (r.correct) setTimeout(() => { setI(i + 1); setFb(null); setGiven(""); }, 600);
        }}
      >
        Submit
      </button>
      {fb && (
        <div className="panel space-y-2 p-4 text-sm">
          <h2>Why am I wrong?</h2>
          <p><strong>Your answer:</strong> {String(fb.your_answer)}</p>
          <p><strong>What this suggests you believe:</strong> {fb.what_this_suggests}</p>
          <p><strong>The missing distinction:</strong> {fb.socratic ? "Try once more — full reveal after a retry on MCQ." : fb.missing_distinction}</p>
          <p>
            <strong>Source evidence:</strong> {fb.source_evidence?.file} cell {fb.source_evidence?.cell_index}
          </p>
          {!fb.try_again && <p><strong>Simple correction:</strong> {fb.simple_correction}</p>}
          {fb.try_again && <p className="text-[#76b900]">Try again</p>}
        </div>
      )}
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<p>Loading…</p>}>
      <PracticeInner />
    </Suspense>
  );
}
