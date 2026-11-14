import { useCallback, useEffect, useState } from "react";

import { api } from "./api.js";
import AuthPanel from "./components/AuthPanel.jsx";
import CategoryPanel from "./components/CategoryPanel.jsx";
import GalleryPanel from "./components/GalleryPanel.jsx";
import ImageUploader from "./components/ImageUploader.jsx";
import SearchPanel from "./components/SearchPanel.jsx";

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
        <div>
          <p className="eyebrow">Projet CBIR · Groupe G13</p>
          <h1>Galerie d’images</h1>
          <p className="subtitle">Explorez vos images et améliorez la recherche avec FRE.</p>
        </div>
        {user && (
          <div className="account-bar">
            <span>{user.username}</span>
            <button className="button button-quiet" onClick={handleLogout} type="button">
              Déconnexion
            </button>
          </div>
        )}
      </header>

      <main>
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
          <div className="workspace">
            <div className="workspace-column">
              <CategoryPanel
                categories={categories}
                onCategoriesChanged={refreshCategories}
                showStatus={showStatus}
              />
              <ImageUploader
                categories={categories}
                onUploaded={refreshGallery}
                showStatus={showStatus}
              />
              <GalleryPanel
                categories={categories}
                images={images}
                offset={galleryOffset}
                pageSize={GALLERY_PAGE_SIZE}
                onRefresh={refreshGallery}
                showStatus={showStatus}
              />
            </div>
            <SearchPanel showStatus={showStatus} />
          </div>
        ) : (
          <AuthPanel onAuthenticated={setUser} showStatus={showStatus} />
        )}
      </main>

      <footer>
        <span>CBIR · Feature Relevance Estimation · G13</span>
        <span>Les sessions de recherche expirent au redémarrage du serveur.</span>
      </footer>
    </>
  );
}
