"use client";

import { useMemo, useState } from "react";
import { apiBase, apiGet, type ApiCase, type Proposal } from "../../lib/api";
import { Panel, Shell, Stat } from "../../ui";

type AuditLog = {
  id: string;
  actor_type: string;
  actor_id: string;
  action: string;
  entity_type: string;
  entity_id: string;
  severity: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export default function InternalChamberPage() {
  const [secret, setSecret] = useState("");
  const [cases, setCases] = useState<ApiCase[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [health, setHealth] = useState<any>(null);
  const [filter, setFilter] = useState("");
  const [authError, setAuthError] = useState("");
  const [unlocking, setUnlocking] = useState(false);
  const [isUnlocked, setIsUnlocked] = useState(false);

  async function adminGet<T>(path: string): Promise<T> {
    const response = await fetch(`${apiBase}${path}`, {
      cache: "no-store",
      headers: { "x-admin-secret": secret }
    });
    if (!response.ok) {
      const error = await response.json().catch(async () => ({ detail: await response.text() }));
      throw new Error(typeof error.detail === "string" ? error.detail : "Admin request failed");
    }
    return response.json();
  }

  async function loadAdmin() {
    if (!secret.trim()) {
      setAuthError("Enter the admin password to unlock the chamber.");
      return;
    }
    setUnlocking(true);
    setAuthError("");
    try {
      const [proposalData, caseRes, auditRes, healthRes] = await Promise.all([
        apiGet<{ proposals: Proposal[] }>("/shadow-council/proposals"),
        adminGet<{ cases: ApiCase[] }>("/admin/cases"),
        adminGet<{ events: AuditLog[] }>("/admin/audit-logs"),
        adminGet<any>("/admin/system-health")
      ]);
      setProposals(proposalData.proposals);
      setCases(caseRes.cases || []);
      setLogs(auditRes.events || []);
      setHealth(healthRes);
      setIsUnlocked(true);
    } catch (error) {
      setIsUnlocked(false);
      setCases([]);
      setLogs([]);
      setHealth(null);
      setProposals([]);
      setAuthError(error instanceof Error ? error.message : "Admin authentication failed.");
    } finally {
      setUnlocking(false);
    }
  }

  const visibleLogs = logs.filter((log) => JSON.stringify(log).toLowerCase().includes(filter.toLowerCase()));
  const fraudAlerts = useMemo(() => cases.filter((item) => item.fraud_report?.suspicious).length, [cases]);

  return (
    <Shell title="Internal Chamber" kicker="Secret admin panel">
      <Panel>
        <h2 className="font-serif text-2xl text-court-gold">Admin Access</h2>
        <div className="mt-4 flex flex-wrap gap-3">
          <input className="min-w-72 rounded border border-white/10 bg-black/40 px-3 py-3" type="password" value={secret} onChange={(event) => setSecret(event.target.value)} placeholder="Admin password" />
          <button className="rounded bg-court-gold px-5 py-3 font-semibold text-black disabled:cursor-not-allowed disabled:opacity-60" disabled={unlocking} onClick={() => loadAdmin()}>
            {unlocking ? "Unlocking..." : isUnlocked ? "Refresh Chamber" : "Unlock Admin"}
          </button>
        </div>
        {authError ? <p className="mt-4 rounded border border-court-crimson/40 bg-court-crimson/10 p-3 text-sm">{authError}</p> : null}
        {!isUnlocked ? <p className="mt-4 text-sm text-court-mist/70">Protected system data stays hidden until the admin password is verified.</p> : null}
      </Panel>

      {!isUnlocked ? null : (
        <>
      <div className="mt-6 grid gap-4 md:grid-cols-4">
        <Stat label="Disputes" value={cases.length} />
        <Stat label="Fraud Alerts" value={fraudAlerts} />
        <Stat label="Council Proposals" value={proposals.length} />
        <Stat label="Audit Events" value={logs.length} />
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <Panel>
          <h2 className="font-serif text-2xl text-court-gold">System Health</h2>
          <p className="mt-3 text-sm">Database ready: {health?.db_ready ? "YES" : "NO"}</p>
          <div className="mt-4 grid gap-2 text-sm">
            <div className="rounded border border-white/10 p-3">Backend: <b>{health?.subsystems?.backend?.status || "unknown"}</b></div>
            <div className="rounded border border-white/10 p-3">Database: <b>{health?.subsystems?.database?.status || "unknown"}</b></div>
            <div className="rounded border border-white/10 p-3">OCR: <b>{health?.subsystems?.ocr?.status || "unknown"}</b></div>
            <div className="rounded border border-white/10 p-3">Payment RPCs: <b>{health?.subsystems?.payment_rpcs?.status || "unknown"}</b></div>
            <div className="rounded border border-white/10 p-3">Contracts: <b>{health?.subsystems?.genlayer_contracts?.status || "unknown"}</b></div>
            <div className="rounded border border-white/10 p-3">Verifier Mode: <b>{health?.subsystems?.payment_verifier?.mode || "unknown"}</b></div>
          </div>
          <div className="mt-4 grid gap-2">
            {(health?.warnings || []).map((warning: string) => <p key={warning} className="rounded border border-court-crimson/40 bg-court-crimson/10 p-2 text-sm">{warning}</p>)}
          </div>
        </Panel>
        <Panel>
          <h2 className="font-serif text-2xl text-court-gold">Bradbury Payment Verifier</h2>
          <div className="mt-4 grid gap-2">
            <p className="rounded border border-white/10 p-2 text-sm">Treasury wallet: <span className="break-all text-court-gold">{health?.subsystems?.payment_verifier?.treasury_wallet || "unknown"}</span></p>
            <p className="rounded border border-white/10 p-2 text-sm">Explorer: <span className="break-all text-court-gold">{health?.subsystems?.payment_verifier?.explorer_base_url || "unknown"}</span></p>
            {(health?.subsystems?.payment_rpcs?.checks || []).map((check: any) => (
              <div key={check.name} className="rounded border border-white/10 p-2 text-sm">
                <div><b>{check.name}</b>: {check.status}</div>
                <div className="break-all text-court-mist/70">{check.rpc_url}</div>
                {check.block_number ? <div>Block: {check.block_number}</div> : null}
                {check.error ? <div className="text-court-crimson">{typeof check.error === "string" ? check.error : JSON.stringify(check.error)}</div> : null}
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <Panel>
          <h2 className="font-serif text-2xl text-court-gold">OCR Runtime</h2>
          <div className="mt-4 grid gap-2 text-sm">
            <div className="rounded border border-white/10 p-2">tesseract: {health?.subsystems?.ocr?.tesseract_installed ? "installed" : "missing"}</div>
            <div className="rounded border border-white/10 p-2">pdftoppm: {health?.subsystems?.ocr?.pdftoppm_installed ? "installed" : "missing"}</div>
            <div className="rounded border border-white/10 p-2">pypdf: {health?.subsystems?.ocr?.pypdf_available ? "available" : "missing"}</div>
            <div className="rounded border border-white/10 p-2">pytesseract: {health?.subsystems?.ocr?.pytesseract_available ? "available" : "missing"}</div>
            <div className="rounded border border-white/10 p-2">Pillow: {health?.subsystems?.ocr?.pillow_available ? "available" : "missing"}</div>
          </div>
        </Panel>
        <Panel>
          <h2 className="font-serif text-2xl text-court-gold">Latest Failures</h2>
          <div className="mt-4 grid gap-2">
            {(health?.latest_failures || []).map((event: any) => (
              <div key={event.id} className="rounded border border-white/10 p-3 text-sm">
                <div><b>{event.action}</b> • {event.severity}</div>
                <div className="text-court-mist/70">{event.entity_type}:{event.entity_id}</div>
                <pre className="mt-2 overflow-auto text-xs">{JSON.stringify(event.metadata, null, 2)}</pre>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <Panel className="mt-6">
        <h2 className="font-serif text-2xl text-court-gold">Audit Logs</h2>
        <input className="mt-4 w-full rounded border border-white/10 bg-black/40 px-3 py-3" placeholder="Filter by user, wallet, action, severity, case, metadata" value={filter} onChange={(event) => setFilter(event.target.value)} />
        <div className="mt-4 max-h-[620px] overflow-auto">
          <table className="w-full min-w-[980px] text-left text-sm">
            <thead className="text-court-gold">
              <tr><th className="p-2">Time</th><th>Severity</th><th>Actor</th><th>Action</th><th>Entity</th><th>Metadata</th></tr>
            </thead>
            <tbody>
              {visibleLogs.map((log) => (
                <tr key={log.id} className="border-t border-white/10">
                  <td className="p-2">{new Date(log.created_at).toLocaleString()}</td>
                  <td>{log.severity}</td>
                  <td>{log.actor_type}:{log.actor_id}</td>
                  <td>{log.action}</td>
                  <td>{log.entity_type}:{log.entity_id}</td>
                  <td><pre className="max-w-md overflow-auto text-xs">{JSON.stringify(log.metadata, null, 2)}</pre></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
        </>
      )}
    </Shell>
  );
}
