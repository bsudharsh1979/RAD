"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";
import Link from "next/link";
import { notebookHref } from "@/lib/paths";

export default function ReviewPage() {
  const [data, setData] = useState<any>(null);
  const [i, setI] = useState(0);
  const [given, setGiven] = useState("");
  const [fb, setFb] = useState<any>(null);
  useEffect(() => {
    api("/review").then(setData);
  }, []);
  if (!data) return <p>Loading reviews…</p>;
  const qs = data.questions || [];
  const q = qs[i];
  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Reviews due today</h1>
      <p style={{ color: "var(--muted)" }}>
        {data.due} FSRS items are due. Cards are generated from misses, weak concepts, and misconceptions.
      </p>
      {qs.length === 0 && (
        <p>
          Nothing due.{" "}
          <Link className="text-[#76b900]" href="/practice?mode=diagnostic">
            Take a diagnostic
          </Link>{" "}
          to schedule reviews.
        </p>
      )}
      {q && (
        <div className="panel space-y-3 p-4">
          <EvidenceBadge type={q.evidence_type} />
          <p>
            {i + 1} / {qs.length}
          </p>
          <p className="text-lg">{q.stem}</p>
          {q.options ? (
            <ul className="space-y-2">
              {q.options.map((o: string) => (
                <li key={o}>
                  <button className={`w-full rounded border px-3 py-2 text-left ${given === o ? "border-[#76b900]" : ""}`} style={{ borderColor: given === o ? "#76b900" : "var(--line)" }} onClick={() => setGiven(o)}>
                    {o}
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <textarea className="field" value={given} onChange={(e) => setGiven(e.target.value)} />
          )}
          <button
            className="rounded bg-[#76b900] px-4 py-2 text-black"
            onClick={async () => {
              const r: any = await api("/questions/attempt", { method: "POST", body: JSON.stringify({ question_id: q.id, given }) });
              setFb(r.feedback);
              if (r.correct) setTimeout(() => { setI(i + 1); setGiven(""); setFb(null); }, 600);
            }}
          >
            Submit
          </button>
          {fb && (
            <div className="text-sm">
              <p>{fb.socratic ? "Try again before the full reveal." : fb.simple_correction}</p>
              <Link className="text-[#76b900]" href={notebookHref(q.source?.file, q.source?.cell_index)}>
                View source
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
