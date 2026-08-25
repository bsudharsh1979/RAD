"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { conceptHref } from "@/lib/paths";

export default function ProgressPage() {
  const [p, setP] = useState<any>(null);
  const [home, setHome] = useState<any>(null);
  const [notes, setNotes] = useState<any[]>([]);
  const [marks, setMarks] = useState<any[]>([]);
  useEffect(() => {
    api<any>("/progress").then(setP);
    api<any>("/home").then(setHome);
    api<any[]>("/notes").then(setNotes).catch(() => setNotes([]));
    api<any[]>("/bookmarks").then(setMarks).catch(() => setMarks([]));
  }, []);
  if (!p || !home) return <p>Loading progress…</p>;
  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Progress</h1>
      <p>Attempts: {p.attempts}</p>
      <p>Assessment readiness: {Math.round((home.assessment_readiness || 0) * 100)}%</p>
      <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
        {(p.heatmap || []).map((h: any) => (
          <Link key={h.concept_id} href={conceptHref(h.concept_id)} className="panel p-3 text-xs">
            <div>{h.name || h.concept_id}</div>
            <div className="mt-1 h-2 rounded bg-[#1c2618]">
              <div className="h-2 rounded bg-[#76b900]" style={{ width: `${Math.round(h.score * 100)}%` }} />
            </div>
          </Link>
        ))}
      </div>
      {!p.heatmap?.length && <p style={{ color: "var(--muted)" }}>Heatmap fills after diagnostic, quizzes, and teach-backs. Viewing is not mastery.</p>}
      <section className="panel p-4 text-sm">
        <h2 className="text-lg">Review later / notes</h2>
        <ul className="mt-2 list-disc pl-5">
          {marks.map((m) => (
            <li key={m.id}>
              {m.label}: {m.target_type} {m.target_id}
            </li>
          ))}
          {notes.map((n) => (
            <li key={n.id}>
              Note on {n.target_type}: {n.body.slice(0, 120)}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
