"use client";

import { useEffect, useState } from "react";
import { apiGet, type ApiCase, type Proposal } from "../../lib/api";
import { Panel, Shell, Stat } from "../../ui";

export default function GovernanceAnalyticsPage() {
  const [cases, setCases] = useState<ApiCase[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);

  useEffect(() => {
    apiGet<{ cases: ApiCase[] }>("/cases/").then((data) => setCases(data.cases)).catch(() => setCases([]));
    apiGet<{ proposals: Proposal[] }>("/shadow-council/proposals").then((data) => setProposals(data.proposals)).catch(() => setProposals([]));
  }, []);

  const participation = proposals.length ? proposals.reduce((sum, item) => sum + item.votes.length, 0) / proposals.length : 0;

  return (
    <Shell title="Governance Analytics" kicker="Public accountability">
      <div className="grid gap-4 md:grid-cols-4">
        <Stat label="Total Cases" value={cases.length} />
        <Stat label="Participation" value={participation.toFixed(1)} />
        <Stat label="Overturns" value={proposals.filter((item) => item.status === "overruled").length} />
        <Stat label="Council Activity" value={proposals.reduce((sum, item) => sum + item.votes.length, 0)} />
      </div>
      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <Panel>
          <h2 className="font-serif text-2xl text-court-gold">Overturn Statistics</h2>
          <div className="mt-4 grid gap-3">
            {proposals.map((item) => (
              <div key={item.id} className="rounded border border-white/10 p-3 text-sm">
                {item.id}: {item.status} / YES {item.yes_weight} / NO {item.no_weight}
              </div>
            ))}
          </div>
        </Panel>
        <Panel>
          <h2 className="font-serif text-2xl text-court-gold">Reputation Rankings</h2>
          <div className="mt-4 grid gap-3">
            {cases.map((item) => (
              <div key={item.id} className="rounded border border-white/10 p-3 text-sm">
                {item.username}: trust score {Math.round(item.verdict.confidence * 100)}
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </Shell>
  );
}
