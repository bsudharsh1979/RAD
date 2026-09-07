"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { notebookHref, topicHref, twinHref } from "@/lib/paths";

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
  concepts?: { id: string; name: string; definition: string }[];
};

type ConceptDetail = {
  concept: {
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
};

export default function LearnInner() {
  const sp = useSearchParams();
  const cid = sp.get("concept");
  const [topics, setTopics] = useState<Topic[] | null>(null);
  const [detail, setDetail] = useState<ConceptDetail | null>(null);

  useEffect(() => {
    api<Topic[]>("/topics").then(setTopics);
  }, []);
  useEffect(() => {
    if (cid) api<ConceptDetail>(`/concepts/${cid}`).then(setDetail);
    else setDetail(null);
  }, [cid]);

  if (!topics) return <p>Loading topics…</p>;

  if (cid && detail?.concept) {
    const c = detail.concept;
    const parent = topics.find((t) => t.concepts?.some((x) => x.id === c.id));
    return (
      <article className="mx-auto max-w-3xl space-y-5">
        {parent && (
          <Link href={topicHref(parent.id)} className="text-sm" style={{ color: "var(--muted)" }}>
            ← {parent.title}
          </Link>
        )}
        <p className="text-xs uppercase tracking-[0.2em] text-[#76b900]">Concept</p>
        <h1 className="text-4xl font-semibold">{c.name}</h1>
        <section className="panel space-y-4 p-6">
          <Block title="What's happening" body={c.engineer || c.definition} />
          <Block title="A picture that sticks" body={c.analogy || c.school} />
          <Block title="School version" body={c.school} />
          <Block title="The trap" body={c.research} />
        </section>
        <div className="flex flex-wrap gap-3">
          <Link className="rounded-lg bg-[#76b900] px-4 py-2 text-black" href={notebookHref(c.notebook_file, c.cell_index)}>
            Open the lecture
          </Link>
          {c.twin_id && (
            <Link className="rounded-lg border px-4 py-2" href={twinHref(c.twin_id)}>
              Try the twin
            </Link>
          )}
          <Link className="rounded-lg border px-4 py-2" href={`/tutor?q=${encodeURIComponent(`Teach me ${c.name} as a mechanism, not a definition.`)}`}>
            Ask the tutor
          </Link>
        </div>
      </article>
    );
  }

  return (
    <div className="space-y-6">
      <header className="max-w-3xl">
        <p className="text-xs uppercase tracking-[0.2em] text-[#76b900]">Learn by topic</p>
        <h1 className="mt-2 text-4xl font-semibold">Pick a story, not a syllabus dump.</h1>
        <p className="mt-3" style={{ color: "var(--muted)" }}>
          Each track is five ideas, one notebook, one twin. Finish when you can explain the moving parts out loud.
        </p>
      </header>
      <div className="grid gap-4 lg:grid-cols-2">
        {topics.map((t) => (
          <Link key={t.id} href={topicHref(t.id)} className="panel block p-5 hover:border-[#76b900]">
            <p className="text-xs uppercase tracking-[0.15em] text-[#76b900]">
              {String(t.order).padStart(2, "0")} · {t.minutes} min
            </p>
            <h2 className="mt-2 text-xl font-medium">{t.title}</h2>
            <p className="mt-2 text-sm leading-relaxed" style={{ color: "var(--muted)" }}>
              {t.hook}
            </p>
            <p className="mt-3 text-sm">Walk away able to: {t.promise}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}

function Block({ title, body }: { title: string; body?: string }) {
  if (!body) return null;
  return (
    <div>
      <h2 className="text-sm font-medium text-[#76b900]">{title}</h2>
      <p className="mt-1 leading-relaxed">{body}</p>
    </div>
  );
}
