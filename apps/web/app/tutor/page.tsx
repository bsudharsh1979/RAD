"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { notebookHref } from "@/lib/paths";

const STARTERS = [
  "What actually happens between the sentence I type and the [MASK] guess?",
  "Why does BERT need a second embedding table just for position?",
  "What are Q, K, and V actually doing in one attention head?",
  "Why does T5's encoder run once while the decoder loops?",
  "Why can a 70B model sit in host RAM and still fail to run on the GPU?",
  "Why does a second turn forget the first if I used LLMChain?",
];

function TutorInner() {
  const sp = useSearchParams();
  const preset = sp.get("q") || sp.get("note");
  const [q, setQ] = useState(preset ? (sp.get("note") ? `Please discuss my note: ${preset}` : preset) : "");
  const [depth, setDepth] = useState("ENGINEER");
  const [mode, setMode] = useState("COURSE");
  const [session, setSession] = useState<string | undefined>();
  const [msgs, setMsgs] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const abortRef = useRef(false);

  useEffect(() => {
    api("/me").then((m: any) => setMode(m.tutor_mode || "COURSE"));
  }, []);

  async function send(text: string) {
    if (!text.trim()) return;
    abortRef.current = false;
    setBusy(true);
    setMsgs((m) => [...m, { role: "user", text }]);
    setQ("");
    try {
      const r: any = await api("/tutor", {
        method: "POST",
        body: JSON.stringify({ content: text, session_id: session, mode, depth }),
      });
      if (abortRef.current) return;
      setSession(r.session_id);
      setMsgs((m) => [...m, r]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4">
      <header>
        <p className="text-xs uppercase tracking-[0.2em] text-[#76b900]">Tutor</p>
        <h1 className="mt-1 text-3xl font-semibold">Ask for the mechanism.</h1>
        <p className="mt-2" style={{ color: "var(--muted)" }}>
          Good questions start with “what happens” or “why,” not “define.” The tutor cites a notebook cell, then
          tells you what to try.
        </p>
      </header>
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <select value={mode} onChange={(e) => setMode(e.target.value)} className="field w-auto py-1" aria-label="Tutor mode">
          <option>COURSE</option>
          <option>RESEARCH</option>
        </select>
        <select value={depth} onChange={(e) => setDepth(e.target.value)} className="field w-auto py-1" aria-label="Explanation depth">
          <option>SCHOOL</option>
          <option>ENGINEER</option>
          <option>RESEARCH</option>
        </select>
      </div>
      <div className="flex flex-wrap gap-2">
        {STARTERS.map((c) => (
          <button
            key={c}
            className="rounded-full border px-3 py-1 text-left text-xs"
            style={{ borderColor: "var(--line)" }}
            onClick={() => send(c)}
          >
            {c}
          </button>
        ))}
      </div>
      <div className="panel min-h-[420px] space-y-5 p-5">
        {msgs.length === 0 && (
          <p style={{ color: "var(--muted)" }}>Pick a starter, or type a “what happens if…” question.</p>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : ""}>
            {m.role === "user" ? (
              <p className="inline-block rounded-lg bg-[#1c2618] px-3 py-2 text-left">{m.text}</p>
            ) : (
              <TeachAnswer m={m} />
            )}
          </div>
        ))}
        {busy && <p>Thinking through the mechanism…</p>}
      </div>
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          send(q);
        }}
      >
        <input className="field flex-1" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Ask the tutor" placeholder="What actually happens when…?" />
        <button className="rounded-lg bg-[#76b900] px-4 text-black" disabled={busy}>
          Send
        </button>
      </form>
    </div>
  );
}

function TeachAnswer({ m }: { m: any }) {
  const blocks = splitTeach(m.text || "");
  return (
    <div className="space-y-3 text-left">
      {blocks.map((b, i) => (
        <div key={i}>
          {b.heading && <h3 className="text-sm font-medium text-[#76b900]">{b.heading}</h3>}
          <p className="mt-1 whitespace-pre-wrap leading-relaxed">{b.body}</p>
        </div>
      ))}
      {m.sources?.length > 0 && (
        <ul className="text-xs" style={{ color: "var(--muted)" }}>
          {m.sources.slice(0, 3).map((s: any) => (
            <li key={s.span_id || `${s.file}-${s.cell_index}`}>
              <Link className="text-[#76b900]" href={notebookHref(s.file, s.cell_index)}>
                {s.file} · cell {s.cell_index}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function splitTeach(text: string): { heading: string; body: string }[] {
  const heads = [
    "What's happening",
    "A picture that sticks",
    "From the notebook",
    "The trap",
    "Try this",
    "Hint, not the answer",
    "Compared side by side",
    "External research",
  ];
  const rest = text.trim();
  const idxs = heads
    .map((h) => ({ h, i: rest.indexOf(h) }))
    .filter((x) => x.i >= 0)
    .sort((a, b) => a.i - b.i);
  if (!idxs.length) return [{ heading: "", body: rest }];
  const parts: { heading: string; body: string }[] = [];
  if (idxs[0].i > 0) parts.push({ heading: "", body: rest.slice(0, idxs[0].i).trim() });
  for (let n = 0; n < idxs.length; n++) {
    const lineEnd = rest.indexOf("\n", idxs[n].i);
    const end = n + 1 < idxs.length ? idxs[n + 1].i : rest.length;
    const heading = (lineEnd === -1 ? rest.slice(idxs[n].i) : rest.slice(idxs[n].i, lineEnd)).trim();
    const body = (lineEnd === -1 ? "" : rest.slice(lineEnd + 1, end)).trim();
    parts.push({ heading, body });
  }
  return parts.filter((p) => p.body || p.heading);
}

export default function TutorPage() {
  return (
    <Suspense fallback={<p>Loading tutor…</p>}>
      <TutorInner />
    </Suspense>
  );
}
