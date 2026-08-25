"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function ProgressPage() {
  const [p, setP] = useState<any>(null);
  const [home, setHome] = useState<any>(null);
  useEffect(() => {
    api("/progress").then(setP);
    api("/home").then(setHome);
  }, []);
  if (!p || !home) return <p>Loading progress…</p>;
  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Progress</h1>
      <p>Attempts: {p.attempts}</p>
      <p>Assessment readiness: {Math.round((home.assessment_readiness || 0) * 100)}%</p>
      <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
        {(p.heatmap || []).map((h: any) => (
          <Link key={h.concept_id} href={`/learn?concept=${h.concept_id}`} className="panel p-3 text-xs">
            <div>{h.concept_id}</div>
            <div className="mt-1 h-2 rounded bg-[#1c2618]">
              <div className="h-2 rounded bg-[#76b900]" style={{ width: `${Math.round(h.score * 100)}%` }} />
            </div>
          </Link>
        ))}
      </div>
      {!p.heatmap?.length && <p className="text-[#9aa89a]">Heatmap fills after diagnostic, quizzes, and teach-backs.</p>}
    </div>
  );
}
