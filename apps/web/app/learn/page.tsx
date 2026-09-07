import { Suspense } from "react";
import LearnInner from "./LearnInner";

export default function Page() {
  return (
    <Suspense fallback={<p>Loading…</p>}>
      <LearnInner />
    </Suspense>
  );
}
