"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";

export default function TutorPage() {
  const [q, setQ] = useState("Explain HuggingFace pipelines using the course notebooks.");
  const [depth, setDepth] = useState("ENGINEER");
  const [mode, setMode] = useState("COURSE");
  const [session, setSession] = useState<string | undefined>();
  const [msgs, setMsgs] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const [voice, setVoice] = useState(false);

  useEffect(() => {
    api("/me").then((m: any) => setMode(m.tutor_mode || "COURSE"));
  }, []);

  async function send(text: string) {
    setBusy(true);
    setMsgs((m) => [...m, { role: "user", text }]);
    const r: any = await api("/tutor", {
      method: "POST",
      body: JSON.stringify({ content: text, session_id: session, mode, depth }),
    });
    setSession(r.session_id);
    setMsgs((m) => [...m, r]);
    setBusy(false);
  }

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl">Tutor</h1>
        <div className="flex gap-2 text-sm">
          <select value={mode} onChange={(e) => setMode(e.target.value)} className="rounded bg-[#141816] p-1" aria-label="Tutor mode">
            <option>COURSE</option>
            <option>RESEARCH</option>
          </select>
          <select value={depth} onChange={(e) => setDepth(e.target.value)} className="rounded bg-[#141816] p-1" aria-label="Explanation depth">
            <option>SCHOOL</option>
            <option>ENGINEER</option>
            <option>RESEARCH</option>
          </select>
          <button className="rounded border border-[#2a322c] px-2" onClick={() => setVoice(!voice)}>
            Voice {voice ? "on" : "off"}
          </button>
        </div>
      </div>
      <div className="flex flex-wrap gap-2 text-xs">
        {["simpler", "deeper", "show source", "quiz me", "give hint", "compare encoder vs decoder", "show digital twin", "let me teach it back", "show current inference telemetry"].map((c) => (
          <button key={c} className="rounded-full border border-[#2a322c] px-2 py-1" onClick={() => send(c)}>
            {c}
          </button>
        ))}
      </div>
      <div className="panel min-h-[420px] space-y-4 p-4">
        {msgs.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : ""}>
            {m.role === "user" ? (
              <p className="inline-block rounded-lg bg-[#1c2618] px-3 py-2">{m.text}</p>
            ) : (
              <div className="space-y-2">
                <EvidenceBadge type={m.evidence_type} />
                <pre className="whitespace-pre-wrap font-sans text-sm">{m.text}</pre>
                {m.sources?.length > 0 && (
                  <ul className="text-xs text-[#9aa89a]">
                    {m.sources.map((s: any) => (
                      <li key={s.span_id}>
                        <Link className="text-[#76b900]" href={`/notebooks/${s.file}`}>
                          View source · {s.file} · cell {s.cell_index}
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
                {m.how_served && (
                  <details className="text-xs text-[#9aa89a]">
                    <summary>How this answer was served</summary>
                    <pre>{JSON.stringify(m.how_served, null, 2)}</pre>
                    <button className="mt-1 text-[#76b900]" onClick={() => send("Explain these metrics")}>
                      Explain these metrics
                    </button>
                  </details>
                )}
              </div>
            )}
          </div>
        ))}
        {busy && <p>Thinking…</p>}
      </div>
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          send(q);
        }}
      >
        <input className="flex-1 rounded-lg bg-[#141816] p-2" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Ask the tutor" />
        <button className="rounded-lg bg-[#76b900] px-4 text-black" disabled={busy}>
          Send
        </button>
      </form>
      {voice && (
        <p className="text-xs text-[#9aa89a]">
          Voice is optional. Interruption is supported by the VoiceProvider interface; configure ElevenLabs/Sarvam in Settings. Barge-in cancels in-flight TTS.
        </p>
      )}
    </div>
  );
}
