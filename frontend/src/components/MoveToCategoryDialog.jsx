import { useState } from "react";

export default function MoveToCategoryDialog({ categories, selectedCount, onMove, onCancel }) {
  const [categoryId, setCategoryId] = useState("");
  const [loading, setLoading] = useState(false);

  function categoryPath(category) {
    const parts = [category.name];
    let parentId = category.parent_id;
    while (parentId) {
      const parent = categories.find((item) => item.id === parentId);
      if (!parent) break;
      parts.unshift(parent.name);
      parentId = parent.parent_id;
    }
    return parts.join(" / ");
  }

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    try {
      await onMove(categoryId ? Number(categoryId) : null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onCancel} role="presentation">
      <form
        aria-modal="true"
        className="modal"
        onClick={(event) => event.stopPropagation()}
        onSubmit={submit}
        role="dialog"
      >
        <h3>Déplacer {selectedCount} image(s)</h3>
        <p className="hint">Choisissez la catégorie de destination.</p>
        <label className="move-category-field">
          Catégorie
          <select onChange={(event) => setCategoryId(event.target.value)} value={categoryId}>
            <option value="">Sans catégorie</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {categoryPath(category)}
              </option>
            ))}
          </select>
        </label>
        <div className="modal-actions">
          <button className="button button-quiet" onClick={onCancel} type="button">
            Annuler
          </button>
          <button autoFocus className="button button-primary" disabled={loading} type="submit">
            {loading ? "Déplacement…" : "Déplacer"}
          </button>
        </div>
      </form>
    </div>
  );
}
