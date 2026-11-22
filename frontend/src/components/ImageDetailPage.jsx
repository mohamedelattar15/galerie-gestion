import {
  ArrowLeft,
  Download,
  Eye,
  ImagePlus,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "../api.js";
import BackgroundAnalysis from "./BackgroundAnalysis.jsx";

const HISTOGRAM_BLOCKS = [
  ["Teinte", 0, 16, "#287b78"],
  ["Saturation", 16, 32, "#4184a5"],
  ["Valeur", 32, 48, "#d18b37"],
];

const MOMENT_LABELS = [
  "Moyenne R",
  "Moyenne V",
  "Moyenne B",
  "Écart R",
  "Écart V",
  "Écart B",
  "Asym. R",
  "Asym. V",
  "Asym. B",
];

const GLCM_LABELS = ["Contraste", "Corrélation", "Énergie", "Homogénéité"];

export default function ImageDetailPage({
  image: initialImage,
  categoryName,
  onBack,
  onChanged,
  onDelete,
  onSearch,
  showStatus,
}) {
  const [image, setImage] = useState(initialImage);
  const [descriptor, setDescriptor] = useState(null);
  const [loading, setLoading] = useState(false);
  const [derived, setDerived] = useState(null);

  useEffect(() => {
    setImage(initialImage);
    setDerived(null);
  }, [initialImage]);

  const loadDescriptors = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api(`/api/images/${image.id}/descriptors`);
      setDescriptor(result.descriptors);
    } catch (error) {
      showStatus(error.message, true);
    } finally {
      setLoading(false);
    }
  }, [image.id, showStatus]);

  useEffect(() => {
    setDescriptor(null);
    loadDescriptors();
  }, [loadDescriptors]);

  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.key === "Escape") onBack();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onBack]);

  return (
    <div className="detail-page">
      <div className="detail-toolbar">
        <button className="button button-quiet" onClick={onBack} type="button">
          <ArrowLeft size={16} /> Retour à la galerie
        </button>
        <div className="detail-toolbar-actions">
          {onSearch && (
            <button className="button button-primary" onClick={() => onSearch(image)} type="button">
              <Search size={16} /> Chercher des similaires
            </button>
          )}
          <a
            className="button button-secondary"
            download={image.filename}
            href={`${image.file_url}?download=1`}
          >
            <Download size={16} /> Télécharger
          </a>
          <button className="button button-quiet" onClick={loadDescriptors} type="button">
            <RefreshCw className={loading ? "spin" : ""} size={16} /> Recalculer
          </button>
          <button className="button button-danger" onClick={onDelete} type="button">
            <Trash2 size={16} /> Supprimer
          </button>
        </div>
      </div>

      <div className="detail-layout">
        <aside className="detail-side">
          <div className="detail-image">
            <img alt={image.filename} src={image.file_url} />
          </div>

          <section className="panel detail-info">
            <h2>{image.filename}</h2>
            <dl className="detail-meta">
              <div>
                <dt>Dimensions</dt>
                <dd>
                  {image.width} × {image.height}
                </dd>
              </div>
              <div>
                <dt>Catégorie</dt>
                <dd>{categoryName ?? "Sans catégorie"}</dd>
              </div>
              <div>
                <dt>Identifiant</dt>
                <dd>#{image.id}</dd>
              </div>
              <div>
                <dt>Importée le</dt>
                <dd>{new Date(image.created_at).toLocaleString("fr-FR")}</dd>
              </div>
            </dl>
          </section>
        </aside>

        <div className="detail-main">
          <section className="panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Analyse visuelle</p>
                <h2>Descripteurs</h2>
              </div>
              {descriptor && (
                <span className="method-tag">
                  {descriptor.color_histogram.length + descriptor.lbp_histogram.length + 25} dimensions
                </span>
              )}
            </div>

            {loading && !descriptor ? (
              <div className="detail-loading">
                <span aria-hidden="true" className="spinner" />
                <p className="hint">Calcul des descripteurs…</p>
              </div>
            ) : descriptor ? (
              <DescriptorView descriptors={descriptor} />
            ) : (
              <p className="hint">Les descripteurs n’ont pas pu être chargés.</p>
            )}
          </section>

          <TransformPanel
            image={image}
            onChanged={async (created) => {
              setDerived(created);
              await onChanged();
            }}
            showStatus={showStatus}
          />

          <BackgroundAnalysis image={image} />

          {derived && (
            <section className="panel derived-panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Résultat</p>
                  <h2>Image transformée créée</h2>
                </div>
                <button
                  aria-label="Fermer le résultat"
                  className="inspector-close"
                  onClick={() => setDerived(null)}
                  type="button"
                >
                  ×
                </button>
              </div>
              <div className="derived-body">
                <img alt={derived.filename} src={derived.file_url} />
                <div className="derived-info">
                  <strong>{derived.filename}</strong>
                  <span className="hint">
                    {derived.width} × {derived.height} · dérivée de #{image.id}
                  </span>
                  <div className="derived-actions">
                    <button
                      className="button button-primary"
                      onClick={() => {
                        setDerived(null);
                        setImage(derived);
                      }}
                      type="button"
                    >
                      Ouvrir cette copie
                    </button>
                    <a
                      className="button button-quiet"
                      download={derived.filename}
                      href={`${derived.file_url}?download=1`}
                    >
                      Télécharger
                    </a>
                  </div>
                </div>
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}

function DescriptorView({ descriptors }) {
  return (
    <div className="descriptor-view">
      <section>
        <h3>Histogrammes HSV et LBP</h3>
        <div className="histogram-grid">
          {HISTOGRAM_BLOCKS.map(([label, start, end, color]) => (
            <figure key={label}>
              <figcaption>{label}</figcaption>
              <Histogram color={color} values={descriptors.color_histogram.slice(start, end)} />
            </figure>
          ))}
          <figure>
            <figcaption>LBP</figcaption>
            <Histogram color="#6d67a8" values={descriptors.lbp_histogram} />
          </figure>
        </div>
      </section>

      <section>
        <h3>Moments de couleur</h3>
        <dl className="metric-grid">
          {descriptors.color_moments.map((value, index) => (
            <div key={`moment-${index}`}>
              <dt>{MOMENT_LABELS[index]}</dt>
              <dd>{Number(value).toFixed(4)}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section>
        <h3>Texture GLCM</h3>
        <dl className="metric-grid">
          {descriptors.glcm.map((value, index) => (
            <div key={GLCM_LABELS[index]}>
              <dt>{GLCM_LABELS[index]}</dt>
              <dd>{Number(value).toFixed(4)}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section>
        <h3>Couleurs dominantes</h3>
        <div className="dominant-colors">
          {[0, 1, 2].map((index) => {
            const rgb = descriptors.dominant_colors.slice(index * 3, index * 3 + 3);
            const proportion = descriptors.dominant_colors[9 + index];
            const color = `rgb(${rgb.map((value) => Math.round(value * 255)).join(" ")})`;
            return (
              <div className="dominant-color" key={index}>
                <span aria-hidden="true" className="swatch" style={{ background: color }} />
                <span>{color}</span>
                <strong>{Math.round(proportion * 100)} %</strong>
              </div>
            );
          })}
        </div>
      </section>

      {descriptors.salient_color && (
        <section>
          <h3>Couleur la plus saturée</h3>
          <p className="hint">
            Les dominantes privilégient la surface : un détail vif minoritaire y échappe.
            Cette couleur signale la teinte la plus saturée de l’image.
          </p>
          <div className="dominant-colors">
            {(() => {
              const values = descriptors.salient_color;
              const rgb = values.slice(0, 3);
              const color = `rgb(${rgb.map((value) => Math.round(value * 255)).join(" ")})`;
              return (
                <div className="dominant-color">
                  <span aria-hidden="true" className="swatch" style={{ background: color }} />
                  <span>{color}</span>
                  <strong>{Math.round(values[3] * 100)} %</strong>
                </div>
              );
            })()}
          </div>
        </section>
      )}
    </div>
  );
}

function Histogram({ color, values }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!context) return;
    const max = Math.max(...values, 1e-8);
    const barWidth = canvas.width / values.length;
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = "#edf3f5";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = color;
    values.forEach((value, index) => {
      const barHeight = (value / max) * (canvas.height - 6);
      context.fillRect(
        index * barWidth + 1,
        canvas.height - barHeight,
        Math.max(1, barWidth - 2),
        barHeight,
      );
    });
  }, [color, values]);

  return (
    <canvas
      aria-label="Histogramme du descripteur"
      className="descriptor-chart"
      height="90"
      ref={canvasRef}
      width="300"
    />
  );
}

function TransformPanel({ image, onChanged, showStatus }) {
  const [operation, setOperation] = useState("rotate");
  const [degrees, setDegrees] = useState(90);
  const [rotationInterpolation, setRotationInterpolation] = useState("nearest");
  const [resizeInterpolation, setResizeInterpolation] = useState("lanczos");
  const [direction, setDirection] = useState("horizontal");
  const [width, setWidth] = useState(Math.max(1, Math.round(image.width / 2)));
  const [height, setHeight] = useState(Math.max(1, Math.round(image.height / 2)));
  const [box, setBox] = useState([0, 0, image.width, image.height]);
  const [keepAspectRatio, setKeepAspectRatio] = useState(true);
  const [cropRatio, setCropRatio] = useState("free");
  const [factor, setFactor] = useState(1);
  const [radius, setRadius] = useState(2);
  const [cutoff, setCutoff] = useState(0);
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const previewUrlRef = useRef(null);

  function clearPreview() {
    if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
    previewUrlRef.current = null;
    setPreviewUrl(null);
  }

  useEffect(
    () => () => {
      if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
    },
    [],
  );

  useEffect(() => {
    setWidth(Math.max(1, Math.round(image.width / 2)));
    setHeight(Math.max(1, Math.round(image.height / 2)));
    setBox([0, 0, image.width, image.height]);
    setCropRatio("free");
    clearPreview();
  }, [image.id, image.width, image.height]);

  function buildPayload() {
    const body = { operation };
    if (operation === "rotate") {
      body.degrees = Number(degrees);
      body.interpolation = rotationInterpolation;
    }
    if (operation === "flip") body.direction = direction;
    if (operation === "resize") {
      body.width = Number(width);
      body.height = Number(height);
      body.keep_aspect_ratio = keepAspectRatio;
      body.interpolation = resizeInterpolation;
    }
    if (operation === "crop") {
      if (cropRatio === "free") body.box = box.map(Number);
      else body.aspect_ratio = cropRatio;
    }
    if (["brightness", "contrast", "saturation", "sharpness"].includes(operation)) {
      body.factor = Number(factor);
    }
    if (operation === "blur") body.radius = Number(radius);
    if (operation === "autocontrast") body.cutoff = Number(cutoff);
    return body;
  }

  function updateResizeWidth(value) {
    setWidth(value);
    const numericWidth = Number(value);
    if (keepAspectRatio && numericWidth > 0) {
      setHeight(String(Math.max(1, Math.round(numericWidth * image.height / image.width))));
    }
    clearPreview();
  }

  function updateResizeHeight(value) {
    setHeight(value);
    const numericHeight = Number(value);
    if (keepAspectRatio && numericHeight > 0) {
      setWidth(String(Math.max(1, Math.round(numericHeight * image.width / image.height))));
    }
    clearPreview();
  }

  async function preview() {
    setPreviewLoading(true);
    try {
      const response = await fetch(`/api/images/${image.id}/transform/preview`, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildPayload()),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.error || `L'aperçu a échoué (${response.status}).`);
      }
      const nextUrl = URL.createObjectURL(await response.blob());
      if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
      previewUrlRef.current = nextUrl;
      setPreviewUrl(nextUrl);
    } catch (error) {
      showStatus(error.message, true);
    } finally {
      setPreviewLoading(false);
    }
  }

  async function transform(event) {
    event.preventDefault();
    const body = buildPayload();
    setLoading(true);
    try {
      const created = await api(`/api/images/${image.id}/transform`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      await onChanged(created);
      clearPreview();
      showStatus("Image dérivée créée; l’originale est conservée.");
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
          <p className="eyebrow">Édition</p>
          <h2>Créer une image transformée</h2>
        </div>
        <ImagePlus size={20} aria-hidden="true" />
      </div>
      <p className="hint">
        Une copie est créée et ajoutée à la galerie; l’image originale n’est jamais modifiée.
      </p>

      <form className="transform-panel" onSubmit={transform}>
        <label>
          Transformation
          <select
            onChange={(event) => {
              setOperation(event.target.value);
              clearPreview();
            }}
            value={operation}
          >
            <optgroup label="Géométrie">
              <option value="rotate">Rotation</option>
              <option value="flip">Miroir</option>
              <option value="resize">Redimensionner</option>
              <option value="crop">Recadrer</option>
            </optgroup>
            <optgroup label="Couleur">
              <option value="brightness">Luminosité</option>
              <option value="contrast">Contraste</option>
              <option value="saturation">Saturation</option>
              <option value="grayscale">Niveaux de gris</option>
              <option value="sepia">Sépia</option>
              <option value="autocontrast">Auto-contraste</option>
            </optgroup>
            <optgroup label="Filtres">
              <option value="sharpness">Netteté</option>
              <option value="blur">Flou gaussien</option>
            </optgroup>
          </select>
        </label>

        {operation === "rotate" && (
          <div className="field-row">
            <label>
              Angle libre (degrés antihoraires)
              <input
                max="360"
                min="-360"
                onChange={(event) => { setDegrees(event.target.value); clearPreview(); }}
                step="0.5"
                type="number"
                value={degrees}
              />
            </label>
            <label>
              Interpolation
              <select
                onChange={(event) => { setRotationInterpolation(event.target.value); clearPreview(); }}
                value={rotationInterpolation}
              >
                <option value="nearest">Voisin le plus proche</option>
                <option value="bilinear">Bilinéaire</option>
                <option value="bicubic">Bicubique</option>
                <option value="lanczos">Lanczos</option>
              </select>
            </label>
          </div>
        )}

        {operation === "flip" && (
          <label>
            Direction
            <select onChange={(event) => { setDirection(event.target.value); clearPreview(); }} value={direction}>
              <option value="horizontal">Horizontale</option>
              <option value="vertical">Verticale</option>
            </select>
          </label>
        )}

        {operation === "resize" && (
          <>
            <div className="field-row">
              <label>
                Largeur
                <input
                  min="1"
                  onChange={(event) => updateResizeWidth(event.target.value)}
                  type="number"
                  value={width}
                />
              </label>
              <label>
                Hauteur
                <input
                  min="1"
                  onChange={(event) => updateResizeHeight(event.target.value)}
                  type="number"
                  value={height}
                />
              </label>
            </div>
            <label className="transform-checkbox">
              <input
                checked={keepAspectRatio}
                onChange={(event) => {
                  const checked = event.target.checked;
                  setKeepAspectRatio(checked);
                  if (checked) {
                    const numericWidth = Number(width);
                    if (numericWidth > 0) {
                      setHeight(
                        String(Math.max(1, Math.round((numericWidth * image.height) / image.width))),
                      );
                    }
                  }
                  clearPreview();
                }}
                type="checkbox"
              />
              Conserver les proportions
            </label>
            <label>
              Interpolation
              <select
                onChange={(event) => {
                  setResizeInterpolation(event.target.value);
                  clearPreview();
                }}
                value={resizeInterpolation}
              >
                <option value="nearest">Voisin le plus proche</option>
                <option value="bilinear">Bilinéaire</option>
                <option value="bicubic">Bicubique</option>
                <option value="lanczos">Lanczos</option>
              </select>
            </label>
          </>
        )}

        {operation === "crop" && (
          <>
            <label>
              Format du recadrage
              <select
                onChange={(event) => { setCropRatio(event.target.value); clearPreview(); }}
                value={cropRatio}
              >
                <option value="free">Recadrage libre (coordonnées)</option>
                <option value="1:1">Carré 1:1</option>
                <option value="4:3">Paysage 4:3</option>
                <option value="16:9">Panoramique 16:9</option>
              </select>
            </label>
            {cropRatio === "free" ? (
              <div className="field-row field-row-4">
                {["Gauche", "Haut", "Droite", "Bas"].map((label, index) => (
                  <label key={label}>
                    {label}
                    <input
                      min="0"
                      onChange={(event) => {
                        const next = [...box];
                        next[index] = event.target.value;
                        setBox(next);
                        clearPreview();
                      }}
                      type="number"
                      value={box[index]}
                    />
                  </label>
                ))}
              </div>
            ) : (
              <p className="hint">Le recadrage {cropRatio} est centré automatiquement.</p>
            )}
          </>
        )}

        {["brightness", "contrast", "saturation", "sharpness"].includes(operation) && (
          <label className="transform-adjustment">
            {({ brightness: "Luminosité", contrast: "Contraste", saturation: "Saturation", sharpness: "Netteté" })[operation]}
            <span className="transform-adjustment-inputs">
              <input
                max="2"
                min="0"
                onChange={(event) => { setFactor(event.target.value); clearPreview(); }}
                step="0.05"
                type="range"
                value={factor}
              />
              <input
                aria-label="Facteur de réglage"
                max="2"
                min="0"
                onChange={(event) => { setFactor(event.target.value); clearPreview(); }}
                step="0.05"
                type="number"
                value={factor}
              />
            </span>
            <small className="hint">1 conserve la valeur d’origine.</small>
          </label>
        )}

        {operation === "blur" && (
          <label className="transform-adjustment">
            Rayon du flou
            <span className="transform-adjustment-inputs">
              <input
                max="20"
                min="0"
                onChange={(event) => { setRadius(event.target.value); clearPreview(); }}
                step="0.5"
                type="range"
                value={radius}
              />
              <input
                max="20"
                min="0"
                onChange={(event) => { setRadius(event.target.value); clearPreview(); }}
                step="0.5"
                type="number"
                value={radius}
              />
            </span>
          </label>
        )}

        {operation === "autocontrast" && (
          <label className="transform-adjustment">
            Coupure de l’auto-contraste (%)
            <span className="transform-adjustment-inputs">
              <input
                max="10"
                min="0"
                onChange={(event) => { setCutoff(event.target.value); clearPreview(); }}
                step="0.1"
                type="range"
                value={cutoff}
              />
              <input
                max="10"
                min="0"
                onChange={(event) => { setCutoff(event.target.value); clearPreview(); }}
                step="0.1"
                type="number"
                value={cutoff}
              />
            </span>
          </label>
        )}

        <div className="transform-actions">
          <button
            className="button button-secondary"
            disabled={loading || previewLoading}
            onClick={preview}
            type="button"
          >
            <Eye size={16} /> {previewLoading ? "Préparation de l’aperçu…" : "Aperçu"}
          </button>
          <button className="button button-primary" disabled={loading || previewLoading} type="submit">
          {loading ? "Création…" : "Créer la copie transformée"}
          </button>
        </div>
      </form>

      {previewUrl && (
        <div className="transform-preview-grid">
          <figure>
            <img alt={`Image originale ${image.filename}`} src={image.file_url} />
            <figcaption>Originale</figcaption>
          </figure>
          <figure>
            <img alt={`Aperçu transformé de ${image.filename}`} src={previewUrl} />
            <figcaption>Aperçu du résultat</figcaption>
          </figure>
        </div>
      )}
    </section>
  );
}
