"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import Link from "next/link";

export default function SettingsPage() {
  const [me, setMe] = useState<any>(null);
  const [prov, setProv] = useState<any>(null);
  const [cost, setCost] = useState<any>(null);
  const [integ, setInteg] = useState<any>(null);
  useEffect(() => {
    api("/me").then(setMe);
    api("/providers").then(setProv);
    api("/cost").then(setCost);
    api("/integrity").then(setInteg);
  }, []);
  if (!me || !prov) return <p>Loading settings…</p>;
  return (
    <div className="space-y-6">
      <h1 className="text-3xl">Settings · APIs</h1>
      <p>Which APIs do you want? Core learning never requires a paid key.</p>
      <ul className="panel divide-y divide-[#2a322c] p-0">
        {Object.entries(prov.status).map(([k, v]) => (
          <li key={k} className="flex justify-between px-4 py-2 text-sm">
            <span>{k}</span>
            <span className={String(v) === "connected" ? "text-[#76b900]" : "text-[#9aa89a]"}>{String(v)}</span>
          </li>
        ))}
      </ul>
      <label className="block">
        Tutor engine
        <select
          className="mt-1 w-full rounded bg-[#141816] p-2"
          value={me.tutor_provider}
          onChange={async (e) => {
            const n = await api("/me", { method: "PATCH", body: JSON.stringify({ tutor_provider: e.target.value }) });
            setMe(n);
          }}
        >
          {prov.choices.tutor.map((t: string) => (
            <option key={t}>{t}</option>
          ))}
        </select>
      </label>
      <label className="block">
        Voice
        <select
          className="mt-1 w-full rounded bg-[#141816] p-2"
          value={me.voice_provider}
          onChange={async (e) => setMe(await api("/me", { method: "PATCH", body: JSON.stringify({ voice_provider: e.target.value }) }))}
        >
          {prov.choices.voice.map((t: string) => (
            <option key={t}>{t}</option>
          ))}
        </select>
      </label>
      <label className="flex gap-2">
        <input
          type="checkbox"
          checked={me.research_enabled}
          onChange={async (e) => setMe(await api("/me", { method: "PATCH", body: JSON.stringify({ research_enabled: e.target.checked }) }))}
        />
        Research Mode / Perplexity
      </label>
      {cost && (
        <div className="panel p-4 text-sm">
          <h2>Cost governance</h2>
          <p>
            {cost.calls} calls · {cost.input_tokens} in / {cost.output_tokens} out · ${cost.cost_usd} / budget ${cost.budget_usd}
          </p>
        </div>
      )}
      {integ && (
        <div className="panel p-4 text-sm">
          <h2>Content integrity</h2>
          <p>
            {integ.sourced}/{integ.questions_total} questions sourced. Notebooks without stored outputs: {String(integ.notebooks_without_outputs)}.
          </p>
        </div>
      )}
      <Link href="/" className="text-[#76b900]">
        Back to home
      </Link>
    </div>
  );
}
