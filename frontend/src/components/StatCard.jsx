export function StatCard({
  title,
  value,
  subtitle,
  variant = "default",
  icon: Icon,
  badge,
  onClick,
}) {
  return (
    <article
      className={`app-stat-card stat-variant-${variant} ${onClick ? "is-clickable" : ""}`}
      onClick={onClick}
    >
      <div className="stat-card-header">
        <span className="stat-card-title">{title}</span>
        {Icon && (
          <span className="stat-card-icon-wrap">
            <Icon size={18} />
          </span>
        )}
      </div>

      <div className="stat-card-body">
        <strong className="stat-card-value">
          {value !== null && value !== undefined ? value : "—"}
        </strong>
        {badge && <span className="stat-card-badge">{badge}</span>}
      </div>

      {subtitle && <p className="stat-card-subtitle">{subtitle}</p>}
    </article>
  );
}
