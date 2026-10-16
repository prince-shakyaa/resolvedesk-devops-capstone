import Badge from "./Badge";
import { timeAgo } from "../api";

export default function TicketTable({ tickets, selectedId, onSelect, loading }) {
  if (loading) return <div className="empty">Loading tickets…</div>;
  if (!tickets.length) return <div className="empty">No tickets match this view.</div>;

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Subject</th>
            <th>Requester</th>
            <th>Category</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Assignee</th>
            <th>Updated</th>
          </tr>
        </thead>
        <tbody>
          {tickets.map((t) => (
            <tr key={t.id} className={t.id === selectedId ? "row--selected" : ""} onClick={() => onSelect(t.id)}>
              <td className="mono">{t.id}</td>
              <td>
                <div className="subject">
                  <b>{t.subject}</b>
                  {t.comment_count > 0 && <small>💬 {t.comment_count}</small>}
                </div>
              </td>
              <td>{t.requester}</td>
              <td>
                <Badge kind="category" value={t.category} />
              </td>
              <td>
                <Badge kind="priority" value={t.priority} />
              </td>
              <td>
                <Badge kind="status" value={t.status} />
              </td>
              <td className={t.assignee ? "" : "muted"}>{t.assignee || "Unassigned"}</td>
              <td className="muted">{timeAgo(t.updated_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
