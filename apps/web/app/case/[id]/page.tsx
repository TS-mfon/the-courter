"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, type ApiCase } from "../../lib/api";
import { Panel, Shell, Stat, VerdictSeal } from "../../ui";

export default function CasePage({ params }: { params: { id: string } }) {
  const [caseRecord, setCaseRecord] = useState<ApiCase | null>(null);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = () => apiGet<ApiCase>(`/cases/${params.id}`).then((data) => {
      if (!cancelled) {
        setCaseRecord(data);
        setLoadError("");
      }
    }).catch((error) => {
      if (!cancelled) {
        setCaseRecord(null);
        setLoadError(error instanceof Error ? error.message : "This case is not available right now.");
      }
    });
    load();
    const timer = setInterval(load, 12000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [params.id]);

  return (
    <Shell title="Case Record" kicker={params.id}>
      {!caseRecord ? (
        <Panel>
          <p>{loadError || "This case is not in local court records."}</p>
          <Link href="/public-cases" className="mt-4 inline-block rounded bg-court-gold px-5 py-3 font-semibold text-black">View Public Cases</Link>
        </Panel>
      ) : (
        <div className="grid gap-5 lg:grid-cols-[0.66fr_0.34fr]">
          <div className="grid gap-5">
            <Panel>
              <h2 className="font-serif text-3xl text-court-gold">Final Verdict</h2>
              {!caseRecord.verdict.finalized ? (
                <div className="mt-4 rounded border border-court-crimson/50 bg-court-crimson/15 p-4">
                  <p className="font-serif text-2xl text-court-gold">Draft Verdict Live, Finality Pending</p>
                  <p className="mt-2 text-sm leading-6 text-court-mist/75">{caseRecord.plain_english_verdict}</p>
                </div>
              ) : (
                <>
                  <p className="mt-4 font-serif text-2xl text-court-gold">{caseRecord.verdict.headline_verdict}</p>
                  <p className="mt-3 text-sm leading-6 text-court-mist">{caseRecord.verdict.final_conclusion}</p>
                </>
              )}
              <div className="mt-5 grid gap-3 text-sm text-court-mist/75 md:grid-cols-2">
                <div className="rounded border border-white/10 bg-white/[0.03] p-3">
                  <p className="text-xs uppercase tracking-[0.18em] text-court-mist/50">Filing Summary</p>
                  <p className="mt-2">{caseRecord.verdict.filing_summary || caseRecord.dispute_type}</p>
                </div>
                <div className="rounded border border-white/10 bg-white/[0.03] p-3">
                  <p className="text-xs uppercase tracking-[0.18em] text-court-mist/50">Evidence Overview</p>
                  <p className="mt-2">{caseRecord.verdict.evidence_overview}</p>
                </div>
              </div>
            </Panel>

            <Panel>
              <h2 className="font-serif text-2xl text-court-gold">Judge Reasoning</h2>
              <div className="mt-4 grid gap-4">
                {caseRecord.verdict.judge_panels.map((panel) => (
                  <section key={panel.judge} className="rounded border border-white/10 bg-white/[0.03] p-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="font-serif text-xl text-court-gold">{panel.judge}</h3>
                        <p className="mt-1 text-sm leading-6 text-court-mist/75">{panel.profile}</p>
                      </div>
                      <span className="rounded border border-court-gold/30 bg-court-gold/10 px-3 py-1 text-sm text-court-gold">
                        {Math.round(panel.confidence * 100)}% confidence
                      </span>
                    </div>
                    <ul className="mt-4 grid gap-2 text-sm leading-6 text-court-mist">
                      {panel.reasoning.map((item) => <li key={item}>- {item}</li>)}
                    </ul>
                    <div className="mt-4 grid gap-3">
                      {panel.cited_laws.map((law) => (
                        <div key={`${panel.judge}-${law.section_id}`} className="rounded border border-white/10 bg-black/30 p-3">
                          <p className="font-semibold text-court-gold">{law.section_id} - {law.title}</p>
                          <p className="mt-1 text-sm text-court-mist/75">{law.summary}</p>
                        </div>
                      ))}
                    </div>
                  </section>
                ))}
              </div>
            </Panel>

            <Panel>
              <h2 className="font-serif text-2xl text-court-gold">Laws Backing The Decision</h2>
              <div className="mt-4 grid gap-3">
                {caseRecord.verdict.law_citations.map((law) => (
                  <div key={law.section_id} className="rounded border border-white/10 bg-black/30 p-3">
                    <p className="font-semibold text-court-gold">{law.section_id} - {law.title}</p>
                    <p className="mt-1 text-sm text-court-mist/75">{law.summary}</p>
                  </div>
                ))}
              </div>
            </Panel>
          </div>

          <div className="grid content-start gap-4">
            <Panel><VerdictSeal confidence={caseRecord.verdict.confidence} /></Panel>
            <Stat label="Winner" value={caseRecord.verdict.winner} />
            <Stat label="Court" value={caseRecord.court_type} />
            <Stat label="OCR" value={caseRecord.ocr?.degraded ? "degraded" : `${caseRecord.ocr?.files_processed || 0} files`} />
            <Panel>
              <h3 className="font-serif text-xl text-court-gold">Reasoning Summary</h3>
              <ul className="mt-3 grid gap-2 text-sm text-court-mist/75">
                {caseRecord.verdict.reasoning_summary.map((item) => <li key={item}>- {item}</li>)}
              </ul>
            </Panel>
            <Panel>
              <h3 className="font-serif text-xl text-court-gold">Contradictions Considered</h3>
              <div className="mt-3 grid gap-2">
                {caseRecord.verdict.contradictions.length ? caseRecord.verdict.contradictions.map((issue) => (
                  <p key={issue} className="rounded border border-court-crimson/30 bg-court-crimson/10 px-3 py-2 text-sm">{issue}</p>
                )) : <p className="text-sm text-court-mist/75">No material contradiction was flagged in the current record.</p>}
              </div>
            </Panel>
          </div>
        </div>
      )}
    </Shell>
  );
}
