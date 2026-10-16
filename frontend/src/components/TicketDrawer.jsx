import { useEffect, useState } from "react";
import Badge from "./Badge";
import { api, STATUSES, PRIORITIES, label, timeAgo } from "../api";

export default function TicketDrawer({ ticketId, onClose, onChanged }) {
  const [ticket, setTicket] = useState(null);
  const [comments, setComments] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    try {
      setError("");
      const [t, c] = await Promise.all([api.getTicket(ticketId), api.listComments(ticketId)]);
      setTicket(t);
      setComments(c);
    } catch (e) {
      setError(e.message);
    }
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticketId]);

  const patch = async (payload) => {
    setBusy(true);
    try {
      await api.updateTicket(ticketId, payload);
      await refresh();
      onChanged();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    if (!window.confirm(`Delete ticket #${ticketId}? This cannot be undone.`)) return;
    await api.deleteTicket(ticketId);
    onChanged();
    onClose();
  };

  const submitComment = async (e) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const body = form.get("body").trim();
    if (!body) return;
    setBusy(true);
    try {
      await api.addComment(ticketId, { author: form.get("author") || "agent", body });
      e.target.reset();
      await refresh();
      onChanged();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const assign = async (e) => {
    e.preventDefault();
    const assignee = new FormData(e.currentTarget).get("assignee").trim();
    await patch({ assignee: assignee || null });
  };

  return (
    <aside className="drawer">
      <div className="drawer__head">
        <div>
          <p className="eyebrow">TICKET #{ticketId}</p>
          <h2>{ticket ? ticket.subject : "Loading…"}</h2>
        </div>
        <button className="close" onClick={onClose} aria-label="Close">
          ×
        </button>
      </div>

      {error && <div className="alert">⚠ {error}</div>}

      {ticket && (
        <>
          <div className="drawer__badges">
            <Badge kind="status" value={ticket.status} />
            <Badge kind="priority" value={ticket.priority} />
            <Badge kind="category" value={ticket.category} />
          </div>

          <dl className="meta">
            <dt>Requester</dt>
            <dd>{ticket.requester}</dd>
            <dt>Assignee</dt>
            <dd>{ticket.assignee || <span className="muted">Unassigned</span>}</dd>
            <dt>Opened</dt>
            <dd>{new Date(ticket.created_at).toLocaleString()}</dd>
            {ticket.resolved_at && (
              <>
                <dt>Resolved</dt>
                <dd>{new Date(ticket.resolved_at).toLocaleString()}</dd>
              </>
            )}
          </dl>

          {ticket.description && <p className="description">{ticket.description}</p>}

          <section className="drawer__section">
            <h3>Workflow</h3>
            <div className="chip-row">
              {STATUSES.map((s) => (
                <button
                  key={s}
                  disabled={busy || s === ticket.status}
                  className={`chip ${s === ticket.status ? "chip--active" : ""}`}
                  onClick={() => patch({ status: s })}
                >
                  {label(s)}
                </button>
              ))}
            </div>
            <div className="chip-row">
              {PRIORITIES.map((p) => (
                <button
                  key={p}
                  disabled={busy || p === ticket.priority}
                  className={`chip chip--ghost ${p === ticket.priority ? "chip--active" : ""}`}
                  onClick={() => patch({ priority: p })}
                >
                  {label(p)}
                </button>
              ))}
            </div>
            <form className="inline-form" onSubmit={assign}>
              <input name="assignee" placeholder="Assign to agent…" defaultValue={ticket.assignee || ""} />
              <button className="secondary" disabled={busy}>
                Assign
              </button>
            </form>
          </section>

          <section className="drawer__section">
            <h3>Activity ({comments.length})</h3>
            {comments.length === 0 && <p className="muted">No comments yet.</p>}
            <ul className="comments">
              {comments.map((c) => (
                <li key={c.id}>
                  <div className="avatar">{c.author.slice(0, 2).toUpperCase()}</div>
                  <div>
                    <b>{c.author}</b> <small>{timeAgo(c.created_at)}</small>
                    <p>{c.body}</p>
                  </div>
                </li>
              ))}
            </ul>
            <form className="comment-form" onSubmit={submitComment}>
              <input name="author" placeholder="Your name" defaultValue="agent" required />
              <textarea name="body" placeholder="Add an update for the requester…" required />
              <button className="primary" disabled={busy}>
                Post update
              </button>
            </form>
          </section>

          <button className="danger" onClick={remove} disabled={busy}>
            Delete ticket
          </button>
        </>
      )}
    </aside>
  );
}
