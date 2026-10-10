import { useState } from "react";
import { SeverityBadge } from "../components/SeverityBadge";
import {
  ReportIcon,
  DownloadIcon,
  FileTextIcon,
  CopyIcon,
  CheckCircleIcon,
  WorkbenchIcon,
} from "../utils/icons";

export function ReportsPage({
  report,
  setActivePage,
  onDownloadPdf,
  onDownloadJson,
  showToast,
}) {
  const [copied, setCopied] = useState(false);

  function handleCopyJson() {
    if (!report) return;
    try {
      const jsonStr = JSON.stringify(report, null, 2);
      navigator.clipboard.writeText(jsonStr);
      setCopied(true);
      if (showToast) {
        showToast("success", "Structured JSON report copied to clipboard!");
      }
      setTimeout(() => setCopied(false), 2500);
    } catch (err) {
      console.error("Clipboard copy failed:", err);
      if (showToast) {
        showToast("error", "Failed to copy to clipboard.");
      }
    }
  }

  return (
    <div className="page-container reports-page">
      {/* Top Banner */}
      <section className="app-card reports-hero-card">
        <div className="card-header">
          <div className="header-icon-title">
            <span className="card-icon-tag tag-cyan">
              <ReportIcon size={20} />
            </span>
            <div>
              <span className="card-eyebrow">EXPORT & COMPLIANCE STATION</span>
              <h2 className="card-title">Reports & Downloads</h2>
            </div>
          </div>
        </div>

        <p className="reports-intro">
          Generate formal audit artifacts for technical reviews, security boards, and CI/CD automation pipelines. Export print-friendly compliance PDFs with executive summaries, or raw machine-readable JSON payloads.
        </p>
      </section>

      {!report ? (
        <section className="app-card empty-state-box">
          <ReportIcon size={36} className="text-muted" />
          <h3>No Audit Report Available</h3>
          <p className="text-muted">
            Execute an API comparison in the Workbench to generate downloadable PDF and JSON compliance reports.
          </p>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setActivePage("workbench")}
          >
            <WorkbenchIcon size={16} />
            <span>Launch API Workbench</span>
          </button>
        </section>
      ) : (
        <div className="reports-grid">
          {/* Export Actions Card */}
          <article className="app-card export-options-card">
            <div className="card-header">
              <div>
                <span className="card-eyebrow">EXPORT FORMATS</span>
                <h3 className="card-title">Select Artifact Format</h3>
              </div>
            </div>

            <div className="export-cards-list">
              {/* PDF Card */}
              <div className="export-action-box">
                <div className="eab-left">
                  <div className="eab-icon eab-pdf">
                    <DownloadIcon size={22} />
                  </div>
                  <div className="eab-text">
                    <strong>Formal Audit Report (PDF)</strong>
                    <p>
                      Formatted compliance PDF containing API Sentinel branding, executive compatibility summary, findings breakdown with severity indicators, and page numbering.
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={onDownloadPdf}
                >
                  <DownloadIcon size={14} />
                  <span>Download PDF</span>
                </button>
              </div>

              {/* JSON File Card */}
              <div className="export-action-box">
                <div className="eab-left">
                  <div className="eab-icon eab-json">
                    <FileTextIcon size={22} />
                  </div>
                  <div className="eab-text">
                    <strong>Machine-Readable JSON Report (.json)</strong>
                    <p>
                      Standard structured JSON representation containing full AST comparison details, versions, and endpoint locations for automated pipelines.
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={onDownloadJson}
                >
                  <DownloadIcon size={14} />
                  <span>Export JSON</span>
                </button>
              </div>

              {/* Clipboard Card */}
              <div className="export-action-box">
                <div className="eab-left">
                  <div className="eab-icon eab-copy">
                    <CopyIcon size={22} />
                  </div>
                  <div className="eab-text">
                    <strong>Copy JSON to Clipboard</strong>
                    <p>
                      Instantly copy the complete JSON audit payload to your system clipboard for pasting into issue trackers or terminal commands.
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={handleCopyJson}
                >
                  {copied ? (
                    <>
                      <CheckCircleIcon size={14} className="text-cyan" />
                      <span>Copied!</span>
                    </>
                  ) : (
                    <>
                      <CopyIcon size={14} />
                      <span>Copy Payload</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </article>

          {/* Active Report Metadata & Preview Card */}
          <article className="app-card report-preview-card">
            <div className="card-header">
              <div>
                <span className="card-eyebrow">AUDIT SUMMARY PREVIEW</span>
                <h3 className="card-title">Active Report Contents</h3>
              </div>
              <SeverityBadge type={report.result} size="md" />
            </div>

            <div className="preview-meta-list">
              <div className="preview-meta-item">
                <span className="p-key">Baseline Specification:</span>
                <span className="p-val">{report.oldFileName} (v{report.oldVersion})</span>
              </div>
              <div className="preview-meta-item">
                <span className="p-key">Target Specification:</span>
                <span className="p-val">{report.newFileName} (v{report.newVersion})</span>
              </div>
              <div className="preview-meta-item">
                <span className="p-key">Overall Verdict:</span>
                <span className="p-val">
                  <strong>{report.result}</strong> (
                  {report.result === "PASS"
                    ? "Safe to merge"
                    : `${report.summary.breakingChanges} breaking issues`}
                  )
                </span>
              </div>
              <div className="preview-meta-item">
                <span className="p-key">Total Schema Findings:</span>
                <span className="p-val">{report.summary.totalChanges} detected</span>
              </div>
              <div className="preview-meta-item">
                <span className="p-key">Breaking Incompatibilities:</span>
                <span className="p-val text-danger font-semibold">
                  {report.summary.breakingChanges}
                </span>
              </div>
              <div className="preview-meta-item">
                <span className="p-key">Warnings:</span>
                <span className="p-val text-warning">{report.summary.warnings}</span>
              </div>
              <div className="preview-meta-item">
                <span className="p-key">Generated Timestamp:</span>
                <span className="p-val text-muted">
                  {new Date(report.generatedAt).toLocaleString()}
                </span>
              </div>
            </div>
          </article>
        </div>
      )}
    </div>
  );
}
