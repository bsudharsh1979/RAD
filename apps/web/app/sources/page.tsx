"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function SourcesPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [q, setQ] = useState("pipeline");
  const [hits, setHits] = useState<any[]>([]);
  useEffect(() => {
    api<any[]>("/sources").then(setRows);
  }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Sources</h1>
      <form
        className="flex gap-2"
        onSubmit={async (e) => {
          e.preventDefault();
          setHits(await api(`/search?q=${encodeURIComponent(q)}`));
        }}
      >
        <input className="flex-1 rounded bg-[#141816] p-2" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search sources" />
        <button className="rounded bg-[#76b900] px-3 text-black">Search</button>
      </form>
      {hits.map((h) => (
        <div key={h.span_id} className="panel p-3 text-sm">
          <Link className="text-[#76b900]" href={`/notebooks/${h.file}`}>
            {h.file} · cell {h.cell_index}
          </Link>
          <p className="text-[#9aa89a]">{h.excerpt.slice(0, 240)}</p>
        </div>
      ))}
      <ul className="space-y-2">
        {rows.map((s) => (
          <li key={s.id}>
            <Link href={`/sources/${s.file}`} className="text-[#76b900]">
              {s.file}
            </Link>{" "}
            · {s.type} · {s.title}
          </li>
        ))}
      </ul>
    </div>
  );
}
