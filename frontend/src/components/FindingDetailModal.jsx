import { SeverityBadge } from "./SeverityBadge";
import { XIcon, AlertTriangleIcon, CheckCircleIcon } from "../utils/icons";

export function FindingDetailModal({ finding, isOpen, onClose }) {
  if (!isOpen || !finding) return null;

  const isBreaking = finding.type === "BREAKING";

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div
        className="modal-card modal-card-wide finding-drawer-card"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div className="finding-modal-title-group">
            <div className="finding-badge-row">
              <SeverityBadge type={finding.type} />
              <span className={`risk-pill risk-${(finding.risk || "low").toLowerCase()}`}>
                {finding.risk} RISK
              </span>
            </div>
            <h3 className="finding-modal-title">{finding.title}</h3>
          </div>
          <button
            type="button"
            className="icon-button modal-close-btn"
            onClick={onClose}
            aria-label="Close details"
          >
            <XIcon size={18} />
          </button>
        </div>

        <div className="modal-body finding-modal-body">
          <div className="detail-section">
            <label className="detail-label">AFFECTED LOCATION / ENDPOINT</label>
            <div className="code-block-highlight">
              <code>{finding.endpoint}</code>
            </div>
          </div>

          <div className="detail-section">
            <label className="detail-label">FINDING DETAILS & DRIFT OBSERVATION</label>
            <p className="detail-text-lead">{finding.description}</p>
          </div>

          <div className="detail-section">
            <label className="detail-label">RECOMMENDED REMEDIATION ACTION</label>
            <div className={`recommendation-box ${isBreaking ? "is-breaking-box" : ""}`}>
              <div className="rec-icon-wrap">
                {isBreaking ? <AlertTriangleIcon size={18} /> : <CheckCircleIcon size={18} />}
              </div>
              <div className="rec-text-wrap">
                <strong>Remediation Strategy:</strong>
                <p>{finding.recommendation}</p>
              </div>
            </div>
          </div>

          <div className="detail-section">
            <label className="detail-label">ENGINE SPECIFICATION CLASSIFICATION</label>
            <div className="spec-meta-grid">
              <div className="spec-meta-item">
                <span className="spec-meta-key">Detection Engine</span>
                <span className="spec-meta-val">FastAPI Deterministic AST Linter</span>
              </div>
              <div className="spec-meta-item">
                <span className="spec-meta-key">Specification Standard</span>
                <span className="spec-meta-val">OpenAPI 3.x Schema AST</span>
              </div>
              <div className="spec-meta-item">
                <span className="spec-meta-key">Production Impact</span>
                <span className="spec-meta-val">
                  {isBreaking
                    ? "Incompatible: Downstream consumers will fail deserialization or 404"
                    : "Non-breaking: Additive schema change; safe for resilient clients"}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
