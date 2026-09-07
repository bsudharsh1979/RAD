"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

export default function ExperimentsPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [msg, setMsg] = useState("");
  const [cmp, setCmp] = useState<any>(null);
  const [explain, setExplain] = useState<any>(null);
  const [a, setA] = useState("");
  const [b, setB] = useState("");

  const refresh = () => api<any[]>("/experiments").then(setRows);
  useEffect(() => {
    refresh();
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Experiments</h1>
      <p style={{ color: "var(--muted)" }}>
        Import AIPerf / JSON / CSV / Prometheus / logs as ACTUAL_RUN. Raw bytes are stored; never overwritten.
        Sample file: <code>course-materials/samples/demo-hf-run.json</code>
      </p>
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
      <ul className="space-y-2 text-sm">
        {rows.map((r) => (
          <li key={r.id} className="panel flex flex-wrap items-center justify-between gap-2 p-3">
            <span>
              {r.name} · {r.kind} · <EvidenceBadge type={r.evidence_type} />
            </span>
            <span className="flex gap-2">
              <button className="rounded border px-2 py-1" style={{ borderColor: "var(--line)" }} onClick={() => setA(r.latest_run_id || r.id)}>
                Use as A
              </button>
              <button className="rounded border px-2 py-1" style={{ borderColor: "var(--line)" }} onClick={() => setB(r.latest_run_id || r.id)}>
                Use as B
              </button>
              <button
                className="rounded border px-2 py-1"
                style={{ borderColor: "var(--line)" }}
                onClick={async () => setExplain(await api(`/experiments/${r.latest_run_id || r.id}/explain`))}
              >
                Explain
              </button>
            </span>
          </li>
        ))}
      </ul>
      <div className="flex flex-wrap gap-2">
        <input className="field flex-1" placeholder="Run A id" value={a} onChange={(e) => setA(e.target.value)} />
        <input className="field flex-1" placeholder="Run B id" value={b} onChange={(e) => setB(e.target.value)} />
        <button className="rounded bg-[#76b900] px-3 text-black" onClick={async () => setCmp(await api("/experiments/compare", { method: "POST", body: JSON.stringify({ a, b }) }))}>
          Compare
        </button>
      </div>
      {cmp && (
        <div className="panel space-y-2 p-4 text-sm">
          <h2>Comparison workbench</h2>
          <p>{cmp.causality}</p>
          <h3>Confounders</h3>
          <ul className="list-disc pl-5">
            {(cmp.confounds || []).map((c: any, i: number) => (
              <li key={i}>
                {c.field}: {String(c.a)} vs {String(c.b)}
              </li>
            ))}
          </ul>
          <MetricBars cmp={cmp} />
          <pre className="overflow-auto text-xs">{JSON.stringify(cmp.deltas || cmp, null, 2)}</pre>
        </div>
      )}
      {explain && (
        <div className="panel space-y-2 p-4 text-sm">
          <h2>Experiment explainer</h2>
          <pre className="overflow-auto text-xs whitespace-pre-wrap">{JSON.stringify(explain, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

function MetricBars({ cmp }: { cmp: any }) {
  const metrics = cmp.normalized_metrics || cmp.metrics || {};
  const keys = Object.keys(metrics).slice(0, 6);
  if (!keys.length) return null;
  return (
    <div className="space-y-2" role="img" aria-label="Normalized metric comparison">
      {keys.map((k) => (
        <div key={k}>
          <div className="text-xs">{k}</div>
          <div className="h-2 rounded bg-[#1c2618]">
            <div className="h-2 rounded bg-[#76b900]" style={{ width: `${Math.min(100, Math.abs(Number(metrics[k]) || 0))}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}
