import { useEffect } from "react";

export default function ConfirmDialog({ title, message, confirmLabel = "Supprimer", onConfirm, onCancel }) {
  useEffect(() => {
    const onKeyDown = (event) => event.key === "Escape" && onCancel();
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onCancel]);

  return (
    <div className="modal-backdrop" onClick={onCancel} role="presentation">
      <div aria-modal="true" className="modal" onClick={(e) => e.stopPropagation()} role="alertdialog">
        <h3>{title}</h3>
        <p className="muted">{message}</p>
        <div className="modal-actions">
          <button className="btn btn-ghost" onClick={onCancel} type="button">
            Annuler
          </button>
          <button autoFocus className="btn btn-danger" onClick={onConfirm} type="button">
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
