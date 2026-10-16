export default function StatCard({ label, value, hint, tone = "neutral" }) {
  return (
    <div className={`stat stat--${tone}`}>
      <small>{label}</small>
      <strong>{value}</strong>
      <span>{hint}</span>
    </div>
  );
}
