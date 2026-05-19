import Link from "next/link";
import { ArrowRight, BriefcaseBusiness, FileSearch, Scale, ShieldCheck, Workflow } from "lucide-react";

export function Shell({ title, kicker, children }: { title: string; kicker?: string; children: React.ReactNode }) {
  return (
    <main className="min-h-screen court-band text-court-mist">
      <nav className="sticky top-0 z-50 border-b border-white/10 bg-black/70 px-4 py-3 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-3 text-sm">
          <Link href="/" className="mr-3 flex items-center gap-2 font-serif text-xl text-court-gold">
            <BriefcaseBusiness size={22} /> The Courter
          </Link>
          {[
            ["/file-case", "Start Review"],
            ["/public-cases", "Decision Records"],
            ["/appeals", "Escalations"],
            ["/judges", "Review Profiles"],
            ["/governance/analytics", "Analytics"]
          ].map(([href, label]) => (
            <Link key={href} className="rounded px-2 py-1 text-court-mist/75 hover:bg-white/10 hover:text-white" href={href}>{label}</Link>
          ))}
        </div>
      </nav>
      <section className="mx-auto max-w-7xl px-4 py-10">
        {kicker ? <p className="text-sm uppercase tracking-[0.25em] text-court-gold/80">{kicker}</p> : null}
        <h1 className="mt-2 max-w-5xl font-serif text-4xl text-court-gold md:text-6xl">{title}</h1>
        <div className="mt-8">{children}</div>
      </section>
    </main>
  );
}

export function Panel({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <section className={`rounded-md border border-white/10 bg-black/35 p-5 shadow-2xl backdrop-blur ${className}`}>{children}</section>;
}

export function PrimaryLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="inline-flex items-center gap-2 rounded bg-court-gold px-5 py-3 font-semibold text-black">
      {children} <ArrowRight size={18} />
    </Link>
  );
}

export function StepBadge({ children }: { children: React.ReactNode }) {
  return <span className="rounded border border-court-gold/40 bg-court-gold/10 px-3 py-1 text-xs uppercase tracking-[0.18em] text-court-gold">{children}</span>;
}

export function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded border border-white/10 bg-white/[0.04] p-4">
      <p className="text-xs uppercase tracking-[0.18em] text-court-mist/50">{label}</p>
      <p className="mt-2 font-serif text-3xl text-court-gold">{value}</p>
    </div>
  );
}

export function CourtFlow() {
  return (
    <div className="grid gap-3 md:grid-cols-5">
      {["Agreement", "Intake", "Evidence Review", "GenLayer Decision", "Escalation"].map((item, index) => (
        <div key={item} className="rounded border border-court-gold/30 bg-court-panel/80 p-4 text-center">
          {index === 0 ? <ShieldCheck className="mx-auto mb-2 text-court-gold" /> : index === 2 ? <FileSearch className="mx-auto mb-2 text-court-gold" /> : <Workflow className="mx-auto mb-2 text-court-gold" />}
          <p className="font-serif">{item}</p>
        </div>
      ))}
    </div>
  );
}

export function VerdictSeal({ confidence }: { confidence: number }) {
  return (
    <div className="grid size-32 place-items-center rounded-full border border-court-gold bg-court-gold/10 text-center shadow-[0_0_40px_rgba(214,170,79,0.25)]">
      <div>
        <Scale className="mx-auto text-court-gold" />
        <p className="mt-1 font-serif text-2xl text-court-gold">{Math.round(confidence * 100)}%</p>
        <p className="text-[10px] uppercase tracking-[0.2em]">confidence</p>
      </div>
    </div>
  );
}
