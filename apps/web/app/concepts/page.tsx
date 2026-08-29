"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { notebookHref, conceptHref } from "@/lib/paths";
import { NotesBar } from "@/components/NotesBar";

export default function ConceptsPage() {
  const [g, setG] = useState<any>(null);
  const [sel, setSel] = useState<string | null>(null);
  const [detail, setDetail] = useState<any>(null);
  useEffect(() => {
    api("/concepts").then(setG);
  }, []);
  useEffect(() => {
    if (sel) api(`/concepts/${sel}`).then(setDetail);
  }, [sel]);
  const clusters = useMemo(() => {
    const m: Record<string, any[]> = {};
    for (const n of g?.nodes || []) (m[n.cluster] ||= []).push(n);
    return m;
  }, [g]);
  const node = g?.nodes?.find((n: any) => n.id === sel);
  const related = (detail?.related || []).map((r: any) => ({
    ...r,
    name: g?.nodes?.find((n: any) => n.id === r.id)?.name || r.id,
  }));
  if (!g) return <p>Loading concept map…</p>;
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">Concept map</h1>
      <p style={{ color: "var(--muted)" }}>
        {g.nodes.length} ideas grouped by mechanism. Open a card, then ask the tutor “what happens,” not “define.”
      </p>
      <div className="grid gap-4 lg:grid-cols-[1fr_340px]">
        <div className="panel overflow-auto p-4">
          <svg viewBox="0 0 640 160" className="mb-4 h-36 w-full" aria-hidden="true">
            {(g.edges || []).slice(0, 40).map((e: any, i: number) => (
              <line key={e.id || i} x1={20 + (i % 12) * 50} y1={30} x2={40 + ((i * 3) % 12) * 50} y2={120} stroke="#76b900" strokeOpacity="0.25" />
            ))}
            <text x={20} y={20} fill="#76b900" fontSize="12">
              PREREQUISITE / PART_OF / CONFUSED_WITH
            </text>
          </svg>
          {Object.entries(clusters).map(([k, nodes]) => (
            <div key={k} className="mb-4">
              <h2 className="text-xs uppercase tracking-wide text-[#76b900]">{k}</h2>
              <div className="mt-2 flex flex-wrap gap-2">
                {nodes.map((n) => (
                  <button
                    key={n.id}
                    onClick={() => setSel(n.id)}
                    className={`rounded-full border px-3 py-1 text-sm ${sel === n.id ? "border-[#76b900] text-[#76b900]" : ""}`}
                    style={sel === n.id ? undefined : { borderColor: "var(--line)" }}
                  >
                    {n.name}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
        <aside className="panel p-4 text-sm">
          {!node && <p>Select a concept.</p>}
          {node && (
            <div className="space-y-2">
              <h2 className="text-xl">{node.name}</h2>
              <p>{node.definition}</p>
              <p style={{ color: "var(--muted)" }}>{node.school}</p>
              <p>{node.engineer}</p>
              <p className="text-xs" style={{ color: "var(--muted)" }}>
                {node.research}
              </p>
              {!!detail?.prerequisites?.length && (
                <p>
                  Prerequisites:{" "}
                  {detail.prerequisites.map((id: string) => (
                    <button key={id} className="mr-1 text-[#76b900]" onClick={() => setSel(id)}>
                      {g.nodes.find((n: any) => n.id === id)?.name || id}
                    </button>
                  ))}
                </p>
              )}
              {!!related.length && (
                <p>
                  Related:{" "}
                  {related.slice(0, 8).map((r: any) => (
                    <span key={r.id + r.relation} className="mr-2">
                      {r.relation} {r.name}
                    </span>
                  ))}
                </p>
              )}
              <p>Mastery: {Math.round((detail?.mastery || 0) * 100)}%</p>
              <Link className="block text-[#76b900]" href={conceptHref(node.id)}>
                Open lesson
              </Link>
              <Link className="block text-[#76b900]" href={notebookHref(node.notebook_file, node.cell_index)}>
                Notebook {node.notebook_file} · cell {node.cell_index}
              </Link>
              {node.twin_id && (
                <Link className="block text-[#76b900]" href={`/twins/${node.twin_id}`}>
                  Digital twin
                </Link>
              )}
              <Link className="block text-[#76b900]" href={`/tutor?q=${encodeURIComponent(`Teach me ${node.name} as a mechanism.`)}`}>
                Ask the tutor
              </Link>
              <NotesBar targetType="concept" targetId={node.id} />
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
