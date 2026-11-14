import { useState } from "react";

import { api, jsonRequest } from "../api.js";

export default function CategoryPanel({
  categories,
  onCategoriesChanged,
  showStatus,
}) {
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
        jsonRequest("POST", {
          name,
          parent_id: parentId ? Number(parentId) : null,
        }),
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
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Organisation</p>
          <h2>Catégories</h2>
        </div>
      </div>
      <form className="inline-form" onSubmit={createCategory}>
        <label>
          Nom
          <input
            maxLength={100}
            onChange={(event) => setName(event.target.value)}
            placeholder="Ex. Fleurs"
            required
            value={name}
          />
        </label>
        <label>
          Catégorie parente
          <select onChange={(event) => setParentId(event.target.value)} value={parentId}>
            <option value="">Aucune — catégorie racine</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {categoryLabel(category)}
              </option>
            ))}
          </select>
        </label>
        <button className="button button-secondary" disabled={loading} type="submit">
          {loading ? "Création…" : "Créer une catégorie"}
        </button>
      </form>
      <ul className="category-list">
        {categories.length === 0 ? (
          <li className="category-empty">Aucune catégorie pour le moment.</li>
        ) : (
          categories.map((category) => (
            <li key={category.id}>
              <span>{categoryLabel(category)}</span>
              <button
                aria-label={`Supprimer la catégorie ${category.name}`}
                className="button button-small"
                onClick={() => removeCategory(category)}
                type="button"
              >
                ×
              </button>
            </li>
          ))
        )}
      </ul>
    </section>
  );
}
