"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { apiPost } from "../lib/api";
import { bradburyNetwork, countries, courts, createIdentity, disputeTypes, loadIdentity, saveIdentity, testCaseExamples, treasuryWallet, validateCivilCase, type CourterIdentity } from "../lib/courter";
import { Panel, Shell, StepBadge, Stat } from "../ui";

export default function FileCasePage() {
  const router = useRouter();
  const [identity, setIdentity] = useState<CourterIdentity | null>(null);
  const [username, setUsername] = useState("");
  const [recoveryKey, setRecoveryKey] = useState("");
  const [court, setCourt] = useState("public");
  const [country, setCountry] = useState("Nigeria");
  const [disputeType, setDisputeType] = useState("Contract");
  const [workflowType, setWorkflowType] = useState("procurement");
  const [counterpartyName, setCounterpartyName] = useState("");
  const [contractReference, setContractReference] = useState("");
  const [claimValueSummary, setClaimValueSummary] = useState("");
  const [agreementConfirmed, setAgreementConfirmed] = useState(false);
  const [claimant, setClaimant] = useState("");
  const [respondent, setRespondent] = useState("");
  const [evidenceSummary, setEvidenceSummary] = useState("");
  const [files, setFiles] = useState<string[]>([]);
  const [fileObjects, setFileObjects] = useState<File[]>([]);
  const [txHash, setTxHash] = useState("");
  const [senderWallet, setSenderWallet] = useState("");
  const [message, setMessage] = useState("");
  const [warning, setWarning] = useState("");
  const [paymentCheck, setPaymentCheck] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => setIdentity(loadIdentity()), []);
  const selectedCourt = useMemo(() => courts.find((item) => item.id === court) || courts[0], [court]);
  const isCivil = validateCivilCase(`${disputeType} ${claimant} ${respondent} ${evidenceSummary}`);

  function handleIdentity() {
    if (!username.trim()) return setMessage("Choose a username first.");
    const current = loadIdentity();
    if (current && recoveryKey && current.username === username && current.recoveryKey === recoveryKey) {
      setIdentity(current);
      return setMessage("Identity restored. Your court records are available.");
    }
    const created = createIdentity(username.trim());
    saveIdentity(created);
    setIdentity(created);
    setRecoveryKey(created.recoveryKey);
    setMessage("Identity created. Save your recovery key before filing.");
  }

  function loadExample(exampleId: string) {
    const example = testCaseExamples.find((item) => item.id === exampleId);
    if (!example) return;
    setCountry(example.country);
    setDisputeType(example.disputeType);
    setWorkflowType(example.disputeType.toLowerCase().replace(/ /g, "_"));
    setClaimant(example.claimant);
    setRespondent(example.respondent);
    setEvidenceSummary(example.evidenceSummary);
    setCounterpartyName(example.title);
    setContractReference(`TEMPLATE-${example.id.toUpperCase()}`);
    setClaimValueSummary("Use template values for demo only");
    setAgreementConfirmed(true);
    setMessage(`Loaded example: ${example.title}`);
    setWarning("");
  }

  async function checkPayment() {
    setMessage("");
    setWarning("");
    setPaymentCheck("");
    if (!senderWallet.startsWith("0x")) return setMessage("Enter the sender wallet that paid on Bradbury.");
    if (!txHash.startsWith("0x")) return setMessage("Enter the Bradbury transaction hash first.");
    try {
      const result = await apiPost<{ ok: boolean; message: string; reason: string }>("/payments/verify", {
        tx_hash: txHash,
        sender_wallet: senderWallet,
        recipient_wallet: treasuryWallet,
        amount_gen: selectedCourt.fee,
        court_type: court,
        finalized: true
      });
      if (!result.ok) {
        setWarning(result.message);
        return;
      }
      setPaymentCheck(result.message);
    } catch (error) {
      const detail = error instanceof Error ? error.message : "Payment verification failed.";
      setWarning(detail);
    }
  }

  async function submitCase() {
    if (submitting) return;
    setMessage("");
    setWarning("");
    if (!identity) return setMessage("Create or recover your anonymous identity first.");
    if (!agreementConfirmed) return setMessage("Confirm that both parties agreed in advance to use this private dispute workflow.");
    if (!isCivil) return setMessage("This workflow is for private commercial disputes, not criminal or violent matters.");
    if (!claimant.trim() || !evidenceSummary.trim()) return setMessage("Add your claim and evidence summary so the review panel has concrete commercial facts.");
    if (!senderWallet.startsWith("0x")) return setMessage("Enter the wallet that sent the GEN payment.");
    if (!txHash.startsWith("0x")) return setMessage("Enter the transaction hash for the GEN payment.");
    const structuredClaimant = [
      `Workflow type: ${workflowType}.`,
      counterpartyName ? `Counterparty: ${counterpartyName}.` : "",
      contractReference ? `Contract reference: ${contractReference}.` : "",
      claimValueSummary ? `Claim value summary: ${claimValueSummary}.` : "",
      "Both parties agreed in advance to use this ADR workflow.",
      claimant,
    ].filter(Boolean).join(" ");
    const structuredEvidenceSummary = [
      evidenceSummary,
      contractReference ? `Reference: ${contractReference}.` : "",
      claimValueSummary ? `Claim size: ${claimValueSummary}.` : "",
    ].filter(Boolean).join(" ");
    const form = new FormData();
    form.append("username", identity.username);
    form.append("country", country);
    form.append("dispute_type", disputeType);
    form.append("court_type", court);
    form.append("claimant_statement", structuredClaimant);
    form.append("respondent_statement", respondent);
    form.append("evidence_summary", structuredEvidenceSummary);
    form.append("workflow_type", workflowType);
    form.append("counterparty_name", counterpartyName);
    form.append("contract_reference", contractReference);
    form.append("claim_value_summary", claimValueSummary);
    form.append("agreement_confirmed", agreementConfirmed ? "true" : "false");
    form.append("tx_hash", txHash);
    form.append("sender_wallet", senderWallet);
    fileObjects.forEach((file) => form.append("files", file));
    try {
      setSubmitting(true);
      setMessage("The platform is verifying payment, structuring evidence, ranking applicable rules, applying review profiles, and submitting the decision flow to GenLayer.");
      const created = await apiPost<{ id: string }>("/cases/submit", form);
      router.push(`/courtroom?case=${created.id}`);
    } catch (error) {
      const detail = error instanceof Error ? error.message : "Case submission failed.";
      if (detail.toLowerCase().includes("payment") || detail.toLowerCase().includes("tx") || detail.toLowerCase().includes("transaction") || detail.toLowerCase().includes("treasury")) {
        setWarning(detail);
      } else {
        setMessage(detail);
      }
      setSubmitting(false);
    }
  }

  return (
    <Shell title="Start A Commercial Dispute Review" kicker="Pre-agreed ADR intake">
      <div className="grid gap-5 lg:grid-cols-[0.72fr_0.28fr]">
        <div className="grid gap-5">
          <Panel>
            <StepBadge>Step 1 - Anonymous Identity</StepBadge>
            <h2 className="mt-3 font-serif text-2xl text-court-gold">Create or restore your workspace identity</h2>
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <input className="rounded border border-white/10 bg-black/40 px-3 py-3" placeholder="Username" value={username} onChange={(event) => setUsername(event.target.value)} />
              <input className="rounded border border-white/10 bg-black/40 px-3 py-3" placeholder="Recovery key if returning" value={recoveryKey} onChange={(event) => setRecoveryKey(event.target.value)} />
              <button className="rounded bg-court-gold px-4 py-3 font-semibold text-black" onClick={handleIdentity}>Continue</button>
            </div>
            {identity ? (
              <div className="mt-4 rounded border border-court-gold/30 bg-court-gold/10 p-3 text-sm">
                <p>Identity active: <b>{identity.username}</b></p>
                <p className="mt-1 break-all">Recovery key: {identity.recoveryKey}</p>
                <p className="mt-1 break-all">Local workspace wallet fingerprint: {identity.hiddenWallet}</p>
              </div>
            ) : null}
          </Panel>

          <Panel>
            <StepBadge>Step 2 - ADR Scope</StepBadge>
            <h2 className="mt-3 font-serif text-2xl text-court-gold">Confirm the dispute belongs in a pre-agreed commercial ADR workflow</h2>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <select className="rounded border border-white/10 bg-black/40 px-3 py-3" value={court} onChange={(event) => setCourt(event.target.value)}>
                {courts.slice(0, 2).map((item) => <option key={item.id} value={item.id}>{item.name} - {item.fee} GEN</option>)}
              </select>
              <select className="rounded border border-white/10 bg-black/40 px-3 py-3" value={workflowType} onChange={(event) => setWorkflowType(event.target.value)}>
                {["procurement", "vendor_payment", "milestone", "sla", "service_delivery"].map((item) => <option key={item} value={item}>{item.replace(/_/g, " ")}</option>)}
              </select>
              <input className="rounded border border-white/10 bg-black/40 px-3 py-3" placeholder="Counterparty name" value={counterpartyName} onChange={(event) => setCounterpartyName(event.target.value)} />
              <input className="rounded border border-white/10 bg-black/40 px-3 py-3" placeholder="Contract / PO / SOW reference" value={contractReference} onChange={(event) => setContractReference(event.target.value)} />
              <input className="rounded border border-white/10 bg-black/40 px-3 py-3" placeholder="Claim value summary e.g. USD 8,500 outstanding" value={claimValueSummary} onChange={(event) => setClaimValueSummary(event.target.value)} />
              <div className="rounded border border-white/10 bg-black/20 px-3 py-3 text-sm text-court-mist/80">
                This workflow is intended for procurement, vendor, milestone, SLA, invoice, and service-delivery disputes where both parties opted in beforehand.
              </div>
            </div>
            <label className="mt-4 flex items-start gap-3 rounded border border-white/10 bg-black/20 p-3 text-sm text-court-mist/80">
              <input type="checkbox" checked={agreementConfirmed} onChange={(event) => setAgreementConfirmed(event.target.checked)} className="mt-1" />
              <span>I confirm both parties agreed in advance to use this private dispute resolution workflow and understand the resulting decision record does not automatically replace local legal enforcement.</span>
            </label>
          </Panel>

          <Panel>
            <StepBadge>Step 3 - Dispute Intake</StepBadge>
            <h2 className="mt-3 font-serif text-2xl text-court-gold">Choose jurisdiction, dispute type, and load a test case if needed</h2>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <select className="rounded border border-white/10 bg-black/40 px-3 py-3" value={country} onChange={(event) => setCountry(event.target.value)}>
                {countries.map((item) => <option key={item}>{item}</option>)}
              </select>
              <select className="rounded border border-white/10 bg-black/40 px-3 py-3" value={disputeType} onChange={(event) => setDisputeType(event.target.value)}>
                {disputeTypes.map((item) => <option key={item}>{item}</option>)}
              </select>
            </div>
            <div className="mt-5 rounded border border-white/10 bg-black/30 p-4">
              <h3 className="font-serif text-xl text-court-gold">Load A Test Template</h3>
              <p className="mt-2 text-sm text-court-mist/70">Use these examples to test the filing flow, law retrieval, judge reasoning, and contract submission without writing a case from scratch.</p>
              <div className="mt-4 grid gap-2 md:grid-cols-2">
                {testCaseExamples.map((example) => (
                  <button key={example.id} className="rounded border border-white/10 bg-black/40 px-3 py-3 text-left text-sm text-court-mist hover:border-court-gold/40" onClick={() => loadExample(example.id)}>
                    <div className="font-semibold text-court-gold">{example.title}</div>
                    <div className="mt-1 text-court-mist/70">{example.country} • {example.disputeType}</div>
                  </button>
                ))}
              </div>
            </div>
          </Panel>

          <Panel>
            <StepBadge>Step 4 - Evidence</StepBadge>
            <div className="mt-4 grid gap-3">
              <textarea className="min-h-28 rounded border border-white/10 bg-black/40 p-3" placeholder="What happened? State the commercial claim clearly." value={claimant} onChange={(event) => setClaimant(event.target.value)} />
              <textarea className="min-h-24 rounded border border-white/10 bg-black/40 p-3" placeholder="Counterparty position, if known." value={respondent} onChange={(event) => setRespondent(event.target.value)} />
              <textarea className="min-h-28 rounded border border-white/10 bg-black/40 p-3" placeholder="Evidence summary: contract clause, invoice, milestone, acceptance note, SLA metric, payment date." value={evidenceSummary} onChange={(event) => setEvidenceSummary(event.target.value)} />
              <p className="text-sm text-court-mist/70">Uploads are optional. Typed facts alone are enough if they include real commercial details.</p>
              <input type="file" multiple accept=".pdf,.png,.jpg,.jpeg,.txt" className="rounded border border-white/10 bg-black/40 px-3 py-3" onChange={(event) => {
                const selected = Array.from(event.target.files || []);
                setFileObjects(selected);
                setFiles(selected.map((file) => file.name));
              }} />
              {files.length ? <p className="text-sm text-court-mist/70">Selected uploads: {files.join(", ")}</p> : null}
            </div>
          </Panel>

          <Panel>
            <StepBadge>Step 5 - Payment Verification</StepBadge>
            <p className="mt-3 text-sm text-court-mist/70">Send exactly <b>{selectedCourt.fee} GEN</b> on <b>{bradburyNetwork.label}</b> to the treasury wallet, then submit the transaction hash and sender wallet.</p>
            <p className="mt-2 text-sm text-court-mist/70">Primary verifier RPC: <span className="text-court-gold">{bradburyNetwork.primaryRpc}</span></p>
            <p className="mt-1 text-sm text-court-mist/70">Fallback verifier RPC: <span className="text-court-gold">{bradburyNetwork.fallbackRpc}</span></p>
            <a className="mt-2 inline-block text-sm text-court-gold underline" href={`${bradburyNetwork.explorerBaseUrl}/address/${treasuryWallet}`} target="_blank" rel="noreferrer">Open Bradbury explorer for the treasury wallet</a>
            <p className="mt-2 break-all rounded bg-black/40 p-3 text-sm text-court-gold">{treasuryWallet}</p>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <input className="rounded border border-white/10 bg-black/40 px-3 py-3" placeholder="Transaction hash" value={txHash} onChange={(event) => setTxHash(event.target.value)} />
              <input className="rounded border border-white/10 bg-black/40 px-3 py-3" placeholder="Sender wallet" value={senderWallet} onChange={(event) => setSenderWallet(event.target.value)} />
            </div>
            <div className="mt-4 flex flex-wrap gap-3">
              <button className="rounded border border-white/10 bg-black/40 px-5 py-3 font-semibold text-court-gold disabled:cursor-not-allowed disabled:opacity-60" disabled={submitting} onClick={checkPayment}>
                Check Payment On Bradbury
              </button>
              <button className="rounded bg-court-gold px-5 py-3 font-semibold text-black disabled:cursor-not-allowed disabled:opacity-60" disabled={submitting} onClick={submitCase}>
              {submitting ? "Submitting For Review..." : "Submit For Review"}
              </button>
            </div>
            {paymentCheck ? <p className="mt-4 rounded border border-court-gold/30 bg-court-gold/10 p-3 text-sm">{paymentCheck}</p> : null}
            {message ? <p className="mt-4 rounded border border-court-crimson/40 bg-court-crimson/15 p-3 text-sm">{message}</p> : null}
          </Panel>
        </div>

        <div className="grid content-start gap-4">
          <Stat label="Selected Court" value={selectedCourt.name} />
          <Stat label="Required Fee" value={`${selectedCourt.fee} GEN`} />
          <Stat label="Payment Network" value={bradburyNetwork.label} />
          <Panel>
            <h3 className="font-serif text-xl text-court-gold">What Happens Next</h3>
            <ol className="mt-3 grid gap-2 text-sm text-court-mist/70">
              <li>Evidence is structured.</li>
              <li>Commercial contradictions are detected.</li>
              <li>Relevant laws and contract-style rules are retrieved.</li>
              <li>Three review profiles are selected.</li>
              <li>A decision record is published and can later be escalated.</li>
            </ol>
          </Panel>
          <Panel>
            <h3 className="font-serif text-xl text-court-gold">5 Test Examples</h3>
            <p className="mt-3 text-sm text-court-mist/70">Templates are available in the main filing flow above. Pick one there to load a full civil test case into the form.</p>
          </Panel>
        </div>
      </div>
      {warning ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4">
          <div className="w-full max-w-lg rounded-md border border-court-crimson/40 bg-[#120b0b] p-6 shadow-2xl">
            <h2 className="font-serif text-2xl text-court-gold">Payment Warning</h2>
            <p className="mt-4 text-sm leading-6 text-court-mist">{warning}</p>
            <div className="mt-6 flex justify-end">
              <button className="rounded bg-court-gold px-4 py-2 font-semibold text-black" onClick={() => setWarning("")}>Close</button>
            </div>
          </div>
        </div>
      ) : null}
    </Shell>
  );
}
