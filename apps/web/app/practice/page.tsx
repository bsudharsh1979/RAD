"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";
import { notebookHref } from "@/lib/paths";

function PracticeInner() {
  const sp = useSearchParams();
  const mode = sp.get("mode");
  const concept = sp.get("concept") || undefined;
  const [qs, setQs] = useState<any[] | null>(null);
  const [i, setI] = useState(0);
  const [given, setGiven] = useState("");
  const [fb, setFb] = useState<any>(null);
  const [correctN, setCorrectN] = useState(0);
  const [summary, setSummary] = useState<any>(null);

  useEffect(() => {
    const url = mode === "diagnostic" ? "/diagnostic" : `/questions?limit=15${concept ? `&concept_id=${concept}` : ""}`;
    api<any>(url).then((r) => {
      setQs(r.questions || r);
      setI(0);
      setFb(null);
      setGiven("");
    });
  }, [mode, concept]);

  useEffect(() => {
    if (qs && i >= qs.length && mode === "diagnostic" && !summary) {
      api("/diagnostic/complete", {
        method: "POST",
        body: JSON.stringify({ answered: qs.length, correct: correctN }),
      }).then(setSummary);
    }
  }, [qs, i, mode, summary, correctN]);

  if (!qs) return <p>Loading practice…</p>;
  if (!qs.length) return <p>No sourced questions for this filter.</p>;

  if (i >= qs.length) {
    return (
      <div className="mx-auto max-w-2xl space-y-4">
        <h1 className="text-3xl">{mode === "diagnostic" ? "Diagnostic complete" : "Practice complete"}</h1>
        <p>
          You answered {qs.length} items · {correctN} marked correct on first reveal path.
        </p>
        {summary?.plan && (
          <div className="panel p-4">
            <h2 className="text-lg">Recommended next 30 minutes</h2>
            <ul className="mt-2 space-y-1">
              {summary.plan.map((p: any) => (
                <li key={p.title}>
                  <Link className="text-[#76b900]" href={p.href}>
                    {p.title} ({p.minutes} min)
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}
        {!!summary?.heatmap?.length && (
          <div className="panel p-4">
            <h2 className="text-lg">Mastery heatmap</h2>
            <div className="mt-2 grid grid-cols-2 gap-2">
              {summary.heatmap.map((h: any) => (
                <Link key={h.concept_id} href={`/learn?concept=${h.concept_id}`} className="text-xs">
                  {h.name || h.concept_id} · {Math.round(h.score * 100)}%
                </Link>
              ))}
            </div>
          </div>
        )}
        <Link className="inline-block rounded bg-[#76b900] px-4 py-2 text-black" href="/">
          Back to home
        </Link>
      </div>
    );
  }

  const q = qs[i];

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <h1 className="text-3xl">{mode === "diagnostic" ? "Adaptive diagnostic" : "Practice"}</h1>
      <p className="text-sm" style={{ color: "var(--muted)" }}>
        {i + 1} / {qs.length} · {q.bloom} · {q.qtype}
      </p>
      <EvidenceBadge type={q.evidence_type} />
      <p className="text-lg">{q.stem}</p>
      {q.options ? (
        <ul className="space-y-2">
          {q.options.map((o: string) => (
            <li key={o}>
              <button
                className={`w-full rounded border px-3 py-2 text-left ${given === o ? "border-[#76b900]" : ""}`}
                style={{ borderColor: given === o ? "#76b900" : "var(--line)" }}
                onClick={() => setGiven(o)}
              >
                {o}
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <textarea className="field" value={given} onChange={(e) => setGiven(e.target.value)} aria-label="Your answer" />
      )}
      <button
        className="rounded bg-[#76b900] px-4 py-2 text-black"
        onClick={async () => {
          const r: any = await api("/questions/attempt", {
            method: "POST",
            body: JSON.stringify({ question_id: q.id, given }),
          });
          setFb(r.feedback);
          if (r.correct) {
            setCorrectN((n) => n + 1);
            setTimeout(() => {
              setI((x) => x + 1);
              setFb(null);
              setGiven("");
            }, 700);
          }
        }}
      >
        Submit
      </button>
      {fb && !fb.try_again && (
        <button className="ml-2 rounded border px-3 py-2" style={{ borderColor: "var(--line)" }} onClick={() => { setI(i + 1); setFb(null); setGiven(""); }}>
          Next
        </button>
      )}
      {fb && (
        <div className="panel space-y-2 p-4 text-sm">
          <h2>Why am I wrong?</h2>
          <p>
            <strong>Your answer:</strong> {String(fb.your_answer)}
          </p>
          <p>
            <strong>What this suggests you believe:</strong> {fb.what_this_suggests}
          </p>
          <p>
            <strong>The missing distinction:</strong>{" "}
            {fb.socratic ? "Try once more — full reveal after a retry on MCQ." : fb.missing_distinction}
          </p>
          <p>
            <strong>Source evidence:</strong>{" "}
            <Link className="text-[#76b900]" href={notebookHref(fb.source_evidence?.file, fb.source_evidence?.cell_index)}>
              {fb.source_evidence?.file} cell {fb.source_evidence?.cell_index}
            </Link>
          </p>
          {!fb.try_again && (
            <p>
              <strong>Simple correction:</strong> {fb.simple_correction}
            </p>
          )}
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
