import { useState } from "react";
import { ConfirmationModal } from "../components/ConfirmationModal";
import {
  SettingsIcon,
  TrashIcon,
} from "../utils/icons";

export function SettingsPage({
  settings,
  onUpdateSettings,
  onClearCache,
  showToast,
}) {
  const [apiUrl, setApiUrl] = useState(settings?.apiBaseUrl || "http://127.0.0.1:8000");
  const [autoNav, setAutoNav] = useState(settings?.autoNavigateToResults ?? true);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  function handleSaveSettings(e) {
    e.preventDefault();
    const updated = {
      ...settings,
      apiBaseUrl: apiUrl.trim() || "http://127.0.0.1:8000",
      autoNavigateToResults: autoNav,
    };
    onUpdateSettings(updated);
    if (showToast) {
      showToast("success", "Preferences saved to browser storage.");
    }
  }

  function handleResetDefaultUrl() {
    setApiUrl("http://127.0.0.1:8000");
    const updated = {
      ...settings,
      apiBaseUrl: "http://127.0.0.1:8000",
    };
    onUpdateSettings(updated);
    if (showToast) {
      showToast("info", "Reset API base URL to default (http://127.0.0.1:8000).");
    }
  }

  function handleConfirmClearCache() {
    onClearCache();
    setShowClearConfirm(false);
  }

  return (
    <div className="page-container settings-page">
      {/* Top Banner */}
      <section className="app-card settings-hero-card">
        <div className="card-header">
          <div className="header-icon-title">
            <span className="card-icon-tag tag-cyan">
              <SettingsIcon size={20} />
            </span>
            <div>
              <span className="card-eyebrow">PREFERENCES</span>
              <h2 className="card-title">Dashboard Settings</h2>
            </div>
          </div>
        </div>

        <p className="settings-intro">
          Client-side dashboard preferences. Settings are persisted locally in browser <code>localStorage</code> without requiring user authentication or external database services.
        </p>
      </section>

      <div className="settings-cards-grid">
        {/* Backend Configuration */}
        <article className="app-card">
          <div className="card-header">
            <div>
              <span className="card-eyebrow">FASTAPI SERVICE</span>
              <h3 className="card-title">Backend Connection URL</h3>
            </div>
          </div>

          <form onSubmit={handleSaveSettings} className="settings-form">
            <div className="form-group">
              <label htmlFor="apiUrlInput" className="form-label">
                API Base URL
              </label>
              <div className="input-btn-group">
                <input
                  id="apiUrlInput"
                  type="text"
                  className="text-input"
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                  placeholder="http://127.0.0.1:8000"
                />
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={handleResetDefaultUrl}
                  title="Reset to http://127.0.0.1:8000"
                >
                  Reset Default
                </button>
              </div>
              <span className="form-help">
                Target FastAPI host for <code>/compare</code> and <code>/health</code> endpoints.
              </span>
            </div>

            <div className="form-group switch-group">
              <label className="switch-label">
                <input
                  type="checkbox"
                  className="switch-checkbox"
                  checked={autoNav}
                  onChange={(e) => setAutoNav(e.target.checked)}
                />
                <span className="switch-text">
                  <strong>Auto-scroll to results upon comparison</strong>
                  <span className="switch-desc">
                    Immediately focus findings table when analysis completes.
                  </span>
                </span>
              </label>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn btn-primary btn-sm">
                Save Preferences
              </button>
            </div>
          </form>
        </article>

        {/* Local Storage Maintenance */}
        <article className="app-card">
          <div className="card-header">
            <div>
              <span className="card-eyebrow">STORAGE & CACHE</span>
              <h3 className="card-title">Browser Data Management</h3>
            </div>
          </div>

          <p className="text-muted text-sm mb-4">
            Analysis history logs and client preferences are stored on this local device. You can purge all saved audit records at any time.
          </p>

          <div className="storage-action-box">
            <div>
              <strong>Purge Local Storage Cache</strong>
              <p className="text-xs text-muted">
                Clears all saved comparison history and restores default dashboard settings.
              </p>
            </div>
            <button
              type="button"
              className="btn btn-ghost btn-sm text-danger"
              onClick={() => setShowClearConfirm(true)}
            >
              <TrashIcon size={14} />
              <span>Purge Local Data</span>
            </button>
          </div>
        </article>

        {/* Technical Architecture Info */}
        <article className="app-card full-width-card">
          <div className="card-header">
            <div>
              <span className="card-eyebrow">SYSTEM SPECIFICATION</span>
              <h3 className="card-title">Architecture & Tech Stack</h3>
            </div>
          </div>

          <div className="tech-stack-grid">
            <div className="tech-stack-item">
              <span className="tech-key">Frontend Framework</span>
              <strong className="tech-val">React 19 (JSX)</strong>
            </div>
            <div className="tech-stack-item">
              <span className="tech-key">Build Tool & Bundler</span>
              <strong className="tech-val">Vite 8</strong>
            </div>
            <div className="tech-stack-item">
              <span className="tech-key">PDF Generator</span>
              <strong className="tech-val">jsPDF 4.2.1</strong>
            </div>
            <div className="tech-stack-item">
              <span className="tech-key">Backend Engine</span>
              <strong className="tech-val">FastAPI + Python 3.14</strong>
            </div>
            <div className="tech-stack-item">
              <span className="tech-key">Comparison Method</span>
              <strong className="tech-val">AST Schema Diffing</strong>
            </div>
            <div className="tech-stack-item">
              <span className="tech-key">Supported Formats</span>
              <strong className="tech-val">OpenAPI 3.x (JSON, YAML)</strong>
            </div>
          </div>
        </article>
      </div>

      <ConfirmationModal
        isOpen={showClearConfirm}
        title="Purge Local Data & Cache?"
        message="This will delete all saved comparisons from browser storage and reset your preferences. This action cannot be undone."
        confirmLabel="Purge Everything"
        confirmVariant="danger"
        onConfirm={handleConfirmClearCache}
        onCancel={() => setShowClearConfirm(false)}
      />
    </div>
  );
}
