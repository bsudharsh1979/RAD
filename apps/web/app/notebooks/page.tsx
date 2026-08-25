"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function NotebooksPage() {
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => {
    api<any[]>("/notebooks").then(setRows);
  }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Notebook studio</h1>
      <p className="text-[#9aa89a]">All eight NVIDIA DLI notebooks. Code is never executed here.</p>
      <div className="grid gap-3 md:grid-cols-2">
        {rows.map((n) => (
          <Link key={n.id} href={`/notebooks/${encodeURIComponent(n.filename)}`} className="panel block p-4 hover:border-[#76b900]">
            <div className="text-xs text-[#76b900]">Lab {n.order}</div>
            <h2 className="text-lg">{String(n.title).replace(/^\d+:\s*/, "")}</h2>
            <p className="mt-2 text-sm text-[#9aa89a]">{n.purpose}</p>
            <p className="mt-1 text-xs">{n.n_cells} cells</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
