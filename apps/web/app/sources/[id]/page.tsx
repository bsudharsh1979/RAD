"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

export default function SourceDetail() {
  const { id } = useParams<{ id: string }>();
  const [d, setD] = useState<any>(null);
  useEffect(() => {
    api(`/sources/${encodeURIComponent(decodeURIComponent(id))}`).then(setD);
  }, [id]);
  if (!d) return <p>Loading source…</p>;
  return (
    <div className="space-y-3">
      <h1 className="text-2xl">{d.artifact.title}</h1>
      <p className="text-sm text-[#9aa89a]">{d.artifact.file}</p>
      {d.spans.map((s: any) => (
        <div key={s.id} className="panel p-3 text-sm">
          <div className="flex justify-between">
            <span className="font-mono text-xs">cell {s.cell_index}</span>
            <EvidenceBadge type={s.evidence_type} />
          </div>
          <p className="mt-1">{s.heading}</p>
          <p className="text-[#9aa89a]">{s.excerpt}</p>
        </div>
      ))}
    </div>
  );
}
