import { useState, useRef } from "react";
import { SeverityBadge } from "../components/SeverityBadge";
import { FindingDetailModal } from "../components/FindingDetailModal";
import { createSampleFiles } from "../utils/samples";
import {
  UploadCloudIcon,
  FileTextIcon,
  XIcon,
  WorkbenchIcon,
  AlertTriangleIcon,
  CheckCircleIcon,
  DownloadIcon,
  SearchIcon,
  SparklesIcon,
  ArrowRightIcon,
} from "../utils/icons";

export function WorkbenchPage({
  oldFile,
  newFile,
  setOldFile,
  setNewFile,
  loading,
  error,
  report,
  onCompare,
  onReset,
  onDownloadPdf,
  onDownloadJson,
  showToast,
}) {
  const [dragOverOld, setDragOverOld] = useState(false);
  const [dragOverNew, setDragOverNew] = useState(false);
  const [selectedFinding, setSelectedFinding] = useState(null);

  // Filters for results section
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  const oldInputRef = useRef(null);
  const newInputRef = useRef(null);

  function formatFileSize(bytes) {
    if (!bytes && bytes !== 0) return "";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  }

  function validateAndSetFile(file, type) {
    if (!file) return;

    const isJson = /\.json$/i.test(file.name);
    const isYaml = /\.(yaml|yml)$/i.test(file.name);

    if (!isJson && !isYaml) {
      if (showToast) {
        showToast("error", "Unsupported file. Please upload an OpenAPI JSON or YAML file (.json, .yaml, .yml).");
      }
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      if (showToast) {
        showToast("error", "File exceeds 2 MB backend limit.");
      }
      return;
    }

    if (type === "old") {
      setOldFile(file);
    } else {
      setNewFile(file);
    }

    if (showToast) {
      showToast("success", `Loaded ${file.name} (${formatFileSize(file.size)})`);
    }
  }

  function handleFileChange(event, type) {
    const file = event.target.files?.[0];
    if (file) {
      validateAndSetFile(file, type);
    }
  }

  function handleDrop(event, type) {
    event.preventDefault();
    if (type === "old") setDragOverOld(false);
    else setDragOverNew(false);

    const file = event.dataTransfer.files?.[0];
    if (file) {
      validateAndSetFile(file, type);
    }
  }

  function handleDragOver(event, type) {
    event.preventDefault();
    if (type === "old") setDragOverOld(true);
    else setDragOverNew(true);
  }

  function handleDragLeave(event, type) {
    event.preventDefault();
    if (type === "old") setDragOverOld(false);
    else setDragOverNew(false);
  }

  function handleLoadSample(type) {
    const { oldFile: sampleOld, newFile: sampleNew, label } = createSampleFiles(type);
    setOldFile(sampleOld);
    setNewFile(sampleNew);
    if (showToast) {
      showToast("success", `Loaded demo specification pair: ${label}`);
    }
  }

  // Filter findings
  const findings = report?.changes || [];
  const filteredFindings = findings.filter((item) => {
    const matchesSev =
      severityFilter === "ALL" ||
      String(item.type).toUpperCase() === severityFilter;

    const q = searchQuery.toLowerCase().trim();
    const matchesSearch =
      !q ||
      item.title?.toLowerCase().includes(q) ||
      item.endpoint?.toLowerCase().includes(q) ||
      item.description?.toLowerCase().includes(q);

    return matchesSev && matchesSearch;
  });

  const breakingCount = findings.filter((f) => f.type === "BREAKING").length;
  const warningCount = findings.filter((f) => f.type === "WARNING").length;
  const infoCount = findings.filter((f) => f.type === "INFO").length;

  return (
    <div className="page-container workbench-page">
      {/* Workbench Header & Quick Samples Bar */}
      <section className="workbench-top-bar">
        <div>
          <h1 className="page-heading">API Comparison Workbench</h1>
          <p className="page-subheading">
            Upload two OpenAPI 3.x specifications to detect breaking changes, removed endpoints, deleted fields, and type mutations.
          </p>
        </div>

        <div className="demo-samples-widget">
          <span className="demo-widget-label">
            <SparklesIcon size={14} />
            <span>Load Demo Specs:</span>
          </span>
          <button
            type="button"
            className="btn btn-ghost btn-xs demo-spec-btn"
            onClick={() => handleLoadSample("contacts")}
            title="Load sample Contacts API (JSON with 3 breaking changes)"
          >
            Contacts API (JSON)
          </button>
          <button
            type="button"
            className="btn btn-ghost btn-xs demo-spec-btn"
            onClick={() => handleLoadSample("products")}
            title="Load sample Products API (YAML with 4 breaking changes)"
          >
            Product Catalog (YAML)
          </button>
        </div>
      </section>

      {/* Two Side-By-Side Upload Panels */}
      <section className="workbench-upload-container">
        <div className="upload-panels-grid">
          {/* Left Panel: OLD API SPECIFICATION */}
          <div
            className={`upload-dropzone ${dragOverOld ? "is-drag-over" : ""} ${
              oldFile ? "has-file" : ""
            }`}
            onDragOver={(e) => handleDragOver(e, "old")}
            onDragLeave={(e) => handleDragLeave(e, "old")}
            onDrop={(e) => handleDrop(e, "old")}
          >
            <div className="dropzone-header">
              <span className="panel-tag tag-old">BASELINE SPECIFICATION</span>
              <span className="step-indicator">01</span>
            </div>

            <div className="dropzone-content">
              {oldFile ? (
                <div className="file-preview-box">
                  <div className="file-icon-badge">
                    <FileTextIcon size={26} />
                  </div>
                  <div className="file-info-text">
                    <strong className="file-info-name" title={oldFile.name}>
                      {oldFile.name}
                    </strong>
                    <span className="file-info-meta">
                      {formatFileSize(oldFile.size)} · OpenAPI Specification
                    </span>
                  </div>

                  <div className="file-actions-row">
                    <button
                      type="button"
                      className="btn btn-ghost btn-xs"
                      onClick={() => oldInputRef.current?.click()}
                    >
                      Replace File
                    </button>
                    <button
                      type="button"
                      className="btn btn-ghost btn-xs text-danger"
                      onClick={() => setOldFile(null)}
                      title="Remove file"
                    >
                      <XIcon size={14} />
                      <span>Remove</span>
                    </button>
                  </div>
                </div>
              ) : (
                <div className="dropzone-empty-state">
                  <div className="upload-icon-circle">
                    <UploadCloudIcon size={32} />
                  </div>
                  <h3>OLD API SPECIFICATION</h3>
                  <p className="dropzone-help">
                    Drag and drop your base OpenAPI file here, or browse from disk.
                  </p>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => oldInputRef.current?.click()}
                  >
                    Browse Files
                  </button>
                  <span className="dropzone-formats">
                    Supports .json, .yaml, .yml (max 2 MB)
                  </span>
                </div>
              )}
            </div>

            <input
              ref={oldInputRef}
              type="file"
              className="hidden-file-input"
              accept=".json,.yaml,.yml,application/json,application/x-yaml,text/yaml"
              onChange={(e) => handleFileChange(e, "old")}
            />
          </div>

          {/* Center Visual Comparison Indicator */}
          <div className="upload-divider-col">
            <div className="vs-badge-glow">
              <span className="vs-text">VS</span>
            </div>
            <div className="vs-line" />
          </div>

          {/* Right Panel: NEW API SPECIFICATION */}
          <div
            className={`upload-dropzone ${dragOverNew ? "is-drag-over" : ""} ${
              newFile ? "has-file" : ""
            }`}
            onDragOver={(e) => handleDragOver(e, "new")}
            onDragLeave={(e) => handleDragLeave(e, "new")}
            onDrop={(e) => handleDrop(e, "new")}
          >
            <div className="dropzone-header">
              <span className="panel-tag tag-new">UPDATED SPECIFICATION</span>
              <span className="step-indicator">02</span>
            </div>

            <div className="dropzone-content">
              {newFile ? (
                <div className="file-preview-box">
                  <div className="file-icon-badge badge-new">
                    <FileTextIcon size={26} />
                  </div>
                  <div className="file-info-text">
                    <strong className="file-info-name" title={newFile.name}>
                      {newFile.name}
                    </strong>
                    <span className="file-info-meta">
                      {formatFileSize(newFile.size)} · OpenAPI Specification
                    </span>
                  </div>

                  <div className="file-actions-row">
                    <button
                      type="button"
                      className="btn btn-ghost btn-xs"
                      onClick={() => newInputRef.current?.click()}
                    >
                      Replace File
                    </button>
                    <button
                      type="button"
                      className="btn btn-ghost btn-xs text-danger"
                      onClick={() => setNewFile(null)}
                      title="Remove file"
                    >
                      <XIcon size={14} />
                      <span>Remove</span>
                    </button>
                  </div>
                </div>
              ) : (
                <div className="dropzone-empty-state">
                  <div className="upload-icon-circle circle-cyan">
                    <UploadCloudIcon size={32} />
                  </div>
                  <h3>NEW API SPECIFICATION</h3>
                  <p className="dropzone-help">
                    Drag and drop your candidate OpenAPI file here, or browse from disk.
                  </p>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => newInputRef.current?.click()}
                  >
                    Browse Files
                  </button>
                  <span className="dropzone-formats">
                    Supports .json, .yaml, .yml (max 2 MB)
                  </span>
                </div>
              )}
            </div>

            <input
              ref={newInputRef}
              type="file"
              className="hidden-file-input"
              accept=".json,.yaml,.yml,application/json,application/x-yaml,text/yaml"
              onChange={(e) => handleFileChange(e, "new")}
            />
          </div>
        </div>

        {/* Error Alert if any */}
        {error && (
          <div className="alert-box alert-danger" role="alert">
            <AlertTriangleIcon size={18} />
            <div className="alert-content">
              <strong>Comparison Engine Error</strong>
              <p>{error}</p>
            </div>
          </div>
        )}

        {/* Action Controls & Guidance */}
        <div className="workbench-actions-bar">
          <div className="actions-left">
            <button
              type="button"
              className="btn btn-primary btn-lg analyze-btn"
              onClick={onCompare}
              disabled={loading || !oldFile || !newFile}
            >
              {loading ? (
                <>
                  <span className="spinner-inline" />
                  <span>Analyzing AST Differences...</span>
                </>
              ) : (
                <>
                  <WorkbenchIcon size={18} />
                  <span>Analyze API Changes</span>
                  <ArrowRightIcon size={16} />
                </>
              )}
            </button>

            <button
              type="button"
              className="btn btn-secondary"
              onClick={onReset}
              disabled={loading || (!oldFile && !newFile && !report)}
            >
              Reset Workspace
            </button>
          </div>

          <div className="actions-right">
            <p className="engine-disclaimer-text">
              Uploaded files are sent via multipart/form-data (<code>old_file</code>, <code>new_file</code>) to the local FastAPI backend (<code>POST /compare</code>).
            </p>
          </div>
        </div>
      </section>

      {/* Loading Progress State */}
      {loading && (
        <section className="app-card loading-state-card" aria-live="polite">
          <div className="loading-card-content">
            <div className="loading-spinner-ring" />
            <div className="loading-text-group">
              <h3>Comparing OpenAPI Specifications</h3>
              <p>
                Sending AST schemas to FastAPI backend engine at <code>http://127.0.0.1:8000/compare</code>...
              </p>
              <div className="loading-step-badges">
                <span className="step-pill">1. Parsing OpenAPI Schema</span>
                <span className="step-pill">2. Detecting Endpoint Drift</span>
                <span className="step-pill">3. Calculating Risk Severity</span>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Post-Comparison Results Section */}
      {report && !loading && (
        <section className="workbench-results-section" aria-live="polite">
          {/* Result Banner */}
          <div className={`results-banner ${report.result === "PASS" ? "banner-pass" : "banner-fail"}`}>
            <div className="banner-left">
              <div className="banner-status-badge">
                <SeverityBadge type={report.result} size="lg" />
              </div>
              <div className="banner-text">
                <h2>
                  {report.result === "PASS"
                    ? "Compatibility Check Passed"
                    : "Breaking Changes Detected"}
                </h2>
                <p>
                  Comparing <strong>{report.oldFileName}</strong> (v{report.oldVersion}) against{" "}
                  <strong>{report.newFileName}</strong> (v{report.newVersion})
                </p>
              </div>
            </div>

            <div className="banner-actions">
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={onDownloadJson}
              >
                <FileTextIcon size={15} />
                <span>Export JSON</span>
              </button>
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={onDownloadPdf}
              >
                <DownloadIcon size={15} />
                <span>Download PDF Report</span>
              </button>
            </div>
          </div>

          {/* Quick Stats Pill Row */}
          <div className="findings-stats-row">
            <div className="findings-stat-pill">
              <span className="stat-label">TOTAL FINDINGS</span>
              <strong className="stat-val">{report.summary.totalChanges}</strong>
            </div>

            <div className="findings-stat-pill pill-danger">
              <span className="stat-label">BREAKING INCOMPATIBILITIES</span>
              <strong className="stat-val text-danger">
                {report.summary.breakingChanges}
              </strong>
            </div>

            <div className="findings-stat-pill pill-warning">
              <span className="stat-label">WARNINGS</span>
              <strong className="stat-val text-warning">
                {report.summary.warnings}
              </strong>
            </div>

            <div className="findings-stat-pill pill-info">
              <span className="stat-label">INFORMATIONAL ADDITIONS</span>
              <strong className="stat-val text-cyan">{infoCount}</strong>
            </div>
          </div>

          {/* Findings Filter & Search Bar */}
          <div className="findings-filter-toolbar">
            <div className="filter-chips-group">
              <button
                type="button"
                className={`filter-chip ${severityFilter === "ALL" ? "is-active" : ""}`}
                onClick={() => setSeverityFilter("ALL")}
              >
                All Changes ({findings.length})
              </button>
              <button
                type="button"
                className={`filter-chip chip-breaking ${severityFilter === "BREAKING" ? "is-active" : ""}`}
                onClick={() => setSeverityFilter("BREAKING")}
              >
                Breaking ({breakingCount})
              </button>
              <button
                type="button"
                className={`filter-chip chip-warning ${severityFilter === "WARNING" ? "is-active" : ""}`}
                onClick={() => setSeverityFilter("WARNING")}
              >
                Warnings ({warningCount})
              </button>
              <button
                type="button"
                className={`filter-chip chip-info ${severityFilter === "INFO" ? "is-active" : ""}`}
                onClick={() => setSeverityFilter("INFO")}
              >
                Informational ({infoCount})
              </button>
            </div>

            <div className="search-box-wrap">
              <SearchIcon size={16} className="search-icon" />
              <input
                type="text"
                className="search-input"
                placeholder="Filter by endpoint or change..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button
                  type="button"
                  className="search-clear-btn"
                  onClick={() => setSearchQuery("")}
                >
                  <XIcon size={14} />
                </button>
              )}
            </div>
          </div>

          {/* Findings Table */}
          {filteredFindings.length === 0 ? (
            <div className="app-card empty-state-box">
              <CheckCircleIcon size={32} className="text-cyan" />
              <h3>No Findings Match Filter</h3>
              <p className="text-muted">
                {findings.length === 0
                  ? "No schema changes were detected between the uploaded specifications."
                  : "Try clearing your search query or switching severity filters."}
              </p>
            </div>
          ) : (
            <div className="app-card findings-table-card">
              <div className="table-responsive">
                <table className="findings-table">
                  <thead>
                    <tr>
                      <th style={{ width: "5%" }}>#</th>
                      <th style={{ width: "14%" }}>Severity</th>
                      <th style={{ width: "24%" }}>Change Title</th>
                      <th style={{ width: "25%" }}>Location / Endpoint</th>
                      <th style={{ width: "24%" }}>Remediation Guidance</th>
                      <th style={{ width: "8%", textAlign: "right" }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredFindings.map((finding, idx) => {
                      const isBreaking = finding.type === "BREAKING";
                      return (
                        <tr
                          key={`${finding.id}-${idx}`}
                          className={`finding-row ${isBreaking ? "row-breaking" : ""}`}
                        >
                          <td className="row-num text-muted">
                            {String(idx + 1).padStart(2, "0")}
                          </td>
                          <td>
                            <SeverityBadge type={finding.type} size="sm" />
                          </td>
                          <td>
                            <div className="change-title-cell">
                              <strong>{finding.title}</strong>
                              <span className="change-details-snippet">
                                {finding.description}
                              </span>
                            </div>
                          </td>
                          <td>
                            <code className="endpoint-code">{finding.endpoint}</code>
                          </td>
                          <td>
                            <span className="recommendation-snippet">
                              {finding.recommendation || "Review and verify client compatibility."}
                            </span>
                          </td>
                          <td style={{ textAlign: "right" }}>
                            <button
                              type="button"
                              className="btn btn-ghost btn-xs text-cyan"
                              onClick={() => setSelectedFinding(finding)}
                              title="Inspect full details"
                            >
                              Inspect →
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </section>
      )}

      {/* Finding Inspection Modal */}
      <FindingDetailModal
        finding={selectedFinding}
        isOpen={Boolean(selectedFinding)}
        onClose={() => setSelectedFinding(null)}
      />
    </div>
  );
}
