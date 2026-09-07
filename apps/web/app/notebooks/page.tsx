"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { topicHref } from "@/lib/paths";

type Topic = { id: string; title: string; notebook: string; hook: string };

export default function NotebooksPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  useEffect(() => {
    api<any[]>("/notebooks").then(setRows);
    api<Topic[]>("/topics").then(setTopics);
  }, []);
  const byFile = useMemo(() => {
    const m: Record<string, Topic[]> = {};
    for (const t of topics) (m[t.notebook] ||= []).push(t);
    return m;
  }, [topics]);
  return (
    <div className="space-y-5">
      <header className="max-w-3xl">
        <p className="text-xs uppercase tracking-[0.2em] text-[#76b900]">Notebook studio</p>
        <h1 className="mt-2 text-4xl font-semibold">Eight labs. Hear them as stories.</h1>
        <p className="mt-3" style={{ color: "var(--muted)" }}>
          Code is never executed here. Open a lab to hear the lecture, then jump to the matching topic.
        </p>
      </header>
      <div className="grid gap-4 md:grid-cols-2">
        {rows.map((n) => (
          <div key={n.id} className="panel p-5">
            <div className="text-xs text-[#76b900]">Lab {n.order}</div>
            <h2 className="mt-1 text-xl font-medium">{String(n.title).replace(/^\d+:\s*/, "")}</h2>
            <p className="mt-2 text-sm leading-relaxed" style={{ color: "var(--muted)" }}>
              {n.purpose}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Link
                href={`/notebooks/${encodeURIComponent(n.filename)}?walkthrough=1`}
                className="rounded-lg bg-[#76b900] px-3 py-1 text-sm text-black"
              >
                Hear the lecture
              </Link>
              {(byFile[n.filename] || []).map((t) => (
                <Link key={t.id} href={topicHref(t.id)} className="rounded-lg border px-3 py-1 text-sm">
                  {t.title}
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
