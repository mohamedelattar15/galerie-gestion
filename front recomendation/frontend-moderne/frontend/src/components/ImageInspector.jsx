import {
  Crop,
  Download,
  FlipHorizontal2,
  RotateCw,
  Scaling,
  Trash2,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "../api.js";

const HISTOGRAM_BLOCKS = [
  ["Teinte", 0, 16, "var(--chart-1)"],
  ["Saturation", 16, 32, "var(--chart-2)"],
  ["Valeur", 32, 48, "var(--chart-3)"],
];

const GLCM_LABELS = ["Contraste", "Corrélation", "Énergie", "Homogénéité"];

export default function ImageInspector({ image, categoryName, onClose, onChanged, onDelete, showStatus }) {
  const [tab, setTab] = useState("descriptors");
  const [descriptor, setDescriptor] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setTab("descriptors");
    setDescriptor(null);
  }, [image.id]);

  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  async function loadDescriptors() {
    setLoading(true);
    try {
      const result = await api(`/api/images/${image.id}/descriptors`);
      setDescriptor(result.descriptors);
    } catch (error) {
      showStatus(error.message, true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="drawer-backdrop" onClick={onClose} role="presentation">
      <aside
        aria-label={`Détails de ${image.filename}`}
        className="drawer"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="drawer-header">
          <div>
            <h2>{image.filename}</h2>
            <p className="muted small">
              {image.width} × {image.height}
              {categoryName ? ` · ${categoryName}` : ""}
            </p>
          </div>
          <button aria-label="Fermer" className="icon-btn" onClick={onClose} type="button">
            <X size={18} />
          </button>
        </header>

        <img alt={image.filename} className="drawer-preview" src={image.file_url} />

        <div className="drawer-actions">
          <a className="btn btn-ghost" download={image.filename} href={`${image.file_url}?download=1`}>
            <Download size={16} /> Télécharger
          </a>
          <button className="btn btn-danger-ghost" onClick={onDelete} type="button">
            <Trash2 size={16} /> Supprimer
          </button>
        </div>

        <nav aria-label="Détails de l’image" className="segmented drawer-tabs" role="tablist">
          {[
            ["descriptors", "Descripteurs"],
            ["transform", "Transformations"],
          ].map(([id, label]) => (
            <button
              aria-selected={tab === id}
              className={tab === id ? "is-active" : ""}
              key={id}
              onClick={() => setTab(id)}
              role="tab"
              type="button"
            >
              {label}
            </button>
          ))}
        </nav>

        <div className="drawer-body">
          {tab === "descriptors" &&
            (descriptor ? (
              <DescriptorView descriptors={descriptor} />
            ) : (
              <div className="drawer-placeholder">
                <p className="muted small">
                  Les descripteurs sont calculés à la demande : histogrammes HSV, moments de couleur,
                  couleurs dominantes, GLCM et LBP.
                </p>
                <button
                  className="btn btn-primary"
                  disabled={loading}
                  onClick={loadDescriptors}
                  type="button"
                >
                  {loading ? "Calcul en cours…" : "Calculer les descripteurs"}
                </button>
              </div>
            ))}

          {tab === "transform" && (
            <TransformPanel
              image={image}
              onChanged={onChanged}
              showStatus={showStatus}
            />
          )}
        </div>
      </aside>
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
            <Histogram color="var(--chart-4)" values={descriptors.lbp_histogram} />
          </figure>
        </div>
      </section>

      <section>
        <h3>Moments de couleur</h3>
        <dl className="metric-grid">
          {descriptors.color_moments.map((value, index) => (
            <div key={`moment-${index}`}>
              <dt>{["Moyenne R", "Moyenne V", "Moyenne B", "Écart R", "Écart V", "Écart B", "Asym. R", "Asym. V", "Asym. B"][index]}</dt>
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
          <div className="dominant-bar">
            {[0, 1, 2].map((index) => {
              const rgb = descriptors.dominant_colors.slice(index * 3, index * 3 + 3);
              const proportion = descriptors.dominant_colors[9 + index];
              const color = `rgb(${rgb.map((value) => Math.round(value * 255)).join(" ")})`;
              return <span key={index} style={{ background: color, flex: Math.max(proportion, 0.02) }} />;
            })}
          </div>
          {[0, 1, 2].map((index) => {
            const rgb = descriptors.dominant_colors.slice(index * 3, index * 3 + 3);
            const proportion = descriptors.dominant_colors[9 + index];
            const color = `rgb(${rgb.map((value) => Math.round(value * 255)).join(" ")})`;
            return (
              <div className="dominant-color" key={`row-${index}`}>
                <span aria-hidden="true" className="swatch" style={{ background: color }} />
                <code>{color}</code>
                <strong>{Math.round(proportion * 100)} %</strong>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}

function Histogram({ color, values }) {
  const max = Math.max(...values, 1e-8);
  return (
    <div aria-label="Histogramme du descripteur" className="histogram" role="img">
      {values.map((value, index) => (
        <span key={index} style={{ background: color, height: `${Math.max(3, (value / max) * 100)}%` }} />
      ))}
    </div>
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
      await api(`/api/images/${image.id}/transform`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      await onChanged();
      showStatus("Image dérivée créée; l’originale est conservée.");
    } catch (error) {
      showStatus(error.message, true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="stack" onSubmit={transform}>
      <p className="muted small">
        Une copie est créée et ajoutée à la galerie; l’image originale n’est jamais modifiée.
      </p>
      <div aria-label="Transformation" className="op-picker" role="radiogroup">
        {[
          ["rotate", "Rotation", RotateCw],
          ["flip", "Miroir", FlipHorizontal2],
          ["resize", "Taille", Scaling],
          ["crop", "Recadrer", Crop],
        ].map(([value, label, Icon]) => (
          <button
            aria-checked={operation === value}
            className={operation === value ? "is-active" : ""}
            key={value}
            onClick={() => setOperation(value)}
            role="radio"
            type="button"
          >
            <Icon size={18} />
            <span>{label}</span>
          </button>
        ))}
      </div>

      {operation === "rotate" && (
        <label className="field">
          <span>Angle (sens antihoraire)</span>
          <select onChange={(event) => setDegrees(event.target.value)} value={degrees}>
            <option value="90">90°</option>
            <option value="180">180°</option>
            <option value="270">270°</option>
          </select>
        </label>
      )}

      {operation === "flip" && (
        <label className="field">
          <span>Direction</span>
          <select onChange={(event) => setDirection(event.target.value)} value={direction}>
            <option value="horizontal">Horizontale</option>
            <option value="vertical">Verticale</option>
          </select>
        </label>
      )}

      {operation === "resize" && (
        <div className="field-row">
          <label className="field">
            <span>Largeur</span>
            <input min="1" onChange={(event) => setWidth(event.target.value)} type="number" value={width} />
          </label>
          <label className="field">
            <span>Hauteur</span>
            <input min="1" onChange={(event) => setHeight(event.target.value)} type="number" value={height} />
          </label>
        </div>
      )}

      {operation === "crop" && (
        <div className="field-row field-row-4">
          {["Gauche", "Haut", "Droite", "Bas"].map((label, index) => (
            <label className="field" key={label}>
              <span>{label}</span>
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

      <button className="btn btn-primary" disabled={loading} type="submit">
        {loading ? "Création…" : "Créer la copie transformée"}
      </button>
    </form>
  );
}
