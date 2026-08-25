"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

type Home = {
  what_i_know: number;
  forgetting: number;
  thirty_minute_plan: { title: string; href: string; minutes: number }[];
  blocking_misconceptions: number;
  notebook_revisit: string;
  twin: string;
  strongest: { id: string; name: string; score: number }[];
  weakest: { id: string; name: string; score: number }[];
  misconception_count: number;
  assessment_readiness: number;
  reviews_due: number;
  resume: { text: string; action: string };
};

type Me = { onboarded: boolean; display_name: string; tutor_provider: string };

export default function HomePage() {
  const [me, setMe] = useState<Me | null>(null);
  const [home, setHome] = useState<Home | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api<Me>("/me")
      .then(setMe)
      .catch((e) => setErr(String(e)));
  }, []);
  useEffect(() => {
    if (me) api<Home>("/home").then(setHome).catch((e) => setErr(String(e)));
  }, [me]);

  if (err) {
    return (
      <div className="panel p-6">
        <h1 className="text-xl">API not reachable</h1>
        <p className="mt-2 text-[#9aa89a]">Start the FastAPI server on port 8000. {err}</p>
      </div>
    );
  }
  if (!me) return <p>Loading…</p>;
  if (!me.onboarded) return <Onboard onDone={() => api<Me>("/me").then(setMe)} />;
  if (!home) return <p>Loading dashboard…</p>;

  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs uppercase tracking-[0.2em] text-[#76b900]">Learner dashboard</p>
        <h1 className="mt-1 text-3xl font-semibold">What should I learn now?</h1>
        <p className="mt-2 max-w-3xl text-[#9aa89a]">{home.resume?.text}</p>
        {home.resume?.action && (
          <Link className="mt-3 inline-block rounded-lg bg-[#76b900] px-4 py-2 text-black" href={home.resume.action}>
            Continue
          </Link>
        )}
      </header>
      <section className="grid gap-4 md:grid-cols-4">
        <Stat label="What I know" value={`${Math.round(home.what_i_know * 100)}%`} />
        <Stat label="Reviews due today" value={String(home.reviews_due)} href="/review" />
        <Stat label="Blocking misconceptions" value={String(home.misconception_count)} href="/practice" />
        <Stat label="Assessment readiness" value={`${Math.round(home.assessment_readiness * 100)}%`} href="/assessment" />
      </section>
      <section className="panel p-5">
        <h2 className="text-lg font-medium">Today’s 30-minute plan</h2>
        <ul className="mt-3 space-y-2">
          {home.thirty_minute_plan.map((p) => (
            <li key={p.title}>
              <Link className="flex justify-between rounded-lg border border-[#2a322c] px-3 py-2 hover:border-[#76b900]" href={p.href}>
                <span>{p.title}</span>
                <span className="text-[#9aa89a]">{p.minutes} min</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>
      <section className="grid gap-4 md:grid-cols-2">
        <div className="panel p-5">
          <h2 className="text-lg">Weakest concepts</h2>
          <List items={home.weakest} />
          <p className="mt-3 text-sm text-[#9aa89a]">
            Revisit notebook: {home.notebook_revisit}. Twin:{" "}
            <Link className="text-[#76b900]" href={`/twins/${home.twin}`}>
              {home.twin}
            </Link>
          </p>
        </div>
        <div className="panel p-5">
          <h2 className="text-lg">Strongest concepts</h2>
          <List items={home.strongest} />
        </div>
      </section>
    </div>
  );
}

function List({ items }: { items: { id: string; name: string; score: number }[] }) {
  if (!items?.length) return <p className="mt-2 text-sm text-[#9aa89a]">Take the diagnostic to populate mastery.</p>;
  return (
    <ul className="mt-2 space-y-1 text-sm">
      {items.map((w) => (
        <li key={w.id}>
          <Link href={`/learn?concept=${w.id}`} className="hover:text-[#76b900]">
            {w.name} · {Math.round(w.score * 100)}%
          </Link>
        </li>
      ))}
    </ul>
  );
}

function Stat({ label, value, href }: { label: string; value: string; href?: string }) {
  const inner = (
    <div className="panel p-4">
      <div className="text-xs uppercase tracking-wide text-[#9aa89a]">{label}</div>
      <div className="mt-1 text-2xl">{value}</div>
    </div>
  );
  return href ? <Link href={href}>{inner}</Link> : inner;
}

function Onboard({ onDone }: { onDone: () => void }) {
  const [prov, setProv] = useState<any>(null);
  const [tutor, setTutor] = useState("demo");
  const [voice, setVoice] = useState("none");
  const [research, setResearch] = useState(false);
  const [name, setName] = useState("Learner");

  useEffect(() => {
    api("/providers").then(setProv);
  }, []);

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <h1 className="text-3xl font-semibold">Which APIs do you want?</h1>
      <p className="text-[#9aa89a]">
        The core academy runs offline with the Demo tutor. Paid APIs are optional and never required to learn the NVIDIA notebooks.
      </p>
      <EvidenceBadge type="SIMULATED_RESULT" /> <EvidenceBadge type="COURSE_SOURCE" />
      {prov && (
        <ul className="text-sm text-[#9aa89a]">
          {Object.entries(prov.status).map(([k, v]) => (
            <li key={k}>
              {k}: {String(v)}
            </li>
          ))}
        </ul>
      )}
      <label className="block">
        Display name
        <input className="mt-1 w-full rounded-lg bg-[#141816] p-2" value={name} onChange={(e) => setName(e.target.value)} />
      </label>
      <label className="block">
        Tutor engine
        <select className="mt-1 w-full rounded-lg bg-[#141816] p-2" value={tutor} onChange={(e) => setTutor(e.target.value)}>
          <option value="demo">Demo (offline)</option>
          <option value="openai">OpenAI Responses API</option>
          <option value="nvidia_nim">NVIDIA NIM</option>
          <option value="huggingface">HuggingFace Inference</option>
        </select>
      </label>
      <label className="block">
        Voice
        <select className="mt-1 w-full rounded-lg bg-[#141816] p-2" value={voice} onChange={(e) => setVoice(e.target.value)}>
          <option value="none">Off</option>
          <option value="elevenlabs">ElevenLabs</option>
          <option value="sarvam">Sarvam (Indic)</option>
          <option value="openai_realtime">OpenAI Realtime</option>
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
        Start learning
      </button>
    </div>
  );
}
