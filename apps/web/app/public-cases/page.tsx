"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, type ApiCase } from "../lib/api";
import { Panel, Shell, Stat } from "../ui";

export default function PublicCasesPage() {
  const [cases, setCases] = useState<ApiCase[]>([]);
  useEffect(() => { apiGet<{ cases: ApiCase[] }>("/cases/?public=true").then((data) => setCases(data.cases)).catch(() => setCases([])); }, []);

  return (
    <Shell title="Public Case Explorer" kicker="Transparency layer">
      <div className="grid gap-4 md:grid-cols-4">
        <Stat label="Public Cases" value={cases.length} />
        <Stat label="Appeals" value={cases.filter((item) => item.status === "appealed").length} />
        <Stat label="Avg Confidence" value={cases.length ? `${Math.round(cases.reduce((sum, item) => sum + item.verdict.confidence, 0) / cases.length * 100)}%` : "0%"} />
        <Stat label="Countries" value={new Set(cases.map((item) => item.country)).size} />
      </div>
      <div className="mt-6 grid gap-4">
        {cases.length === 0 ? (
          <Panel>
            <p>No public cases yet. File a case to publish the first court record.</p>
            <Link href="/file-case" className="mt-4 inline-block rounded bg-court-gold px-5 py-3 font-semibold text-black">File A Case</Link>
          </Panel>
        ) : cases.map((item) => (
          <Panel key={item.id}>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h2 className="font-serif text-2xl text-court-gold">{item.id}</h2>
                <p className="mt-1 text-sm text-court-mist/60">{item.country} / {item.dispute_type} / {item.court_type}</p>
                <p className="mt-3 max-w-3xl text-court-mist/80">{item.plain_english_verdict}</p>
              </div>
              <Link href={`/case/${item.id}`} className="rounded bg-court-gold px-4 py-2 font-semibold text-black">Open Record</Link>
            </div>
            <div className="mt-4 flex flex-wrap gap-2 text-xs">
              <span className="rounded border border-court-gold/30 px-3 py-1">Confidence {Math.round(item.verdict.confidence * 100)}%</span>
              <span className="rounded border border-court-gold/30 px-3 py-1">Winner {item.verdict.winner}</span>
              <span className="rounded border border-court-gold/30 px-3 py-1">Judges {item.verdict.judges_used.join(", ")}</span>
            </div>
          </Panel>
        ))}
      </div>
    </Shell>
  );
}
