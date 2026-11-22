import { Check, RotateCcw, Sparkles, ThumbsDown, ThumbsUp, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { api } from "../api.js";
import Dropzone from "./Dropzone.jsx";

const MODE_LABELS = {
  global: "Global (référence)",
  variance: "Pondération par variance",
  adaptive: "Adaptatif (segmentation)",
};

export default function SearchPanel({ galleryImage, onClearGalleryImage, showStatus }) {
  const [queryFile, setQueryFile] = useState(null);
  const [queryPreview, setQueryPreview] = useState(null);
  const [topK, setTopK] = useState(10);
  const [sessionId, setSessionId] = useState(null);
  const [iteration, setIteration] = useState(0);
  const [results, setResults] = useState([]);
  const [feedback, setFeedback] = useState({});
  const [loading, setLoading] = useState(false);
  const [loadingAction, setLoadingAction] = useState(null);
  const [corpus, setCorpus] = useState(null);
  const [mode, setMode] = useState("global");
  const [availableModes, setAvailableModes] = useState(["global"]);

  const galleryQuery = galleryImage?.id ?? null;

  const relevantCount = useMemo(
    () => Object.values(feedback).filter((value) => value === "relevant").length,
    [feedback],
  );
  const nonRelevantCount = useMemo(
    () => Object.values(feedback).filter((value) => value === "non_relevant").length,
    [feedback],
  );

  useEffect(() => {
    if (!queryFile) {
      setQueryPreview(null);
      return undefined;
    }
    const url = URL.createObjectURL(queryFile);
    setQueryPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [queryFile]);

  useEffect(() => {
    api("/health")
      .then((result) => {
        const modes = result?.descriptor_modes ?? [];
        if (modes.length > 0) setAvailableModes(modes);
      })
      .catch(() => setAvailableModes(["global"]));
  }, []);

  function reset() {
    setQueryFile(null);
    setSessionId(null);
    setResults([]);
    setFeedback({});
    setIteration(0);
    setCorpus(null);
    onClearGalleryImage?.();
  }

  async function search(event) {
    event.preventDefault();
    if (!queryFile && !galleryQuery) return;
    const formData = new FormData();
    if (galleryQuery) formData.append("gallery_image_id", String(galleryQuery));
    else formData.append("query", queryFile);
    formData.append("top_k", String(topK));
    formData.append("descriptor_mode", mode);
    setLoading(true);
    setLoadingAction("search");
    try {
      const result = await api("/api/search", { method: "POST", body: formData });
      setSessionId(result.session_id);
      setIteration(0);
      setResults(result.results);
      setFeedback({});
      setCorpus(result.corpus ?? null);
      showStatus(`${result.results.length} résultat(s) affiché(s).`);
    } catch (error) {
      showStatus(error.message, true);
    } finally {
      setLoading(false);
      setLoadingAction(null);
    }
  }

  async function applyFeedback() {
    if (!sessionId || relevantCount < 2) return;
    const relevantIds = [];
    const nonRelevantIds = [];
    for (const [imageId, choice] of Object.entries(feedback)) {
      if (choice === "relevant") relevantIds.push(Number(imageId));
      if (choice === "non_relevant") nonRelevantIds.push(Number(imageId));
    }
    setLoading(true);
    setLoadingAction("feedback");
    try {
      const result = await api("/api/search/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          relevant_ids: relevantIds,
          non_relevant_ids: nonRelevantIds,
          top_k: Number(topK),
          descriptor_mode: mode,
        }),
      });
      setIteration(result.iteration);
      setResults(result.results);
      setFeedback({});
      showStatus(
        `Itération FRE ${result.iteration} terminée. ${result.ignored_non_relevant_count} image(s) non pertinente(s) reçue(s); la formule FRE de G13 met à jour les poids à partir des positives.`,
      );
    } catch (error) {
      showStatus(error.message, true);
    } finally {
      setLoading(false);
      setLoadingAction(null);
    }
  }

  function toggleFeedback(imageId, value) {
    setFeedback((previous) => {
      const next = { ...previous };
      if (next[imageId] === value) delete next[imageId];
      else next[imageId] = value;
      return next;
    });
  }

  return (
    <div className="search-layout">
      <aside className="panel search-query">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Recherche par le contenu</p>
            <h2>Image requête</h2>
          </div>
          <span className="method-tag">FRE · G13</span>
        </div>

        <form aria-busy={loadingAction === "search"} className="stack search-form" onSubmit={search}>
          {galleryImage ? (
            <div className="gallery-query">
              <img alt={galleryImage.filename} src={galleryImage.file_url} />
              <div>
                <strong>{galleryImage.filename}</strong>
                <span className="hint">Image de votre galerie</span>
              </div>
              <button
                aria-label="Retirer l’image de la galerie"
                className="inspector-close"
                onClick={onClearGalleryImage}
                type="button"
              >
                ×
              </button>
            </div>
          ) : (
            <Dropzone
              compact={Boolean(queryPreview)}
              hint="Glissez-déposez ou cliquez"
              label="Choisir une image"
              onFiles={(files) => setQueryFile(files[0])}
            >
              {queryPreview && (
                <div className="query-preview">
                  <img alt="Aperçu de l’image requête" src={queryPreview} />
                  <span>{queryFile.name}</span>
                </div>
              )}
            </Dropzone>
          )}

          <label>
            Nombre de résultats
            <input
              max={100}
              min={1}
              onChange={(event) => setTopK(event.target.value)}
              required
              type="number"
              value={topK}
            />
          </label>

          {availableModes.length > 1 && (
            <label>
              Traitement du fond
              <select onChange={(event) => setMode(event.target.value)} value={mode}>
                {availableModes.map((name) => (
                  <option key={name} value={name}>
                    {MODE_LABELS[name] ?? name}
                  </option>
                ))}
              </select>
            </label>
          )}

          <button
            className="button button-primary"
            disabled={loading || (!queryFile && !galleryQuery)}
            type="submit"
          >
            {loadingAction === "search" ? (
              <><span aria-hidden="true" className="button-spinner" /> Recherche en cours…</>
            ) : (
              <><Sparkles size={16} /> Lancer la recherche</>
            )}
          </button>
          {sessionId && (
            <button className="button button-quiet" onClick={reset} type="button">
              <RotateCcw size={16} /> Nouvelle recherche
            </button>
          )}
        </form>

        <details className="search-guide">
          <summary>Étapes de recherche et retour FRE</summary>
          <div className="search-guide-body">
            <p className="hint">
              Catalogue : <strong>GHIM-10K</strong>
              {corpus
                ? ` · ${corpus.images.toLocaleString("fr-FR")} images · ${corpus.categories} catégories`
                : " · 10 000 images · 20 catégories"}
            </p>
            <ol>
              <li>Choisissez une image pour lancer la recherche visuelle.</li>
              <li>Marquez au moins deux résultats comme pertinentes.</li>
              <li>Appliquez FRE pour ajuster le classement.</li>
            </ol>
            <p className="search-guide-note">
              Les votes « non pertinente » sont enregistrés, mais FRE pour G13 met à jour les poids à partir des images pertinentes.
            </p>
          </div>
        </details>
      </aside>

      <section aria-busy={loading} className="search-results">
        {results.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon">
              <Sparkles size={26} />
            </span>
            <h3>{sessionId && !loading ? "Aucun résultat disponible" : "Prêt à chercher"}</h3>
            <p className="hint">
              Choisissez une image requête pour afficher les images les plus similaires.
            </p>
          </div>
        ) : (
          <>
            <div className="results-head">
              <div className="results-title">
                <p className="eyebrow">Résultats de recherche</p>
                <h2>Images similaires</h2>
                <p className="hint">Classement par contenu visuel · la distance la plus faible indique l’image la plus proche.</p>
              </div>
              <div className="results-badges">
                <span className="method-tag">{iteration === 0 ? "Recherche initiale" : `Itération FRE ${iteration}`}</span>
                <span className="result-count">{results.length} / {topK} résultats</span>
                <span className="result-mode">{MODE_LABELS[mode] ?? mode}</span>
              </div>
            </div>

            <div className={`result-grid${loading ? " is-loading" : ""}`}>
              {results.map((result, index) => (
                <ResultCard
                  choice={feedback[result.id]}
                  key={`${iteration}-${result.id}`}
                  onToggle={toggleFeedback}
                  rank={index + 1}
                  result={result}
                  style={{ "--result-order": index }}
                />
              ))}
            </div>

            <div className="feedback-bar">
              <div className="feedback-progress">
                <div className="feedback-counts">
                  <span className="feedback-positive-count">
                    <ThumbsUp size={15} /> {relevantCount} <b>pertinente{relevantCount > 1 ? "s" : ""}</b>
                  </span>
                  <span className="feedback-negative-count">
                    <ThumbsDown size={15} /> {nonRelevantCount} <b>non pertinente{nonRelevantCount > 1 ? "s" : ""}</b>
                  </span>
                </div>
                <div aria-live="polite" className="feedback-instruction">
                  {relevantCount < 2
                    ? `Sélectionnez encore ${2 - relevantCount} image${2 - relevantCount > 1 ? "s" : ""} pertinente${2 - relevantCount > 1 ? "s" : ""} pour activer FRE.`
                    : "Votre sélection est prête pour l’itération FRE."}
                </div>
              </div>
              <button
                className="button button-primary"
                disabled={loading || relevantCount < 2}
                onClick={applyFeedback}
                type="button"
              >
                {loadingAction === "feedback" ? (
                  <><span aria-hidden="true" className="button-spinner" /> Mise à jour du classement…</>
                ) : (
                  <><Check size={16} /> Appliquer FRE</>
                )}
              </button>
            </div>
          </>
        )}
      </section>
    </div>
  );
}

function ResultCard({ result, rank, choice, onToggle, style }) {
  return (
    <article className={`result${choice ? ` is-${choice}` : ""}`} style={style}>
      <div className="result-media">
        <img
          alt={`Résultat ${result.id}`}
          loading="lazy"
          src={`/api/indexed-images/${result.id}/file`}
        />
        <span className="rank">#{rank}</span>
        {choice && (
          <span className="result-flag">
            {choice === "relevant" ? <ThumbsUp size={14} /> : <X size={14} />}
          </span>
        )}
      </div>
      <div className="result-body">
        <div className="result-meta">
          <strong title={result.path}>{result.category}</strong>
          <small title="Une distance plus faible indique une image plus proche de la requête.">
            Distance {Number(result.distance).toFixed(4)}
          </small>
        </div>
        <div aria-label={`Évaluer la pertinence de ${result.path}`} className="vote">
          <button
            aria-pressed={choice === "relevant"}
            className={choice === "relevant" ? "is-on-good" : ""}
            onClick={() => onToggle(result.id, "relevant")}
            type="button"
          >
            <ThumbsUp size={15} /> Pertinente
          </button>
          <button
            aria-pressed={choice === "non_relevant"}
            className={choice === "non_relevant" ? "is-on-bad" : ""}
            onClick={() => onToggle(result.id, "non_relevant")}
            type="button"
          >
            <ThumbsDown size={15} /> Non pertinente
          </button>
        </div>
      </div>
    </article>
  );
}
