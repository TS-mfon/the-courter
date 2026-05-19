"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, type ApiCase } from "../lib/api";
import { Panel, Shell, StepBadge, VerdictSeal } from "../ui";

function profileLabel(name: string) {
  return name.startsWith("Justice ") ? `${name.replace(/^Justice\s+/, "")} profile` : name;
}

const stages = [
  "Submission received",
  "Payment confirmed",
  "Evidence structured",
  "Rules retrieved",
  "Review profiles applied",
  "Decision draft assembled",
  "GenLayer finality pending",
  "Decision ready"
];

export default function CourtroomPage() {
  const [activeCase, setActiveCase] = useState<ApiCase | null>(null);
  const [stage, setStage] = useState(0);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get("case");
    if (!id) return;
    let cancelled = false;
    const load = () => apiGet<ApiCase>(`/cases/${id}`).then((data) => {
      if (!cancelled) {
        setActiveCase(data);
        setLoadError("");
      }
    }).catch((error) => {
      if (!cancelled) {
        setActiveCase(null);
        setLoadError(error instanceof Error ? error.message : "No case has entered the courtroom yet.");
      }
    });
    load();
    const timer = setInterval(load, 12000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);
  useEffect(() => {
    const timer = setInterval(() => setStage((current) => Math.min(stages.length - 1, current + 1)), 900);
    return () => clearInterval(timer);
  }, []);

  return (
    <Shell title="Live Review" kicker="Consensus-backed decision flow">
      {!activeCase ? (
        <Panel>
          <p>{loadError || "No dispute review is active right now."}</p>
          <Link href="/file-case" className="mt-4 inline-block rounded bg-court-gold px-5 py-3 font-semibold text-black">Start A Review</Link>
        </Panel>
      ) : (
        <div className="grid gap-5 lg:grid-cols-[0.68fr_0.32fr]">
          <Panel className="overflow-hidden">
            <div className="relative min-h-[420px] rounded bg-black/70 p-8">
              <div className="absolute inset-x-0 top-0 h-28 bg-gradient-to-b from-court-crimson/60 to-transparent" />
              <div className="absolute left-6 top-0 h-full w-16 bg-gradient-to-r from-court-crimson/70 to-transparent opacity-60" />
              <div className="absolute right-6 top-0 h-full w-16 bg-gradient-to-l from-court-crimson/70 to-transparent opacity-60" />
              <div className="relative z-10 grid min-h-[360px] place-items-center text-center">
                <div>
                  <StepBadge>{stages[stage]}</StepBadge>
                  <p className="mt-6 font-serif text-4xl text-court-gold md:text-6xl">
                    {stage < 7 ? "Commercial review in progress" : activeCase.verdict.finalized ? "Decision Ready" : "Draft Decision Ready"}
                  </p>
                  <div className="mx-auto mt-8 grid max-w-xl grid-cols-3 gap-4">
                    {activeCase.verdict.judges_used.map((judge) => (
                      <div key={judge} className="rounded-t-full border border-court-gold/30 bg-court-gold/10 p-5 pt-12 text-sm shadow-[0_0_45px_rgba(214,170,79,0.15)]">{profileLabel(judge)}</div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </Panel>
          <Panel>
            <h2 className="font-serif text-2xl text-court-gold">{activeCase.id}</h2>
            <p className="mt-2 text-sm text-court-mist/60">{activeCase.country} / {activeCase.dispute_type} / {activeCase.court_type}</p>
            <div className="mt-5 flex justify-center"><VerdictSeal confidence={activeCase.verdict.confidence} /></div>
            <p className="mt-5 rounded border border-court-gold/30 bg-court-gold/10 p-4 font-serif text-2xl text-court-gold">
              {activeCase.verdict.finalized ? `Recommended outcome: ${activeCase.verdict.winner}` : `Draft outcome: ${activeCase.verdict.winner}`}
            </p>
            <p className="mt-4 font-serif text-xl text-court-gold">{activeCase.verdict.headline_verdict || activeCase.plain_english_verdict}</p>
            <p className="mt-3 text-sm leading-6 text-court-mist/75">{activeCase.verdict.final_conclusion || activeCase.plain_english_verdict}</p>
            <div className="mt-5 flex flex-wrap gap-2">
              <Link href={`/case/${activeCase.id}`} className="rounded bg-court-gold px-4 py-2 font-semibold text-black">Open Decision Record</Link>
              <Link href="/appeals" className="rounded border border-court-gold px-4 py-2">Escalate Review</Link>
            </div>
          </Panel>
        </div>
      )}
    </Shell>
  );
}
