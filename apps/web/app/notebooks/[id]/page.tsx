"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

const TABS = ["CODE", "PLAIN_ENGLISH", "LINE_BY_LINE", "WHY_THIS_EXISTS", "WHAT_SHOULD_HAPPEN", "HOW_TO_VERIFY", "COMMON_FAILURE", "TRY_MODIFYING"];

export default function NotebookDetail() {
  const { id } = useParams<{ id: string }>();
  const [nb, setNb] = useState<any>(null);
  const [tab, setTab] = useState("CODE");
  const [open, setOpen] = useState<number | null>(0);
  useEffect(() => {
    api(`/notebooks/${id}`).then(setNb);
  }, [id]);
  if (!nb) return <p>Loading notebook…</p>;
  return (
    <div className="space-y-4">
      <Link href="/notebooks" className="text-sm text-[#9aa89a]">
        ← All notebooks
      </Link>
      <h1 className="text-3xl">{nb.title}</h1>
      <p className="text-[#9aa89a]">{nb.purpose}</p>
      <p className="text-sm">Why it matters: {nb.why_it_matters}</p>
      <p className="text-sm">Expected outcome: {nb.expected_outcome}</p>
      <div className="panel p-3 text-sm">
        Flow cells: {nb.flow.join(", ") || "see headings in cells"}
      </div>
      {nb.cells.map((c: any) => (
        <section key={c.id} className="panel p-4">
          <button className="flex w-full items-center justify-between text-left" onClick={() => setOpen(open === c.cell_index ? null : c.cell_index)}>
            <span className="font-mono text-xs">
              [{c.cell_index}] {c.cell_type}
            </span>
            <EvidenceBadge type={c.evidence_type} />
          </button>
          {open === c.cell_index && (
            <div className="mt-3 space-y-2">
              <div className="flex flex-wrap gap-1">
                {TABS.map((t) => (
                  <button key={t} className={`rounded px-2 py-1 text-xs ${tab === t ? "bg-[#76b900] text-black" : "bg-[#1c2618]"}`} onClick={() => setTab(t)}>
                    {t.replaceAll("_", " ")}
                  </button>
                ))}
              </div>
              <pre className="max-h-[420px] overflow-auto whitespace-pre-wrap rounded bg-[#0b0d0c] p-3 text-xs">
                {c.tabs[tab] || (tab === "CODE" ? c.source : "")}
              </pre>
              {c.cell_type === "code" && (
                <p className="text-xs text-amber-300">
                  Execution blocked. Flags: {(c.safety_flags || []).join(", ") || "none"}. Stored output: {c.stored_output ? "yes (ACTUAL stored)" : "none — EXPECTED_RESULT only"}.
                </p>
              )}
            </div>
          )}
        </section>
      ))}
    </div>
  );
}
