"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";

export default function ConceptsPage() {
  const [g, setG] = useState<any>(null);
  const [sel, setSel] = useState<string | null>(null);
  useEffect(() => {
    api("/concepts").then(setG);
  }, []);
  const clusters = useMemo(() => {
    const m: Record<string, any[]> = {};
    for (const n of g?.nodes || []) (m[n.cluster] ||= []).push(n);
    return m;
  }, [g]);
  const node = g?.nodes?.find((n: any) => n.id === sel);
  if (!g) return <p>Loading concept map…</p>;
  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Concept map</h1>
      <p className="text-[#9aa89a]">{g.nodes.length} concepts · {g.edges.length} relations from the NVIDIA notebooks.</p>
      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <div className="panel overflow-auto p-4">
          {Object.entries(clusters).map(([k, nodes]) => (
            <div key={k} className="mb-4">
              <h2 className="text-xs uppercase tracking-wide text-[#76b900]">{k}</h2>
              <div className="mt-2 flex flex-wrap gap-2">
                {nodes.map((n) => (
                  <button key={n.id} onClick={() => setSel(n.id)} className={`rounded-full border px-3 py-1 text-sm ${sel === n.id ? "border-[#76b900] text-[#76b900]" : "border-[#2a322c]"}`}>
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
              <p className="text-[#9aa89a]">{node.school}</p>
              <Link className="block text-[#76b900]" href={`/learn?concept=${node.id}`}>
                Open lesson
              </Link>
              <Link className="block text-[#76b900]" href={`/notebooks/${node.notebook_file}`}>
                Notebook {node.notebook_file} · cell {node.cell_index}
              </Link>
              {node.twin_id && (
                <Link className="block text-[#76b900]" href={`/twins/${node.twin_id}`}>
                  Digital twin
                </Link>
              )}
              <Link className="block text-[#76b900]" href={`/practice?concept=${node.id}`}>
                Quiz
              </Link>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
