"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "@/lib/api";

type Step = {
  kind: string;
  title: string;
  narration: string;
  cell_start: number;
  cell_end: number;
  duration_s: number;
  chars?: number;
};

type Walkthrough = {
  file: string;
  depth: string;
  title: string;
  steps: Step[];
  disclaimer?: string;
};

type Clip = { b64: string; mime: string };

const DEPTH_KEY = "walkthrough-depth";

export function WalkthroughPlayer({
  notebookId,
  onRange,
  autoOpen = false,
}: {
  notebookId: string;
  onRange?: (start: number, end: number) => void;
  autoOpen?: boolean;
}) {
  const [open, setOpen] = useState(autoOpen);
  const [depth, setDepth] = useState<"simple" | "expert">("simple");
  const [data, setData] = useState<Walkthrough | null>(null);
  const [idx, setIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [err, setErr] = useState<string | null>(null);
  const [hint, setHint] = useState<string | null>(null);
  const [loadingVoice, setLoadingVoice] = useState(false);
  const audioEl = useRef<HTMLAudioElement | null>(null);
  const cache = useRef<Map<string, Clip>>(new Map());
  const gen = useRef(0);

  useEffect(() => {
    const saved = localStorage.getItem(DEPTH_KEY);
    if (saved === "expert" || saved === "simple") setDepth(saved);
  }, []);

  useEffect(() => {
    if (!open) return;
    setErr(null);
    setHint(null);
    api<Walkthrough>(`/notebooks/${encodeURIComponent(notebookId)}/walkthrough?depth=${depth}`)
      .then((d) => {
        setData(d);
        setIdx(0);
      })
      .catch((e) => setErr(String(e)));
  }, [open, notebookId, depth]);

  const step = data?.steps[idx];

  useEffect(() => {
    if (step && onRange) onRange(step.cell_start, step.cell_end);
  }, [step, onRange]);

  const prefetch = useCallback(async (text: string): Promise<Clip | null> => {
    const hit = cache.current.get(text);
    if (hit) return hit;
    const r: any = await api("/voice/tts", {
      method: "POST",
      body: JSON.stringify({ text, provider: "auto", clip: false, language: "en" }),
    });
    if (r?.audio_b64) {
      const clip = { b64: r.audio_b64 as string, mime: (r.mime as string) || "audio/mpeg" };
      cache.current.set(text, clip);
      return clip;
    }
    return null;
  }, []);

  useEffect(() => {
    if (!open || !step) return;
    void prefetch(step.narration).catch(() => null);
  }, [open, step, prefetch]);

  const stopVoice = useCallback(() => {
    gen.current += 1;
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    const el = audioEl.current;
    if (el) {
      el.onended = null;
      el.onerror = null;
      el.pause();
    }
  }, []);

  const advance = useCallback(() => {
    setIdx((i) => {
      const last = (data?.steps.length || 1) - 1;
      if (i >= last) {
        setPlaying(false);
        return i;
      }
      return i + 1;
    });
  }, [data?.steps.length]);

  const speak = useCallback(
    async (text: string) => {
      const my = ++gen.current;
      setHint(null);
      setLoadingVoice(true);
      let clip: Clip | null = cache.current.get(text) || null;
      if (!clip) {
        try {
          clip = await prefetch(text);
        } catch {
          clip = null;
        }
      }
      if (my !== gen.current) return;
      setLoadingVoice(false);

      const el = audioEl.current;
      if (clip && el) {
        el.src = `data:${clip.mime};base64,${clip.b64}`;
        el.playbackRate = speed;
        el.onended = () => {
          if (my === gen.current) advance();
        };
        el.onerror = () => {
          if (my !== gen.current) return;
          setHint("Could not play the audio file. Press Play again, or use Next.");
          setPlaying(false);
        };
        try {
          await el.play();
          return;
        } catch {
          if (my !== gen.current) return;
          setHint("Voice is cached — press Play once more (browsers block autoplay after a network wait).");
          setPlaying(false);
          return;
        }
      }

      if (typeof window === "undefined" || !window.speechSynthesis) {
        setHint("No voice in this browser. Read the lecture and use Next.");
        setPlaying(false);
        return;
      }
      const u = new SpeechSynthesisUtterance(text);
      u.rate = Math.max(0.6, Math.min(1.6, 0.93 * speed));
      u.onend = () => {
        if (my === gen.current) advance();
      };
      u.onerror = (ev) => {
        if (my !== gen.current) return;
        const why = (ev as SpeechSynthesisErrorEvent).error;
        if (why === "interrupted" || why === "canceled") return;
        setHint("Browser voice failed. Use Next, or press Play again.");
        setPlaying(false);
      };
      window.speechSynthesis.speak(u);
    },
    [advance, prefetch, speed],
  );

  useEffect(() => {
    if (!playing || !step) return;
    void speak(step.narration);
    return () => stopVoice();
  }, [playing, idx, step, speak, stopVoice]);

  const go = (next: number) => {
    if (!data) return;
    stopVoice();
    setPlaying(false);
    setIdx(Math.max(0, Math.min(data.steps.length - 1, next)));
  };

  const toggleDepth = (d: "simple" | "expert") => {
    stopVoice();
    setPlaying(false);
    setDepth(d);
    localStorage.setItem(DEPTH_KEY, d);
  };

  const stages = useMemo(() => data?.steps.filter((s) => s.kind === "stage") || [], [data]);

  if (!open) {
    return (
      <button className="rounded-lg bg-[#76b900] px-4 py-2 text-sm font-medium text-black" onClick={() => setOpen(true)}>
        Play audio lecture
      </button>
    );
  }

  return (
    <div className="sticky bottom-3 z-20 panel p-5 shadow-lg" data-testid="walkthrough-player">
      <audio ref={audioEl} preload="auto" className="hidden" />
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-xs uppercase tracking-[0.15em] text-[#76b900]">Audio lecture</p>
          <h2 className="text-lg font-medium">{data?.title || "Loading walkthrough…"}</h2>
        </div>
        <div className="flex gap-2">
          <button
            className={`rounded px-2 py-1 text-xs ${depth === "simple" ? "bg-[#76b900] text-black" : "border"}`}
            onClick={() => toggleDepth("simple")}
          >
            SIMPLE
          </button>
          <button
            className={`rounded px-2 py-1 text-xs ${depth === "expert" ? "bg-[#76b900] text-black" : "border"}`}
            onClick={() => toggleDepth("expert")}
          >
            EXPERT
          </button>
          <button
            className="rounded border px-2 py-1 text-xs"
            onClick={() => {
              stopVoice();
              setPlaying(false);
              setOpen(false);
              if (onRange) onRange(-1, -1);
            }}
          >
            Close
          </button>
        </div>
      </div>
      {err && <p className="mt-2 text-sm text-amber-400">{err}</p>}
      {hint && <p className="mt-2 text-sm text-amber-300">{hint}</p>}
      {loadingVoice && <p className="mt-2 text-xs" style={{ color: "var(--muted)" }}>Fetching voice…</p>}
      {step && (
        <div className="mt-3 space-y-3">
          <p className="text-xs" style={{ color: "var(--muted)" }}>
            {idx + 1}/{data?.steps.length} · {step.kind.replace("_", " ")} · cells {step.cell_start}–{step.cell_end}
          </p>
          <p className="text-base leading-relaxed">{step.narration}</p>
          <div className="flex flex-wrap items-center gap-2">
            <button className="rounded border px-3 py-1 text-sm" onClick={() => go(idx - 1)}>
              Prev
            </button>
            <button
              className="rounded bg-[#76b900] px-4 py-1 text-sm font-medium text-black"
              onClick={() => {
                if (playing) {
                  stopVoice();
                  setPlaying(false);
                } else {
                  setPlaying(true);
                }
              }}
            >
              {playing ? "Pause" : "Play"}
            </button>
            <button className="rounded border px-3 py-1 text-sm" onClick={() => go(idx + 1)}>
              Next
            </button>
            <label className="text-xs">
              Speed{" "}
              <select
                className="field inline-block w-auto py-0"
                value={speed}
                onChange={(e) => setSpeed(Number(e.target.value))}
              >
                {[0.75, 1, 1.25, 1.5].map((s) => (
                  <option key={s} value={s}>
                    {s}×
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="flex flex-wrap gap-1">
            {data?.steps.map((s, i) => (
              <button
                key={`${s.kind}-${i}`}
                className={`rounded px-2 py-1 text-[11px] ${i === idx ? "bg-[#1c2618] text-[#76b900]" : "bg-[#171c18]"}`}
                onClick={() => go(i)}
                title={s.title}
              >
                {s.kind === "stage" ? s.title : s.kind.replace("_", " ")}
              </button>
            ))}
          </div>
          {stages.length > 0 && (
            <p className="text-xs" style={{ color: "var(--muted)" }}>
              This stage covers cells {step.cell_start}–{step.cell_end}
            </p>
          )}
        </div>
      )}
      <p className="mt-3 text-[11px]" style={{ color: "var(--muted)" }}>
        {data?.disclaimer}
      </p>
    </div>
  );
}
