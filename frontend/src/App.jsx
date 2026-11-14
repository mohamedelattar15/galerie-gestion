import { useCallback, useEffect, useState } from "react";

import { api } from "./api.js";
import AuthPanel from "./components/AuthPanel.jsx";
import Workspace from "./components/Workspace.jsx";

const GALLERY_PAGE_SIZE = 24;

export default function App() {
  const [user, setUser] = useState(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const [categories, setCategories] = useState([]);
  const [images, setImages] = useState([]);
  const [galleryOffset, setGalleryOffset] = useState(0);
  const [status, setStatus] = useState("");
  const [statusIsError, setStatusIsError] = useState(false);

  const showStatus = useCallback((message, isError = false) => {
    setStatus(message);
    setStatusIsError(isError);
  }, []);

  const refreshCategories = useCallback(async () => {
    const result = await api("/api/categories");
    setCategories(result);
  }, []);

  const refreshGallery = useCallback(async (offset = 0) => {
    const result = await api(`/api/images?limit=${GALLERY_PAGE_SIZE}&offset=${offset}`);
    setImages(result.images);
    setGalleryOffset(offset);
  }, []);

  useEffect(() => {
    api("/api/auth/me")
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setCheckingSession(false));
  }, []);

  useEffect(() => {
    if (!user) {
      setCategories([]);
      setImages([]);
      return;
    }
    Promise.all([refreshCategories(), refreshGallery()])
      .then(() => showStatus("Galerie prête."))
      .catch((error) => showStatus(error.message, true));
  }, [user, refreshCategories, refreshGallery, showStatus]);

  const handleLogout = async () => {
    try {
      await api("/api/auth/logout", { method: "POST" });
      setUser(null);
      showStatus("Vous êtes déconnecté.");
    } catch (error) {
      showStatus(error.message, true);
    }
  };

  return (
    <>
      <header className="site-header">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">G13</span>
          <div>
            <h1>Galerie d’images</h1>
            <p className="subtitle">Recherche par le contenu · Feature Relevance Estimation</p>
          </div>
        </div>
        {user && (
          <div className="account-bar">
            <span className="account-name">{user.username}</span>
            <button className="button button-quiet" onClick={handleLogout} type="button">
              Déconnexion
            </button>
          </div>
        )}
      </header>

      <main className="app-main">
        <p
          className={`status-message${statusIsError ? " is-error" : ""}`}
          role="status"
          aria-live="polite"
        >
          {checkingSession ? "Vérification de la session…" : status}
        </p>

        {checkingSession ? (
          <p className="empty-state">Chargement de votre espace…</p>
        ) : user ? (
          <Workspace
            categories={categories}
            images={images}
            offset={galleryOffset}
            pageSize={GALLERY_PAGE_SIZE}
            onCategoriesChanged={refreshCategories}
            onGalleryChanged={refreshGallery}
            showStatus={showStatus}
          />
        ) : (
          <AuthPanel onAuthenticated={setUser} showStatus={showStatus} />
        )}
      </main>

      <footer>
        <span>CBIR · Feature Relevance Estimation · G13</span>
        <span>Les sessions de recherche expirent au redémarrage du serveur.</span>
      </footer>    </>
  );
}
