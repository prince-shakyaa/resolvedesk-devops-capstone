import { useCallback, useEffect, useState } from "react";
import { api, STATUSES, PRIORITIES, label } from "./api";
import StatCard from "./components/StatCard";
import TicketTable from "./components/TicketTable";
import TicketDrawer from "./components/TicketDrawer";
import NewTicketModal from "./components/NewTicketModal";

const EMPTY_STATS = { total: 0, open: 0, in_progress: 0, resolved: 0, closed: 0, urgent_open: 0, unassigned: 0 };

export default function App() {
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState(EMPTY_STATS);
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(null);
  const [showNew, setShowNew] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastSync, setLastSync] = useState(null);

  const load = useCallback(async () => {
    try {
      setError("");
      const [list, s] = await Promise.all([api.listTickets({ status, priority, q: query }), api.stats()]);
      setTickets(list);
      setStats(s);
      setLastSync(new Date());
    } catch (e) {
      setError(`${e.message}. Is the backend and PostgreSQL running?`);
    } finally {
      setLoading(false);
    }
  }, [status, priority, query]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const id = setInterval(load, 15000);
    return () => clearInterval(id);
  }, [load]);

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand__mark">✓</span>
          <div>
            <b>ResolveDesk</b>
            <small>IT Helpdesk</small>
          </div>
        </div>
        <nav>
          <a className={status === "" ? "active" : ""} onClick={() => setStatus("")}>
            ▦ <span>All tickets</span> <em>{stats.total}</em>
          </a>
          {STATUSES.map((s) => (
            <a key={s} className={status === s ? "active" : ""} onClick={() => setStatus(s)}>
              {s === "OPEN" ? "○" : s === "IN_PROGRESS" ? "◔" : s === "RESOLVED" ? "✓" : "■"}{" "}
              <span>{label(s)}</span> <em>{stats[s.toLowerCase()]}</em>
            </a>
          ))}
        </nav>
        <div className="sidebar__bottom">
          <div className="pipeline">
            <span>Git</span>
            <i />
            <span>CI</span>
            <i />
            <span>Scan</span>
            <i />
            <span>Helm</span>
          </div>
          <small className="muted">
            {lastSync ? `Synced ${lastSync.toLocaleTimeString()}` : "Connecting…"}
          </small>
        </div>
      </aside>

      <main className="main">
        <header>
          <div>
            <p className="eyebrow">SUPPORT QUEUE</p>
            <h1>{status ? label(status) : "All tickets"}</h1>
            <p className="muted">Track, triage and resolve requests from across the company.</p>
          </div>
          <button className="primary" onClick={() => setShowNew(true)}>
            ＋ New ticket
          </button>
        </header>

        {error && <div className="alert">⚠ {error}</div>}

        <section className="stats">
          <StatCard label="Open" value={stats.open} hint="awaiting triage" tone="open" />
          <StatCard label="In progress" value={stats.in_progress} hint="being worked" tone="progress" />
          <StatCard label="Urgent" value={stats.urgent_open} hint="needs attention now" tone="urgent" />
          <StatCard label="Unassigned" value={stats.unassigned} hint="no agent yet" tone="neutral" />
          <StatCard label="Resolved" value={stats.resolved + stats.closed} hint="all time" tone="done" />
        </section>

        <section className="panel">
          <div className="panel__head">
            <input
              className="search"
              placeholder="Search subject…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <div className="filters">
              <button className={priority === "" ? "selected" : ""} onClick={() => setPriority("")}>
                Any priority
              </button>
              {PRIORITIES.map((p) => (
                <button key={p} className={priority === p ? "selected" : ""} onClick={() => setPriority(p)}>
                  {label(p)}
                </button>
              ))}
            </div>
          </div>
          <TicketTable tickets={tickets} selectedId={selected} onSelect={setSelected} loading={loading} />
        </section>
      </main>

      {selected && <TicketDrawer ticketId={selected} onClose={() => setSelected(null)} onChanged={load} />}
      {showNew && (
        <NewTicketModal
          onClose={() => setShowNew(false)}
          onCreated={(t) => {
            setShowNew(false);
            setSelected(t.id);
            load();
          }}
        />
      )}
    </div>
  );
}
