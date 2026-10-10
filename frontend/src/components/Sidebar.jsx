import {
  ShieldIcon,
  DashboardIcon,
  WorkbenchIcon,
  HistoryIcon,
  BreakingIcon,
  RiskIcon,
  RecommendationIcon,
  ReportIcon,
  BackendIcon,
  SettingsIcon,
  XIcon,
} from "../utils/icons";

export function Sidebar({
  activePage,
  setActivePage,
  report,
  historyCount = 0,
  backendConnected = false,
  mobileOpen = false,
  setMobileOpen,
}) {
  const breakingCount = report?.summary?.breakingChanges ?? 0;

  const navSections = [
    {
      label: "OVERVIEW",
      items: [
        { id: "dashboard", label: "Dashboard", icon: DashboardIcon },
        { id: "workbench", label: "API Workbench", icon: WorkbenchIcon, highlight: true },
        {
          id: "history",
          label: "Analysis History",
          icon: HistoryIcon,
          badge: historyCount > 0 ? String(historyCount) : null,
        },
      ],
    },
    {
      label: "INSIGHTS",
      items: [
        {
          id: "breaking",
          label: "Breaking Changes",
          icon: BreakingIcon,
          badge: breakingCount > 0 ? String(breakingCount) : null,
          badgeDanger: breakingCount > 0,
        },
        { id: "risk", label: "Risk Insights", icon: RiskIcon },
        { id: "recommendations", label: "Recommendations", icon: RecommendationIcon },
      ],
    },
    {
      label: "REPORTS",
      items: [
        { id: "reports", label: "Reports & Downloads", icon: ReportIcon },
      ],
    },
    {
      label: "SYSTEM",
      items: [
        {
          id: "backend",
          label: "Backend Status",
          icon: BackendIcon,
          dot: backendConnected ? "status-dot-green" : "status-dot-red",
        },
        { id: "settings", label: "Settings", icon: SettingsIcon },
      ],
    },
  ];

  function handleNavigate(id) {
    setActivePage(id);
    if (setMobileOpen) {
      setMobileOpen(false);
    }
  }

  return (
    <>
      {mobileOpen && (
        <div
          className="sidebar-backdrop"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside className={`app-sidebar ${mobileOpen ? "is-mobile-open" : ""}`}>
        <div className="sidebar-brand-box">
          <div className="sidebar-brand" onClick={() => handleNavigate("dashboard")}>
            <div className="brand-shield-glow">
              <ShieldIcon size={22} className="brand-shield-icon" />
              <span className="brand-pulse-dot" />
            </div>
            <div className="brand-text">
              <span className="brand-name">API Sentinel</span>
              <span className="brand-tagline">API Intelligence Platform</span>
            </div>
          </div>

          <button
            type="button"
            className="sidebar-mobile-close"
            onClick={() => setMobileOpen(false)}
            aria-label="Close menu"
          >
            <XIcon size={20} />
          </button>
        </div>

        <nav className="sidebar-nav">
          {navSections.map((sec) => (
            <div key={sec.label} className="nav-group">
              <div className="nav-group-title">{sec.label}</div>
              <ul className="nav-items-list">
                {sec.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = activePage === item.id;
                  return (
                    <li key={item.id}>
                      <button
                        type="button"
                        className={`nav-link ${isActive ? "is-active" : ""} ${
                          item.highlight ? "is-workbench-link" : ""
                        }`}
                        onClick={() => handleNavigate(item.id)}
                      >
                        <span className="nav-icon-wrap">
                          <Icon size={18} />
                        </span>
                        <span className="nav-link-text">{item.label}</span>

                        {item.dot && (
                          <span
                            className={`nav-dot ${item.dot}`}
                            title={backendConnected ? "Live" : "Offline"}
                          />
                        )}

                        {item.badge && (
                          <span
                            className={`nav-badge ${
                              item.badgeDanger ? "badge-danger" : "badge-neutral"
                            }`}
                          >
                            {item.badge}
                          </span>
                        )}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div
            className="sidebar-status-card"
            onClick={() => handleNavigate("backend")}
            role="button"
            tabIndex={0}
            title="Click to check Backend Status"
          >
            <div className="sidebar-status-row">
              <span
                className={`live-indicator-dot ${
                  backendConnected ? "is-online" : "is-offline"
                }`}
              />
              <span className="sidebar-status-text">
                {backendConnected ? "FastAPI Connected" : "Backend Offline"}
              </span>
            </div>
            <span className="sidebar-status-sub">127.0.0.1:8000 · OpenAPI 3.x</span>
          </div>
        </div>
      </aside>
    </>
  );
}
