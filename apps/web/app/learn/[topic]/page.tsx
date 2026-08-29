"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { conceptHref, notebookHref, twinHref } from "@/lib/paths";

type Concept = {
  id: string;
  name: string;
  definition: string;
  analogy: string;
  school: string;
  engineer: string;
  research: string;
  notebook_file: string;
  cell_index: number;
  twin_id: string;
};

type Topic = {
  id: string;
  order: number;
  title: string;
  hook: string;
  promise: string;
  minutes: number;
  notebook: string;
  twin: string;
  ask: string;
  concepts: Concept[];
};

export default function TopicPage() {
  const { topic } = useParams<{ topic: string }>();
  const [data, setData] = useState<Topic | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => {
    api<Topic>(`/topics/${topic}`)
      .then((t) => {
        setData(t);
        setOpen(t.concepts?.[0]?.id || null);
      })
      .catch((e) => setErr(String(e)));
  }, [topic]);

  if (err) return <p className="text-amber-300">Unknown topic. {err}</p>;
  if (!data) return <p>Loading story…</p>;

  return (
    <article className="mx-auto max-w-3xl space-y-6">
      <Link href="/learn" className="text-sm" style={{ color: "var(--muted)" }}>
        ← All topics
      </Link>
      <header>
        <p className="text-xs uppercase tracking-[0.2em] text-[#76b900]">
          Story {data.order} · {data.minutes} minutes
        </p>
        <h1 className="mt-2 text-4xl font-semibold leading-tight">{data.title}</h1>
        <p className="mt-4 text-lg leading-relaxed">{data.hook}</p>
        <p className="mt-3" style={{ color: "var(--muted)" }}>
          You’ll walk away able to: {data.promise}
        </p>
      </header>
      <div className="flex flex-wrap gap-3">
        <Link className="rounded-lg bg-[#76b900] px-4 py-2 text-black" href={notebookHref(data.notebook)}>
          Hear the lecture
        </Link>
        <Link className="rounded-lg border px-4 py-2" href={twinHref(data.twin)}>
          Run the twin
        </Link>
        <Link className="rounded-lg border px-4 py-2" href={`/tutor?q=${encodeURIComponent(data.ask)}`}>
          Ask the tutor this
        </Link>
      </div>
      <section className="space-y-3">
        <h2 className="text-sm uppercase tracking-[0.15em] text-[#76b900]">The moving parts</h2>
        {data.concepts.map((c, i) => {
          const shown = open === c.id;
          return (
            <div key={c.id} className="panel overflow-hidden">
              <button
                className="flex w-full items-center justify-between px-5 py-4 text-left"
                onClick={() => setOpen(shown ? null : c.id)}
              >
                <span>
                  <span className="mr-2 text-xs text-[#76b900]">{i + 1}</span>
                  {c.name}
                </span>
                <span className="text-xs" style={{ color: "var(--muted)" }}>
                  {shown ? "Hide" : "Teach me"}
                </span>
              </button>
              {shown && (
                <div className="space-y-3 border-t px-5 pb-5 pt-3" style={{ borderColor: "var(--line)" }}>
                  <p className="leading-relaxed">{c.engineer || c.definition}</p>
                  {(c.analogy || c.school) && (
                    <p className="text-sm" style={{ color: "var(--muted)" }}>
                      Picture: {c.analogy || c.school}
                    </p>
                  )}
                  {c.research && (
                    <p className="text-sm">
                      Trap: {c.research}
                    </p>
                  )}
                  <Link className="text-sm text-[#76b900]" href={conceptHref(c.id)}>
                    Open as a full lesson
                  </Link>
                </div>
              )}
            </div>
          );
        })}
      </section>
    </article>
  );
}
