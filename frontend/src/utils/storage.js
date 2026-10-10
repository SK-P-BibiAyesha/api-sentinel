const HISTORY_KEY = "api_sentinel_history_v1";
const SETTINGS_KEY = "api_sentinel_settings_v1";

export function getStoredHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (err) {
    console.error("Failed to read history from localStorage:", err);
    return [];
  }
}

export function saveComparisonToHistory(report) {
  if (!report) return null;
  try {
    const history = getStoredHistory();
    const entry = {
      id: "hist_" + Date.now() + "_" + Math.random().toString(36).slice(2, 7),
      timestamp: new Date().toISOString(),
      oldFileName: report.oldFileName || "old-spec",
      newFileName: report.newFileName || "new-spec",
      oldVersion: report.oldVersion || "unknown",
      newVersion: report.newVersion || "unknown",
      totalChanges: report.summary?.totalChanges ?? 0,
      breakingChanges: report.summary?.breakingChanges ?? 0,
      warnings: report.summary?.warnings ?? 0,
      result: report.result || "UNKNOWN",
      findingsCount: report.changes?.length ?? 0,
      fullReport: report,
    };

    // Keep up to 30 recent history runs
    const updated = [entry, ...history.filter(h => h.id !== entry.id)].slice(0, 30);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
    return entry;
  } catch (err) {
    console.error("Failed to save history to localStorage:", err);
    return null;
  }
}

export function deleteStoredHistoryItem(id) {
  try {
    const history = getStoredHistory();
    const updated = history.filter((item) => item.id !== id);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
    return updated;
  } catch (err) {
    console.error("Failed to delete history item:", err);
    return [];
  }
}

export function clearAllStoredHistory() {
  try {
    localStorage.removeItem(HISTORY_KEY);
    return true;
  } catch (err) {
    console.error("Failed to clear history:", err);
    return false;
  }
}

const DEFAULT_SETTINGS = {
  apiBaseUrl: "http://127.0.0.1:8000",
  autoNavigateToResults: true,
  compactFindingsView: false,
  highlightBreakingOnly: false,
};

export function getStoredSettings() {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (!raw) return { ...DEFAULT_SETTINGS };
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
  } catch (err) {
    console.error("Failed to load settings:", err);
    return { ...DEFAULT_SETTINGS };
  }
}

export function saveStoredSettings(settings) {
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    return true;
  } catch (err) {
    console.error("Failed to save settings:", err);
    return false;
  }
}

