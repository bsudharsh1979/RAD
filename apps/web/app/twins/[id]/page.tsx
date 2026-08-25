"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";
import { TwinViz } from "@/components/TwinViz";
import { notebookHref } from "@/lib/paths";
import { NotesBar } from "@/components/NotesBar";

export default function TwinPage() {
  const { id } = useParams<{ id: string }>();
  const [meta, setMeta] = useState<any>(null);
  const [params, setParams] = useState<Record<string, any>>({});
  const [state, setState] = useState<any>(null);
  const [pred, setPred] = useState("");
  const [predId, setPredId] = useState<string | null>(null);
  const [locked, setLocked] = useState(false);

  useEffect(() => {
    setState(null);
    setLocked(false);
    setPredId(null);
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
      <p style={{ color: "var(--muted)" }}>{meta.summary}</p>
      <EvidenceBadge type="SIMULATED_RESULT" />
      <p className="text-sm">
        Source:{" "}
        <Link className="text-[#76b900]" href={notebookHref(meta.notebook_file)}>
          {meta.notebook_file}
        </Link>
        . Predict before running.
      </p>
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
                  className="field mt-1"
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
                <input className="field mt-1" value={params[c.key] || ""} onChange={(e) => setParams({ ...params, [c.key]: e.target.value })} />
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
              <span className="ml-2" style={{ color: "var(--muted)" }}>
                {String(params[c.key])}
              </span>
            </label>
          ))}
          <textarea className="field" placeholder="Your prediction" value={pred} onChange={(e) => setPred(e.target.value)} />
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
          <p className="text-xs" style={{ color: "var(--muted)" }}>
            Outcome hidden until you lock a prediction (active learning).
          </p>
        </div>
        <div className="space-y-3">
          <TwinViz scenario={id} params={params} state={state} />
          {state && (
            <div className="panel p-4">
              <EvidenceBadge type={state.evidence_type} />
              <h2 className="mt-2 text-sm font-medium">Your prediction vs simulated observation</h2>
              <p className="text-sm">You predicted: {pred || "(empty)"}</p>
              <p className="mt-2 text-sm">{state.teaching}</p>
              <pre className="mt-3 max-h-80 overflow-auto text-xs" style={{ color: "var(--muted)" }}>
                {JSON.stringify(state, null, 2)}
              </pre>
            </div>
          )}
          <NotesBar targetType="twin" targetId={String(id)} />
        </div>
      </div>
    </div>
  );
}
