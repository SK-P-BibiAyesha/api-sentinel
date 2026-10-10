
import { useState } from "react";
import "./App.css";

const mockReport = {
  summary: {
    totalChanges: 3,
    breakingChanges: 2,
    warnings: 1,
  },
  changes: [
    {
      title: "Endpoint removed",
      endpoint: "DELETE /api/users/{id}",
      type: "BREAKING",
      risk: "HIGH",
      description:
        "An endpoint available in the old API is missing from the new API.",
      recommendation:
        "Restore the endpoint or confirm that all clients have migrated.",
    },
    {
      title: "Required field added",
      endpoint: "POST /api/users",
      type: "BREAKING",
      risk: "HIGH",
      description:
        "A new required field may cause older client requests to fail.",
      recommendation:
        "Make the field optional or update all client applications before deployment.",
    },
    {
      title: "Response field changed",
      endpoint: "GET /api/products",
      type: "WARNING",
      risk: "MEDIUM",
      description:
        "A response field has changed and may affect clients that depend on it.",
      recommendation:
        "Check client usage and document the response change.",
    },
  ],
};

function App() {
  const [oldFile, setOldFile] = useState(null);
  const [newFile, setNewFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");

  function handleFileChange(event, fileType) {
    const file = event.target.files?.[0];

    if (!file) return;

    setError("");
    setReport(null);

    if (!file.name.toLowerCase().endsWith(".json")) {
      setError("Please select a JSON file.");
      event.target.value = "";
      if (fileType === "old") setOldFile(null);
      else setNewFile(null);
      return;
    }

    if (fileType === "old") setOldFile(file);
    else setNewFile(file);
  }

  async function compareApis() {
    if (!oldFile || !newFile) {
      setError("Please upload both old and new API JSON files.");
      return;
    }

    setError("");
    setReport(null);
    setLoading(true);

    try {
      // Validate that both uploaded files contain valid JSON.
      const oldText = await oldFile.text();
      const newText = await newFile.text();

      JSON.parse(oldText);
      JSON.parse(newText);

      // Demo mode: show mock results until the backend is connected.
      await new Promise((resolve) => setTimeout(resolve, 900));

      setReport({
        ...mockReport,
        oldFileName: oldFile.name,
        newFileName: newFile.name,
        generatedAt: new Date().toISOString(),
        mode: "DEMO - MOCK RESULTS",
      });
    } catch {
      setError(
        "One of the files contains invalid JSON. Please check both files and try again."
      );
    } finally {
      setLoading(false);
    }
  }

  function downloadReport() {
    if (!report) return;

    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "api-comparison-report.json";
    link.click();

    URL.revokeObjectURL(url);
  }

  function resetDashboard() {
    setOldFile(null);
    setNewFile(null);
    setReport(null);
    setError("");
    setLoading(false);

    document.querySelectorAll('input[type="file"]').forEach((input) => {
      input.value = "";
    });
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#" aria-label="API Guard home">
          <span className="brand-icon">A</span>
          <span>API Guard</span>
        </a>

        <span className="demo-badge">FRONTEND DEMO</span>
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
              Select your existing API JSON file.
            </span>
            <span className="file-picker">
              {oldFile ? "Change file" : "Choose JSON file"}
            </span>
            <span className="file-name">
              {oldFile ? oldFile.name : "No file selected"}
            </span>
            <input
              type="file"
              accept=".json,application/json"
              onChange={(event) => handleFileChange(event, "old")}
            />
          </label>

          <label className="upload-card">
            <span className="file-icon new-icon">02</span>
            <span className="upload-title">New API specification</span>
            <span className="upload-description">
              Select the updated API JSON file.
            </span>
            <span className="file-picker">
              {newFile ? "Change file" : "Choose JSON file"}
            </span>
            <span className="file-name">
              {newFile ? newFile.name : "No file selected"}
            </span>
            <input
              type="file"
              accept=".json,application/json"
              onChange={(event) => handleFileChange(event, "new")}
            />
          </label>
        </div>

        {error && <p className="error-message">{error}</p>}

        <div className="action-row">
          <button
            className="primary-button"
            onClick={compareApis}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner" />
                Analyzing APIs...
              </>
            ) : (
              "Compare APIs →"
            )}
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
          Files are read locally in your browser in this demo.
        </p>
      </section>

      {loading && (
        <section className="panel loading-panel" aria-live="polite">
          <span className="spinner large-spinner" />
          <div>
            <h3>Analyzing API specifications</h3>
            <p>Validating files and preparing the demo report...</p>
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
            </div>

            <button className="primary-button" onClick={downloadReport}>
              ↓ Download report
            </button>
          </div>

          <div className="demo-notice">
            <strong>Demo results</strong>
            <span>
              These are sample findings, not findings calculated from your
              uploaded API specifications.
            </span>
          </div>

          <div className="stats-grid">
            <article className="stat-card">
              <span>Total findings</span>
              <strong>{report.summary.totalChanges}</strong>
              <small>Potential changes</small>
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

          <div className="findings-list">
            {report.changes.map((change, index) => (
              <article className="finding-card" key={change.endpoint}>
                <div className="finding-top">
                  <span className="finding-number">
                    {String(index + 1).padStart(2, "0")}
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

                <p className="finding-description">{change.description}</p>

                <div className="recommendation">
                  <strong>Recommended action</strong>
                  <p>{change.recommendation}</p>
                </div>
              </article>
            ))}
          </div>

          <div className="report-footer">
            <div>
              <strong>Next step</strong>
              <p>
                Review all findings with your development team before
                deployment.
              </p>
            </div>
            <button className="secondary-button" onClick={downloadReport}>
              Export JSON ↓
            </button>
          </div>
        </section>
      )}

      <footer className="footer">
        API Guard · API Change Detection Dashboard · React + Vite
      </footer>
    </main>
  );
}

export default App;
