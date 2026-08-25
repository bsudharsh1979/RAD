"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

export default function AssessmentPage() {
  const [a, setA] = useState<any>(null);
  useEffect(() => {
    api("/assessment").then(setA);
  }, []);
  if (!a) return <p>Loading assessment arena…</p>;
  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Assessment arena</h1>
      <EvidenceBadge type="COURSE_SOURCE" />
      <p>{a.brief}</p>
      <p>Pass rule: {a.pass_rule} of {a.features.length} features.</p>
      <ul className="list-disc pl-6">
        {a.features.map((f: string) => (
          <li key={f}>{f}</li>
        ))}
      </ul>
      <p className="text-[#9aa89a]">The tutor grades reasoning, not a leaked solution. Design in the twin, then defend.</p>
      <Link className="inline-block rounded bg-[#76b900] px-4 py-2 text-black" href={`/twins/${a.twin}`}>
        Open assessment twin
      </Link>
      <Link className="ml-3 text-[#76b900]" href="/practice?concept=c-assess">
        Practice design questions
      </Link>
      <ul className="mt-4 space-y-2 text-sm">
        {a.questions?.map((q: any) => (
          <li key={q.id} className="panel p-3">
            {q.stem}
          </li>
        ))}
      </ul>
    </div>
  );
}
