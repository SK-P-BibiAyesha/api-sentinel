import {
  RiskIcon,
  ShieldIcon,
  WorkbenchIcon,
} from "../utils/icons";

export function RiskInsightsPage({ report, setActivePage }) {
  const findings = report?.changes || [];
  const totalFindings = findings.length;
  const infoCount = findings.filter((f) => f.type === "INFO").length;

  const highRiskCount = findings.filter((f) => f.risk === "HIGH").length;
  const medRiskCount = findings.filter((f) => f.risk === "MEDIUM").length;
  const lowRiskCount = findings.filter((f) => f.risk === "LOW").length;

  // Breakdown by change titles / categories
  const categoriesMap = findings.reduce((acc, f) => {
    const key = f.title || "Schema Change";
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});

  const categories = Object.entries(categoriesMap).sort((a, b) => b[1] - a[1]);

  return (
    <div className="page-container risk-insights-page">
      {/* Engine Architecture Callout */}
      <section className="app-card risk-architecture-card">
        <div className="card-header">
          <div className="header-icon-title">
            <span className="card-icon-tag">
              <ShieldIcon size={20} />
            </span>
            <div>
              <span className="card-eyebrow">COMPLIANCE METHODOLOGY</span>
              <h2 className="card-title">Deterministic AST Rule Engine</h2>
            </div>
          </div>
          <span className="engine-badge-pill">Deterministic Linter (Non-Heuristic)</span>
        </div>

        <p className="arch-card-text">
          Unlike probabilistic or generative AI tools that hallucinate schema diffs, API Sentinel employs a <strong>100% deterministic Abstract Syntax Tree (AST) comparison engine</strong>. Every finding is mathematically verified against the OpenAPI 3.x schema definition.
        </p>

        <div className="arch-rules-grid">
          <div className="arch-rule-box">
            <strong>Endpoint Parity Rule</strong>
            <p>Verifies all URI path items exist across specification revisions.</p>
          </div>
          <div className="arch-rule-box">
            <strong>HTTP Method Integrity</strong>
            <p>Guarantees existing verbs (GET, POST, PUT, DELETE) are not dropped.</p>
          </div>
          <div className="arch-rule-box">
            <strong>Response Field Completeness</strong>
            <p>Detects removed properties from 200 OK application/json response schemas.</p>
          </div>
          <div className="arch-rule-box">
            <strong>Type Coercion & Safety</strong>
            <p>Detects type mutation between string, integer, number, boolean, and object.</p>
          </div>
        </div>
      </section>

      {!report ? (
        <section className="app-card empty-state-box">
          <RiskIcon size={32} className="text-muted" />
          <h3>No Analysis Loaded</h3>
          <p className="text-muted">
            Run an API comparison in the Workbench to generate risk metrics and distribution charts.
          </p>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setActivePage("workbench")}
          >
            <WorkbenchIcon size={16} />
            <span>Open API Workbench</span>
          </button>
        </section>
      ) : (
        <>
          {/* Risk Severity Breakdown Cards */}
          <section className="risk-metrics-row">
            <div className="risk-metric-card risk-metric-high">
              <span className="rm-label">HIGH PRODUCTION RISK</span>
              <strong className="rm-val">{highRiskCount}</strong>
              <p className="rm-desc">Immediate consumer disruption if deployed.</p>
            </div>

            <div className="risk-metric-card risk-metric-med">
              <span className="rm-label">MEDIUM RISK (WARNINGS)</span>
              <strong className="rm-val">{medRiskCount}</strong>
              <p className="rm-desc">Potential compatibility friction or deprecation.</p>
            </div>

            <div className="risk-metric-card risk-metric-low">
              <span className="rm-label">LOW RISK (ADDITIVE)</span>
              <strong className="rm-val">{lowRiskCount}</strong>
              <p className="rm-desc">Safe schema additions; backwards-compatible.</p>
            </div>
          </section>

          {/* Detailed Severity Distribution & Change Categories */}
          <section className="risk-split-grid">
            {/* Left: Change Category Breakdown */}
            <article className="app-card">
              <div className="card-header">
                <div>
                  <span className="card-eyebrow">CHANGE CLASSIFICATION</span>
                  <h3 className="card-title">Findings by Category</h3>
                </div>
              </div>

              <div className="category-list">
                {categories.length === 0 ? (
                  <p className="text-muted">No schema changes recorded.</p>
                ) : (
                  categories.map(([category, count]) => {
                    const pct = totalFindings ? Math.round((count / totalFindings) * 100) : 0;
                    return (
                      <div key={category} className="category-row">
                        <div className="cat-row-header">
                          <span className="cat-name">{category}</span>
                          <span className="cat-count-badge">
                            {count} ({pct}%)
                          </span>
                        </div>
                        <div className="cat-progress-track">
                          <div
                            className="cat-progress-bar"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </article>

            {/* Right: Manual Review Guidance */}
            <article className="app-card">
              <div className="card-header">
                <div>
                  <span className="card-eyebrow">TRIAGE PROTOCOL</span>
                  <h3 className="card-title">Manual Review Guidance</h3>
                </div>
              </div>

              <div className="manual-review-content">
                <div className="review-step-item">
                  <div className="step-num-badge">1</div>
                  <div className="step-text">
                    <strong>Triage High-Risk Violations</strong>
                    <p>
                      Address all {highRiskCount} HIGH RISK items first. Verify whether consumer client applications or mobile frontends depend on the altered fields.
                    </p>
                  </div>
                </div>

                <div className="review-step-item">
                  <div className="step-num-badge">2</div>
                  <div className="step-text">
                    <strong>Review Version Numbering Strategy</strong>
                    <p>
                      Under Semantic Versioning (SemVer), any breaking response modification or removed route requires bumping the <strong>MAJOR</strong> version (e.g., v1.0.0 → v2.0.0).
                    </p>
                  </div>
                </div>

                <div className="review-step-item">
                  <div className="step-num-badge">3</div>
                  <div className="step-text">
                    <strong>Validate Client Tolerance</strong>
                    <p>
                      Ensure consumers implement permissive JSON parsing so newly added fields ({infoCount} detected) do not cause validation exceptions.
                    </p>
                  </div>
                </div>
              </div>
            </article>
          </section>
        </>
      )}
    </div>
  );
}
