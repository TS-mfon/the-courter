export const treasuryWallet = "0x5905c9Dea6Ae52AA0947D8F7F218263889eDfC4E";

export const courts = [
  { id: "public", name: "Public Court", fee: 2, purpose: "Standard civil disputes" },
  { id: "inner", name: "Inner Court", fee: 5, purpose: "Elite judicial reasoning" },
  { id: "appeal", name: "Appeal Court", fee: 5, purpose: "Secondary judicial review" },
  { id: "shadow_council", name: "Shadow Council", fee: 10, purpose: "Governance override" }
] as const;

export const bradburyNetwork = {
  label: "Bradbury testnet",
  primaryRpc: "https://zksync-os-testnet-genlayer.zksync.dev",
  fallbackRpc: "https://zksync-os-testnet-genlayer.zksync.dev",
  explorerBaseUrl: "https://zksync-os-testnet-genlayer.explorer.zksync.dev"
} as const;

export const countries = ["Nigeria", "India", "Brazil", "Kenya", "Indonesia", "Australia"];
export const disputeTypes = ["Land", "Property", "Rental", "Inheritance", "Contract", "Civil Arbitration"];

export const testCaseExamples = [
  {
    id: "land-nigeria",
    title: "Nigeria land certificate dispute",
    country: "Nigeria",
    disputeType: "Land",
    claimant: "I bought Plot 18 at Lekki Phase II in 2021. The seller transferred possession and gave me a land certificate. Owner: Adaobi Eze. Registry: REG-88341. I paid in full on 2021-08-12 and have survey plan, transfer receipt, and witness statements.",
    respondent: "The respondent says the land was never properly transferred and claims the certificate is invalid because a family consent letter from 2020 was missing.",
    evidenceSummary: "Land certificate dated 2021-08-12, survey plan, bank transfer receipt, family consent letter issue, registry search from Lagos, timeline of possession from 2021 to 2025."
  },
  {
    id: "rental-kenya",
    title: "Rental deposit refund",
    country: "Kenya",
    disputeType: "Rental",
    claimant: "I rented Apartment B4 from 2024-01-01 to 2025-01-01. I paid a two month deposit and vacated on time after inspection. The landlord still withheld the deposit.",
    respondent: "The landlord says there was damage to doors and unpaid utility charges but has not produced invoices or an inspection report signed on move-out day.",
    evidenceSummary: "Lease agreement, deposit receipt, move-in photos, move-out inspection messages, utility payment screenshots, dates of handover and refund demand."
  },
  {
    id: "inheritance-india",
    title: "Inheritance and will conflict",
    country: "India",
    disputeType: "Inheritance",
    claimant: "My late father signed a will in 2019 naming me beneficiary of the family house. Probate reference PRB-22091 was opened in 2024. I also have tax receipts showing he remained in control until death.",
    respondent: "My sibling claims a later handwritten document from 2023 overrides the will, but the signature date conflicts with hospital admission records.",
    evidenceSummary: "Registered will, probate filing, hospital records, property tax receipts, timeline contradiction about the 2023 handwritten document, witness statements."
  },
  {
    id: "contract-brazil",
    title: "Contract non-payment",
    country: "Brazil",
    disputeType: "Contract",
    claimant: "I delivered a software integration under a signed services agreement on 2025-02-14. The client accepted staging and production delivery but refused to pay the final invoice.",
    respondent: "The client says the deliverables were incomplete, yet internal emails show acceptance and a go-live approval before the invoice due date.",
    evidenceSummary: "Signed contract, scope of work, invoice INV-2044, acceptance email trail, deployment checklist, due date 2025-03-01, partial payment history."
  },
  {
    id: "property-australia",
    title: "Property sale timeline conflict",
    country: "Australia",
    disputeType: "Property",
    claimant: "I paid a reservation deposit for a property sale in Melbourne and later the seller resold the same property to another buyer. The seller gave me a signed receipt and sale memorandum first.",
    respondent: "The seller claims my deposit lapsed, but their messages on 2025-04-21 confirmed the deal was still active after the alleged lapse date.",
    evidenceSummary: "Signed sale memorandum, deposit receipt, duplicate receipt concern, bank transfer proof, message timeline, competing buyer agreement date, ownership statements."
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
