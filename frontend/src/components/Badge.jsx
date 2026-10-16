import { label } from "../api";

export default function Badge({ kind, value }) {
  return <span className={`badge badge--${kind} badge--${value.toLowerCase()}`}>{label(value)}</span>;
}
