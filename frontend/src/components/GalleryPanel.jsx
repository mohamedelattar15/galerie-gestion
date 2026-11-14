import { useState } from "react";

import { api } from "../api.js";
import ImageInspector from "./ImageInspector.jsx";

export default function GalleryPanel({
  categories,
  images,
  offset,
  pageSize,
  onRefresh,
  showStatus,
}) {
  const [selected, setSelected] = useState(null);
  const categoryNames = new Map(categories.map((category) => [category.id, category.name]));
  const hasPreviousPage = offset > 0;
  const hasNextPage = images.length === pageSize;

  async function removeImage(image) {
    if (!window.confirm(`Supprimer « ${image.filename} » ?`)) return;
    try {
      await api(`/api/images/${image.id}`, { method: "DELETE" });
      setSelected(null);
      await onRefresh(offset);
      showStatus("Image supprimée.");
    } catch (error) {
      showStatus(error.message, true);
    }
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Images personnelles</p>
          <h2>Ma galerie</h2>
        </div>
        <button className="button button-quiet" onClick={() => onRefresh(offset)} type="button">
          Actualiser
        </button>
      </div>

      <div className="image-grid">
        {images.length === 0 ? (
          <p className="empty-state gallery-empty">
            {hasPreviousPage
              ? "Cette page est vide. Revenez à la page précédente."
              : "Votre galerie est vide. Importez quelques images pour commencer."}
          </p>
        ) : (
          images.map((image) => (
            <article className="image-card gallery-card" key={image.id}>
              <button className="card-open" onClick={() => setSelected(image)} type="button">
                <img alt={image.filename} loading="lazy" src={image.file_url} />
                <span className="card-caption">
                  <strong>{image.filename}</strong>
                  <small>
                    {image.width} × {image.height}
                    {image.category_id ? ` · ${categoryNames.get(image.category_id)}` : ""}
                  </small>
                </span>
              </button>
              <div className="card-hover-actions">
                <a
                  className="button button-quiet"
                  download={image.filename}
                  href={`${image.file_url}?download=1`}
                >
                  Télécharger
                </a>
                <button
                  className="button button-quiet"
                  onClick={() => removeImage(image)}
                  type="button"
                >
                  Supprimer
                </button>
              </div>
            </article>
          ))
        )}
      </div>

      {(hasPreviousPage || hasNextPage) && (
        <nav aria-label="Pagination de la galerie" className="gallery-pagination">
          <button
            className="button button-quiet"
            disabled={!hasPreviousPage}
            onClick={() => onRefresh(Math.max(0, offset - pageSize))}
            type="button"
          >
            Précédent
          </button>
          <span className="hint">
            Images {offset + 1} à {offset + images.length}
          </span>
          <button
            className="button button-quiet"
            disabled={!hasNextPage}
            onClick={() => onRefresh(offset + pageSize)}
            type="button"
          >
            Suivant
          </button>
        </nav>
      )}

      {selected && (
        <ImageInspector
          categoryName={categoryNames.get(selected.category_id)}
          image={selected}
          onChanged={() => onRefresh(offset)}
          onClose={() => setSelected(null)}
          showStatus={showStatus}
        />
      )}
    </section>
  );
}
