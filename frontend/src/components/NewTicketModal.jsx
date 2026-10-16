import { useState } from "react";
import { api, CATEGORIES, PRIORITIES, label } from "../api";

export default function NewTicketModal({ onClose, onCreated }) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setBusy(true);
    setError("");
    try {
      const created = await api.createTicket({
        subject: f.get("subject"),
        description: f.get("description"),
        category: f.get("category"),
        priority: f.get("priority"),
        requester: f.get("requester"),
        assignee: f.get("assignee") || null,
      });
      onCreated(created);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <form className="modal" onSubmit={submit} onClick={(e) => e.stopPropagation()}>
        <div className="modal__head">
          <div>
            <p className="eyebrow">NEW TICKET</p>
            <h2>Report an issue</h2>
          </div>
          <button type="button" className="close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        {error && <div className="alert">⚠ {error}</div>}
        <label>
          Subject
          <input name="subject" required minLength={3} placeholder="e.g. Cannot connect to office Wi-Fi" />
        </label>
        <label>
          Description
          <textarea name="description" placeholder="What happened? What did you already try?" />
        </label>
        <div className="form-row">
          <label>
            Category
            <select name="category" defaultValue="SOFTWARE">
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {label(c)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Priority
            <select name="priority" defaultValue="MEDIUM">
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>
                  {label(p)}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="form-row">
          <label>
            Requester
            <input name="requester" required placeholder="name@company.com" />
          </label>
          <label>
            Assignee (optional)
            <input name="assignee" placeholder="agent name" />
          </label>
        </div>
        <button className="primary full" disabled={busy}>
          {busy ? "Creating…" : "Create ticket"}
        </button>
      </form>
    </div>
  );
}
