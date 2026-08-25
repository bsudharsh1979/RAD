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
    <div className="space-y-4">
      <h1 className="text-3xl">Digital twins</h1>
      <p className="text-[#9aa89a]">
        Web twins share TwinStateEngine with the optional Omniverse bridge. Every number is a simulation unless you import an ACTUAL_RUN.
      </p>
      <div className="grid gap-3 md:grid-cols-2">
        {rows.map((t) => (
          <Link key={t.id} href={`/twins/${t.id}`} className="panel block p-4 hover:border-[#76b900]">
            <h2 className="text-lg">{t.name}</h2>
            <p className="mt-2 text-sm text-[#9aa89a]">{t.summary}</p>
            <p className="mt-2 text-xs">{t.notebook_file}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
