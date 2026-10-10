import { useState } from "react";
import { SeverityBadge } from "../components/SeverityBadge";
import { ConfirmationModal } from "../components/ConfirmationModal";
import {
  HistoryIcon,
  TrashIcon,
  WorkbenchIcon,
  InfoIcon,
  ArrowRightIcon,
} from "../utils/icons";

export function HistoryPage({
  history = [],
  onLoadHistoryItem,
  onDeleteItem,
  onClearAllHistory,
  setActivePage,
}) {
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [itemToDelete, setItemToDelete] = useState(null);

  function confirmClearAll() {
    onClearAllHistory();
    setShowClearConfirm(false);
  }

  function confirmDeleteItem() {
    if (itemToDelete) {
      onDeleteItem(itemToDelete.id);
      setItemToDelete(null);
    }
  }

  return (
    <div className="page-container history-page">
      {/* Top Banner & Notice */}
      <section className="app-card history-notice-card">
        <div className="card-header">
          <div className="header-icon-title">
            <span className="card-icon-tag">
              <HistoryIcon size={20} />
            </span>
            <div>
              <span className="card-eyebrow">LOCAL AUDIT TRAIL</span>
              <h2 className="card-title">Analysis History</h2>
            </div>
          </div>

          {history.length > 0 && (
            <button
              type="button"
              className="btn btn-ghost btn-sm text-danger"
              onClick={() => setShowClearConfirm(true)}
            >
              <TrashIcon size={14} />
              <span>Clear All History</span>
            </button>
          )}
        </div>

        <div className="storage-disclaimer-box">
          <InfoIcon size={16} className="text-cyan" />
          <p>
            <strong>Client-Side Storage Notice:</strong> This history is stored strictly in your browser&apos;s <code>localStorage</code> on this device. Historical audits are preserved across page reloads without requiring any server-side database or user authentication.
          </p>
        </div>
      </section>

      {/* History Items Table / List */}
      <section className="history-content-section">
        {history.length === 0 ? (
          <div className="app-card empty-state-box">
            <HistoryIcon size={36} className="text-muted" />
            <h3>No Saved Analysis History</h3>
            <p className="text-muted">
              Comparisons executed in the API Workbench will automatically be recorded here for quick review.
            </p>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => setActivePage("workbench")}
            >
              <WorkbenchIcon size={16} />
              <span>Launch API Workbench</span>
            </button>
          </div>
        ) : (
          <div className="app-card history-table-card">
            <div className="table-responsive">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Specifications Compared</th>
                    <th>API Versions</th>
                    <th>Total Changes</th>
                    <th>Breaking</th>
                    <th>Result</th>
                    <th style={{ textAlign: "right" }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((item) => (
                    <tr key={item.id} className="history-row">
                      <td className="history-time-cell">
                        <strong>
                          {new Date(item.timestamp).toLocaleDateString(undefined, {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                          })}
                        </strong>
                        <span className="time-sub">
                          {new Date(item.timestamp).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </td>

                      <td>
                        <div className="history-files-cell">
                          <span className="hist-file old-file" title={item.oldFileName}>
                            {item.oldFileName}
                          </span>
                          <span className="hist-vs">vs</span>
                          <span className="hist-file new-file" title={item.newFileName}>
                            {item.newFileName}
                          </span>
                        </div>
                      </td>

                      <td>
                        <span className="ver-badge-code">
                          v{item.oldVersion} → v{item.newVersion}
                        </span>
                      </td>

                      <td>
                        <strong>{item.totalChanges}</strong>
                      </td>

                      <td>
                        <span
                          className={`font-semibold ${
                            item.breakingChanges > 0 ? "text-danger" : "text-muted"
                          }`}
                        >
                          {item.breakingChanges}
                        </span>
                      </td>

                      <td>
                        <SeverityBadge type={item.result} size="sm" />
                      </td>

                      <td style={{ textAlign: "right" }}>
                        <div className="hist-actions-group">
                          {item.fullReport && (
                            <button
                              type="button"
                              className="btn btn-secondary btn-xs"
                              onClick={() => onLoadHistoryItem(item)}
                              title="Restore this comparison report into view"
                            >
                              <span>Restore Run</span>
                              <ArrowRightIcon size={12} />
                            </button>
                          )}
                          <button
                            type="button"
                            className="icon-button btn-xs text-danger"
                            onClick={() => setItemToDelete(item)}
                            title="Delete this history entry"
                          >
                            <TrashIcon size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>

      {/* Confirmation Modals */}
      <ConfirmationModal
        isOpen={showClearConfirm}
        title="Clear Analysis History?"
        message="This will delete all saved comparison history from your browser's localStorage. This action cannot be undone."
        confirmLabel="Clear All History"
        confirmVariant="danger"
        onConfirm={confirmClearAll}
        onCancel={() => setShowClearConfirm(false)}
      />

      <ConfirmationModal
        isOpen={Boolean(itemToDelete)}
        title="Delete History Entry?"
        message={`Remove the audit record for "${itemToDelete?.oldFileName} vs ${itemToDelete?.newFileName}" from browser storage?`}
        confirmLabel="Delete Entry"
        confirmVariant="danger"
        onConfirm={confirmDeleteItem}
        onCancel={() => setItemToDelete(null)}
      />
    </div>
  );
}
