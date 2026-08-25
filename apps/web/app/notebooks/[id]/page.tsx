"use client";

import { Suspense, useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";
import { NotesBar } from "@/components/NotesBar";

const TABS = ["CODE", "PLAIN_ENGLISH", "LINE_BY_LINE", "WHY_THIS_EXISTS", "WHAT_SHOULD_HAPPEN", "HOW_TO_VERIFY", "COMMON_FAILURE", "TRY_MODIFYING"];

function NotebookInner() {
  const { id } = useParams<{ id: string }>();
  const sp = useSearchParams();
  const jump = sp.get("cell");
  const [nb, setNb] = useState<any>(null);
  const [tab, setTab] = useState("CODE");
  const [open, setOpen] = useState<number | null>(jump ? Number(jump) : 0);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const nid = decodeURIComponent(id);
    api(`/notebooks/${encodeURIComponent(nid)}`)
      .then((d) => {
        setNb(d);
        if (jump != null) setOpen(Number(jump));
      })
      .catch((e) => setErr(String(e)));
  }, [id, jump]);

  if (err) return <p>Could not load notebook. {err}</p>;
  if (!nb) return <p>Loading notebook…</p>;
  return (
    <div className="space-y-4">
      <Link href="/notebooks" className="text-sm" style={{ color: "var(--muted)" }}>
        ← All notebooks
      </Link>
      <h1 className="text-3xl">{nb.title}</h1>
      <p style={{ color: "var(--muted)" }}>{nb.purpose}</p>
      <p className="text-sm">Why it matters: {nb.why_it_matters}</p>
      <p className="text-sm">Expected outcome: {nb.expected_outcome}</p>
      <div className="panel p-3 text-sm">Flow cells: {nb.flow.join(", ") || "see headings in cells"}</div>
      {nb.cells.map((c: any) => (
        <section key={c.id} id={`cell-${c.cell_index}`} className={`panel p-4 ${open === c.cell_index ? "ring-1 ring-[#76b900]" : ""}`}>
          <button className="flex w-full items-center justify-between text-left" onClick={() => setOpen(open === c.cell_index ? null : c.cell_index)}>
            <span className="font-mono text-xs">
              [{c.cell_index}] {c.cell_type}
            </span>
            <EvidenceBadge type={c.stored_output ? "ACTUAL_RUN" : c.cell_type === "code" ? "EXPECTED_RESULT" : "COURSE_SOURCE"} />
          </button>
          {open === c.cell_index && (
            <div className="mt-3 space-y-2">
              <div className="flex flex-wrap gap-1">
                {TABS.map((t) => (
                  <button key={t} className={`rounded px-2 py-1 text-xs ${tab === t ? "bg-[#76b900] text-black" : "bg-[#1c2618] text-[#e8eee6]"}`} onClick={() => setTab(t)}>
                    {t.replaceAll("_", " ")}
                  </button>
                ))}
              </div>
              <pre className="max-h-[420px] overflow-auto whitespace-pre-wrap rounded p-3 text-xs" style={{ background: "var(--bg)" }}>
                {c.tabs[tab] || (tab === "CODE" ? c.source : "No commentary stored for this tab.")}
              </pre>
              {c.cell_type === "code" && (
                <p className="text-xs text-amber-500">
                  Execution blocked. Flags: {(c.safety_flags || []).join(", ") || "none"}. Stored output:{" "}
                  {c.stored_output ? "yes (ACTUAL stored)" : "none — EXPECTED_RESULT only"}.
                </p>
              )}
              <NotesBar targetType="notebook_cell" targetId={c.id} />
            </div>
          )}
        </section>
      ))}
    </div>
  );
}

export default function NotebookDetail() {
  return (
    <Suspense fallback={<p>Loading notebook…</p>}>
      <NotebookInner />
    </Suspense>
  );
}
