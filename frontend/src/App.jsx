import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "./api.js";
import AuthPanel from "./components/AuthPanel.jsx";
import Toasts from "./components/Toasts.jsx";
import Workspace from "./components/Workspace.jsx";
import { useTheme } from "./hooks/useTheme.js";

const GALLERY_PAGE_SIZE = 24;

export default function App() {
  const [theme, toggleTheme] = useTheme();
  const [user, setUser] = useState(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const [categories, setCategories] = useState([]);
  const [images, setImages] = useState([]);
  const [galleryOffset, setGalleryOffset] = useState(0);
  const [galleryLoading, setGalleryLoading] = useState(false);
  const galleryCategoryRef = useRef(null);
  const gallerySortRef = useRef("created_desc");
  const gallerySearchRef = useRef("");
  const [toasts, setToasts] = useState([]);
  const toastId = useRef(0);

  const dismissToast = useCallback((id) => {
    setToasts((list) => list.filter((toast) => toast.id !== id));
  }, []);

  const showStatus = useCallback(
    (message, isError = false) => {
      const id = ++toastId.current;
      setToasts((list) => [...list.slice(-3), { id, message, isError }]);
      window.setTimeout(() => dismissToast(id), isError ? 8000 : 4500);
    },
    [dismissToast],
  );

  const refreshCategories = useCallback(async () => {
    setCategories(await api("/api/categories"));
  }, []);

  const refreshGallery = useCallback(
    async (offset = 0, categoryId = undefined, sort = undefined, search = undefined) => {
      if (categoryId !== undefined) galleryCategoryRef.current = categoryId;
      if (sort !== undefined) gallerySortRef.current = sort;
      if (search !== undefined) gallerySearchRef.current = search;
      const activeCategoryId = galleryCategoryRef.current;
      setGalleryLoading(true);
      try {
        const query = new URLSearchParams({
          limit: String(GALLERY_PAGE_SIZE),
          offset: String(offset),
          sort: gallerySortRef.current,
        });
        if (activeCategoryId !== null && activeCategoryId !== "") {
          query.set("category_id", String(activeCategoryId));
        }
        if (gallerySearchRef.current) query.set("q", gallerySearchRef.current);
        const result = await api(`/api/images?${query.toString()}`);
        setImages(result.images);
        setGalleryOffset(offset);
      } finally {
        setGalleryLoading(false);
      }
    },
    [],
  );

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
      galleryCategoryRef.current = null;
      gallerySortRef.current = "created_desc";
      gallerySearchRef.current = "";
      return;
    }
    Promise.all([refreshCategories(), refreshGallery()]).catch((error) =>
      showStatus(error.message, true),
    );
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

  let content;
  if (checkingSession) {
    content = (
      <div className="splash">
        <span aria-hidden="true" className="spinner" />
        <p>Vérification de la session…</p>
      </div>
    );
  } else if (user) {
    content = (
      <Workspace
        categories={categories}
        galleryLoading={galleryLoading}
        images={images}
        offset={galleryOffset}
        onCategoriesChanged={refreshCategories}
        onGalleryChanged={refreshGallery}
        onLogout={handleLogout}
        onToggleTheme={toggleTheme}
        pageSize={GALLERY_PAGE_SIZE}
        showStatus={showStatus}
        theme={theme}
        user={user}
      />
    );
  } else {
    content = (
      <AuthPanel
        onAuthenticated={setUser}
        onToggleTheme={toggleTheme}
        showStatus={showStatus}
        theme={theme}
      />
    );
  }

  return (
    <>
      {content}
      <Toasts onDismiss={dismissToast} toasts={toasts} />
    </>
  );
}
