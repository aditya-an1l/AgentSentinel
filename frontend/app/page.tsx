'use client';

import { useCallback, useEffect, useState } from "react";

type Health = { status: string; model_mode: string; nano_model: string | null; ultra_configured: boolean; tavily_configured: boolean };
type Stats = { total_events: number; allow: number; deny: number; escalate: number; confirm: number; average_recorded_latency_ms: number | null };
type EventRow = { id: number; created_at: string; session_id: string; tool: string; verdict: string; reason: string; screening_source: string; executed: boolean; latency_ms: number };
type Scenario = { id: string; title: string; description: string; expected: string };
const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

function Metric({ label, value, detail }: { label: string; value: string | number; detail: string }) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>;
}
function Badge({ value }: { value: string }) { return <span className={`badge ${value}`}>{value}</span>; }

export default function Dashboard() {
  const [health, setHealth] = useState<Health | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [events, setEvents] = useState<EventRow[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState("");
  const [tool, setTool] = useState("filesystem.list");
  const [args, setArgs] = useState('{"path":"."}');
  const [session, setSession] = useState("dashboard-session");

  const refresh = useCallback(async () => {
    try {
      const [h, s, e, v] = await Promise.all([
        fetch(`${API}/api/health`, { cache: "no-store" }),
        fetch(`${API}/api/stats`, { cache: "no-store" }),
        fetch(`${API}/api/events?limit=40`, { cache: "no-store" }),
        fetch(`${API}/api/scenarios`, { cache: "no-store" })
      ]);
      if (![h, s, e, v].every((response) => response.ok)) throw new Error("API request failed");
      setHealth(await h.json()); setStats(await s.json()); setEvents(await e.json()); setScenarios(await v.json());
    } catch { setNotice("Cannot reach the API. Start the stack with docker compose up --build."); }
  }, []);

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 5000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  async function runScenario(id: string) {
    setBusy(id); setNotice("");
    try {
      const response = await fetch(`${API}/api/demo/run/${id}`, { method: "POST" });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Scenario request failed");
      setNotice(`${data.scenario.title}: ${data.verdict}${data.executed ? " · tool executed" : " · not executed"}`);
      await refresh();
    } catch (error) { setNotice(error instanceof Error ? error.message : "Scenario failed"); }
    finally { setBusy(null); }
  }

  async function submitTool(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy("manual"); setNotice("");
    try {
      const response = await fetch(`${API}/api/tool-calls`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: session, tool, arguments: JSON.parse(args) })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Tool call failed");
      setNotice(`${data.verdict.toUpperCase()}: ${data.reason}`);
      await refresh();
    } catch (error) { setNotice(error instanceof Error ? error.message : "Invalid JSON or request"); }
    finally { setBusy(null); }
  }

  async function reset() {
    if (!window.confirm("Clear the local event log and sandbox workspace?")) return;
    setBusy("reset");
    try {
      const response = await fetch(`${API}/api/reset`, { method: "POST" });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Reset failed");
      setNotice(data.message); await refresh();
    } catch (error) { setNotice(error instanceof Error ? error.message : "Reset failed"); }
    finally { setBusy(null); }
  }

  const examples: Record<string, string> = {
    shell: '{"command":"pwd"}',
    "filesystem.list": '{"path":"."}',
    "filesystem.read": '{"path":"notes.txt"}',
    "filesystem.write": '{"path":"notes.txt","content":"hello from AgentSentinel"}',
    "web.search": '{"query":"AI agent security research"}'
  };

  return <main className="shell">
    <header className="topbar">
      <div><div className="eyebrow">RUNTIME SECURITY · MVP</div><h1>Agent<span>Sentinel</span></h1>
        <p className="subtitle">Tool-call screening and flight recorder for AI agents.</p></div>
      <div className="status"><i className={health?.status === "ok" ? "online" : ""} />
        {health?.status === "ok" ? "API connected" : "API unavailable"}
        <b>{health?.model_mode ?? "checking"} mode</b></div>
    </header>

    {notice && <div className="notice" role="status">{notice}</div>}

    <section className="metrics">
      <Metric label="Recorded calls" value={stats?.total_events ?? "—"} detail="Events in local SQLite store" />
      <Metric label="Allowed" value={stats?.allow ?? "—"} detail="Passed screening" />
      <Metric label="Denied" value={stats?.deny ?? "—"} detail="Rejected before execution" />
      <Metric label="Escalated" value={stats?.escalate ?? "—"} detail="Held for deeper review" />
    </section>

    <section className="columns">
      <div className="panel">
        <div className="panel-title"><div><div className="eyebrow">DEMO WORKSPACE</div><h2>Replay a scenario</h2></div><small>{scenarios.length} scenarios</small></div>
        {scenarios.map((item) => <div className="scenario" key={item.id}>
          <div><strong>{item.title}</strong><p>{item.description}</p><small>Expected: {item.expected}</small></div>
          <button disabled={busy !== null} onClick={() => void runScenario(item.id)}>{busy === item.id ? "Running…" : "Run"}</button>
        </div>)}
      </div>

      <div className="panel">
        <div className="eyebrow">MANUAL REQUEST</div><h2>Inspect a tool call</h2>
        <form onSubmit={submitTool} className="form">
          <label>Session ID<input value={session} onChange={(e) => setSession(e.target.value)} maxLength={120} /></label>
          <label>Tool<select value={tool} onChange={(e) => { setTool(e.target.value); setArgs(examples[e.target.value]); }}>
            {Object.keys(examples).map((name) => <option key={name} value={name}>{name}</option>)}
          </select></label>
          <label>Arguments (JSON)<textarea value={args} onChange={(e) => setArgs(e.target.value)} rows={6} spellCheck={false} /></label>
          <button className="primary" disabled={busy !== null}>{busy === "manual" ? "Screening…" : "Screen and execute if allowed"}</button>
        </form>
        <p className="config">Provider: <b>{health?.model_mode ?? "—"}</b> · Tavily: <b>{health?.tavily_configured ? "configured" : "not configured"}</b><br />
          Mock mode is a local heuristic, not a live model response.</p>
      </div>
    </section>

    <section className="panel">
      <div className="panel-title"><div><div className="eyebrow">FLIGHT RECORDER</div><h2>Recent tool-call events</h2></div>
        <div className="actions"><small>Refreshes every 5 seconds</small><button onClick={() => void refresh()}>Refresh</button><button className="danger" disabled={busy !== null} onClick={() => void reset()}>Reset demo</button></div>
      </div>
      <div className="table-scroll"><table><thead><tr><th>Event</th><th>Tool</th><th>Verdict</th><th>Source</th><th>Executed</th><th>Time</th></tr></thead>
        <tbody>{events.map((item) => <tr key={item.id}><td>#{item.id}<small>{new Date(item.created_at).toLocaleTimeString()}</small></td>
          <td><code>{item.tool}</code><small>{item.session_id}</small></td><td><Badge value={item.verdict} /></td>
          <td>{item.screening_source}</td><td>{item.executed ? "Yes" : "No"}</td><td>{item.latency_ms.toFixed(1)} ms</td></tr>)}
          {events.length === 0 && <tr><td colSpan={6} className="empty">No events yet. Run a scenario to populate the timeline.</td></tr>}
        </tbody></table></div>
      <p className="footnote">Recorded latency is local end-to-end proxy time, not a model benchmark. SQLite is mutable local storage, not an immutable audit system.</p>
    </section>
    <footer><span>AgentSentinel · MVP 0.1.0</span><span>Aditya Anil · Ashreya Gatla</span></footer>
  </main>;
}
