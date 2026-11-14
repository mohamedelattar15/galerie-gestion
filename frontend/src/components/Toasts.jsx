import { AlertCircle, CheckCircle2, X } from "lucide-react";

export default function Toasts({ toasts, onDismiss }) {
  return (
    <div aria-live="polite" className="toasts" role="status">
      {toasts.map((toast) => (
        <div className={`toast${toast.isError ? " is-error" : ""}`} key={toast.id}>
          {toast.isError ? <AlertCircle size={18} /> : <CheckCircle2 size={18} />}
          <span>{toast.message}</span>
          <button
            aria-label="Fermer la notification"
            onClick={() => onDismiss(toast.id)}
            type="button"
          >
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}
