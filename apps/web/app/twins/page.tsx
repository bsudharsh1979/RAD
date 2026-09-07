"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function TwinsIndex() {
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => {
    api<any[]>("/twins").then(setRows);
  }, []);
  return (
    <div className="space-y-5">
      <header className="max-w-3xl">
        <p className="text-xs uppercase tracking-[0.2em] text-[#76b900]">Digital twins</p>
        <h1 className="mt-2 text-4xl font-semibold">Predict first. Then watch the mechanism.</h1>
        <p className="mt-3" style={{ color: "var(--muted)" }}>
          Every number is a simulation unless you import an ACTUAL_RUN. Lock a prediction before you run.
        </p>
      </header>
      <div className="grid gap-3 md:grid-cols-2">
        {rows.map((t) => (
          <Link key={t.id} href={`/twins/${t.id}`} className="panel block p-4 hover:border-[#76b900]">
            <h2 className="text-lg font-medium">{t.name}</h2>
            <p className="mt-2 text-sm leading-relaxed" style={{ color: "var(--muted)" }}>
              {t.summary}
            </p>
            <p className="mt-2 text-xs">{t.notebook_file}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
