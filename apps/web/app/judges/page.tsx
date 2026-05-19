import { Panel, Shell, Stat } from "../ui";

const judges = [
  ["Veritas profile", "Strict evidence handling and textual rule discipline"],
  ["Harmony profile", "Settlement-oriented commercial balancing"],
  ["Equity profile", "Fairness, proportionality, and outcome balance"],
  ["Ratio profile", "Chronology, documentary causation, and burden of proof"],
  ["Lex profile", "Formal doctrine and clause precision"],
  ["Sentinel profile", "Fraud detection and procedural discipline"],
  ["Nova profile", "Adaptive reasoning for modern service disputes"],
  ["Meridian profile", "Balanced middle-path analysis"],
  ["Obsidian profile", "High scrutiny of weak or unsupported claims"],
  ["Astra profile", "Systems-level reasoning across records"],
  ["Dominion profile", "Authority, finality, and enforcement logic"]
];

export default function JudgesPage() {
  return (
    <Shell title="Review Profiles" kicker="Structured reasoning profiles">
      <div className="grid gap-4 md:grid-cols-3">
        <Stat label="Profiles" value={judges.length} />
        <Stat label="Default Panel" value="3" />
        <Stat label="Published Onchain" value="Leader Result" />
      </div>
      <Panel className="mt-6">
        <p className="text-sm leading-6 text-court-mist/75">
          These profiles shape the review draft used during commercial dispute analysis. The final published decision is the leader result stored onchain; supporting profile viewpoints remain part of the offchain case record and operator diagnostics.
        </p>
      </Panel>
      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {judges.map(([name, description]) => (
          <Panel key={name}>
            <h2 className="font-serif text-2xl text-court-gold">{name}</h2>
            <p className="mt-3 text-sm leading-6 text-court-mist/70">{description}</p>
          </Panel>
        ))}
      </div>
    </Shell>
  );
}
