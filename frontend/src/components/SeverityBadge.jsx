export function SeverityBadge({ type, size = "md", label }) {
  const norm = String(type || "").toUpperCase();
  const text = label || norm;

  let colorClass = "badge-neutral";
  if (norm === "BREAKING" || norm === "FAIL" || norm === "HIGH") {
    colorClass = "badge-danger";
  } else if (norm === "WARNING" || norm === "WARN" || norm === "MEDIUM") {
    colorClass = "badge-warning";
  } else if (norm === "INFO" || norm === "LOW") {
    colorClass = "badge-info";
  } else if (norm === "PASS" || norm === "HEALTHY" || norm === "SUCCESS") {
    colorClass = "badge-success";
  }

  return (
    <span className={`severity-badge ${colorClass} badge-${size}`}>
      <span className="badge-dot" />
      {text}
    </span>
  );
}
