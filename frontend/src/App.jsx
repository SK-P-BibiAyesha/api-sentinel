import { useState, useEffect, useCallback } from "react";
import { Sidebar } from "./components/Sidebar";
import { Header } from "./components/Header";
import { ToastContainer } from "./components/Toast";

import { DashboardPage } from "./pages/DashboardPage";
import { WorkbenchPage } from "./pages/WorkbenchPage";
import { BreakingChangesPage } from "./pages/BreakingChangesPage";
import { RiskInsightsPage } from "./pages/RiskInsightsPage";
import { RecommendationsPage } from "./pages/RecommendationsPage";
import { HistoryPage } from "./pages/HistoryPage";
import { ReportsPage } from "./pages/ReportsPage";
import { BackendStatusPage } from "./pages/BackendStatusPage";
import { SettingsPage } from "./pages/SettingsPage";

import { exportReportToPdf } from "./utils/pdfExport";
import {
  getStoredHistory,
  saveComparisonToHistory,
  deleteStoredHistoryItem,
  clearAllStoredHistory,
  getStoredSettings,
  saveStoredSettings,
} from "./utils/storage";

import "./App.css";

export default function App() {
  const [activePage, setActivePage] = useState("dashboard");
  const [mobileOpen, setMobileOpen] = useState(false);

  // Settings
  const [settings, setSettings] = useState(() => getStoredSettings());

  // Files & Report State
  const [oldFile, setOldFile] = useState(null);
  const [newFile, setNewFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");

  // History State
  const [history, setHistory] = useState(() => getStoredHistory());

  // Backend Health Telemetry
  const [backendConnected, setBackendConnected] = useState(false);
  const [checkingBackend, setCheckingBackend] = useState(false);
  const [backendHealthData, setBackendHealthData] = useState(null);
  const [backendRootData, setBackendRootData] = useState(null);
  const [lastCheckedTime, setLastCheckedTime] = useState(null);
  const [pingLatency, setPingLatency] = useState(null);
  const [backendError, setBackendError] = useState("");

  // Toast Notifications
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((type, message) => {
    const id = Date.now() + Math.random().toString(36).slice(2, 6);
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3800);
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Manual Probe Backend Health (event triggered)
  const checkBackendHealth = useCallback(async () => {
    setCheckingBackend(true);
    setBackendError("");
    const startTime = performance.now();

    try {
      const baseUrl = settings.apiBaseUrl || "http://127.0.0.1:8000";

      const healthRes = await fetch(`${baseUrl}/health`, {
        method: "GET",
        headers: { Accept: "application/json" },
      });

      const latency = Math.round(performance.now() - startTime);
      setPingLatency(latency);

      if (!healthRes.ok) {
        throw new Error(`Health check returned HTTP ${healthRes.status}`);
      }

      const healthData = await healthRes.json().catch(() => ({}));
      setBackendHealthData(healthData);

      const rootRes = await fetch(`${baseUrl}/`, {
        method: "GET",
        headers: { Accept: "application/json" },
      });
      if (rootRes.ok) {
        const rootData = await rootRes.json().catch(() => ({}));
        setBackendRootData(rootData);
      }

      setBackendConnected(true);
      setLastCheckedTime(new Date().toISOString());
    } catch (err) {
      setBackendConnected(false);
      setBackendError(err.message || "Failed to reach backend.");
      setLastCheckedTime(new Date().toISOString());
    } finally {
      setCheckingBackend(false);
    }
  }, [settings.apiBaseUrl]);

  // Initial check on mount without synchronous setState in effect body
  useEffect(() => {
    let isMounted = true;
    const baseUrl = settings.apiBaseUrl || "http://127.0.0.1:8000";
    const startTime = performance.now();

    fetch(`${baseUrl}/health`, {
      method: "GET",
      headers: { Accept: "application/json" },
    })
      .then(async (res) => {
        const latency = Math.round(performance.now() - startTime);
        if (!isMounted) return;
        setPingLatency(latency);
        if (res.ok) {
          const healthData = await res.json().catch(() => ({}));
          setBackendHealthData(healthData);
          setBackendConnected(true);
        } else {
          setBackendConnected(false);
          setBackendError(`Health probe returned HTTP ${res.status}`);
        }
        setLastCheckedTime(new Date().toISOString());
      })
      .catch((err) => {
        if (!isMounted) return;
        setBackendConnected(false);
        setBackendError(err.message || "Failed to reach backend.");
        setLastCheckedTime(new Date().toISOString());
      });

    fetch(`${baseUrl}/`, {
      method: "GET",
      headers: { Accept: "application/json" },
    })
      .then(async (res) => {
        if (res.ok && isMounted) {
          const rootData = await res.json().catch(() => ({}));
          setBackendRootData(rootData);
        }
      })
      .catch(() => {});

    return () => {
      isMounted = false;
    };
  }, [settings.apiBaseUrl]);

  // Execute Comparison against POST /compare
  async function handleCompare() {
    if (!oldFile || !newFile) {
      setError("Please select both baseline and candidate API specifications.");
      showToast("error", "Please upload both old and new API specification files.");
      return;
    }

    setError("");
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("old_file", oldFile);
      formData.append("new_file", newFile);

      const baseUrl = settings.apiBaseUrl || "http://127.0.0.1:8000";
      const response = await fetch(`${baseUrl}/compare`, {
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

      // Map backend findings to normalized structure preserving all existing rules
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
          description: finding.details || "No additional details provided.",
          recommendation:
            severity === "BREAKING"
              ? "Review this breaking change and update affected clients before deployment."
              : "Review this change and verify whether client updates are required.",
        };
      });

      const newReport = {
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
      };

      setReport(newReport);

      // Persist to localStorage history
      saveComparisonToHistory(newReport);
      setHistory(getStoredHistory());

      const breakingCount = newReport.summary.breakingChanges;
      if (breakingCount > 0) {
        showToast("error", `Comparison completed: ${breakingCount} breaking changes detected!`);
      } else {
        showToast("success", "Comparison completed: API is fully backward-compatible (PASS).");
      }

      if (settings.autoNavigateToResults) {
        // Scroll smoothly to results in workbench
        setTimeout(() => {
          const resultsEl = document.querySelector(".workbench-results-section");
          if (resultsEl) {
            resultsEl.scrollIntoView({ behavior: "smooth" });
          }
        }, 100);
      }
    } catch (err) {
      const msg =
        err.message ||
        "Could not connect to the backend. Check that FastAPI is running at " +
          (settings.apiBaseUrl || "http://127.0.0.1:8000");
      setError(msg);
      showToast("error", msg);
    } finally {
      setLoading(false);
    }
  }

  // PDF Export
  function handleDownloadPdf() {
    if (!report) {
      showToast("error", "No comparison report available to export.");
      return;
    }
    try {
      exportReportToPdf(report);
      showToast("success", "Audit PDF generated and downloaded successfully.");
    } catch (err) {
      console.error("PDF export error:", err);
      showToast("error", "Failed to generate PDF report.");
    }
  }

  // JSON Export
  function handleDownloadJson() {
    if (!report) {
      showToast("error", "No comparison report available to export.");
      return;
    }

    try {
      const blob = new Blob([JSON.stringify(report, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `api-sentinel-report-${report.oldVersion}-to-${report.newVersion}.json`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      showToast("success", "JSON report exported successfully.");
    } catch (err) {
      console.error("JSON export error:", err);
      showToast("error", "Failed to export JSON report.");
    }
  }

  // Reset Workspace
  function handleResetWorkspace() {
    setOldFile(null);
    setNewFile(null);
    setReport(null);
    setError("");
    showToast("info", "Workspace reset. Ready for new comparison.");
  }

  // Load a Saved History Run
  function handleLoadHistoryItem(item) {
    if (item?.fullReport) {
      setReport(item.fullReport);
      setActivePage("workbench");
      showToast(
        "success",
        `Restored audit: ${item.oldFileName} vs ${item.newFileName}`
      );
    }
  }

  // Delete an item from History
  function handleDeleteHistoryItem(id) {
    const updated = deleteStoredHistoryItem(id);
    setHistory(updated);
    showToast("info", "Audit record removed from history.");
  }

  // Clear All History
  function handleClearAllHistory() {
    clearAllStoredHistory();
    setHistory([]);
    showToast("info", "Analysis history cleared.");
  }

  // Save Settings
  function handleUpdateSettings(newSettings) {
    saveStoredSettings(newSettings);
    setSettings(newSettings);
  }

  // Purge Local Storage Cache
  function handleClearCache() {
    clearAllStoredHistory();
    setHistory([]);
    const defaultSettings = {
      apiBaseUrl: "http://127.0.0.1:8000",
      autoNavigateToResults: true,
      compactFindingsView: false,
      highlightBreakingOnly: false,
    };
    saveStoredSettings(defaultSettings);
    setSettings(defaultSettings);
    showToast("info", "Local storage purged and settings restored to default.");
  }

  return (
    <div className="app-shell-root">
      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
        report={report}
        historyCount={history.length}
        backendConnected={backendConnected}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
      />

      <div className="app-main-viewport">
        <Header
          activePage={activePage}
          setActivePage={setActivePage}
          backendConnected={backendConnected}
          checkingBackend={checkingBackend}
          onRefreshBackend={checkBackendHealth}
          onOpenMobile={() => setMobileOpen(true)}
        />

        <main className="app-page-content">
          {activePage === "dashboard" && (
            <DashboardPage
              report={report}
              setActivePage={setActivePage}
              history={history}
              backendConnected={backendConnected}
              onDownloadPdf={handleDownloadPdf}
              onDownloadJson={handleDownloadJson}
              onLoadHistoryItem={handleLoadHistoryItem}
            />
          )}

          {activePage === "workbench" && (
            <WorkbenchPage
              oldFile={oldFile}
              newFile={newFile}
              setOldFile={setOldFile}
              setNewFile={setNewFile}
              loading={loading}
              error={error}
              report={report}
              onCompare={handleCompare}
              onReset={handleResetWorkspace}
              onDownloadPdf={handleDownloadPdf}
              onDownloadJson={handleDownloadJson}
              showToast={showToast}
            />
          )}

          {activePage === "breaking" && (
            <BreakingChangesPage
              report={report}
              setActivePage={setActivePage}
              onDownloadPdf={handleDownloadPdf}
            />
          )}

          {activePage === "risk" && (
            <RiskInsightsPage
              report={report}
              setActivePage={setActivePage}
            />
          )}

          {activePage === "recommendations" && (
            <RecommendationsPage
              report={report}
              setActivePage={setActivePage}
            />
          )}

          {activePage === "history" && (
            <HistoryPage
              history={history}
              onLoadHistoryItem={handleLoadHistoryItem}
              onDeleteItem={handleDeleteHistoryItem}
              onClearAllHistory={handleClearAllHistory}
              setActivePage={setActivePage}
            />
          )}

          {activePage === "reports" && (
            <ReportsPage
              report={report}
              setActivePage={setActivePage}
              onDownloadPdf={handleDownloadPdf}
              onDownloadJson={handleDownloadJson}
              showToast={showToast}
            />
          )}

          {activePage === "backend" && (
            <BackendStatusPage
              apiBaseUrl={settings.apiBaseUrl || "http://127.0.0.1:8000"}
              backendConnected={backendConnected}
              checkingBackend={checkingBackend}
              backendHealthData={backendHealthData}
              backendRootData={backendRootData}
              lastCheckedTime={lastCheckedTime}
              pingLatency={pingLatency}
              backendError={backendError}
              onCheckBackend={checkBackendHealth}
            />
          )}

          {activePage === "settings" && (
            <SettingsPage
              settings={settings}
              onUpdateSettings={handleUpdateSettings}
              onClearCache={handleClearCache}
              showToast={showToast}
            />
          )}
        </main>

        <footer className="app-global-footer">
          <div className="footer-left">
            <span>API Sentinel v1.0.0</span>
            <span className="footer-sep">·</span>
            <span>Microservice Drift Detector & Compatibility Linter</span>
          </div>
          <div className="footer-right">
            <span>React 19 + Vite</span>
            <span className="footer-sep">·</span>
            <span>FastAPI Engine</span>
          </div>
        </footer>
      </div>

      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
