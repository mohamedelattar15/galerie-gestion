import { useEffect } from "react";

export default function ConfirmDialog({
  title,
  message,
  confirmLabel = "Supprimer",
  onConfirm,
  onCancel,
}) {
  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.key === "Escape") onCancel();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onCancel]);

  return (
    <div className="modal-backdrop" onClick={onCancel} role="presentation">
      <div
        aria-modal="true"
        className="modal"
        onClick={(event) => event.stopPropagation()}
        role="alertdialog"
      >
        <h3>{title}</h3>
        <p className="hint">{message}</p>
        <div className="modal-actions">
          <button className="button button-quiet" onClick={onCancel} type="button">
            Annuler
          </button>
          <button autoFocus className="button button-danger" onClick={onConfirm} type="button">
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
