"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { topicHref } from "@/lib/paths";

type Topic = {
  id: string;
  order: number;
  title: string;
  hook: string;
  promise: string;
  minutes: number;
  notebook: string;
  twin: string;
};

type Me = { onboarded: boolean; display_name: string; tutor_provider: string };

export default function HomePage() {
  const [me, setMe] = useState<Me | null>(null);
  const [topics, setTopics] = useState<Topic[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api<Me>("/me")
      .then(setMe)
      .catch((e) => setErr(String(e)));
  }, []);
  useEffect(() => {
    api<Topic[]>("/topics")
      .then(setTopics)
      .catch((e) => setErr(String(e)));
  }, []);

  if (err) {
    return (
      <div className="panel p-6">
        <h1 className="text-xl">API not reachable</h1>
        <p className="mt-2" style={{ color: "var(--muted)" }}>
          Start the FastAPI server on port 8000. {err}
        </p>
      </div>
    );
  }
  if (!me) return <p>Loading…</p>;
  if (!me.onboarded) return <Onboard onDone={() => api<Me>("/me").then(setMe)} />;

  return (
    <div className="space-y-8">
      <header className="max-w-3xl">
        <p className="text-xs uppercase tracking-[0.2em] text-[#76b900]">Ten stories, one course</p>
        <h1 className="mt-2 text-4xl font-semibold leading-tight">Learn what the model is actually doing.</h1>
        <p className="mt-3 text-lg" style={{ color: "var(--muted)" }}>
          Not a glossary. Each topic is a mechanism you can explain out loud — then check with a lecture and a
          simulated twin.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link className="rounded-lg bg-[#76b900] px-4 py-2 text-black" href="/learn/the-black-box">
            Start with the black box
          </Link>
          <Link className="rounded-lg border px-4 py-2" href="/tutor">
            Ask the tutor
          </Link>
        </div>
      </header>
      <section className="grid gap-4 md:grid-cols-2">
        {(topics || []).map((t) => (
          <Link key={t.id} href={topicHref(t.id)} className="panel group block p-5 transition hover:border-[#76b900]">
            <p className="text-xs uppercase tracking-[0.15em] text-[#76b900]">
              Story {t.order} · {t.minutes} min
            </p>
            <h2 className="mt-2 text-xl font-medium">{t.title}</h2>
            <p className="mt-2 text-sm leading-relaxed" style={{ color: "var(--muted)" }}>
              {t.hook}
            </p>
            <p className="mt-3 text-sm">You’ll walk away able to: {t.promise}</p>
          </Link>
        ))}
      </section>
    </div>
  );
}

function Onboard({ onDone }: { onDone: () => void }) {
  const [prov, setProv] = useState<any>(null);
  const [tutor, setTutor] = useState("demo");
  const [voice, setVoice] = useState("none");
  const [research, setResearch] = useState(false);
  const [name, setName] = useState("Learner");

  useEffect(() => {
    api("/providers").then((p: any) => {
      setProv(p);
      const st = p?.status || {};
      if (st.nvidia_nim === "connected") setTutor("nvidia_nim");
      if (st.elevenlabs === "connected" || st.voice_elevenlabs === "connected") setVoice("elevenlabs");
    });
  }, []);

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <p className="text-xs uppercase tracking-[0.2em] text-[#76b900]">Welcome</p>
      <h1 className="text-3xl font-semibold">Ten stories. Real mechanisms.</h1>
      <p style={{ color: "var(--muted)" }}>
        Demo works offline. If NVIDIA NIM is connected, the tutor can teach in full sentences instead of reciting
        terms. Voice is optional.
      </p>
      {prov && (
        <ul className="text-sm" style={{ color: "var(--muted)" }} aria-label="Provider status">
          {Object.entries(prov.status || {}).map(([k, v]) => (
            <li key={k}>
              {k}: {String(v)}
            </li>
          ))}
        </ul>
      )}
      <label className="block">
        Display name
        <input className="field mt-1" value={name} onChange={(e) => setName(e.target.value)} />
      </label>
      <label className="block">
        Tutor engine
        <select className="field mt-1" value={tutor} onChange={(e) => setTutor(e.target.value)}>
          <option value="demo">Demo (offline, still teaches the mechanism)</option>
          <option value="nvidia_nim">NVIDIA NIM</option>
          <option value="openai">OpenAI Responses API</option>
          <option value="huggingface">HuggingFace Inference</option>
        </select>
      </label>
      <label className="block">
        Voice
        <select className="field mt-1" value={voice} onChange={(e) => setVoice(e.target.value)}>
          <option value="none">Off</option>
          <option value="elevenlabs">ElevenLabs</option>
          <option value="sarvam">Sarvam (Indic)</option>
        </select>
      </label>
      <label className="flex items-center gap-2">
        <input type="checkbox" checked={research} onChange={(e) => setResearch(e.target.checked)} />
        Enable Research Mode (Perplexity) — labeled EXTERNAL_RESEARCH
      </label>
      <button
        className="rounded-lg bg-[#76b900] px-4 py-2 text-black"
        onClick={async () => {
          await api("/onboard", {
            method: "POST",
            body: JSON.stringify({
              display_name: name,
              tutor_provider: tutor,
              voice_provider: voice,
              research_enabled: research,
            }),
          });
          onDone();
        }}
      >
        Start with the first story
      </button>
    </div>
  );
}
