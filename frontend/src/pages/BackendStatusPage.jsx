import { SeverityBadge } from "../components/SeverityBadge";
import {
  BackendIcon,
  RefreshIcon,
  AlertTriangleIcon,
  ExternalLinkIcon,
} from "../utils/icons";

export function BackendStatusPage({
  apiBaseUrl,
  backendConnected,
  checkingBackend,
  backendHealthData,
  backendRootData,
  lastCheckedTime,
  pingLatency,
  backendError,
  onCheckBackend,
}) {
  return (
    <div className="page-container backend-status-page">
      {/* Top Hero Card */}
      <section className="app-card backend-hero-card">
        <div className="card-header">
          <div className="header-icon-title">
            <span className="card-icon-tag tag-cyan">
              <BackendIcon size={20} />
            </span>
            <div>
              <span className="card-eyebrow">FASTAPI SERVICE TELEMETRY</span>
              <h2 className="card-title">Backend Status & Health Diagnostics</h2>
            </div>
          </div>

          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={onCheckBackend}
            disabled={checkingBackend}
          >
            <span className={checkingBackend ? "is-spinning" : ""}>
              <RefreshIcon size={14} />
            </span>
            <span>{checkingBackend ? "Testing Connection..." : "Check Connection"}</span>
          </button>
        </div>

        <p className="backend-intro">
          Real-time connection monitoring for the local API Sentinel FastAPI comparison service running at <code>{apiBaseUrl}</code>.
        </p>

        {/* Live Diagnostics Card */}
        <div className="diagnostics-status-grid">
          <div className="diag-item">
            <span className="diag-label">CONNECTION STATE</span>
            <div className="diag-state-row">
              <span
                className={`live-indicator-dot ${
                  backendConnected ? "is-online" : "is-offline"
                }`}
              />
              <strong className={backendConnected ? "text-success" : "text-danger"}>
                {checkingBackend
                  ? "Probing..."
                  : backendConnected
                  ? "Connected & Operational"
                  : "Disconnected / Unreachable"}
              </strong>
            </div>
          </div>

          <div className="diag-item">
            <span className="diag-label">SERVICE HEALTH PROBE</span>
            <div className="diag-val-row">
              <SeverityBadge
                type={backendConnected ? "HEALTHY" : "FAIL"}
                size="sm"
                label={backendHealthData?.status || (backendConnected ? "healthy" : "offline")}
              />
            </div>
          </div>

          <div className="diag-item">
            <span className="diag-label">MEASURED LATENCY</span>
            <div className="diag-val-row">
              <strong className="text-cyan">
                {pingLatency !== null ? `${pingLatency} ms` : "—"}
              </strong>
              <span className="text-muted text-xs">round-trip</span>
            </div>
          </div>

          <div className="diag-item">
            <span className="diag-label">LAST PROBED</span>
            <div className="diag-val-row">
              <span className="text-muted text-sm">
                {lastCheckedTime
                  ? new Date(lastCheckedTime).toLocaleTimeString()
                  : "Not checked yet"}
              </span>
            </div>
          </div>
        </div>

        {backendError && (
          <div className="alert-box alert-danger mt-4" role="alert">
            <AlertTriangleIcon size={18} />
            <div className="alert-content">
              <strong>Connection Error</strong>
              <p>{backendError}</p>
              <span className="text-xs text-muted">
                Ensure the FastAPI backend process is started via <code>python -m uvicorn backend.api:app --reload</code> or your configured backend runner.
              </span>
            </div>
          </div>
        )}
      </section>

      {/* Raw Backend Probe Responses */}
      <section className="backend-probes-grid">
        <article className="app-card">
          <div className="card-header">
            <div>
              <span className="card-eyebrow">HTTP PROBE 1</span>
              <h3 className="card-title">GET /health</h3>
            </div>
            <span className="badge-neutral font-mono text-xs">Probe</span>
          </div>

          <div className="code-block-wrap">
            <pre className="code-pre">
              {JSON.stringify(backendHealthData || { status: backendConnected ? "healthy" : "error" }, null, 2)}
            </pre>
          </div>
          <span className="text-xs text-muted">
            Returns JSON health status verification probe for load balancers.
          </span>
        </article>

        <article className="app-card">
          <div className="card-header">
            <div>
              <span className="card-eyebrow">HTTP PROBE 2</span>
              <h3 className="card-title">GET /</h3>
            </div>
            <span className="badge-neutral font-mono text-xs">Metadata</span>
          </div>

          <div className="code-block-wrap">
            <pre className="code-pre">
              {JSON.stringify(backendRootData || { message: "API Sentinel is running", docs: "/docs" }, null, 2)}
            </pre>
          </div>
          <span className="text-xs text-muted">
            Returns service identification banner and Swagger documentation path.
          </span>
        </article>
      </section>

      {/* Contract & Endpoints Documentation */}
      <section className="app-card backend-endpoints-card">
        <div className="card-header">
          <div>
            <span className="card-eyebrow">BACKEND CONTRACT CATALOG</span>
            <h3 className="card-title">Configured Endpoints</h3>
          </div>
          <a
            href={`${apiBaseUrl}/docs`}
            target="_blank"
            rel="noreferrer"
            className="btn btn-ghost btn-xs text-cyan"
          >
            <span>Open FastAPI Swagger UI</span>
            <ExternalLinkIcon size={13} />
          </a>
        </div>

        <div className="table-responsive">
          <table className="endpoints-table">
            <thead>
              <tr>
                <th style={{ width: "12%" }}>Method</th>
                <th style={{ width: "24%" }}>Route</th>
                <th style={{ width: "26%" }}>Request Payload</th>
                <th style={{ width: "38%" }}>Purpose & Response</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>
                  <span className="http-badge http-get">GET</span>
                </td>
                <td>
                  <code>/</code>
                </td>
                <td className="text-muted text-xs">None</td>
                <td>Root status message and Swagger documentation pointer.</td>
              </tr>
              <tr>
                <td>
                  <span className="http-badge http-get">GET</span>
                </td>
                <td>
                  <code>/health</code>
                </td>
                <td className="text-muted text-xs">None</td>
                <td>Health check probe returning <code>{`{"status": "healthy"}`}</code>.</td>
              </tr>
              <tr>
                <td>
                  <span className="http-badge http-post">POST</span>
                </td>
                <td>
                  <code>/compare</code>
                </td>
                <td>
                  <span className="font-mono text-xs">
                    multipart/form-data: <code>old_file</code>, <code>new_file</code>
                  </span>
                </td>
                <td>
                  Executes deterministic OpenAPI comparison. Returns <code>old_version</code>, <code>new_version</code>, <code>total_changes</code>, <code>breaking_changes</code>, <code>result</code>, and <code>findings[]</code>.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
