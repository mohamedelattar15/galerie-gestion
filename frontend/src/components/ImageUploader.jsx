import { useState } from "react";

import { api } from "../api.js";

export default function ImageUploader({ categories, onUploaded, showStatus }) {
  const [files, setFiles] = useState([]);
  const [categoryId, setCategoryId] = useState("");
  const [loading, setLoading] = useState(false);
  const categoryNames = new Map(categories.map((category) => [category.id, category.name]));

  async function upload(event) {
    event.preventDefault();
    if (files.length === 0) return;
    setLoading(true);
    const formData = new FormData();
    for (const file of files) formData.append("images", file);
    if (categoryId) formData.append("category_id", categoryId);
    try {
      const result = await api("/api/images", { method: "POST", body: formData });
      const failures = result.results.filter((image) => image.error);
      const failureDetails = failures
        .map((image) => `${image.filename}: ${image.error}`)
        .join(" · ");
      await onUploaded();
      showStatus(
        `${result.created} image(s) importée(s), ${result.failed} échec(s).${failureDetails ? ` ${failureDetails}` : ""}`,
        failures.length > 0,
      );
      setFiles([]);
      event.target.reset();
    } catch (error) {
      showStatus(error.message, true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Collection</p>
          <h2>Importer des images</h2>
        </div>
      </div>
      <form className="inline-form" onSubmit={upload}>
        <label className="file-label">
          Images (jusqu’à 32)
          <input
            accept="image/*"
            multiple
            onChange={(event) => setFiles(Array.from(event.target.files || []))}
            required
            type="file"
          />
        </label>
        <label>
          Catégorie
          <select onChange={(event) => setCategoryId(event.target.value)} value={categoryId}>
            <option value="">Sans catégorie</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.parent_id
                  ? `${categoryNames.get(category.parent_id)} / ${category.name}`
                  : category.name}
              </option>
            ))}
          </select>
        </label>
        <button className="button button-primary" disabled={loading} type="submit">
          {loading ? "Importation…" : "Importer"}
        </button>
      </form>
      {files.length > 0 && (
        <p className="hint" aria-live="polite">
          {files.length} fichier(s) sélectionné(s) : {files.map((file) => file.name).join(", ")}
        </p>
      )}
    </section>
  );
}
