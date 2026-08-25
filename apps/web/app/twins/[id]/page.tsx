"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";
import { TwinViz } from "@/components/TwinViz";

export default function TwinPage() {
  const { id } = useParams<{ id: string }>();
  const [meta, setMeta] = useState<any>(null);
  const [params, setParams] = useState<Record<string, any>>({});
  const [state, setState] = useState<any>(null);
  const [pred, setPred] = useState("");
  const [predId, setPredId] = useState<string | null>(null);
  const [locked, setLocked] = useState(false);

  useEffect(() => {
    api<any[]>("/twins").then((rows) => {
      const t = rows.find((x) => x.id === id);
      setMeta(t);
      const p: Record<string, any> = {};
      for (const c of t?.controls || []) p[c.key] = c.default;
      setParams(p);
    });
  }, [id]);

  if (!meta) return <p>Loading twin…</p>;

  return (
    <div className="space-y-4">
      <h1 className="text-3xl">{meta.name}</h1>
      <p className="text-[#9aa89a]">{meta.summary}</p>
      <EvidenceBadge type="SIMULATED_RESULT" />
      <p className="text-sm">Source notebook: {meta.notebook_file}. Predict before running when the lesson asks.</p>
      <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
        <div className="panel space-y-3 p-4">
          {meta.controls.map((c: any) => (
            <label key={c.key} className="block text-sm">
              {c.key}
              {c.type === "bool" ? (
                <input
                  type="checkbox"
                  className="ml-2"
                  checked={!!params[c.key]}
                  onChange={(e) => setParams({ ...params, [c.key]: e.target.checked })}
                />
              ) : c.type === "enum" ? (
                <select
                  className="mt-1 w-full rounded bg-[#0b0d0c] p-1"
                  value={params[c.key]}
                  onChange={(e) => setParams({ ...params, [c.key]: isNaN(Number(e.target.value)) ? e.target.value : Number(e.target.value) })}
                >
                  {(c.options || []).map((o: any) => (
                    <option key={String(o)} value={o}>
                      {String(o)}
                    </option>
                  ))}
                </select>
              ) : c.type === "string" ? (
                <input className="mt-1 w-full rounded bg-[#0b0d0c] p-1" value={params[c.key] || ""} onChange={(e) => setParams({ ...params, [c.key]: e.target.value })} />
              ) : (
                <input
                  type="range"
                  className="mt-1 w-full"
                  min={c.min ?? 0}
                  max={c.max ?? 100}
                  step={c.type === "float" ? 0.01 : 1}
                  value={params[c.key] ?? 0}
                  onChange={(e) => setParams({ ...params, [c.key]: Number(e.target.value) })}
                />
              )}
              <span className="ml-2 text-[#9aa89a]">{String(params[c.key])}</span>
            </label>
          ))}
          <textarea className="w-full rounded bg-[#0b0d0c] p-2 text-sm" placeholder="Your prediction" value={pred} onChange={(e) => setPred(e.target.value)} />
          <button
            className="w-full rounded border border-[#76b900] px-3 py-2"
            onClick={async () => {
              const r: any = await api("/twins/predict", {
                method: "POST",
                body: JSON.stringify({ twin_id: id, prompt: pred, predicted: { note: pred } }),
              });
              setPredId(r.prediction_id);
              setLocked(true);
            }}
          >
            Lock prediction
          </button>
          <button
            className="w-full rounded bg-[#76b900] px-3 py-2 text-black disabled:opacity-40"
            disabled={!locked}
            onClick={async () => {
              const r: any = await api("/twins/run", {
                method: "POST",
                body: JSON.stringify({ scenario: id, params, prediction_id: predId }),
              });
              setState(r.state);
            }}
          >
            Run simulation
          </button>
          <p className="text-xs text-[#9aa89a]">Outcome hidden until you lock a prediction (active learning).</p>
        </div>
        <div className="space-y-3">
          <TwinViz scenario={id} params={params} state={state} />
          {state && (
            <div className="panel p-4">
              <EvidenceBadge type={state.evidence_type} />
              <p className="mt-2 text-sm">{state.teaching}</p>
              <pre className="mt-3 max-h-80 overflow-auto text-xs text-[#9aa89a]">{JSON.stringify(state, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
