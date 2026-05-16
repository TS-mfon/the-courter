"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost, type ApiCase } from "../lib/api";
import { treasuryWallet } from "../lib/courter";
import { Panel, Shell, StepBadge } from "../ui";

export default function AppealsPage() {
  const [cases, setCases] = useState<ApiCase[]>([]);
  const [caseId, setCaseId] = useState("");
  const [grounds, setGrounds] = useState("");
  const [txHash, setTxHash] = useState("");
  const [senderWallet, setSenderWallet] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    apiGet<{ cases: ApiCase[] }>("/cases/").then((data) => {
      setCases(data.cases);
      setCaseId(data.cases[0]?.id || "");
    }).catch(() => setCases([]));
  }, []);

  async function submitAppeal() {
    try {
      await apiPost("/appeals/", { case_id: caseId, username: "court-user", grounds, tx_hash: txHash, sender_wallet: senderWallet });
      setMessage("Appeal accepted. Different judges reviewed the verdict and finalized the appeal record.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Appeal failed.");
    }
  }

  return (
    <Shell title="Appeal Court" kicker="Secondary judicial review">
      <div className="grid gap-5 lg:grid-cols-[0.65fr_0.35fr]">
        <Panel>
          <StepBadge>Appeal Fee - 5 GEN</StepBadge>
          <h2 className="mt-3 font-serif text-2xl text-court-gold">Challenge a finalized verdict</h2>
          <div className="mt-4 grid gap-3">
            <select className="rounded border border-white/10 bg-black/40 px-3 py-3" value={caseId} onChange={(event) => setCaseId(event.target.value)}>
              {cases.map((item) => <option key={item.id} value={item.id}>{item.id} - {item.dispute_type}</option>)}
            </select>
            <textarea className="min-h-32 rounded border border-white/10 bg-black/40 p-3" placeholder="Explain what the first verdict missed." value={grounds} onChange={(event) => setGrounds(event.target.value)} />
            <input className="rounded border border-white/10 bg-black/40 px-3 py-3" placeholder="Appeal payment tx hash" value={txHash} onChange={(event) => setTxHash(event.target.value)} />
            <input className="rounded border border-white/10 bg-black/40 px-3 py-3" placeholder="Sender wallet" value={senderWallet} onChange={(event) => setSenderWallet(event.target.value)} />
            <button className="w-fit rounded bg-court-gold px-5 py-3 font-semibold text-black" onClick={submitAppeal}>Submit Appeal</button>
          </div>
          {message ? <p className="mt-4 rounded border border-court-gold/30 bg-court-gold/10 p-3 text-sm">{message}</p> : null}
        </Panel>
        <Panel>
          <h3 className="font-serif text-xl text-court-gold">Treasury</h3>
          <p className="mt-3 break-all text-sm text-court-mist/70">{treasuryWallet}</p>
          <p className="mt-4 text-sm leading-6 text-court-mist/70">Appeals always select a different judge panel from the original case.</p>
          <Link href="/public-cases" className="mt-4 inline-block rounded border border-court-gold px-4 py-2">View Updated Records</Link>
        </Panel>
      </div>
    </Shell>
  );
}
