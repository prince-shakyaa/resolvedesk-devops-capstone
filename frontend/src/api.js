const BASE = "/api";

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      if (body.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  return response.status === 204 ? null : response.json();
}

export const api = {
  listTickets: (params = {}) => {
    const query = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "")
    ).toString();
    return request(`/tickets${query ? `?${query}` : ""}`);
  },
  stats: () => request("/tickets/stats"),
  getTicket: (id) => request(`/tickets/${id}`),
  createTicket: (payload) => request("/tickets", { method: "POST", body: JSON.stringify(payload) }),
  updateTicket: (id, payload) => request(`/tickets/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteTicket: (id) => request(`/tickets/${id}`, { method: "DELETE" }),
  listComments: (id) => request(`/tickets/${id}/comments`),
  addComment: (id, payload) =>
    request(`/tickets/${id}/comments`, { method: "POST", body: JSON.stringify(payload) }),
};

export const STATUSES = ["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"];
export const PRIORITIES = ["LOW", "MEDIUM", "HIGH", "URGENT"];
export const CATEGORIES = ["HARDWARE", "SOFTWARE", "NETWORK", "ACCESS", "OTHER"];

export const label = (value) =>
  value
    .toLowerCase()
    .split("_")
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");

export function timeAgo(iso) {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} hr ago`;
  return `${Math.floor(diff / 86400)} d ago`;
}
