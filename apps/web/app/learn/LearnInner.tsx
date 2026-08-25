"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

export default function LearnInner() {
  const sp = useSearchParams();
  const cid = sp.get("concept");
  const [graph, setGraph] = useState<any>(null);
  const [detail, setDetail] = useState<any>(null);
  const [step, setStep] = useState(0);
  const [pred, setPred] = useState("");

  useEffect(() => {
    api("/concepts").then(setGraph);
  }, []);
  useEffect(() => {
    if (cid) api(`/concepts/${cid}`).then(setDetail);
    else setDetail(null);
  }, [cid]);

  const current = useMemo(() => {
    if (detail) return detail.concept;
    return graph?.nodes?.[0];
  }, [detail, graph]);

  if (!graph) return <p>Loading lessons…</p>;
  const steps = detail?.lesson || [
    { name: "EXPLAIN" },
    { name: "VISUALIZE" },
    { name: "PREDICT" },
    { name: "EXPERIMENT" },
    { name: "OBSERVE" },
    { name: "EXPLAIN_BACK" },
    { name: "DIAGNOSE" },
    { name: "PRACTICE" },
    { name: "MASTERY_UPDATE" },
  ];
  const st = steps[step]?.name || "EXPLAIN";

  return (
    <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
      <aside className="panel max-h-[80vh] overflow-auto p-3">
        <h2 className="mb-2 text-sm uppercase tracking-wide text-[#9aa89a]">Concepts</h2>
        {graph.nodes.map((n: any) => (
          <Link
            key={n.id}
            href={`/learn?concept=${n.id}`}
            className={`block rounded px-2 py-1 text-sm ${cid === n.id ? "bg-[#1c2618] text-[#76b900]" : "hover:bg-[#171c18]"}`}
          >
            {n.name}
          </Link>
        ))}
      </aside>
      {current && (
        <article className="space-y-4">
          <EvidenceBadge type="COURSE_SOURCE" />
          <h1 className="text-3xl">{current.name}</h1>
          <p className="text-[#9aa89a]">{current.definition}</p>
          <div className="flex flex-wrap gap-2 text-sm">
            {steps.map((s: any, i: number) => (
              <button
                key={s.name}
                className={`rounded-full px-3 py-1 ${i === step ? "bg-[#76b900] text-black" : "bg-[#1c2618]"}`}
                onClick={() => setStep(i)}
              >
                {s.name}
              </button>
            ))}
          </div>
          <div className="panel p-5 space-y-3">
            {st === "EXPLAIN" && (
              <>
                <h3>School</h3>
                <p>{detail?.concept?.school || current.school}</p>
                <h3>Engineer</h3>
                <p>{detail?.concept?.engineer || current.engineer}</p>
                <h3>Research</h3>
                <p>{detail?.concept?.research || current.research}</p>
              </>
            )}
            {st === "VISUALIZE" && (
              <p>
                Open the{" "}
                <Link className="text-[#76b900]" href={`/twins/${current.twin_id || "pipeline-flow"}`}>
                  digital twin
                </Link>{" "}
                and source{" "}
                <Link className="text-[#76b900]" href={`/notebooks/${current.notebook_file}`}>
                  {current.notebook_file} · cell {current.cell_index}
                </Link>
                .
              </p>
            )}
            {st === "PREDICT" && (
              <div>
                <p className="mb-2">Lock a prediction before simulated metrics are treated as observed.</p>
                <textarea className="w-full rounded bg-[#0b0d0c] p-2" value={pred} onChange={(e) => setPred(e.target.value)} />
                <button
                  className="mt-2 rounded bg-[#76b900] px-3 py-1 text-black"
                  onClick={async () => {
                    await api("/twins/predict", {
                      method: "POST",
                      body: JSON.stringify({
                        twin_id: current.twin_id || "pipeline-flow",
                        prompt: "lesson",
                        predicted: { note: pred },
                      }),
                    });
                    setStep(Math.min(step + 1, steps.length - 1));
                  }}
                >
                  Lock prediction
                </button>
              </div>
            )}
            {st === "EXPERIMENT" && (
              <Link className="text-[#76b900]" href={`/twins/${current.twin_id || "pipeline-flow"}`}>
                Run the twin (SIMULATED_RESULT)
              </Link>
            )}
            {st === "OBSERVE" && <p>Compare your locked prediction to the twin. Simulations are never ACTUAL_RUN.</p>}
            {st === "EXPLAIN_BACK" && <Teach conceptId={current.id} />}
            {st === "DIAGNOSE" && (
              <Link href="/practice" className="text-[#76b900]">
                Practice misconception items
              </Link>
            )}
            {st === "PRACTICE" && (
              <Link href={`/practice?concept=${current.id}`} className="text-[#76b900]">
                Open sourced questions
              </Link>
            )}
            {st === "MASTERY_UPDATE" && <p>Viewing is not mastery. Quiz, predict, and teach-back update scores.</p>}
          </div>
        </article>
      )}
    </div>
  );
}

function Teach({ conceptId }: { conceptId: string }) {
  const [t, setT] = useState("");
  const [r, setR] = useState<any>(null);
  return (
    <div>
      <textarea className="w-full rounded bg-[#0b0d0c] p-2" placeholder="Let me explain…" value={t} onChange={(e) => setT(e.target.value)} />
      <button
        className="mt-2 rounded bg-[#76b900] px-3 py-1 text-black"
        onClick={async () =>
          setR(await api("/teachback", { method: "POST", body: JSON.stringify({ concept_id: conceptId, transcript: t }) }))
        }
      >
        Submit teach-back
      </button>
      {r && <pre className="mt-3 overflow-auto text-xs text-[#9aa89a]">{JSON.stringify(r, null, 2)}</pre>}
    </div>
  );
}
