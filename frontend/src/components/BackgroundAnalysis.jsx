import { useEffect, useState } from "react";

import { api } from "../api.js";

const MODE_LABELS = {
  adaptive: "Adaptatif (segmentation si le fond est distinct)",
  variance: "Variance (pondération des zones détaillées)",
};

export default function BackgroundAnalysis({ image }) {
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    api(`/api/images/${image.id}/analysis`)
      .then((result) => {
        if (active) setAnalysis(result);
      })
      .catch((requestError) => {
        if (active) setError(requestError.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [image.id]);

  return (
    <section className="panel background-analysis">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Analyse du fond</p>
          <h2>Séparabilité et segmentation</h2>
        </div>
      </div>
      {loading ? (
        <p className="hint">Analyse de l’image…</p>
      ) : error ? (
        <p className="hint" role="status">{error}</p>
      ) : (
        <>
          <div className="background-analysis-summary">
            <span>
              Ratio de séparabilité : <strong>{analysis.separability_ratio.toFixed(2)}</strong>
            </span>
            <span>
              Mode conseillé : <strong>{MODE_LABELS[analysis.recommended_mode]}</strong>
            </span>
            {analysis.mask_available ? (
              <span>
                Surface détectée comme objet : <strong>{Math.round(analysis.mask_fraction * 100)} %</strong>
              </span>
            ) : (
              <span className="hint">Le masque est jugé trop incertain pour être affiché.</span>
            )}
          </div>
          <div className="background-analysis-grid">
            <figure>
              <img alt={`Image originale ${image.filename}`} src={image.file_url} />
              <figcaption>Image originale</figcaption>
            </figure>
            <figure>
              <img alt="Carte des différences avec la couleur du bord" src={analysis.background_map_url} />
              <figcaption>Différence estimée avec le fond du bord</figcaption>
            </figure>
            {analysis.mask_url && (
              <figure>
                <img alt="Masque segmenté, blanc pour l’objet et noir pour le fond" src={analysis.mask_url} />
                <figcaption>Masque : blanc = objet, noir = fond</figcaption>
              </figure>
            )}
          </div>
          <p className="hint background-analysis-note">
            La carte et le masque utilisent la couleur moyenne des bords comme estimation du fond.
            Ils illustrent le mode adaptatif et ne remplacent pas un outil de segmentation sémantique.
          </p>
        </>
      )}
    </section>
  );
}
