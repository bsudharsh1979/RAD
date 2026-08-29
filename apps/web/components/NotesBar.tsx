"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export function NotesBar({ targetType, targetId }: { targetType: string; targetId: string }) {
  const [body, setBody] = useState("");
  const [saved, setSaved] = useState("");
  return (
    <div className="mt-3 space-y-2 text-sm">
      <textarea
        className="w-full rounded bg-[color:var(--bg)] p-2"
        placeholder="Personal note…"
        value={body}
        onChange={(e) => setBody(e.target.value)}
        aria-label="Personal note"
      />
      <div className="flex flex-wrap gap-2">
        <button
          className="rounded border border-[color:var(--line)] px-2 py-1"
          onClick={async () => {
            await api("/notes", { method: "POST", body: JSON.stringify({ target_type: targetType, target_id: targetId, body }) });
            setSaved("Note saved");
          }}
        >
          Save note
        </button>
        <button
          className="rounded border border-[color:var(--line)] px-2 py-1"
          onClick={async () => {
            await api("/bookmarks", {
              method: "POST",
              body: JSON.stringify({ target_type: targetType, target_id: targetId, label: "Review later" }),
            });
            setSaved("Bookmarked for Review later");
          }}
        >
          Review later
        </button>
        <a className="rounded border border-[color:var(--line)] px-2 py-1" href={`/tutor?note=${encodeURIComponent(body)}`}>
          Ask tutor about my note
        </a>
      </div>
      {saved && <p className="text-xs text-[color:var(--muted)]">{saved}</p>}
    </div>
  );
}
