import Link from "next/link";
import { Gavel, Scale, Shield } from "lucide-react";

export function Shell({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <main className="min-h-screen court-band">
      <nav className="flex flex-wrap items-center gap-4 border-b border-white/10 px-6 py-4 text-sm">
        <Link href="/" className="font-serif text-xl text-court-gold">The Courter</Link>
        <Link href="/file-case">File Case</Link>
        <Link href="/courtroom">Courtroom</Link>
        <Link href="/appeals">Appeals</Link>
        <Link href="/public-cases">Public Cases</Link>
        <Link href="/shadow-council">Shadow Council</Link>
        <Link href="/judges">Judges</Link>
      </nav>
      <section className="mx-auto max-w-6xl px-6 py-12">
        <h1 className="font-serif text-4xl text-court-gold md:text-6xl">{title}</h1>
        <div className="mt-8">{children}</div>
      </section>
    </main>
  );
}

export function CourtCard({ title, body }: { title: string; body: string }) {
  return (
    <article className="rounded border border-white/10 bg-black/30 p-5 shadow-2xl">
      <h2 className="flex items-center gap-2 font-serif text-2xl text-court-gold">
        <Scale size={22} /> {title}
      </h2>
      <p className="mt-3 text-sm leading-6 text-court-mist/80">{body}</p>
    </article>
  );
}

export function CourtHierarchy() {
  return (
    <div className="grid gap-4 md:grid-cols-4">
      {["Public Court", "Inner Court", "Appeal Court", "Shadow Council"].map((court) => (
        <div key={court} className="rounded border border-court-gold/30 bg-court-panel/80 p-4 text-center">
          <Gavel className="mx-auto mb-2 text-court-gold" />
          <p className="font-serif text-lg">{court}</p>
        </div>
      ))}
    </div>
  );
}

export function SecurityNotice() {
  return (
    <p className="mt-6 flex items-center gap-2 text-sm text-court-mist/70">
      <Shield size={16} /> Civil arbitration only. Criminal accusations are rejected.
    </p>
  );
}
