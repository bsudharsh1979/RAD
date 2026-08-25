"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { EvidenceBadge } from "@/components/EvidenceBadge";
import { TwinViz } from "@/components/TwinViz";

const STEPS = [
  ["understand", "Understand the workload"],
  ["hypothesis", "Form a hypothesis"],
  ["choose_features", "Choose features"],
  ["run_simulation", "Run simulation"],
  ["inspect", "Inspect results"],
  ["import_optional", "Import real results (optional)"],
  ["recommend", "Recommend"],
  ["defend", "Defend"],
];

export default function AssessmentPage() {
  const [a, setA] = useState<any>(null);
  const [step, setStep] = useState(0);
  const [hyp, setHyp] = useState("");
  const [feats, setFeats] = useState<Record<string, boolean>>({
    memory: true,
    image: true,
    code: false,
    toxicity: true,
    emotion: false,
  });
  const [tox, setTox] = useState(0.2);
  const [state, setState] = useState<any>(null);
  const [defense, setDefense] = useState("");
  const [grade, setGrade] = useState<any>(null);

  useEffect(() => {
    api("/assessment").then(setA);
  }, []);
  if (!a) return <p>Loading assessment arena…</p>;
  const n = Object.values(feats).filter(Boolean).length;
  const key = STEPS[step][0];

  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Assessment arena</h1>
      <EvidenceBadge type="COURSE_SOURCE" />
      <p>{a.brief}</p>
      <p>
        Pass rule: {a.pass_rule} of {a.features.length} features. Grader model: {a.constraints?.model}.
      </p>
      <div className="flex flex-wrap gap-2 text-xs">
        {STEPS.map(([k, label], i) => (
          <button
            key={k}
            className={`rounded-full px-3 py-1 ${i === step ? "bg-[#76b900] text-black" : "border"}`}
            style={i === step ? undefined : { borderColor: "var(--line)" }}
            onClick={() => setStep(i)}
          >
            {i + 1}. {label}
          </button>
        ))}
      </div>
      <div className="panel space-y-3 p-5">
        {key === "understand" && (
          <div className="space-y-2 text-sm">
            <p>Build a custom LangChain agent that talks to the learner via Ask-For-Input Tool.</p>
            <ul className="list-disc pl-5">
              <li>Image trigger: {a.constraints.image_syntax}</li>
              <li>Code trigger: fenced {a.constraints.code_fence}</li>
              <li>ToxicityModel reward = {a.constraints.toxicity_reward}</li>
            </ul>
            <p style={{ color: "var(--muted)" }}>The platform does not leak a completed solution notebook.</p>
          </div>
        )}
        {key === "hypothesis" && (
          <textarea
            className="field min-h-32"
            placeholder="What architecture will you defend? Which 3+ features, and why?"
            value={hyp}
            onChange={(e) => setHyp(e.target.value)}
          />
        )}
        {key === "choose_features" && (
          <ul className="space-y-2">
            {a.features.map((f: string) => (
              <li key={f}>
                <label className="flex gap-2">
                  <input
                    type="checkbox"
                    checked={!!feats[f]}
                    onChange={(e) => setFeats({ ...feats, [f]: e.target.checked })}
                  />
                  {f}
                </label>
              </li>
            ))}
            <p>
              Selected {n}/5 {n >= 3 ? "meets pass count" : "below pass count"}
            </p>
          </ul>
        )}
        {key === "run_simulation" && (
          <div>
            <p className="mb-2 text-sm">Lock the hypothesis, then simulate. Outcome is SIMULATED_RESULT.</p>
            <label className="block text-sm">
              User toxicity slider (for inverted reward)
              <input type="range" min={0} max={1} step={0.01} value={tox} onChange={(e) => setTox(Number(e.target.value))} className="w-full" />
              {tox}
            </label>
            <button
              className="mt-3 rounded bg-[#76b900] px-4 py-2 text-black"
              onClick={async () => {
                const p: any = await api("/twins/predict", {
                  method: "POST",
                  body: JSON.stringify({ twin_id: "assessment-agent", prompt: hyp, predicted: { features: feats } }),
                });
                const r: any = await api("/twins/run", {
                  method: "POST",
                  body: JSON.stringify({
                    scenario: "assessment-agent",
                    params: { ...feats, user_toxicity: tox },
                    prediction_id: p.prediction_id,
                  }),
                });
                setState(r.state);
                setStep(4);
              }}
            >
              Run assessment twin
            </button>
          </div>
        )}
        {key === "inspect" && (
          <div>
            {!state && <p>Run the simulation first.</p>}
            {state && (
              <>
                <EvidenceBadge type={state.evidence_type} />
                <TwinViz scenario="assessment-agent" params={{ ...feats, user_toxicity: tox }} state={state} />
                <p className="mt-2 text-sm">{state.teaching}</p>
              </>
            )}
          </div>
        )}
        {key === "import_optional" && (
          <p>
            Optional: import a real GPU run on{" "}
            <Link className="text-[#76b900]" href="/experiments">
              Experiments
            </Link>{" "}
            as ACTUAL_RUN. Do not treat this simulation as measured.
          </p>
        )}
        {key === "recommend" && (
          <p>
            Recommendation: implement {n} features ({n >= 3 ? "would pass the count rule" : "would fail the count rule"}).
            Toxicity reward at slider {tox} is {state ? state.toxicity_reward : (1 - tox).toFixed(2)} (simulated).
          </p>
        )}
        {key === "defend" && (
          <div>
            <textarea
              className="field min-h-40"
              placeholder="Defend: user-as-tool loop, inverted toxicity reward, 13B GPTQ grader, why these features…"
              value={defense}
              onChange={(e) => setDefense(e.target.value)}
            />
            <button
              className="mt-3 rounded bg-[#76b900] px-4 py-2 text-black"
              onClick={async () =>
                setGrade(
                  await api("/assessment/defend", {
                    method: "POST",
                    body: JSON.stringify({ hypothesis: hyp, defense, features: feats, twin_state: state }),
                  }),
                )
              }
            >
              Submit defense
            </button>
            {grade && (
              <div className="mt-3 space-y-1 text-sm">
                <EvidenceBadge type={grade.evidence_type} />
                <p>Quality {grade.quality} · features {grade.implemented_count}/5</p>
                <p>Covered: {grade.correctly_explained.join(", ") || "none"}</p>
                <p>Missing: {grade.missing.join(", ") || "none"}</p>
                <p style={{ color: "var(--muted)" }}>{grade.note}</p>
              </div>
            )}
          </div>
        )}
      </div>
      <div className="flex justify-between">
        <button className="rounded border px-3 py-1" style={{ borderColor: "var(--line)" }} disabled={step === 0} onClick={() => setStep(step - 1)}>
          Back
        </button>
        <button className="rounded bg-[#76b900] px-3 py-1 text-black" disabled={step === STEPS.length - 1} onClick={() => setStep(step + 1)}>
          Next step
        </button>
      </div>
      <Link className="text-[#76b900]" href="/practice?concept=c-assess">
        Practice design questions
      </Link>
    </div>
  );
}
