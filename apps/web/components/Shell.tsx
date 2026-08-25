"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

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
  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-56 shrink-0 border-r border-[#2a322c] bg-[#0e110f] p-4 md:block">
        <Link href="/" className="mb-6 block">
          <div className="text-xs uppercase tracking-[0.2em] text-[#76b900]">LLM Twin Academy</div>
          <div className="mt-1 text-sm text-[#9aa89a]">NVIDIA DLI · RAD / LLMs</div>
        </Link>
        <nav className="flex flex-col gap-1" aria-label="Main">
          {LINKS.map(([label, href]) => {
            const active = href === "/" ? path === "/" : path.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={`rounded-lg px-3 py-2 text-sm ${active ? "bg-[#1c2618] text-[#76b900]" : "text-[#c5d0c4] hover:bg-[#171c18]"}`}
              >
                {label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-[#2a322c] px-4 py-3 md:hidden">
          <span className="text-sm text-[#76b900]">LLM Twin Academy</span>
          <select
            aria-label="Navigate"
            className="bg-[#141816] text-sm"
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
        <header className="flex items-center justify-between border-b border-[#2a322c] px-4 py-3 md:px-8">
          <span className="text-sm text-[#9aa89a] md:hidden">LLM Twin Academy</span>
          <span className="hidden text-sm text-[#9aa89a] md:inline">Source-grounded · evidence-labeled · no silent GPU claims</span>
          <button
            className="rounded border border-[#2a322c] px-2 py-1 text-xs"
            onClick={() => document.documentElement.classList.toggle("light")}
          >
            Light / dark
          </button>
        </header>
        <main className="min-w-0 flex-1 p-4 md:p-8">{children}</main>
      </div>
    </div>
  );
}
