import { CourtFlow, Panel, PrimaryLink, Shell, Stat } from "./ui";
import { courts, disputeTypes, treasuryWallet } from "./lib/courter";

export default function HomePage() {
  return (
    <Shell title="The Courter" kicker="Autonomous AI Judicial Civilization Protocol">
      <section className="grid min-h-[70vh] items-center gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <div>
          <p className="max-w-3xl text-xl leading-8 text-court-mist/85">
            File a civil dispute, submit evidence, verify GEN payment, watch the AI jury deliberate,
            receive a finalized verdict, appeal if needed, and escalate to the Shadow Council.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <PrimaryLink href="/file-case">File A Case</PrimaryLink>
            <PrimaryLink href="/public-cases">Explore Public Cases</PrimaryLink>
            <PrimaryLink href="/shadow-council">Enter Shadow Council</PrimaryLink>
          </div>
          <p className="mt-6 max-w-2xl text-sm leading-6 text-court-mist/60">
            Civil arbitration only. Criminal accusations, imprisonment matters, and violent crime claims are rejected before court submission.
          </p>
        </div>
        <Panel className="relative overflow-hidden">
          <div className="absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-court-crimson/40 to-transparent" />
          <div className="relative mx-auto grid aspect-[4/5] max-w-sm place-items-center rounded-t-full border border-court-gold/30 bg-black/50">
            <div className="size-40 rounded-full bg-court-gold/15 shadow-[0_0_90px_rgba(214,170,79,0.45)]" />
            <div className="absolute bottom-10 text-center">
              <p className="font-serif text-3xl text-court-gold">The Jury Awaits</p>
              <p className="mt-2 text-sm text-court-mist/60">Transparent consensus. Finalized verdicts.</p>
            </div>
          </div>
        </Panel>
      </section>

      <CourtFlow />

      <section className="mt-10 grid gap-4 md:grid-cols-4">
        {courts.map((court) => <Stat key={court.id} label={court.purpose} value={`${court.fee} GEN`} />)}
      </section>

      <section className="mt-10 grid gap-4 lg:grid-cols-3">
        <Panel>
          <h2 className="font-serif text-2xl text-court-gold">Supported Civil Disputes</h2>
          <div className="mt-4 flex flex-wrap gap-2">
            {disputeTypes.map((type) => <span key={type} className="rounded border border-white/10 px-3 py-2 text-sm">{type}</span>)}
          </div>
        </Panel>
        <Panel>
          <h2 className="font-serif text-2xl text-court-gold">Treasury Wallet</h2>
          <p className="mt-4 break-all text-sm text-court-mist/70">{treasuryWallet}</p>
          <p className="mt-3 text-sm text-court-mist/60">All court fees are verified against this address.</p>
        </Panel>
        <Panel>
          <h2 className="font-serif text-2xl text-court-gold">How It Works</h2>
          <p className="mt-4 text-sm leading-6 text-court-mist/70">
            Identity, payment, evidence, OCR-style structuring, contradiction detection, legal retrieval,
            judge selection, verdict generation, appeals, public records, governance.
          </p>
        </Panel>
      </section>
    </Shell>
  );
}
