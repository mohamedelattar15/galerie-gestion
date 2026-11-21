import { ChevronLeft, ChevronRight, Download, ImagePlus, RefreshCw, Trash2 } from "lucide-react";
import { useState } from "react";

import { api } from "../api.js";
import ConfirmDialog from "./ConfirmDialog.jsx";
import ImageDetailPage from "./ImageDetailPage.jsx";

export default function GalleryPanel({
  categories,
  images,
  loading,
  offset,
  pageSize,
  onRefresh,
  onGoImport,
  onSearch,
  showStatus,
}) {
  const [selected, setSelected] = useState(null);
  const [toDelete, setToDelete] = useState(null);
  const categoryNames = new Map(categories.map((category) => [category.id, category.name]));
  const hasPreviousPage = offset > 0;
  const hasNextPage = images.length === pageSize;

  async function removeImage(image) {
    setToDelete(null);
    try {
      await api(`/api/images/${image.id}`, { method: "DELETE" });
      setSelected(null);
      await onRefresh(offset);
      showStatus("Image supprimée.");
    } catch (error) {
      showStatus(error.message, true);
    }
  }

  if (selected) {
    return (
      <>
        <ImageDetailPage
          categoryName={categoryNames.get(selected.category_id)}
          image={selected}
          onBack={() => setSelected(null)}
          onChanged={() => onRefresh(offset)}
          onDelete={() => setToDelete(selected)}
          onSearch={onSearch}
          showStatus={showStatus}
        />
        {toDelete && (
          <ConfirmDialog
            message="Cette action est définitive. Les copies transformées ne sont pas affectées."
            onCancel={() => setToDelete(null)}
            onConfirm={() => removeImage(toDelete)}
            title={`Supprimer « ${toDelete.filename} » ?`}
          />
        )}
      </>
    );
  }

  return (
    <section>
      <div className="toolbar">
        <span className="hint">
          {images.length > 0 ? `Images ${offset + 1} à ${offset + images.length}` : "Aucune image"}
        </span>
        <button className="button button-quiet" onClick={() => onRefresh(offset)} type="button">
          <RefreshCw className={loading ? "spin" : ""} size={16} /> Actualiser
        </button>
      </div>

      {images.length === 0 ? (
        <div className="empty-state">
          <span className="empty-icon">
            <ImagePlus size={26} />
          </span>
          <h3>{hasPreviousPage ? "Cette page est vide" : "Votre galerie est vide"}</h3>
          <p className="hint">
            {hasPreviousPage
              ? "Revenez à la page précédente."
              : "Importez quelques images pour commencer."}
          </p>
          {!hasPreviousPage && (
            <button className="button button-primary" onClick={onGoImport} type="button">
              Importer des images
            </button>
          )}
        </div>
      ) : (
        <div className="gallery-grid">
          {images.map((image) => (
            <article className="tile" key={image.id}>
              <button className="tile-open" onClick={() => setSelected(image)} type="button">
                <img alt={image.filename} loading="lazy" src={image.file_url} />
                <span className="tile-caption">
                  <strong>{image.filename}</strong>
                  <small>
                    {image.width} × {image.height}
                    {image.category_id ? ` · ${categoryNames.get(image.category_id)}` : ""}
                  </small>
                </span>
              </button>
              <div className="tile-actions">
                <a
                  aria-label={`Télécharger ${image.filename}`}
                  className="icon-btn icon-btn-glass"
                  download={image.filename}
                  href={`${image.file_url}?download=1`}
                  title="Télécharger"
                >
                  <Download size={16} />
                </a>
                <button
                  aria-label={`Supprimer ${image.filename}`}
                  className="icon-btn icon-btn-glass"
                  onClick={() => setToDelete(image)}
                  title="Supprimer"
                  type="button"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </article>
          ))}
        </div>
      )}

      {(hasPreviousPage || hasNextPage) && (
        <nav aria-label="Pagination de la galerie" className="pagination">
          <button
            className="button button-quiet"
            disabled={!hasPreviousPage}
            onClick={() => onRefresh(Math.max(0, offset - pageSize))}
            type="button"
          >
            <ChevronLeft size={16} /> Précédent
          </button>
          <span className="hint">Page {Math.floor(offset / pageSize) + 1}</span>
          <button
            className="button button-quiet"
            disabled={!hasNextPage}
            onClick={() => onRefresh(offset + pageSize)}
            type="button"
          >
            Suivant <ChevronRight size={16} />
          </button>
        </nav>
      )}

      {toDelete && (
        <ConfirmDialog
          message="Cette action est définitive. Les copies transformées ne sont pas affectées."
          onCancel={() => setToDelete(null)}
          onConfirm={() => removeImage(toDelete)}
          title={`Supprimer « ${toDelete.filename} » ?`}
        />
      )}
    </section>
  );
}
