"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { notebookHref } from "@/lib/paths";

type Risk = {
  id: string;
  title: string;
  kind: string;
  leading_signal: string;
  spot_it_live: string;
  mitigation: string;
  example: string;
  twin: string;
  source_file: string;
};

export default function RisksPage() {
  const [rows, setRows] = useState<Risk[]>([]);
  useEffect(() => {
    api<Risk[]>("/risks").then(setRows);
  }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Risk radar</h1>
      <p style={{ color: "var(--muted)" }}>
        Curated technical, security, and business risks in our own words. Drill the matching twin — numbers there stay
        simulated.
      </p>
      <div className="grid gap-3 md:grid-cols-2">
        {rows.map((r) => (
          <article key={r.id} className="panel space-y-2 p-4">
            <p className="text-xs uppercase tracking-[0.15em] text-[#76b900]">{r.kind}</p>
            <h2 className="text-lg">{r.title}</h2>
            <p className="text-sm">
              <strong>Leading signal:</strong> {r.leading_signal}
            </p>
            <p className="text-sm">
              <strong>Spot it live:</strong> {r.spot_it_live}
            </p>
            <p className="text-sm">
              <strong>Mitigation:</strong> {r.mitigation}
            </p>
            <p className="text-sm" style={{ color: "var(--muted)" }}>
              Example: {r.example}
            </p>
            <div className="flex gap-3 text-sm">
              <Link className="text-[#76b900]" href={`/twins/${r.twin}`}>
                Twin drill
              </Link>
              <Link className="text-[#76b900]" href={notebookHref(r.source_file)}>
                {r.source_file}
              </Link>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
