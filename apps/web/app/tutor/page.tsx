"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";
import { notebookHref } from "@/lib/paths";

function TutorInner() {
  const sp = useSearchParams();
  const [q, setQ] = useState(sp.get("note") ? `Please discuss my note: ${sp.get("note")}` : "Explain HuggingFace pipelines using the course notebooks.");
  const [depth, setDepth] = useState("ENGINEER");
  const [mode, setMode] = useState("COURSE");
  const [session, setSession] = useState<string | undefined>();
  const [msgs, setMsgs] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const [voice, setVoice] = useState(false);
  const [listening, setListening] = useState(false);
  const recRef = useRef<any>(null);
  const abortRef = useRef(false);

  useEffect(() => {
    api("/me").then((m: any) => setMode(m.tutor_mode || "COURSE"));
  }, []);

  async function send(text: string) {
    abortRef.current = false;
    setBusy(true);
    setMsgs((m) => [...m, { role: "user", text }]);
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

  function bargeIn() {
    abortRef.current = true;
    setBusy(false);
    window.speechSynthesis?.cancel();
    recRef.current?.stop?.();
    setListening(false);
  }

  function listen() {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      setMsgs((m) => [...m, { role: "assistant", text: "Browser speech recognition is unavailable. Type instead.", evidence_type: "TUTOR_INTERPRETATION" }]);
      return;
    }
    const rec = new SR();
    recRef.current = rec;
    rec.lang = "en-US";
    rec.onresult = (ev: any) => {
      const t = ev.results[0][0].transcript;
      setQ(t);
      send(t);
    };
    rec.onend = () => setListening(false);
    setListening(true);
    rec.start();
  }

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl">Tutor</h1>
        <div className="flex gap-2 text-sm">
          <select value={mode} onChange={(e) => setMode(e.target.value)} className="field w-auto py-1" aria-label="Tutor mode">
            <option>COURSE</option>
            <option>RESEARCH</option>
          </select>
          <select value={depth} onChange={(e) => setDepth(e.target.value)} className="field w-auto py-1" aria-label="Explanation depth">
            <option>SCHOOL</option>
            <option>ENGINEER</option>
            <option>RESEARCH</option>
          </select>
          <button className="rounded border px-2" style={{ borderColor: "var(--line)" }} onClick={() => setVoice(!voice)}>
            Voice {voice ? "on" : "off"}
          </button>
        </div>
      </div>
      <div className="flex flex-wrap gap-2 text-xs">
        {["simpler", "deeper", "show source", "quiz me", "give hint", "compare encoder vs decoder", "show digital twin", "let me teach it back", "show current inference telemetry"].map((c) => (
          <button key={c} className="rounded-full border px-2 py-1" style={{ borderColor: "var(--line)" }} onClick={() => send(c)}>
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
                  <ul className="text-xs" style={{ color: "var(--muted)" }}>
                    {m.sources.map((s: any) => (
                      <li key={s.span_id}>
                        <Link className="text-[#76b900]" href={notebookHref(s.file, s.cell_index)}>
                          View source · {s.file} · cell {s.cell_index}
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
                {m.quiz && (
                  <div className="rounded border p-3 text-sm" style={{ borderColor: "var(--line)" }}>
                    <p>{m.quiz.stem}</p>
                    <Link className="text-[#76b900]" href={`/practice?concept=${m.quiz.concept_id}`}>
                      Answer in Practice (no reveal here)
                    </Link>
                  </div>
                )}
                {m.how_served && (
                  <details className="text-xs" style={{ color: "var(--muted)" }}>
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
        <input className="field flex-1" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Ask the tutor" />
        <button className="rounded-lg bg-[#76b900] px-4 text-black" disabled={busy}>
          Send
        </button>
      </form>
      {voice && (
        <div className="flex flex-wrap gap-2 text-sm">
          <button className="rounded border px-3 py-1" style={{ borderColor: "var(--line)" }} onClick={listen}>
            {listening ? "Listening…" : "Speak"}
          </button>
          <button className="rounded border px-3 py-1" style={{ borderColor: "var(--line)" }} onClick={bargeIn}>
            Stop / barge-in
          </button>
          <p className="text-xs" style={{ color: "var(--muted)" }}>
            Browser speech is optional. ElevenLabs/Sarvam stay off unless configured in Settings. Interruption cancels in-flight speech.
          </p>
        </div>
      )}
    </div>
  );
}

export default function TutorPage() {
  return (
    <Suspense fallback={<p>Loading tutor…</p>}>
      <TutorInner />
    </Suspense>
  );
}
