"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import Link from "next/link";

export default function ReviewPage() {
  const [data, setData] = useState<any>(null);
  useEffect(() => {
    api("/review").then(setData);
  }, []);
  if (!data) return <p>Loading reviews…</p>;
  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Reviews due today</h1>
      <p className="text-[#9aa89a]">{data.due} FSRS items are due. Cards are generated from misses, weak concepts, and misconceptions.</p>
      {data.questions?.length === 0 && (
        <p>
          Nothing due. <Link className="text-[#76b900]" href="/practice?mode=diagnostic">Take a diagnostic</Link> to schedule reviews.
        </p>
      )}
      <ul className="space-y-2">
        {data.questions?.map((q: any) => (
          <li key={q.id} className="panel p-3">
            <Link href="/practice">{q.stem.slice(0, 180)}</Link>
            <div className="text-xs text-[#9aa89a]">{q.source.file}</div>
          </li>
        ))}
      </ul>
    </div>
  );
}
