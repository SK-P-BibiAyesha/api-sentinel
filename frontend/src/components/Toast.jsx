import { CheckCircleIcon, AlertTriangleIcon, InfoIcon, XIcon } from "../utils/icons";

export function ToastContainer({ toasts = [], onDismiss }) {
  if (!toasts || toasts.length === 0) return null;

  return (
    <div className="toast-container" aria-live="polite">
      {toasts.map((toast) => {
        let Icon = InfoIcon;
        if (toast.type === "success") Icon = CheckCircleIcon;
        if (toast.type === "error" || toast.type === "danger") Icon = AlertTriangleIcon;

        return (
          <div key={toast.id} className={`toast-item toast-${toast.type || "info"}`}>
            <span className="toast-icon">
              <Icon size={18} />
            </span>
            <div className="toast-message">{toast.message}</div>
            {onDismiss && (
              <button
                type="button"
                className="toast-close"
                onClick={() => onDismiss(toast.id)}
                aria-label="Dismiss toast"
              >
                <XIcon size={14} />
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}
