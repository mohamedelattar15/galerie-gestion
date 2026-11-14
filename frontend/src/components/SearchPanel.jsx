import { useEffect, useMemo, useState } from "react";

import { api } from "../api.js";

export default function SearchPanel({ showStatus }) {
  const [queryFile, setQueryFile] = useState(null);
  const [queryPreview, setQueryPreview] = useState(null);
  const [topK, setTopK] = useState(10);
  const [sessionId, setSessionId] = useState(null);
  const [iteration, setIteration] = useState(0);
  const [results, setResults] = useState([]);
  const [feedback, setFeedback] = useState({});
  const [loading, setLoading] = useState(false);

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
    const previewUrl = URL.createObjectURL(queryFile);
    setQueryPreview(previewUrl);
    return () => URL.revokeObjectURL(previewUrl);
  }, [queryFile]);

  async function search(event) {
    event.preventDefault();
    if (!queryFile) return;
    const formData = new FormData();
    formData.append("query", queryFile);
    formData.append("top_k", String(topK));
    setLoading(true);
    try {
      const result = await api("/api/search", { method: "POST", body: formData });
      setSessionId(result.session_id);
      setIteration(0);
      setResults(result.results);
      setFeedback({});
      showStatus(`${result.results.length} résultat(s) affiché(s).`);
    } catch (error) {
      showStatus(error.message, true);
    } finally {
      setLoading(false);
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
    try {
      const result = await api("/api/search/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          relevant_ids: relevantIds,
          non_relevant_ids: nonRelevantIds,
          top_k: Number(topK),
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
    }
  }

  function chooseFeedback(imageId, value) {
    setFeedback((previous) => ({ ...previous, [imageId]: value }));
  }

  return (
    <section className="panel search-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Recherche par le contenu</p>
          <h2>Recherche similaire</h2>
        </div>
        <span className="method-tag">FRE · G13</span>
      </div>
      <p className="hint">
        La recherche utilise l’index GHIM-10K pré-calculé. Après les premiers résultats,
        marquez au moins deux images pertinentes pour appliquer FRE.
      </p>
      <form className="inline-form search-form" onSubmit={search}>
        <label className="file-label">
          Image requête
          <input
            accept="image/*"
            onChange={(event) => setQueryFile(event.target.files?.[0] || null)}
            required
            type="file"
          />
        </label>
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
        <button className="button button-primary" disabled={loading || !queryFile} type="submit">
          {loading && iteration === 0 ? "Recherche…" : "Rechercher"}
        </button>
      </form>

      {queryPreview && (
        <div className="query-preview">
          <img alt="Aperçu de l’image requête" src={queryPreview} />
          <span>{queryFile.name}</span>
        </div>
      )}

      {results.length > 0 && (
        <>
          <div className="feedback-summary" aria-live="polite">
            <strong>Itération {iteration}</strong>
            <span>{relevantCount} pertinente(s)</span>
            <span>{nonRelevantCount} non pertinente(s)</span>
          </div>
          <div className="image-grid search-results">
            {results.map((result) => (
              <SearchResultCard
                choice={feedback[result.id]}
                key={result.id}
                onChoose={chooseFeedback}
                result={result}
              />
            ))}
          </div>
          <div className="feedback-actions">
            <button
              className="button button-secondary"
              disabled={loading || relevantCount < 2}
              onClick={applyFeedback}
              type="button"
            >
              {loading && iteration > 0
                ? "Mise à jour FRE…"
                : `Appliquer FRE (${relevantCount} positives)`}
            </button>
            {relevantCount < 2 && (
              <span className="hint">Sélectionnez au moins deux images pertinentes.</span>
            )}
          </div>
        </>
      )}
      {!loading && sessionId && results.length === 0 && (
        <p className="empty-state">Aucun résultat disponible.</p>
      )}
    </section>
  );
}

function SearchResultCard({ choice, onChoose, result }) {
  const options = [
    ["relevant", "Pertinente"],
    ["non_relevant", "Non pertinente"],
  ];
  return (
    <article className={`image-card search-result-card${choice ? ` is-${choice}` : ""}`}>
      <img
        alt={`Résultat ${result.id}`}
        loading="lazy"
        src={`/api/indexed-images/${result.id}/file`}
      />
      <div className="image-card-body">
        <h3>{result.path}</h3>
        <p className="image-meta">
          {result.category} · distance {Number(result.distance).toFixed(4)}
        </p>
        <div aria-label={`Feedback pour ${result.path}`} className="feedback-options" role="radiogroup">
          {options.map(([value, label]) => (
            <label
              className={choice === value ? "is-selected" : ""}
              key={value}
            >
              <input
                checked={choice === value}
                name={`feedback-${result.id}`}
                onChange={() => onChoose(result.id, value)}
                type="radio"
                value={value}
              />
              {label}
            </label>
          ))}
        </div>
      </div>
    </article>
  );
}
