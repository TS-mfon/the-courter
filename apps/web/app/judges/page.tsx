import { Panel, Shell, Stat } from "../ui";

const judges = [
  ["Justice Veritas", "Strict ownership, evidence, legal text"],
  ["Justice Harmony", "Compromise, settlement, social stability"],
  ["Justice Equity", "Fairness, proportionality, humanitarian balance"],
  ["Justice Ratio", "Rational legal causation, chronology, documentary proof"],
  ["Justice Lex", "Formal doctrine and statutory precision"],
  ["Justice Sentinel", "Fraud detection and procedural discipline"],
  ["Justice Nova", "Modern disputes and adaptive civil reasoning"],
  ["Justice Meridian", "Balanced middle-path analysis"],
  ["Justice Obsidian", "Hard scrutiny of weak claims"],
  ["Justice Astra", "Broad systems reasoning"],
  ["Justice Dominion", "Authority, finality, and enforcement"]
];

export default function JudgesPage() {
  return (
    <Shell title="Judicial Personas" kicker="Judge persona engine">
      <div className="grid gap-4 md:grid-cols-3">
        <Stat label="Judge Profiles" value={judges.length} />
        <Stat label="Standard Jury" value="3" />
        <Stat label="Appeal Rule" value="Different Judges" />
      </div>
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
