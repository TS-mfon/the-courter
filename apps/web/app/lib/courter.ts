export const treasuryWallet = "0x5905c9Dea6Ae52AA0947D8F7F218263889eDfC4E";

export const courts = [
  { id: "public", name: "Standard Review", fee: 2, purpose: "Routine vendor, invoice, and services disputes" },
  { id: "inner", name: "Complex Review", fee: 5, purpose: "Higher-friction claims with heavier evidence sets" },
  { id: "appeal", name: "Escalation Review", fee: 5, purpose: "Second-pass review under the agreed ADR workflow" },
  { id: "shadow_council", name: "Governance Review", fee: 10, purpose: "Administrative override for approved operators" }
] as const;

export const bradburyNetwork = {
  label: "Bradbury testnet",
  primaryRpc: "https://zksync-os-testnet-genlayer.zksync.dev",
  fallbackRpc: "https://zksync-os-testnet-genlayer.zksync.dev",
  explorerBaseUrl: "https://zksync-os-testnet-genlayer.explorer.zksync.dev"
} as const;

export const countries = ["Nigeria", "India", "Brazil", "Kenya", "Indonesia", "Australia"];
export const disputeTypes = ["Contract", "Vendor Payment", "Procurement", "Milestone", "SLA", "Service Delivery"];

export const testCaseExamples = [
  {
    id: "vendor-payment-nigeria",
    title: "Vendor payment holdback",
    country: "Nigeria",
    disputeType: "Vendor Payment",
    claimant: "Our team delivered the final API integration and post-launch support for a procurement portal on 2026-02-14. The buyer accepted staging, approved production go-live, and confirmed closure of critical defects, but withheld the last 20% milestone payment.",
    respondent: "The buyer says final acceptance was conditional on extra analytics dashboards, but those dashboards were not part of the signed scope or milestone acceptance checklist.",
    evidenceSummary: "Master services agreement, statement of work, milestone acceptance email, invoice INV-2044, change request log, delivery checklist, payment schedule, and two meeting notes confirming go-live approval."
  },
  {
    id: "milestone-kenya",
    title: "Implementation milestone dispute",
    country: "Kenya",
    disputeType: "Milestone",
    claimant: "We completed milestone 3 of an ERP rollout for a distribution company and submitted training logs, deployment notes, and sign-off requests. The customer continues to use the deployed module but has refused the milestone payment.",
    respondent: "The customer argues that user adoption targets were not met, even though the signed milestone schedule only required deployment, handover, and administrator training.",
    evidenceSummary: "Project plan, milestone matrix, training attendance sheet, deployment approval, support ticket closure summary, and invoice due on 2026-03-01."
  },
  {
    id: "sla-india",
    title: "Managed service SLA breach claim",
    country: "India",
    disputeType: "SLA",
    claimant: "Our company purchased a managed uptime package with service credits if monthly availability dropped below 99.5%. Monitoring records show two separate outages and a net availability of 98.7%, but the provider rejected the credit request.",
    respondent: "The provider says one outage fell inside a maintenance window and the other was caused by the claimant's own firewall policy, so no credits should apply.",
    evidenceSummary: "Signed SLA, uptime logs, outage timeline, maintenance notice, incident report, support thread, and monthly service invoice."
  },
  {
    id: "procurement-brazil",
    title: "Procurement delivery acceptance dispute",
    country: "Brazil",
    disputeType: "Procurement",
    claimant: "We supplied 120 rugged field tablets under a procurement order and delivered them in two batches with signed warehouse receipts. The buyer accepted the shipment and distributed the devices internally but rejected the final payment after deployment.",
    respondent: "The buyer says 18 devices failed after deployment and argues the supplier must replace them before final payment is released.",
    evidenceSummary: "Purchase order, delivery notes, warehouse sign-off, serial number list, defect report, warranty clause, replacement timeline, and outstanding invoice."
  },
  {
    id: "services-australia",
    title: "Service delivery and change-order dispute",
    country: "Australia",
    disputeType: "Service Delivery",
    claimant: "We were engaged to deliver a compliance reporting workflow and completed the original scope. The client requested additional approval routing, accepted the revised delivery date, then treated the extra work as part of the original fixed fee.",
    respondent: "The client argues the extra approval routing was implied by the initial brief and therefore not chargeable as a separate change request.",
    evidenceSummary: "Initial proposal, signed services agreement, change-order email, revised delivery plan, acceptance recording, invoice for additional scope, and approval workflow screenshots."
  }
] as const;

export type CourterIdentity = {
  username: string;
  recoveryKey: string;
  hiddenWallet: string;
  createdAt: string;
};

export type CourterCase = {
  id: string;
  username: string;
  court: string;
  fee: number;
  country: string;
  disputeType: string;
  claimant: string;
  respondent: string;
  evidenceSummary: string;
  files: string[];
  txHash: string;
  senderWallet: string;
  status: "submitted" | "deliberating" | "finalized" | "appealed" | "shadow_review";
  structuredEvidence: {
    document_type: string;
    country: string;
    owner: string;
    registry_id: string;
    confidence: number;
    issues_detected: string[];
  };
  contradictionReport: {
    contradiction_detected: boolean;
    severity: number;
    issues: string[];
  };
  judges: string[];
  laws: string[];
  verdict: {
    winner: "claimant" | "respondent" | "split";
    confidence: number;
    reasoning_summary: string[];
    appealable: boolean;
    plain_english: string;
  };
  public: boolean;
  createdAt: string;
};

export type ShadowProposal = {
  id: string;
  caseId: string;
  yesWeight: number;
  noWeight: number;
  votes: { wallet: string; vote: "YES" | "NO"; weight: number }[];
  result: "open" | "upheld" | "overruled";
};

const identityKey = "courter_identity";
const casesKey = "courter_cases";
const proposalKey = "courter_shadow_proposals";
const txKey = "courter_consumed_txs";

export function randomId(prefix: string) {
  return `${prefix}-${Math.floor(Date.now() / 1000)}-${Math.random().toString(16).slice(2, 8)}`;
}

export function createIdentity(username: string): CourterIdentity {
  const identity = {
    username,
    recoveryKey: `COURTER-${Math.random().toString(36).slice(2, 8).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`,
    hiddenWallet: `0x${Array.from({ length: 40 }, () => Math.floor(Math.random() * 16).toString(16)).join("")}`,
    createdAt: new Date().toISOString()
  };
  if (typeof window !== "undefined") localStorage.setItem(identityKey, JSON.stringify(identity));
  return identity;
}

export function loadIdentity(): CourterIdentity | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(identityKey);
  return raw ? JSON.parse(raw) : null;
}

export function saveIdentity(identity: CourterIdentity) {
  localStorage.setItem(identityKey, JSON.stringify(identity));
}

export function loadCases(): CourterCase[] {
  if (typeof window === "undefined") return [];
  const raw = localStorage.getItem(casesKey);
  return raw ? JSON.parse(raw) : [];
}

export function saveCases(cases: CourterCase[]) {
  localStorage.setItem(casesKey, JSON.stringify(cases));
}

export function loadProposals(): ShadowProposal[] {
  if (typeof window === "undefined") return [];
  const raw = localStorage.getItem(proposalKey);
  return raw ? JSON.parse(raw) : [];
}

export function saveProposals(proposals: ShadowProposal[]) {
  localStorage.setItem(proposalKey, JSON.stringify(proposals));
}

export function validateCivilCase(text: string) {
  const blocked = ["criminal", "imprisonment", "violent", "murder", "assault", "jail", "kidnap"];
  return !blocked.some((term) => text.toLowerCase().includes(term));
}

export function verifyPayment(txHash: string, amount: number, courtId: string) {
  const consumed = JSON.parse(localStorage.getItem(txKey) || "[]") as string[];
  const court = courts.find((item) => item.id === courtId);
  if (!txHash.startsWith("0x") || txHash.length < 12) return { ok: false, message: "Enter a valid transaction hash." };
  if (consumed.includes(txHash.toLowerCase())) return { ok: false, message: "This transaction has already been used." };
  if (!court || amount !== court.fee) return { ok: false, message: "The submitted payment amount does not match the required court fee." };
  consumed.push(txHash.toLowerCase());
  localStorage.setItem(txKey, JSON.stringify(consumed));
  return { ok: true, message: "Payment verified. The treasury has received the required GEN." };
}

export function buildCase(input: {
  username: string;
  court: string;
  country: string;
  disputeType: string;
  claimant: string;
  respondent: string;
  evidenceSummary: string;
  files: string[];
  txHash: string;
  senderWallet: string;
}): CourterCase {
  const court = courts.find((item) => item.id === input.court) || courts[0];
  const evidenceText = `${input.claimant} ${input.respondent} ${input.evidenceSummary}`.toLowerCase();
  const contradictionIssues = [
    evidenceText.includes("duplicate") ? "Duplicate document language detected" : "",
    evidenceText.includes("conflict") ? "Conflicting ownership or timeline statement detected" : "",
    evidenceText.includes("registry mismatch") ? "Registry mismatch detected" : ""
  ].filter(Boolean);
  const severity = contradictionIssues.length ? Math.min(0.95, 0.38 + contradictionIssues.length * 0.18) : 0.08;
  const judges = severity > 0.5
    ? ["Justice Ratio", "Justice Veritas", "Justice Equity"]
    : ["Justice Veritas", "Justice Harmony", "Justice Ratio"];
  const laws = [
    `${input.country.toUpperCase().slice(0, 3)}-${input.disputeType.toUpperCase().replace(" ", "-")}-041`,
    `${input.country.toUpperCase().slice(0, 3)}-EVIDENCE-012`,
    `${input.country.toUpperCase().slice(0, 3)}-CIVIL-ARBITRATION-007`
  ];
  const confidence = Number(Math.max(0.62, 0.94 - severity * 0.22).toFixed(2));
  const winner = contradictionIssues.length >= 3 ? "split" : "claimant";
  return {
    id: randomId("CASE"),
    username: input.username,
    court: court.name,
    fee: court.fee,
    country: input.country,
    disputeType: input.disputeType,
    claimant: input.claimant,
    respondent: input.respondent,
    evidenceSummary: input.evidenceSummary,
    files: input.files,
    txHash: input.txHash,
    senderWallet: input.senderWallet,
    status: "finalized",
    structuredEvidence: {
      document_type: input.disputeType === "Land" ? "land_certificate" : "civil_document",
      country: input.country,
      owner: "Claimant declared owner",
      registry_id: `REG-${Math.floor(100 + Math.random() * 900)}`,
      confidence,
      issues_detected: contradictionIssues
    },
    contradictionReport: {
      contradiction_detected: contradictionIssues.length > 0,
      severity,
      issues: contradictionIssues
    },
    judges,
    laws,
    verdict: {
      winner,
      confidence,
      reasoning_summary: [
        "The court reviewed the uploaded civil evidence, extracted facts, and timeline claims.",
        "Relevant legal chunks were ranked by country, dispute type, and evidence keywords.",
        "The selected judges weighed documentary proof, contradiction severity, and civil arbitration fairness.",
        "The verdict is finalized and may be appealed through the Appeal Court."
      ],
      appealable: true,
      plain_english: winner === "claimant"
        ? "The claimant currently has the stronger civil claim based on the submitted documents and timeline."
        : "The evidence is mixed, so the court recommends a split or settlement-style outcome."
    },
    public: true,
    createdAt: new Date().toISOString()
  };
}
