"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost, type ApiCase, type Proposal } from "../lib/api";
import { treasuryWallet } from "../lib/courter";
import { Panel, Shell, Stat, StepBadge } from "../ui";

export default function ShadowCouncilPage() {
  const [cases, setCases] = useState<ApiCase[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [caseId, setCaseId] = useState("");
  const [wallet, setWallet] = useState("");
  const [txHash, setTxHash] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    apiGet<{ cases: ApiCase[] }>("/cases/").then((data) => {
      setCases(data.cases);
      setCaseId(data.cases[0]?.id || "");
    }).catch(() => setCases([]));
    apiGet<{ proposals: Proposal[] }>("/shadow-council/proposals").then((data) => setProposals(data.proposals)).catch(() => setProposals([]));
  }, []);

  async function createProposal() {
    try {
      const proposal = await apiPost<Proposal>("/shadow-council/proposals", { case_id: caseId, username: "court-user", tx_hash: txHash, sender_wallet: wallet || "0xsender" });
      setProposals([proposal, ...proposals]);
      setMessage("Governance review opened. Weighted voting may begin.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Proposal creation failed.");
    }
  }

  async function vote(proposalId: string, voteValue: "YES" | "NO") {
    try {
      const proposal = await apiPost<Proposal>("/shadow-council/vote", { proposal_id: proposalId, wallet, vote: voteValue });
      setProposals(proposals.map((item) => item.id === proposalId ? proposal : item));
      setMessage(proposal.final_message || `${wallet.slice(0, 8)}... voted ${voteValue} on ${proposalId}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Vote failed.");
    }
  }

  return (
    <Shell title="Governance Review" kicker="Restricted operator override flow">
      <div className="grid gap-5 lg:grid-cols-[0.62fr_0.38fr]">
        <Panel>
          <StepBadge>Governance Override - 10 GEN</StepBadge>
          <h2 className="mt-3 font-serif text-3xl text-court-gold">Open a governance review</h2>
          <div className="mt-4 grid gap-3">
            <select className="rounded border border-white/10 bg-black/40 px-3 py-3" value={caseId} onChange={(event) => setCaseId(event.target.value)}>
              {cases.map((item) => <option key={item.id} value={item.id}>{item.id}</option>)}
            </select>
            <input className="rounded border border-white/10 bg-black/40 px-3 py-3" placeholder="10 GEN payment tx hash" value={txHash} onChange={(event) => setTxHash(event.target.value)} />
            <button className="w-fit rounded bg-court-gold px-5 py-3 font-semibold text-black" onClick={createProposal}>Create Proposal</button>
          </div>
          <p className="mt-4 break-all text-sm text-court-mist/60">Treasury: {treasuryWallet}</p>
        </Panel>
        <Panel>
          <h3 className="font-serif text-2xl text-court-gold">Reviewer Wallet</h3>
          <input className="mt-4 w-full rounded border border-white/10 bg-black/40 px-3 py-3" placeholder="Whitelisted governance wallet" value={wallet} onChange={(event) => setWallet(event.target.value)} />
          <p className="mt-3 text-sm text-court-mist/60">Only whitelisted governance wallets can vote. One vote per wallet per proposal.</p>
          {message ? <p className="mt-4 rounded border border-court-gold/30 bg-court-gold/10 p-3 text-sm">{message}</p> : null}
        </Panel>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-3">
        <Stat label="Open Proposals" value={proposals.filter((item) => item.status === "active").length} />
        <Stat label="Overruled" value={proposals.filter((item) => item.status === "overruled").length} />
        <Stat label="Upheld" value={proposals.filter((item) => item.status === "upheld").length} />
      </div>

      <div className="mt-6 grid gap-4">
        {proposals.map((proposal) => (
          <Panel key={proposal.id}>
            <div className="flex flex-wrap justify-between gap-4">
              <div>
                <h3 className="font-serif text-2xl text-court-gold">{proposal.id}</h3>
              <p className="text-sm text-court-mist/60">Case {proposal.case_id} / Result {proposal.status}</p>
              </div>
              <div className="flex gap-2">
                <button className="rounded border border-court-gold px-4 py-2" onClick={() => vote(proposal.id, "YES")}>Vote YES</button>
                <button className="rounded border border-court-crimson px-4 py-2" onClick={() => vote(proposal.id, "NO")}>Vote NO</button>
              </div>
            </div>
            <p className="mt-3 text-sm">YES_WEIGHT {proposal.yes_weight} / NO_WEIGHT {proposal.no_weight}</p>
            <div className="mt-3 grid gap-2 text-sm text-court-mist/70">
              {proposal.votes.map((vote) => <p key={`${proposal.id}-${vote.wallet}`}>{vote.wallet.slice(0, 8)}... voted {vote.vote} with weight {vote.weight}</p>)}
            </div>
          </Panel>
        ))}
      </div>
    </Shell>
  );
}
