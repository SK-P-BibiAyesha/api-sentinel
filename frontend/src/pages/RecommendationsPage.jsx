import { SeverityBadge } from "../components/SeverityBadge";
import {
  RecommendationIcon,
  CheckCircleIcon,
  WorkbenchIcon,
  ArrowRightIcon,
} from "../utils/icons";

export function RecommendationsPage({ report, setActivePage }) {
  const findings = report?.changes || [];

  return (
    <div className="page-container recommendations-page">
      {/* Top Banner */}
      <section className="app-card playbook-hero-card">
        <div className="card-header">
          <div className="header-icon-title">
            <span className="card-icon-tag tag-cyan">
              <RecommendationIcon size={20} />
            </span>
            <div>
              <span className="card-eyebrow">ENGINEERING REMEDIATION PLAYBOOK</span>
              <h2 className="card-title">Backward Compatibility Strategies</h2>
            </div>
          </div>
        </div>

        <p className="playbook-intro">
          When schema drift or breaking changes are detected, follow these proven architectural strategies to safeguard active clients without halting product iteration:
        </p>

        <div className="playbook-strategies-grid">
          <div className="strategy-card">
            <strong>1. Expand and Contract Pattern</strong>
            <p>
              Never rename or delete a field in a single release. First introduce the new property (Expand), migrate consumers, and deprecate the old property before eventual decommissioning (Contract).
            </p>
          </div>

          <div className="strategy-card">
            <strong>2. RFC 8594 Deprecation & Sunset Headers</strong>
            <p>
              Attach standard HTTP headers <code>Deprecation: true</code> and <code>Sunset: 2027-01-01</code> to notify consumer gateways programmatically before turning off legacy endpoints.
            </p>
          </div>

          <div className="strategy-card">
            <strong>3. URI Path Versioning (/v1 → /v2)</strong>
            <p>
              When breaking response data types or removing mandatory parameters, mount a new routing path rather than mutating existing routes in-place.
            </p>
          </div>
        </div>
      </section>

      {/* Report Remediation Action Items */}
      <section className="remediation-items-section">
        <div className="section-title-row">
          <div>
            <h2 className="section-title">
              Action Items for Current Audit ({findings.length})
            </h2>
            <p className="section-subtitle">
              {report
                ? `Specific recommendations for ${report.oldFileName} → ${report.newFileName}`
                : "No comparison report active."}
            </p>
          </div>

          {report && (
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => setActivePage("workbench")}
            >
              <span>View Findings in Workbench</span>
              <ArrowRightIcon size={14} />
            </button>
          )}
        </div>

        {!report ? (
          <div className="app-card empty-state-box">
            <RecommendationIcon size={32} className="text-muted" />
            <h3>No Active Findings</h3>
            <p className="text-muted">
              Run an API comparison in the Workbench to generate tailored remediation recommendations.
            </p>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => setActivePage("workbench")}
            >
              <WorkbenchIcon size={16} />
              <span>Open API Workbench</span>
            </button>
          </div>
        ) : findings.length === 0 ? (
          <div className="app-card empty-state-box">
            <div className="empty-icon-ring ring-success">
              <CheckCircleIcon size={32} />
            </div>
            <h3>No Action Required</h3>
            <p className="text-muted">
              All checks passed! The candidate specification maintains full backward compatibility.
            </p>
          </div>
        ) : (
          <div className="recommendations-list">
            {findings.map((item, idx) => {
              const isBreaking = item.type === "BREAKING";
              return (
                <div
                  key={`${item.id}-${idx}`}
                  className={`app-card rec-card-item ${isBreaking ? "is-breaking-rec" : ""}`}
                >
                  <div className="rec-card-top">
                    <div className="rec-badges-group">
                      <SeverityBadge type={item.type} size="sm" />
                      <span className="rec-index-tag">Item #{idx + 1}</span>
                    </div>
                    <code className="rec-endpoint-code">{item.endpoint}</code>
                  </div>

                  <h3 className="rec-finding-title">{item.title}</h3>
                  <p className="rec-finding-desc">{item.description}</p>

                  <div className="rec-solution-box">
                    <div className="rec-solution-header">
                      <span className="rec-solution-tag">
                        {isBreaking ? "MANDATORY REMEDIATION ACTION" : "RECOMMENDED ACTION"}
                      </span>
                    </div>
                    <p className="rec-solution-text">
                      {item.recommendation ||
                        "Review this schema change with consumer teams to confirm no client regressions occur."}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
