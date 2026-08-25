"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

export default function ExperimentsPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [msg, setMsg] = useState("");
  const [cmp, setCmp] = useState<any>(null);
  const [a, setA] = useState("");
  const [b, setB] = useState("");

  const refresh = () => api<any[]>("/experiments").then(setRows);
  useEffect(() => {
    refresh();
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Experiments</h1>
      <p className="text-[#9aa89a]">Import AIPerf / JSON / CSV / Prometheus / logs as ACTUAL_RUN. Raw bytes are stored; never overwritten.</p>
      <EvidenceBadge type="ACTUAL_RUN" />
      <input
        type="file"
        aria-label="Import experiment file"
        onChange={async (e) => {
          const f = e.target.files?.[0];
          if (!f) return;
          const fd = new FormData();
          fd.append("file", f);
          const r = await fetch("/api/experiments/import", { method: "POST", body: fd });
          const j = await r.json();
          setMsg(JSON.stringify(j.normalized));
          if (!a) setA(j.run_id);
          else setB(j.run_id);
          refresh();
        }}
      />
      {msg && <pre className="panel overflow-auto p-3 text-xs">{msg}</pre>}
      <ul className="text-sm">
        {rows.map((r) => (
          <li key={r.id}>
            {r.name} · {r.kind} · {r.id}
          </li>
        ))}
      </ul>
      <div className="flex gap-2">
        <input className="flex-1 rounded bg-[#141816] p-2" placeholder="Run A id" value={a} onChange={(e) => setA(e.target.value)} />
        <input className="flex-1 rounded bg-[#141816] p-2" placeholder="Run B id" value={b} onChange={(e) => setB(e.target.value)} />
        <button
          className="rounded bg-[#76b900] px-3 text-black"
          onClick={async () => setCmp(await api("/experiments/compare", { method: "POST", body: JSON.stringify({ a, b }) }))}
        >
          Compare
        </button>
      </div>
      {cmp && (
        <div className="panel p-4 text-sm">
          <h2>Confounders</h2>
          <pre className="text-xs">{JSON.stringify(cmp, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
