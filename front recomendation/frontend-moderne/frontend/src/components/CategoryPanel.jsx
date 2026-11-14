import { FolderPlus, Folder, X } from "lucide-react";
import { useState } from "react";

import { api, jsonRequest } from "../api.js";

export default function CategoryPanel({ categories, onCategoriesChanged, showStatus }) {
  const [name, setName] = useState("");
  const [parentId, setParentId] = useState("");
  const [loading, setLoading] = useState(false);
  const namesById = new Map(categories.map((category) => [category.id, category.name]));
  const categoryLabel = (category) =>
    `${category.parent_id ? `${namesById.get(category.parent_id)} / ` : ""}${category.name}`;

  async function createCategory(event) {
    event.preventDefault();
    setLoading(true);
    try {
      await api(
        "/api/categories",
        jsonRequest("POST", { name, parent_id: parentId ? Number(parentId) : null }),
      );
      setName("");
      await onCategoriesChanged();
      showStatus("Catégorie créée.");
    } catch (error) {
      showStatus(error.message, true);
    } finally {
      setLoading(false);
    }
  }

  async function removeCategory(category) {
    try {
      await api(`/api/categories/${category.id}`, { method: "DELETE" });
      await onCategoriesChanged();
      showStatus("Catégorie supprimée.");
    } catch (error) {
      showStatus(error.message, true);
    }
  }

  return (
    <section className="card">
      <div className="card-head">
        <h2>Catégories</h2>
        <span className="badge">{categories.length}</span>
      </div>

      <form className="stack" onSubmit={createCategory}>
        <label className="field">
          <span>Nom</span>
          <input maxLength={100} onChange={(e) => setName(e.target.value)} placeholder="Ex. Fleurs" required value={name} />
        </label>
        <label className="field">
          <span>Catégorie parente</span>
          <select onChange={(e) => setParentId(e.target.value)} value={parentId}>
            <option value="">Aucune — catégorie racine</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>{categoryLabel(category)}</option>
            ))}
          </select>
        </label>
        <button className="btn btn-secondary" disabled={loading} type="submit">
          <FolderPlus size={16} /> {loading ? "Création…" : "Créer la catégorie"}
        </button>
      </form>

      <ul className="category-list">
        {categories.length === 0 ? (
          <li className="muted category-empty">Aucune catégorie pour le moment.</li>
        ) : (
          categories.map((category) => (
            <li key={category.id}>
              <Folder size={16} />
              <span>{categoryLabel(category)}</span>
              <button
                aria-label={`Supprimer la catégorie ${category.name}`}
                className="icon-btn icon-btn-small"
                onClick={() => removeCategory(category)}
                type="button"
              >
                <X size={14} />
              </button>
            </li>
          ))
        )}
      </ul>
    </section>
  );
}
