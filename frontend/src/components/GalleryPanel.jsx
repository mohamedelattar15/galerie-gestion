import { useEffect, useRef, useState } from "react";

import { api } from "../api.js";

export default function GalleryPanel({
  categories,
  images,
  offset,
  pageSize,
  onRefresh,
  showStatus,
}) {
  const categoryNames = new Map(categories.map((category) => [category.id, category.name]));
  const hasPreviousPage = offset > 0;
  const hasNextPage = images.length === pageSize;

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
            <ImageCard
              categoryName={categoryNames.get(image.category_id)}
              image={image}
              key={image.id}
              onRefresh={() => onRefresh(offset)}
              showStatus={showStatus}
            />
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
    </section>
  );
}

function ImageCard({ categoryName, image, onRefresh, showStatus }) {
  const [descriptor, setDescriptor] = useState(null);
  const [loadingDescriptors, setLoadingDescriptors] = useState(false);

  async function loadDescriptors() {
    setLoadingDescriptors(true);
    try {
      const result = await api(`/api/images/${image.id}/descriptors`);
      setDescriptor(result.descriptors);
    } catch (error) {
      showStatus(error.message, true);
    } finally {
      setLoadingDescriptors(false);
    }
  }

  async function removeImage() {
    if (!window.confirm(`Supprimer « ${image.filename} » ?`)) return;
    try {
      await api(`/api/images/${image.id}`, { method: "DELETE" });
      await onRefresh();
      showStatus("Image supprimée.");
    } catch (error) {
      showStatus(error.message, true);
    }
  }

  return (
    <article className="image-card">
      <img alt={image.filename} loading="lazy" src={image.file_url} />
      <div className="image-card-body">
        <h3>{image.filename}</h3>
        <p className="image-meta">
          {image.width} × {image.height}
          {categoryName ? ` · ${categoryName}` : ""}
        </p>
        <div className="card-actions">
          <a
            className="button button-quiet"
            download={image.filename}
            href={`${image.file_url}?download=1`}
          >
            Télécharger
          </a>
          <button className="button button-quiet" onClick={removeImage} type="button">
            Supprimer
          </button>
        </div>
        <details className="transform-box">
          <summary>Voir les descripteurs</summary>
          {descriptor ? (
            <DescriptorView descriptors={descriptor} />
          ) : (
            <button
              className="button button-secondary descriptor-load"
              disabled={loadingDescriptors}
              onClick={loadDescriptors}
              type="button"
            >
              {loadingDescriptors ? "Calcul…" : "Calculer les descripteurs"}
            </button>
          )}
        </details>
        <TransformForm image={image} onRefresh={onRefresh} showStatus={showStatus} />
      </div>
    </article>
  );
}

function TransformForm({ image, onRefresh, showStatus }) {
  const [operation, setOperation] = useState("rotate");
  const [width, setWidth] = useState(512);
  const [height, setHeight] = useState(512);
  const [left, setLeft] = useState(0);
  const [upper, setUpper] = useState(0);
  const [right, setRight] = useState(image.width);
  const [lower, setLower] = useState(image.height);
  const [direction, setDirection] = useState("horizontal");
  const [loading, setLoading] = useState(false);

  async function transform(event) {
    event.preventDefault();
    const body = { operation };
    if (operation === "rotate") body.degrees = 90;
    if (operation === "flip") body.direction = direction;
    if (operation === "resize") {
      body.width = Number(width);
      body.height = Number(height);
    }
    if (operation === "crop") {
      body.box = [Number(left), Number(upper), Number(right), Number(lower)];
    }
    setLoading(true);
    try {
      await api(`/api/images/${image.id}/transform`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      await onRefresh();
      showStatus("Image dérivée créée; l’originale est conservée.");
    } catch (error) {
      showStatus(error.message, true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <details className="transform-box">
      <summary>Créer une image transformée</summary>
      <form className="transform-form" onSubmit={transform}>
        <label>
          Transformation
          <select onChange={(event) => setOperation(event.target.value)} value={operation}>
            <option value="rotate">Rotation 90°</option>
            <option value="flip">Miroir</option>
            <option value="resize">Redimensionner</option>
            <option value="crop">Recadrer</option>
          </select>
        </label>
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
          <>
            <NumberField label="Largeur" min={1} onChange={setWidth} value={width} />
            <NumberField label="Hauteur" min={1} onChange={setHeight} value={height} />
          </>
        )}
        {operation === "crop" && (
          <>
            <NumberField label="Gauche" min={0} onChange={setLeft} value={left} />
            <NumberField label="Haut" min={0} onChange={setUpper} value={upper} />
            <NumberField label="Droite" min={1} onChange={setRight} value={right} />
            <NumberField label="Bas" min={1} onChange={setLower} value={lower} />
          </>
        )}
        <button className="button button-secondary" disabled={loading} type="submit">
          {loading ? "Création…" : "Créer une copie"}
        </button>
      </form>
    </details>
  );
}

function NumberField({ label, min, onChange, value }) {
  return (
    <label>
      {label}
      <input
        min={min}
        onChange={(event) => onChange(event.target.value)}
        required
        type="number"
        value={value}
      />
    </label>
  );
}

function DescriptorView({ descriptors }) {
  return (
    <div className="descriptor-panel">
      <h4>Histogrammes HSV</h4>
      {[
        ["Teinte", descriptors.color_histogram.slice(0, 16), "#287b78"],
        ["Saturation", descriptors.color_histogram.slice(16, 32), "#4184a5"],
        ["Valeur", descriptors.color_histogram.slice(32, 48), "#d18b37"],
        ["LBP", descriptors.lbp_histogram, "#6d67a8"],
      ].map(([label, values, color]) => (
        <div key={label}>
          <h4>{label}</h4>
          <Histogram color={color} values={values} />
        </div>
      ))}
      <h4>Moments et texture GLCM</h4>
      <dl className="descriptor-values">
        {[
          ...descriptors.color_moments.map((value, index) => [`Moment ${index + 1}`, value]),
          ...descriptors.glcm.map((value, index) => [
            ["Contraste", "Corrélation", "Énergie", "Homogénéité"][index],
            value,
          ]),
        ].map(([label, value]) => (
          <div className="descriptor-value" key={label}>
            <dt>{label}</dt>
            <dd>{Number(value).toFixed(4)}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function Histogram({ color, values }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef?.current;
    const context = canvas?.getContext("2d");
    if (!context) return;
    const max = Math.max(...values, 1e-8);
    const barWidth = canvas.width / values.length;
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = "#edf3f5";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = color;
    values.forEach((value, index) => {
      const barHeight = (value / max) * (canvas.height - 8);
      context.fillRect(
        index * barWidth + 1,
        canvas.height - barHeight,
        Math.max(1, barWidth - 2),
        barHeight,
      );
    });
  }, [canvasRef, color, values]);

  return (
    <canvas
      aria-label="Histogramme du descripteur"
      className="descriptor-chart"
      height="100"
      ref={canvasRef}
      width="320"
    />
  );
}
