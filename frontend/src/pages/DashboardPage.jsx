import { StatCard } from "../components/StatCard";
import { SeverityBadge } from "../components/SeverityBadge";
import {
  WorkbenchIcon,
  BreakingIcon,
  AlertTriangleIcon,
  CheckCircleIcon,
  DownloadIcon,
  FileTextIcon,
  ArrowRightIcon,
  HistoryIcon,
  ShieldIcon,
  PulseIcon,
} from "../utils/icons";

export function DashboardPage({
  report,
  setActivePage,
  history = [],
  backendConnected,
  onDownloadPdf,
  onDownloadJson,
  onLoadHistoryItem,
}) {
  const hasReport = Boolean(report);

  // Compute severity breakdown strictly from real findings
  const findings = report?.changes || [];
  const totalFindings = findings.length;
  const breakingCount = findings.filter((f) => f.type === "BREAKING").length;
  const warningCount = findings.filter((f) => f.type === "WARNING").length;
  const infoCount = findings.filter((f) => f.type === "INFO").length;

  const breakingPct = totalFindings ? Math.round((breakingCount / totalFindings) * 100) : 0;
  const warningPct = totalFindings ? Math.round((warningCount / totalFindings) * 100) : 0;
  const infoPct = totalFindings ? Math.round((infoCount / totalFindings) * 100) : 0;

  return (
    <div className="page-container dashboard-page">
      {/* Top Hero / Welcome Banner */}
      <section className="dash-hero-card">
        <div className="dash-hero-content">
          <div className="dash-hero-badge">
            <span className="hero-badge-dot" />
            <span>AUTOMATED MICROSERVICE API DRIFT DETECTOR</span>
          </div>
          <h1 className="dash-hero-title">
            Detect breaking API changes <br />
            <span className="text-gradient">before they break production.</span>
          </h1>
          <p className="dash-hero-desc">
            API Sentinel performs deterministic Abstract Syntax Tree (AST) comparison across OpenAPI 3.x specifications to catch deleted endpoints, modified response fields, and breaking type drift before deployment.
          </p>

          <div className="dash-hero-actions">
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => setActivePage("workbench")}
            >
              <WorkbenchIcon size={18} />
              <span>Launch API Workbench</span>
              <ArrowRightIcon size={16} />
            </button>

            {hasReport && (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setActivePage("breaking")}
              >
                <BreakingIcon size={18} />
                <span>View {breakingCount} Breaking Changes</span>
              </button>
            )}
          </div>
        </div>

        <div className="dash-hero-stats-badge">
          <div className="hero-pulse-shield">
            <ShieldIcon size={38} className="shield-svg" />
            <PulseIcon size={24} className="pulse-svg" />
          </div>
          <div className="hero-status-pill">
            <span className={`pill-dot ${backendConnected ? "dot-online" : "dot-offline"}`} />
            <span>{backendConnected ? "FastAPI Engine Active" : "Backend Offline"}</span>
          </div>
          <span className="hero-subtext">OpenAPI 3.x Linter</span>
        </div>
      </section>

      {/* Summary Stat Cards */}
      <section className="stats-grid-row">
        <StatCard
          title="Total Changes Detected"
          value={hasReport ? report.summary.totalChanges : "—"}
          subtitle={hasReport ? "AST schema differences" : "Run comparison to analyze"}
          icon={FileTextIcon}
          variant="default"
        />

        <StatCard
          title="Breaking Changes"
          value={hasReport ? report.summary.breakingChanges : "—"}
          subtitle={
            hasReport
              ? breakingCount > 0
                ? "Immediate client risk detected"
                : "Zero breaking changes"
              : "No comparison data yet"
          }
          icon={BreakingIcon}
          variant={hasReport && breakingCount > 0 ? "danger" : "default"}
          badge={
            hasReport && breakingCount > 0 ? (
              <SeverityBadge type="BREAKING" size="sm" />
            ) : null
          }
        />

        <StatCard
          title="Warnings & Deprecations"
          value={hasReport ? report.summary.warnings : "—"}
          subtitle={hasReport ? "Potential drift notices" : "No comparison data yet"}
          icon={AlertTriangleIcon}
          variant={hasReport && warningCount > 0 ? "warning" : "default"}
        />

        <StatCard
          title="Overall Compatibility Result"
          value={hasReport ? report.result : "—"}
          subtitle={
            hasReport
              ? report.result === "PASS"
                ? "Safe for production consumers"
                : "Requires migration or fixes"
              : "Awaiting API upload"
          }
          icon={hasReport && report.result === "PASS" ? CheckCircleIcon : AlertTriangleIcon}
          variant={
            hasReport
              ? report.result === "PASS"
                ? "success"
                : "danger"
              : "default"
          }
          badge={
            hasReport ? (
              <SeverityBadge type={report.result} size="md" />
            ) : null
          }
        />
      </section>

      {/* Main Grid: Latest Analysis Panel & Visual Compatibility Distribution */}
      <section className="dash-two-col-grid">
        {/* Latest Analysis Panel */}
        <article className="app-card latest-analysis-card">
          <div className="card-header">
            <div>
              <span className="card-eyebrow">LATEST AUDIT EXECUTION</span>
              <h2 className="card-title">Latest Analysis Summary</h2>
            </div>
            {hasReport && <SeverityBadge type={report.result} size="md" />}
          </div>

          {hasReport ? (
            <div className="latest-analysis-body">
              <div className="analysis-versions-banner">
                <div className="version-pill-group">
                  <span className="ver-label">BASE SPEC:</span>
                  <span className="ver-badge">v{report.oldVersion}</span>
                  <span className="ver-filename" title={report.oldFileName}>
                    {report.oldFileName}
                  </span>
                </div>

                <span className="ver-arrow">→</span>

                <div className="version-pill-group">
                  <span className="ver-label">TARGET SPEC:</span>
                  <span className="ver-badge">v{report.newVersion}</span>
                  <span className="ver-filename" title={report.newFileName}>
                    {report.newFileName}
                  </span>
                </div>
              </div>

              <div className="analysis-meta-summary">
                <div className="meta-row">
                  <span className="meta-key">Total Schema Changes:</span>
                  <strong className="meta-val">{report.summary.totalChanges}</strong>
                </div>
                <div className="meta-row">
                  <span className="meta-key">Breaking Incompatibilities:</span>
                  <strong className="meta-val text-danger">
                    {report.summary.breakingChanges}
                  </strong>
                </div>
                <div className="meta-row">
                  <span className="meta-key">Warning Notifications:</span>
                  <strong className="meta-val text-warning">
                    {report.summary.warnings}
                  </strong>
                </div>
                <div className="meta-row">
                  <span className="meta-key">Evaluated At:</span>
                  <span className="meta-val text-muted">
                    {new Date(report.generatedAt).toLocaleString()}
                  </span>
                </div>
              </div>

              <div className="analysis-card-footer">
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => setActivePage("workbench")}
                >
                  <span>Open Full Findings Table</span>
                  <ArrowRightIcon size={14} />
                </button>

                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={onDownloadPdf}
                >
                  <DownloadIcon size={14} />
                  <span>Download Audit PDF</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="empty-state-box">
              <div className="empty-icon-ring">
                <WorkbenchIcon size={32} />
              </div>
              <h3>No Analysis Run Yet</h3>
              <p>
                Upload your baseline and candidate OpenAPI 3.x specifications in the Workbench to evaluate schema drift, deleted endpoints, and breaking changes.
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
          )}
        </article>

        {/* Compatibility Overview & Severity Distribution */}
        <article className="app-card severity-distribution-card">
          <div className="card-header">
            <div>
              <span className="card-eyebrow">RISK TELEMETRY</span>
              <h2 className="card-title">Compatibility Overview</h2>
            </div>
            <span className="info-badge-tag">Deterministic Linter</span>
          </div>

          {hasReport && totalFindings > 0 ? (
            <div className="distribution-body">
              <p className="distribution-lead">
                Distribution of detected changes categorized by backward-compatibility risk level:
              </p>

              {/* Visual Multi-Segment Bar */}
              <div className="distribution-stacked-bar">
                {breakingPct > 0 && (
                  <div
                    className="bar-segment seg-breaking"
                    style={{ width: `${breakingPct}%` }}
                    title={`Breaking: ${breakingCount} (${breakingPct}%)`}
                  />
                )}
                {warningPct > 0 && (
                  <div
                    className="bar-segment seg-warning"
                    style={{ width: `${warningPct}%` }}
                    title={`Warnings: ${warningCount} (${warningPct}%)`}
                  />
                )}
                {infoPct > 0 && (
                  <div
                    className="bar-segment seg-info"
                    style={{ width: `${infoPct}%` }}
                    title={`Informational: ${infoCount} (${infoPct}%)`}
                  />
                )}
              </div>

              {/* Legend & Breakdown Rows */}
              <div className="distribution-list">
                <div className="distribution-row">
                  <div className="dist-row-left">
                    <span className="dist-color-dot dot-breaking" />
                    <span className="dist-name">Breaking Changes</span>
                    <span className="dist-desc">(Deletions, Type Mismatches)</span>
                  </div>
                  <div className="dist-row-right">
                    <strong className="dist-count text-danger">{breakingCount}</strong>
                    <span className="dist-pct">({breakingPct}%)</span>
                  </div>
                </div>

                <div className="distribution-row">
                  <div className="dist-row-left">
                    <span className="dist-color-dot dot-warning" />
                    <span className="dist-name">Warnings & Deprecations</span>
                    <span className="dist-desc">(Deprecations, Status)</span>
                  </div>
                  <div className="dist-row-right">
                    <strong className="dist-count text-warning">{warningCount}</strong>
                    <span className="dist-pct">({warningPct}%)</span>
                  </div>
                </div>

                <div className="distribution-row">
                  <div className="dist-row-left">
                    <span className="dist-color-dot dot-info" />
                    <span className="dist-name">Informational Additions</span>
                    <span className="dist-desc">(New Endpoints, Fields)</span>
                  </div>
                  <div className="dist-row-right">
                    <strong className="dist-count text-cyan">{infoCount}</strong>
                    <span className="dist-pct">({infoPct}%)</span>
                  </div>
                </div>
              </div>

              <div className="compatibility-verdict-box">
                <div className="verdict-icon">
                  {report.result === "PASS" ? (
                    <CheckCircleIcon size={20} />
                  ) : (
                    <AlertTriangleIcon size={20} />
                  )}
                </div>
                <div className="verdict-text">
                  <strong>
                    {report.result === "PASS"
                      ? "Backward Compatibility Verified"
                      : "Breaking Changes Prevent Safe Merge"}
                  </strong>
                  <p>
                    {report.result === "PASS"
                      ? "No breaking schema differences were detected. Existing API consumers can safely interact with the new specification."
                      : "Breaking changes were detected. Review the affected endpoints and update consumer SDKs or migration paths before release."}
                  </p>
                </div>
              </div>
            </div>
          ) : hasReport ? (
            <div className="empty-state-box">
              <div className="empty-icon-ring ring-success">
                <CheckCircleIcon size={32} />
              </div>
              <h3>100% Backward Compatible</h3>
              <p>Zero changes or drift detected between the provided specifications.</p>
            </div>
          ) : (
            <div className="empty-state-box">
              <p className="text-muted">
                Run a comparison to generate the risk breakdown and compatibility telemetry.
              </p>
            </div>
          )}
        </article>
      </section>

      {/* Quick Actions & Recent Runs */}
      <section className="dash-bottom-grid">
        {/* Quick Actions Panel */}
        <article className="app-card">
          <div className="card-header">
            <div>
              <span className="card-eyebrow">WORKFLOW CONTROLS</span>
              <h2 className="card-title">Quick Actions</h2>
            </div>
          </div>

          <div className="quick-actions-grid">
            <button
              type="button"
              className="quick-action-card"
              onClick={() => setActivePage("workbench")}
            >
              <div className="qa-icon-wrap qa-cyan">
                <WorkbenchIcon size={20} />
              </div>
              <div className="qa-text">
                <strong>Compare API Versions</strong>
                <p>Upload OpenAPI JSON or YAML specs to run AST comparison.</p>
              </div>
              <ArrowRightIcon size={16} className="qa-arrow" />
            </button>

            <button
              type="button"
              className={`quick-action-card ${!hasReport ? "is-disabled" : ""}`}
              onClick={() => hasReport && setActivePage("breaking")}
              disabled={!hasReport}
            >
              <div className="qa-icon-wrap qa-red">
                <BreakingIcon size={20} />
              </div>
              <div className="qa-text">
                <strong>Inspect Breaking Changes</strong>
                <p>
                  {hasReport
                    ? `Review ${breakingCount} high-risk schema violations.`
                    : "Available after executing an API comparison."}
                </p>
              </div>
              <ArrowRightIcon size={16} className="qa-arrow" />
            </button>

            <button
              type="button"
              className={`quick-action-card ${!hasReport ? "is-disabled" : ""}`}
              onClick={onDownloadPdf}
              disabled={!hasReport}
            >
              <div className="qa-icon-wrap qa-indigo">
                <DownloadIcon size={20} />
              </div>
              <div className="qa-text">
                <strong>Download Audit PDF</strong>
                <p>
                  {hasReport
                    ? "Generate formal compliance report via jsPDF."
                    : "Run comparison to generate exportable PDF."}
                </p>
              </div>
              <ArrowRightIcon size={16} className="qa-arrow" />
            </button>

            <button
              type="button"
              className={`quick-action-card ${!hasReport ? "is-disabled" : ""}`}
              onClick={onDownloadJson}
              disabled={!hasReport}
            >
              <div className="qa-icon-wrap qa-emerald">
                <FileTextIcon size={20} />
              </div>
              <div className="qa-text">
                <strong>Export Raw JSON</strong>
                <p>
                  {hasReport
                    ? "Export structured findings payload for CI/CD."
                    : "Run comparison to export JSON results."}
                </p>
              </div>
              <ArrowRightIcon size={16} className="qa-arrow" />
            </button>
          </div>
        </article>

        {/* Recent Analysis History Snippet */}
        <article className="app-card">
          <div className="card-header">
            <div>
              <span className="card-eyebrow">AUDIT TRAIL</span>
              <h2 className="card-title">Recent History</h2>
            </div>
            {history.length > 0 && (
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => setActivePage("history")}
              >
                <span>View All ({history.length})</span>
                <ArrowRightIcon size={14} />
              </button>
            )}
          </div>

          {history.length > 0 ? (
            <div className="history-preview-list">
              {history.slice(0, 3).map((item) => (
                <div key={item.id} className="history-preview-item">
                  <div className="hist-prev-top">
                    <span className="hist-prev-files">
                      {item.oldFileName} <span className="text-muted">vs</span> {item.newFileName}
                    </span>
                    <SeverityBadge type={item.result} size="sm" />
                  </div>

                  <div className="hist-prev-meta">
                    <span className="hist-prev-ver">
                      v{item.oldVersion} → v{item.newVersion}
                    </span>
                    <span className="hist-prev-breaking text-danger">
                      {item.breakingChanges} breaking
                    </span>
                    <span className="hist-prev-time">
                      {new Date(item.timestamp).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>

                  {item.fullReport && (
                    <button
                      type="button"
                      className="btn btn-ghost btn-xs hist-load-btn"
                      onClick={() => onLoadHistoryItem(item)}
                    >
                      Restore This Run →
                    </button>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state-box compact-empty">
              <HistoryIcon size={24} className="text-muted" />
              <p className="text-muted">No comparison history saved yet.</p>
              <span className="text-xs text-muted">
                Completed analyses will be preserved in browser storage.
              </span>
            </div>
          )}
        </article>
      </section>
    </div>
  );
}
