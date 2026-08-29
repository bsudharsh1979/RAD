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
  const [unavailable, setUnavailable] = useState(false);
  const utterRef = useRef<SpeechSynthesisUtterance | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const finishTimes = useRef<number[]>([]);
  const cacheKey = useRef<string>("");

  useEffect(() => {
    const saved = localStorage.getItem(DEPTH_KEY);
    if (saved === "expert" || saved === "simple") setDepth(saved);
  }, []);

  useEffect(() => {
    if (!open) return;
    const key = `${notebookId}:${depth}`;
    cacheKey.current = key;
    setErr(null);
    setUnavailable(false);
    finishTimes.current = [];
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

  const stopVoice = useCallback(() => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = "";
      audioRef.current = null;
    }
    utterRef.current = null;
  }, []);

  const speak = useCallback(
    async (text: string, onEnd: () => void) => {
      stopVoice();
      try {
        const r: any = await api("/voice/tts", {
          method: "POST",
          body: JSON.stringify({ text, provider: "auto", clip: false, language: "en" }),
        });
        if (r?.audio_b64) {
          const a = new Audio(`data:${r.mime || "audio/mpeg"};base64,${r.audio_b64}`);
          a.playbackRate = speed;
          a.onended = () => onEnd();
          a.onerror = () => {
            setUnavailable(true);
            setPlaying(false);
          };
          audioRef.current = a;
          await a.play();
          return;
        }
      } catch {
        /* fall through to browser voice */
      }
      if (!window.speechSynthesis) {
        setUnavailable(true);
        setPlaying(false);
        return;
      }
      const u = new SpeechSynthesisUtterance(text);
      u.rate = Math.max(0.6, Math.min(1.6, 0.93 * speed));
      const started = Date.now();
      u.onend = () => {
        const elapsed = Date.now() - started;
        if (elapsed < 400) {
          finishTimes.current.push(elapsed);
          if (finishTimes.current.filter((t) => t < 400).length >= 2) {
            setUnavailable(true);
            setPlaying(false);
            stopVoice();
            return;
          }
        } else {
          finishTimes.current = [];
        }
        onEnd();
      };
      u.onerror = () => {
        setUnavailable(true);
        setPlaying(false);
      };
      utterRef.current = u;
      window.speechSynthesis.speak(u);
    },
    [speed, stopVoice],
  );

  const go = useCallback(
    (next: number) => {
      if (!data) return;
      const bounded = Math.max(0, Math.min(data.steps.length - 1, next));
      setIdx(bounded);
    },
    [data],
  );

  useEffect(() => {
    if (!playing || !step || unavailable) return;
    void speak(step.narration, () => {
      if (idx < (data?.steps.length || 1) - 1) {
        setIdx((i) => i + 1);
      } else {
        setPlaying(false);
      }
    });
    return () => stopVoice();
  }, [playing, idx, step, speak, stopVoice, unavailable, data?.steps.length]);

  const toggleDepth = (d: "simple" | "expert") => {
    stopVoice();
    setPlaying(false);
    setDepth(d);
    localStorage.setItem(DEPTH_KEY, d);
  };

  const stages = useMemo(() => data?.steps.filter((s) => s.kind === "stage") || [], [data]);

  if (!open) {
    return (
      <button className="rounded bg-[#76b900] px-3 py-2 text-sm text-black" onClick={() => setOpen(true)}>
        Play audio lecture
      </button>
    );
  }

  return (
    <div className="sticky bottom-3 z-20 panel p-4 shadow-lg" data-testid="walkthrough-player">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-xs uppercase tracking-[0.15em] text-[#76b900]">Audio lecture</p>
          <h2 className="text-lg">{data?.title || "Loading walkthrough…"}</h2>
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
      {unavailable && (
        <p className="mt-2 text-sm text-amber-400">audio unavailable — step through manually</p>
      )}
      {step && (
        <div className="mt-3 space-y-2">
          <p className="text-xs" style={{ color: "var(--muted)" }}>
            {idx + 1}/{data?.steps.length} · {step.kind.replace("_", " ")} · cells {step.cell_start}–{step.cell_end} · ~
            {step.duration_s}s
          </p>
          <p className="text-sm leading-relaxed">{step.narration}</p>
          <div className="flex flex-wrap items-center gap-2">
            <button className="rounded border px-2 py-1 text-xs" onClick={() => go(idx - 1)}>
              Prev
            </button>
            <button
              className="rounded bg-[#76b900] px-3 py-1 text-xs text-black"
              onClick={() => {
                if (unavailable) return;
                setPlaying((p) => !p);
                if (playing) stopVoice();
              }}
            >
              {playing ? "Pause" : "Play"}
            </button>
            <button className="rounded border px-2 py-1 text-xs" onClick={() => go(idx + 1)}>
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
                onClick={() => {
                  stopVoice();
                  setPlaying(false);
                  setIdx(i);
                }}
                title={`${s.title} · ${s.duration_s}s`}
              >
                {s.kind === "stage" ? s.title : s.kind.replace("_", " ")} · {s.duration_s}s
              </button>
            ))}
          </div>
          {stages.length > 0 && (
            <p className="text-xs" style={{ color: "var(--muted)" }}>
              Narrating this stage: cells {step.cell_start}–{step.cell_end}
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
