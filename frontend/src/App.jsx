
import { useState } from "react";
import { jsPDF } from "jspdf";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

function App() {
  const [oldFile, setOldFile] = useState(null);
  const [newFile, setNewFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");

  // Validate and store the selected API specification.
  function handleFileChange(event, fileType) {
    const file = event.target.files?.[0];

    if (!file) return;

    setError("");
    setReport(null);

    const isJson = /\.json$/i.test(file.name);
    const isYaml = /\.(yaml|yml)$/i.test(file.name);

    if (!isJson && !isYaml) {
      setError("Please select an OpenAPI JSON or YAML file.");
      event.target.value = "";

      if (fileType === "old") {
        setOldFile(null);
      } else {
        setNewFile(null);
      }

      return;
    }

    if (fileType === "old") {
      setOldFile(file);
    } else {
      setNewFile(file);
    }
  }

  // Send both files to the FastAPI backend.
  async function compareApis() {
    if (!oldFile || !newFile) {
      setError("Please upload both old and new API specification files.");
      return;
    }

    setError("");
    setReport(null);
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("old_file", oldFile);
      formData.append("new_file", newFile);

      const response = await fetch(`${API_BASE_URL}/compare`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const detail =
          typeof data.detail === "string"
            ? data.detail
            : Array.isArray(data.detail)
              ? data.detail.map((item) => item.msg).join(", ")
              : "The backend could not compare these files.";

        throw new Error(detail);
      }

      const findings = (data.findings || []).map((finding, index) => {
        const severity = String(finding.severity || "INFO").toUpperCase();

        const risk =
          severity === "BREAKING"
            ? "HIGH"
            : severity === "WARNING"
              ? "MEDIUM"
              : "LOW";

        return {
          id: index,
          title: finding.change || "API change detected",
          endpoint: finding.location || "Unknown endpoint",
          type: severity,
          risk,
          description:
            finding.details || "No additional details provided.",
          recommendation:
            severity === "BREAKING"
              ? "Review this breaking change and update affected clients before deployment."
              : "Review this change and verify whether client updates are required.",
        };
      });

      setReport({
        summary: {
          totalChanges: data.total_changes ?? findings.length,
          breakingChanges: data.breaking_changes ?? 0,
          warnings: data.warnings ?? 0,
        },
        changes: findings,
        oldFileName: oldFile.name,
        newFileName: newFile.name,
        generatedAt: new Date().toISOString(),
        result: data.result || "UNKNOWN",
        oldVersion: data.old_version || "Unknown",
        newVersion: data.new_version || "Unknown",
      });
    } catch (err) {
      setError(
        err.message ||
          "Could not connect to the backend. Check that FastAPI is running."
      );
    } finally {
      setLoading(false);
    }
  }

  // Generate a downloadable PDF report.
  function downloadReport() {
    if (!report) return;

    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 18;
    const contentWidth = pageWidth - margin * 2;
    const footerSpace = 18;
    let y = 20;

    function ensureSpace(requiredHeight = 12) {
      if (y + requiredHeight > pageHeight - footerSpace) {
        doc.addPage();
        y = 20;
      }
    }

    function addWrappedText(text, fontSize = 10) {
      doc.setFontSize(fontSize);

      const lines = doc.splitTextToSize(
        String(text ?? ""),
        contentWidth
      );

      const lineHeight = fontSize * 0.5;
      const requiredHeight = lines.length * lineHeight + 4;

      ensureSpace(requiredHeight);
      doc.text(lines, margin, y);
      y += requiredHeight;
    }

    // Report title
    doc.setFont("helvetica", "bold");
    doc.setFontSize(20);
    doc.text("API Sentinel", margin, y);
    y += 9;

    doc.setFontSize(13);
    doc.text("Backward Compatibility Analysis Report", margin, y);
    y += 10;

    doc.setFont("helvetica", "normal");

    addWrappedText(`Generated: ${new Date().toLocaleString()}`);
    addWrappedText(`Old API file: ${report.oldFileName}`);
    addWrappedText(`New API file: ${report.newFileName}`);
    addWrappedText(`Old API version: ${report.oldVersion}`);
    addWrappedText(`New API version: ${report.newVersion}`);
    addWrappedText(`Overall result: ${report.result}`);

    y += 3;
    doc.setFont("helvetica", "bold");
    addWrappedText("EXECUTIVE SUMMARY", 13);

    doc.setFont("helvetica", "normal");
    addWrappedText(
      `Total changes detected: ${report.summary.totalChanges}`
    );
    addWrappedText(
      `Breaking changes: ${report.summary.breakingChanges}`
    );
    addWrappedText(`Warnings: ${report.summary.warnings}`);

    y += 3;
    doc.setFont("helvetica", "bold");
    addWrappedText("DETAILED FINDINGS", 13);

    if (report.changes.length === 0) {
      doc.setFont("helvetica", "normal");
      addWrappedText(
        "No changes were detected by the implemented comparison rules."
      );
    }

    report.changes.forEach((change, index) => {
      y += 3;
      ensureSpace(20);

      doc.setFont("helvetica", "bold");
      addWrappedText(`${index + 1}. ${change.title}`);

      doc.setFont("helvetica", "normal");
      addWrappedText(`Endpoint: ${change.endpoint}`);
      addWrappedText(`Severity: ${change.type}`);
      addWrappedText(`Risk level: ${change.risk}`);
      addWrappedText(`Details: ${change.description}`);
      addWrappedText(`Recommendation: ${change.recommendation}`);
    });

    y += 3;
    doc.setFont("helvetica", "bold");
    addWrappedText("DISCLAIMER", 11);

    doc.setFont("helvetica", "normal");
    addWrappedText(
      "This report reflects the comparison rules implemented in API Sentinel. " +
        "Review all findings before deployment. Changes not covered by the implemented rules may remain undetected."
    );

    // Add page numbers to all pages.
    const totalPages = doc.internal.getNumberOfPages();

    for (let page = 1; page <= totalPages; page += 1) {
      doc.setPage(page);
      doc.setFontSize(9);
      doc.text(
        `API Sentinel | Page ${page} of ${totalPages}`,
        pageWidth / 2,
        pageHeight - 8,
        { align: "center" }
      );
    }

    doc.save("api-sentinel-compatibility-report.pdf");
  }

  // Download the raw comparison results as JSON.
  function downloadJsonReport() {
    if (!report) return;

    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "api-sentinel-compatibility-report.json";
    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
  }

  // Clear the dashboard.
  function resetDashboard() {
    setOldFile(null);
    setNewFile(null);
    setReport(null);
    setError("");

    document.querySelectorAll('input[type="file"]').forEach((input) => {
      input.value = "";
    });
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#" aria-label="API Sentinel home">
          <span className="brand-icon">A</span>
          <span>API Sentinel</span>
        </a>

        <span className="demo-badge">LIVE BACKEND</span>
      </header>

      <section className="hero">
        <p className="eyebrow">API COMPATIBILITY ANALYZER</p>
        <h1>Find breaking API changes before deployment.</h1>
        <p className="hero-text">
          Compare two API specifications, identify potential risks,
          and review recommendations before releasing your next version.
        </p>
      </section>

      <section className="panel upload-panel">
        <div className="section-heading">
          <div>
            <h2>Compare API versions</h2>
            <p>Upload your old and new API specification files.</p>
          </div>
          <span className="step-label">STEP 01</span>
        </div>

        <div className="upload-grid">
          <label className="upload-card">
            <span className="file-icon">01</span>
            <span className="upload-title">Old API specification</span>
            <span className="upload-description">
              Select your existing OpenAPI JSON or YAML file.
            </span>
            <span className="file-picker">
              {oldFile ? "Change file" : "Choose API file"}
            </span>
            <span className="file-name">
              {oldFile ? oldFile.name : "No file selected"}
            </span>
            <input
              type="file"
              accept=".json,.yaml,.yml,application/json"
              onChange={(event) => handleFileChange(event, "old")}
            />
          </label>

          <label className="upload-card">
            <span className="file-icon new-icon">02</span>
            <span className="upload-title">New API specification</span>
            <span className="upload-description">
              Select the updated OpenAPI JSON or YAML file.
            </span>
            <span className="file-picker">
              {newFile ? "Change file" : "Choose API file"}
            </span>
            <span className="file-name">
              {newFile ? newFile.name : "No file selected"}
            </span>
            <input
              type="file"
              accept=".json,.yaml,.yml,application/json"
              onChange={(event) => handleFileChange(event, "new")}
            />
          </label>
        </div>

        {error && (
          <p className="error-message" role="alert">
            {error}
          </p>
        )}

        <div className="action-row">
          <button
            className="primary-button"
            onClick={compareApis}
            disabled={loading}
          >
            {loading ? "Analyzing APIs..." : "Compare APIs →"}
          </button>

          <button
            className="secondary-button"
            onClick={resetDashboard}
            disabled={loading}
          >
            Reset
          </button>
        </div>

        <p className="privacy-note">
          Selected files are sent to your local FastAPI backend for comparison.
        </p>
      </section>

      {loading && (
        <section className="panel loading-panel" aria-live="polite">
          <span className="spinner large-spinner" />
          <div>
            <h3>Analyzing API specifications</h3>
            <p>Sending files to the API Sentinel backend...</p>
          </div>
        </section>
      )}

      {report && !loading && (
        <section className="results-section" aria-live="polite">
          <div className="section-heading results-heading">
            <div>
              <p className="eyebrow">ANALYSIS RESULTS</p>
              <h2>Comparison report</h2>
              <p>
                {report.oldFileName} <span className="muted">vs.</span>{" "}
                {report.newFileName}
              </p>
              <p>
                API versions: {report.oldVersion} → {report.newVersion}
              </p>
            </div>

            <button className="primary-button" onClick={downloadReport}>
              ↓ Download PDF
            </button>
          </div>

          <div className="demo-notice">
            <strong>Backend result: {report.result}</strong>
            <span>
              These findings were returned by your local FastAPI backend.
            </span>
          </div>

          <div className="stats-grid">
            <article className="stat-card">
              <span>Total findings</span>
              <strong>{report.summary.totalChanges}</strong>
              <small>Detected changes</small>
            </article>

            <article className="stat-card danger-stat">
              <span>Breaking changes</span>
              <strong>{report.summary.breakingChanges}</strong>
              <small>May affect existing clients</small>
            </article>

            <article className="stat-card warning-stat">
              <span>Warnings</span>
              <strong>{report.summary.warnings}</strong>
              <small>Needs further review</small>
            </article>
          </div>

          <div className="findings-header">
            <div>
              <h2>Detected issues</h2>
              <p>Review each finding and its recommended action.</p>
            </div>
            <span className="count-badge">
              {report.changes.length} findings
            </span>
          </div>

          {report.changes.length === 0 ? (
            <div className="panel">
              No changes were detected by the current comparison rules.
            </div>
          ) : (
            <div className="findings-list">
              {report.changes.map((change) => (
                <article
                  className="finding-card"
                  key={`${change.id}-${change.endpoint}`}
                >
                  <div className="finding-top">
                    <span className="finding-number">
                      {String(change.id + 1).padStart(2, "0")}
                    </span>

                    <div className="finding-title">
                      <h3>{change.title}</h3>
                      <code>{change.endpoint}</code>
                    </div>

                    <span
                      className={`risk-badge ${change.risk.toLowerCase()}`}
                    >
                      {change.risk} RISK
                    </span>
                  </div>

                  <p className="finding-description">
                    {change.description}
                  </p>

                  <div className="recommendation">
                    <strong>Recommended action</strong>
                    <p>{change.recommendation}</p>
                  </div>
                </article>
              ))}
            </div>
          )}

          <div className="report-footer">
            <div>
              <strong>Next step</strong>
              <p>
                Review the findings with your development team before
                deployment.
              </p>
            </div>

            <button
              className="secondary-button"
              onClick={downloadJsonReport}
            >
              Export JSON ↓
            </button>
          </div>
        </section>
      )}

      <footer className="footer">
        API Sentinel · API Change Detection Dashboard · React + FastAPI
      </footer>
    </main>
  );
}

export default App;
