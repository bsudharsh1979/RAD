"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const LINKS = [
  ["Home", "/"],
  ["Learn", "/learn"],
  ["Tutor", "/tutor"],
  ["Concept Map", "/concepts"],
  ["Notebooks", "/notebooks"],
  ["Digital Twins", "/twins"],
  ["Experiments", "/experiments"],
  ["Practice", "/practice"],
  ["Review", "/review"],
  ["Assessment", "/assessment"],
  ["Progress", "/progress"],
  ["Sources", "/sources"],
  ["Settings", "/settings"],
];

export function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const [light, setLight] = useState(false);
  useEffect(() => {
    document.documentElement.classList.toggle("light", light);
    document.documentElement.classList.toggle("dark", !light);
  }, [light]);
  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-56 shrink-0 border-r p-4 md:block" style={{ borderColor: "var(--line)", background: "var(--panel)" }}>
        <Link href="/" className="mb-6 block">
          <div className="text-xs uppercase tracking-[0.2em] text-[#76b900]">LLM Twin Academy</div>
          <div className="mt-1 text-sm" style={{ color: "var(--muted)" }}>
            NVIDIA DLI · RAD / LLMs
          </div>
        </Link>
        <nav className="flex flex-col gap-1" aria-label="Main">
          {LINKS.map(([label, href]) => {
            const active = href === "/" ? path === "/" : path.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={`rounded-lg px-3 py-2 text-sm ${active ? "bg-[#1c2618] text-[#76b900]" : "hover:bg-[#171c18]"}`}
              >
                {label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b px-4 py-3 md:hidden" style={{ borderColor: "var(--line)" }}>
          <span className="text-sm text-[#76b900]">LLM Twin Academy</span>
          <select
            aria-label="Navigate"
            className="field w-auto py-1"
            onChange={(e) => {
              window.location.href = e.target.value;
            }}
            value={LINKS.find(([, h]) => (h === "/" ? path === "/" : path.startsWith(h)))?.[1] || "/"}
          >
            {LINKS.map(([l, h]) => (
              <option key={h} value={h}>
                {l}
              </option>
            ))}
          </select>
        </header>
        <header className="flex items-center justify-between border-b px-4 py-3 md:px-8" style={{ borderColor: "var(--line)" }}>
          <span className="hidden text-sm md:inline" style={{ color: "var(--muted)" }}>
            Source-grounded · evidence-labeled · no silent GPU claims
          </span>
          <button
            className="rounded border px-2 py-1 text-xs"
            style={{ borderColor: "var(--line)" }}
            onClick={() => setLight((v) => !v)}
            aria-pressed={light}
          >
            {light ? "Dark mode" : "Light mode"}
          </button>
        </header>
        <main className="min-w-0 flex-1 p-4 md:p-8">{children}</main>
      </div>
    </div>
  );
}
