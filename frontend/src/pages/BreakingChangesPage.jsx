import { useState } from "react";
import { SeverityBadge } from "../components/SeverityBadge";
import { FindingDetailModal } from "../components/FindingDetailModal";
import {
  BreakingIcon,
  CheckCircleIcon,
  WorkbenchIcon,
  DownloadIcon,
} from "../utils/icons";

export function BreakingChangesPage({ report, setActivePage, onDownloadPdf }) {
  const [selectedFinding, setSelectedFinding] = useState(null);

  const findings = report?.changes || [];
  const breakingChanges = findings.filter((f) => f.type === "BREAKING");

  // Group breaking changes by endpoint
  const groupedByEndpoint = breakingChanges.reduce((acc, curr) => {
    const key = curr.endpoint || "General / Schema";
    if (!acc[key]) acc[key] = [];
    acc[key].push(curr);
    return acc;
  }, {});

  const endpointKeys = Object.keys(groupedByEndpoint);

  return (
    <div className="page-container breaking-page">
      {/* Educational Banner: Why Backward Compatibility Matters */}
      <section className="app-card compatibility-education-card">
        <div className="edu-card-header">
          <div className="edu-icon-wrap">
            <BreakingIcon size={24} />
          </div>
          <div>
            <span className="card-eyebrow text-danger">MISSION-CRITICAL INSIGHT</span>
            <h2 className="card-title">Why Breaking API Changes Matter</h2>
          </div>
        </div>

        <p className="edu-text">
          In microservice architectures and public developer ecosystems, client applications depend on predictable schemas. Abruptly deleting routes, altering payload properties, or mutating primitive types (such as integers to strings) leads to immediate production failures:
        </p>

        <div className="edu-pillars-grid">
          <div className="edu-pillar-item">
            <strong className="text-danger">1. Client Deserialization Failures</strong>
            <p>
              Strongly-typed mobile apps and backend consumers crash when expected types change or required response fields are removed without deprecation.
            </p>
          </div>

          <div className="edu-pillar-item">
            <strong className="text-danger">2. Cascading Microservice Outages</strong>
            <p>
              Upstream gateways and BFF (Backend-for-Frontend) aggregators throw unhandled HTTP 500/502 errors when downstream schemas silently drift.
            </p>
          </div>

          <div className="edu-pillar-item">
            <strong className="text-danger">3. Costly Consumer Downtime</strong>
            <p>
              Unlike backend bugfixes, third-party clients and mobile apps take days or weeks to roll out app store updates to patch broken endpoints.
            </p>
          </div>
        </div>
      </section>

      {/* Breaking Changes Listing */}
      <section className="breaking-content-section">
        <div className="section-title-row">
          <div>
            <h2 className="section-title">
              Detected Incompatibilities ({breakingChanges.length})
            </h2>
            <p className="section-subtitle">
              {report
                ? `Analyzing drift between ${report.oldFileName} (v${report.oldVersion}) and ${report.newFileName} (v${report.newVersion}).`
                : "No active comparison report loaded."}
            </p>
          </div>

          {breakingChanges.length > 0 && (
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={onDownloadPdf}
            >
              <DownloadIcon size={14} />
              <span>Export Audit PDF</span>
            </button>
          )}
        </div>

        {!report ? (
          <div className="app-card empty-state-box">
            <WorkbenchIcon size={32} className="text-muted" />
            <h3>No Comparison Data Available</h3>
            <p className="text-muted">
              Run an API comparison in the Workbench to detect breaking changes and schema drift.
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
        ) : breakingChanges.length === 0 ? (
          <div className="app-card empty-state-box">
            <div className="empty-icon-ring ring-success">
              <CheckCircleIcon size={32} />
            </div>
            <h3>Zero Breaking Changes Detected</h3>
            <p className="text-muted">
              The candidate specification is fully backward-compatible according to the AST comparison rules.
            </p>
          </div>
        ) : (
          <div className="breaking-groups-list">
            {endpointKeys.map((endpoint) => (
              <div key={endpoint} className="app-card endpoint-breaking-card">
                <div className="endpoint-header-row">
                  <div className="endpoint-info">
                    <span className="endpoint-label">AFFECTED LOCATION</span>
                    <code className="endpoint-title">{endpoint}</code>
                  </div>
                  <span className="endpoint-count-badge">
                    {groupedByEndpoint[endpoint].length} breaking issue
                    {groupedByEndpoint[endpoint].length > 1 ? "s" : ""}
                  </span>
                </div>

                <div className="endpoint-issues-list">
                  {groupedByEndpoint[endpoint].map((item, idx) => (
                    <article key={idx} className="breaking-issue-item">
                      <div className="issue-item-top">
                        <div className="issue-badge-group">
                          <SeverityBadge type="BREAKING" size="sm" />
                          <span className="risk-pill risk-high">HIGH RISK</span>
                        </div>
                        <strong className="issue-change-title">{item.title}</strong>
                      </div>

                      <p className="issue-details-text">{item.description}</p>

                      <div className="issue-rec-box">
                        <span className="rec-box-tag">REQUIRED REMEDIATION:</span>
                        <p>{item.recommendation}</p>
                      </div>

                      <div className="issue-footer-actions">
                        <button
                          type="button"
                          className="btn btn-ghost btn-xs text-cyan"
                          onClick={() => setSelectedFinding(item)}
                        >
                          Inspect AST Specification Details →
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Modal */}
      <FindingDetailModal
        finding={selectedFinding}
        isOpen={Boolean(selectedFinding)}
        onClose={() => setSelectedFinding(null)}
      />
    </div>
  );
}
