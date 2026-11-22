import { ChevronLeft, ChevronRight, Download, ImagePlus, RefreshCw, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { api, jsonRequest } from "../api.js";
import ConfirmDialog from "./ConfirmDialog.jsx";
import ImageDetailPage from "./ImageDetailPage.jsx";
import MoveToCategoryDialog from "./MoveToCategoryDialog.jsx";

export default function GalleryPanel({
  categories,
  images,
  loading,
  offset,
  pageSize,
  onRefresh: onRefreshGallery,
  onGoImport,
  onSearch,
  showStatus,
}) {
  const [selected, setSelected] = useState(null);
  const [toDelete, setToDelete] = useState(null);
  const [selectedIds, setSelectedIds] = useState(() => new Set());
  const [confirmBatchDelete, setConfirmBatchDelete] = useState(false);
  const [showMoveDialog, setShowMoveDialog] = useState(false);
  const [downloadingSelection, setDownloadingSelection] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState("");
  const [sortBy, setSortBy] = useState("created_desc");
  const [searchInput, setSearchInput] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const categoryNames = new Map(categories.map((category) => [category.id, category.name]));
  const hasPreviousPage = offset > 0;
  const hasNextPage = images.length === pageSize;
  const pageIds = images.map((image) => image.id);
  const allPageSelected = pageIds.length > 0 && pageIds.every((id) => selectedIds.has(id));

  function refreshGalleryPage(nextOffset = offset) {
    return onRefreshGallery(nextOffset, categoryFilter || null, sortBy, appliedSearch);
  }

  function submitSearch(event) {
    event.preventDefault();
    const search = searchInput.trim();
    setAppliedSearch(search);
    setSelectedIds(new Set());
    onRefreshGallery(0, categoryFilter || null, sortBy, search).catch((error) =>
      showStatus(error.message, true),
    );
  }

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

  useEffect(() => {
    const visibleIds = new Set(pageIds);
    setSelectedIds((current) => {
      const next = new Set([...current].filter((id) => visibleIds.has(id)));
      return next.size === current.size ? current : next;
    });
  }, [images]);

  function toggleImageSelection(imageId) {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (next.has(imageId)) next.delete(imageId);
      else next.add(imageId);
      return next;
    });
  }

  function togglePageSelection() {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (allPageSelected) pageIds.forEach((id) => next.delete(id));
      else pageIds.forEach((id) => next.add(id));
      return next;
    });
  }

  async function removeImage(image) {
    setToDelete(null);
    try {
      await api(`/api/images/${image.id}`, { method: "DELETE" });
      setSelected(null);
      await refreshGalleryPage(offset);
      showStatus("Image supprimée.");
    } catch (error) {
      showStatus(error.message, true);
    }
  }

  async function removeSelectedImages() {
    const ids = [...selectedIds];
    setConfirmBatchDelete(false);
    try {
      const report = await api(
        "/api/images/batch-delete",
        jsonRequest("POST", { image_ids: ids }),
      );
      setSelectedIds(new Set());
      const nextOffset =
        report.failed.length === 0 && ids.length === images.length && offset > 0
          ? offset - pageSize
          : offset;
      await refreshGalleryPage(nextOffset);
      const failedCount = report.failed?.length ?? 0;
      if (failedCount) {
        showStatus(`${report.succeeded.length} image(s) supprimée(s), ${failedCount} échec(s).`, true);
      } else {
        showStatus(`${report.succeeded.length} image(s) supprimée(s).`);
      }
    } catch (error) {
      showStatus(error.message, true);
    }
  }

  async function moveSelectedImages(categoryId) {
    const ids = [...selectedIds];
    try {
      const report = await api(
        "/api/images/batch-move",
        jsonRequest("POST", { image_ids: ids, category_id: categoryId }),
      );
      setSelectedIds(new Set());
      const movingOutOfFilter =
        categoryFilter !== "" && String(categoryId ?? "") !== categoryFilter;
      const nextOffset =
        movingOutOfFilter && ids.length === images.length && offset > 0
          ? offset - pageSize
          : offset;
      await refreshGalleryPage(nextOffset);
      if (report.failed.length) {
        showStatus(
          `${report.succeeded.length} image(s) déplacée(s), ${report.failed.length} échec(s).`,
          true,
        );
      } else {
        showStatus(`${report.succeeded.length} image(s) déplacée(s).`);
      }
      setShowMoveDialog(false);
    } catch (error) {
      showStatus(error.message, true);
    }
  }

  async function downloadSelectedImages() {
    const ids = [...selectedIds];
    setDownloadingSelection(true);
    try {
      const response = await fetch("/api/images/batch-download", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_ids: ids }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.error || `Le téléchargement a échoué (${response.status}).`);
      }
      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = "galerie-images.zip";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 5000);
      showStatus(`${ids.length} image(s) ajoutée(s) à l'archive ZIP.`);
    } catch (error) {
      showStatus(error.message, true);
    } finally {
      setDownloadingSelection(false);
    }
  }

  if (selected) {
    return (
      <>
        <ImageDetailPage
          categoryName={categoryNames.get(selected.category_id)}
          image={selected}
          onBack={() => setSelected(null)}
          onChanged={() => refreshGalleryPage(offset)}
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
        <div className="gallery-bulk-actions">
          <label className="gallery-filter">
            Catégorie
            <select
              onChange={(event) => {
                const value = event.target.value;
                setCategoryFilter(value);
                setSelectedIds(new Set());
                onRefreshGallery(0, value || null, sortBy, appliedSearch).catch((error) =>
                  showStatus(error.message, true),
                );
              }}
              value={categoryFilter}
            >
              <option value="">Toutes les catégories</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {categoryPath(category)}
                </option>
              ))}
            </select>
          </label>
          <label className="gallery-filter">
            Trier par
            <select
              onChange={(event) => {
                const value = event.target.value;
                setSortBy(value);
                setSelectedIds(new Set());
                onRefreshGallery(0, categoryFilter || null, value, appliedSearch).catch((error) =>
                  showStatus(error.message, true),
                );
              }}
              value={sortBy}
            >
              <option value="created_desc">Plus récentes</option>
              <option value="created_asc">Plus anciennes</option>
              <option value="name_asc">Nom (A–Z)</option>
            </select>
          </label>
          {images.length > 0 && (
            <button className="button button-quiet" onClick={togglePageSelection} type="button">
              {allPageSelected ? "Tout désélectionner" : "Tout sélectionner"}
            </button>
          )}
          {selectedIds.size > 0 && (
            <>
              <span className="hint">{selectedIds.size} sélectionnée(s)</span>
              <button
                className="button button-danger"
                onClick={() => setConfirmBatchDelete(true)}
                type="button"
              >
                <Trash2 size={16} /> Supprimer la sélection
              </button>
              <button
                className="button button-secondary"
                onClick={() => setShowMoveDialog(true)}
                type="button"
              >
                Déplacer la sélection
              </button>
              <button
                className="button button-secondary"
                disabled={downloadingSelection}
                onClick={downloadSelectedImages}
                type="button"
              >
                <Download size={16} />
                {downloadingSelection ? "Préparation du ZIP…" : "Télécharger la sélection"}
              </button>
            </>
          )}
          <button className="button button-quiet" onClick={() => refreshGalleryPage(offset)} type="button">
            <RefreshCw className={loading ? "spin" : ""} size={16} /> Actualiser
          </button>
        </div>
      </div>

      <form className="gallery-search" onSubmit={submitSearch}>
        <label>
          Rechercher par nom de fichier
          <input
            maxLength="100"
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Ex. vacances"
            type="search"
            value={searchInput}
          />
        </label>
        <button className="button button-secondary" type="submit">Rechercher</button>
        {appliedSearch && (
          <button
            className="button button-quiet"
            onClick={() => {
              setSearchInput("");
              setAppliedSearch("");
              setSelectedIds(new Set());
              onRefreshGallery(0, categoryFilter || null, sortBy, "").catch((error) =>
                showStatus(error.message, true),
              );
            }}
            type="button"
          >
            Effacer
          </button>
        )}
      </form>

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
            <article
              className={`tile${selectedIds.has(image.id) ? " is-selected" : ""}`}
              key={image.id}
            >
              <label className="tile-select">
                <input
                  aria-label={`Sélectionner ${image.filename}`}
                  checked={selectedIds.has(image.id)}
                  onChange={() => toggleImageSelection(image.id)}
                  type="checkbox"
                />
              </label>
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
            onClick={() => refreshGalleryPage(Math.max(0, offset - pageSize))}
            type="button"
          >
            <ChevronLeft size={16} /> Précédent
          </button>
          <span className="hint">Page {Math.floor(offset / pageSize) + 1}</span>
          <button
            className="button button-quiet"
            disabled={!hasNextPage}
            onClick={() => refreshGalleryPage(offset + pageSize)}
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
      {confirmBatchDelete && (
        <ConfirmDialog
          message={`Cette action est définitive. Les images ayant des copies transformées ne seront pas supprimées.`}
          onCancel={() => setConfirmBatchDelete(false)}
          onConfirm={removeSelectedImages}
          title={`Supprimer ${selectedIds.size} image(s) sélectionnée(s) ?`}
        />
      )}
      {showMoveDialog && (
        <MoveToCategoryDialog
          categories={categories}
          onCancel={() => setShowMoveDialog(false)}
          onMove={moveSelectedImages}
          selectedCount={selectedIds.size}
        />
      )}
    </section>
  );
}
