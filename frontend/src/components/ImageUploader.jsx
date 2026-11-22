import { UploadCloud, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { uploadWithProgress } from "../api.js";
import Dropzone from "./Dropzone.jsx";

const MAX_FILES = 32;

export default function ImageUploader({ categories, onUploaded, showStatus }) {
  const [files, setFiles] = useState([]);
  const [categoryId, setCategoryId] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(null);
  const categoryNames = new Map(categories.map((category) => [category.id, category.name]));

  const previews = useMemo(
    () => files.map((file) => ({ file, url: URL.createObjectURL(file) })),
    [files],
  );
  useEffect(() => () => previews.forEach((preview) => URL.revokeObjectURL(preview.url)), [previews]);

  function addFiles(incoming) {
    if (files.length + incoming.length > MAX_FILES) {
      showStatus(`Maximum ${MAX_FILES} images par import.`, true);
    }
    setFiles([...files, ...incoming].slice(0, MAX_FILES));
  }

  async function upload(event) {
    event.preventDefault();
    if (files.length === 0) return;
    setLoading(true);
    setUploadProgress(0);
    const formData = new FormData();
    for (const file of files) formData.append("images", file);
    if (categoryId) formData.append("category_id", categoryId);
    try {
      const result = await uploadWithProgress("/api/images", formData, setUploadProgress);
      const failures = result.results.filter((image) => image.error);
      const details = failures.map((image) => `${image.filename}: ${image.error}`).join(" · ");
      await onUploaded();
      showStatus(
        `${result.created} image(s) importée(s), ${result.failed} échec(s).${details ? ` ${details}` : ""}`,
        failures.length > 0,
      );
      setFiles([]);
    } catch (error) {
      showStatus(error.message, true);
    } finally {
      setLoading(false);
      setUploadProgress(null);
    }
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Collection</p>
          <h2>Importer des images</h2>
        </div>
        {files.length > 0 && (
          <span className="method-tag">
            {files.length}/{MAX_FILES}
          </span>
        )}
      </div>

      <form aria-busy={loading} className="stack" onSubmit={upload}>
        <Dropzone
          hint={`Glissez-déposez ou cliquez · jusqu’à ${MAX_FILES} images`}
          label="Ajouter des images"
          multiple
          onFiles={addFiles}
        />

        {previews.length > 0 && (
          <div className="thumb-strip">
            {previews.map(({ file, url }, index) => (
              <figure className="thumb" key={`${file.name}-${index}`}>
                <img alt={file.name} src={url} />
                <button
                  aria-label={`Retirer ${file.name}`}
                  onClick={() => setFiles(files.filter((_, position) => position !== index))}
                  type="button"
                >
                  <X size={12} />
                </button>
              </figure>
            ))}
          </div>
        )}

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

        <button
          aria-busy={loading}
          className="button button-primary"
          disabled={loading || files.length === 0}
          type="submit"
        >
          {loading ? <span aria-hidden="true" className="button-spinner" /> : <UploadCloud size={16} />}
          {loading
            ? uploadProgress >= 100
              ? "Traitement des images…"
              : `Envoi ${uploadProgress ?? 0} %`
            : "Importer"}
        </button>
        {loading && (
          <div aria-label="Progression de l’import" className="upload-progress" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow={uploadProgress ?? 0}>
            <div className="upload-progress-track">
              <span style={{ width: `${uploadProgress ?? 0}%` }} />
            </div>
            <span className="hint">
              {uploadProgress >= 100 ? "Fichiers transmis, traitement en cours…" : `${uploadProgress ?? 0} % envoyé`}
            </span>
          </div>
        )}
      </form>
    </section>
  );
}
