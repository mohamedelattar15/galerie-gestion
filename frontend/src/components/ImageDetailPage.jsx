import {
  ArrowLeft,
  Download,
  ImagePlus,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "../api.js";

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
  const [direction, setDirection] = useState("horizontal");
  const [width, setWidth] = useState(Math.round(image.width / 2));
  const [height, setHeight] = useState(Math.round(image.height / 2));
  const [box, setBox] = useState([0, 0, image.width, image.height]);
  const [loading, setLoading] = useState(false);

  async function transform(event) {
    event.preventDefault();
    const body = { operation };
    if (operation === "rotate") body.degrees = Number(degrees);
    if (operation === "flip") body.direction = direction;
    if (operation === "resize") {
      body.width = Number(width);
      body.height = Number(height);
    }
    if (operation === "crop") body.box = box.map(Number);
    setLoading(true);
    try {
      const created = await api(`/api/images/${image.id}/transform`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      await onChanged(created);
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
          <select onChange={(event) => setOperation(event.target.value)} value={operation}>
            <option value="rotate">Rotation</option>
            <option value="flip">Miroir</option>
            <option value="resize">Redimensionner</option>
            <option value="crop">Recadrer</option>
          </select>
        </label>

        {operation === "rotate" && (
          <label>
            Angle (sens antihoraire)
            <select onChange={(event) => setDegrees(event.target.value)} value={degrees}>
              <option value="90">90°</option>
              <option value="180">180°</option>
              <option value="270">270°</option>
            </select>
          </label>
        )}

        {operation === "flip" && (
          <label>
            Direction
            <select onChange={(event) => setDirection(event.target.value)} value={direction}>
              <option value="horizontal">Horizontale</option>
              <option value="vertical">Verticale</option>
            </select>
          </label>
        )}

        {operation === "resize" && (
          <div className="field-row">
            <label>
              Largeur
              <input
                min="1"
                onChange={(event) => setWidth(event.target.value)}
                type="number"
                value={width}
              />
            </label>
            <label>
              Hauteur
              <input
                min="1"
                onChange={(event) => setHeight(event.target.value)}
                type="number"
                value={height}
              />
            </label>
          </div>
        )}

        {operation === "crop" && (
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
                  }}
                  type="number"
                  value={box[index]}
                />
              </label>
            ))}
          </div>
        )}

        <button className="button button-primary" disabled={loading} type="submit">
          {loading ? "Création…" : "Créer la copie transformée"}
        </button>
      </form>
    </section>
  );
}
