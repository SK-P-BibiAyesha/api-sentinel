import { MenuIcon, RefreshIcon, WorkbenchIcon } from "../utils/icons";

const PAGE_TITLES = {
  dashboard: { title: "API Intelligence Dashboard", subtitle: "Understand API changes before they impact your consumers." },
  workbench: { title: "API Comparison Workbench", subtitle: "Automated drift detection and backward-compatibility linter." },
  history: { title: "Analysis History", subtitle: "Local audit logs of executed API schema comparisons." },
  breaking: { title: "Breaking Changes Analysis", subtitle: "Inspect detected incompatibilities and consumer risks." },
  risk: { title: "Risk Insights & Impact", subtitle: "Deterministic risk severity distributions and schema metrics." },
  recommendations: { title: "Remediation Playbook", subtitle: "Engineering guidance to preserve backward compatibility." },
  reports: { title: "Reports & Export Center", subtitle: "Download audit PDFs and export structured JSON reports." },
  backend: { title: "FastAPI Backend Health", subtitle: "Live service connection status and endpoint diagnostics." },
  settings: { title: "Dashboard Settings", subtitle: "Configure interface preferences and local storage options." },
};

export function Header({
  activePage,
  setActivePage,
  backendConnected,
  checkingBackend,
  onRefreshBackend,
  onOpenMobile,
}) {
  const pageInfo = PAGE_TITLES[activePage] || PAGE_TITLES.dashboard;

  const todayStr = new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date());

  return (
    <header className="app-top-header">
      <div className="header-left">
        <button
          type="button"
          className="header-hamburger-btn"
          onClick={onOpenMobile}
          aria-label="Open navigation menu"
        >
          <MenuIcon size={22} />
        </button>

        <div className="header-breadcrumbs">
          <span className="crumb-root">API Sentinel</span>
          <span className="crumb-sep">/</span>
          <span className="crumb-current">{pageInfo.title}</span>
        </div>
      </div>

      <div className="header-right">
        <div className="header-date-pill" title="System date">
          <span className="date-text">{todayStr}</span>
        </div>

        <button
          type="button"
          className={`backend-pill ${backendConnected ? "is-connected" : "is-disconnected"}`}
          onClick={onRefreshBackend}
          title={
            backendConnected
              ? "Backend is live at 127.0.0.1:8000. Click to refresh."
              : "Backend unreachable. Click to retry connection."
          }
        >
          <span className={`pill-dot ${backendConnected ? "dot-online" : "dot-offline"}`} />
          <span className="pill-text">
            {checkingBackend
              ? "Checking..."
              : backendConnected
              ? "Backend Live"
              : "Backend Offline"}
          </span>
          <span className={`pill-refresh-icon ${checkingBackend ? "is-spinning" : ""}`}>
            <RefreshIcon size={13} />
          </span>
        </button>

        {activePage !== "workbench" && (
          <button
            type="button"
            className="btn btn-primary btn-sm header-action-btn"
            onClick={() => setActivePage("workbench")}
          >
            <WorkbenchIcon size={15} />
            <span>New Comparison</span>
          </button>
        )}
      </div>
    </header>
  );
}
