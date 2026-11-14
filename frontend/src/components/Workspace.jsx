import { Images, LogOut, Moon, ScanSearch, Sun, UploadCloud } from "lucide-react";
import { useState } from "react";

import CategoryPanel from "./CategoryPanel.jsx";
import GalleryPanel from "./GalleryPanel.jsx";
import ImageUploader from "./ImageUploader.jsx";
import SearchPanel from "./SearchPanel.jsx";

const TABS = [
  {
    id: "search",
    label: "Recherche",
    title: "Recherche par le contenu",
    subtitle: "Trouvez des images similaires et affinez avec FRE.",
    Icon: ScanSearch,
  },
  {
    id: "gallery",
    label: "Galerie",
    title: "Ma galerie",
    subtitle: "Parcourez, inspectez et transformez vos images.",
    Icon: Images,
  },
  {
    id: "manage",
    label: "Importer",
    title: "Importer & organiser",
    subtitle: "Ajoutez des images et structurez vos catégories.",
    Icon: UploadCloud,
  },
];

export default function Workspace({
  user,
  theme,
  onToggleTheme,
  onLogout,
  categories,
  images,
  offset,
  pageSize,
  galleryLoading,
  onCategoriesChanged,
  onGalleryChanged,
  showStatus,
}) {
  const [tab, setTab] = useState("search");
  const current = TABS.find((item) => item.id === tab);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">G13</span>
          <span className="brand-name">Galerie CBIR</span>
        </div>

        <nav aria-label="Sections de l’application" className="nav" role="tablist">
          {TABS.map(({ id, label, Icon }) => (
            <button
              aria-selected={tab === id}
              className={`nav-item${tab === id ? " is-active" : ""}`}
              key={id}
              onClick={() => setTab(id)}
              role="tab"
              type="button"
            >
              <Icon size={19} />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-chip">
            <span className="avatar">{user.username.slice(0, 1).toUpperCase()}</span>
            <span className="user-name">{user.username}</span>
          </div>
          <div className="sidebar-actions">
            <button
              aria-label="Changer de thème"
              className="icon-btn"
              onClick={onToggleTheme}
              title="Changer de thème"
              type="button"
            >
              {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button
              aria-label="Déconnexion"
              className="icon-btn"
              onClick={onLogout}
              title="Déconnexion"
              type="button"
            >
              <LogOut size={18} />
            </button>
          </div>
        </div>
      </aside>

      <main className="content">
        <header className="page-header">
          <h1>{current.title}</h1>
          <p className="hint">{current.subtitle}</p>
        </header>

        <div hidden={tab !== "search"}>
          <SearchPanel showStatus={showStatus} />
        </div>

        <div hidden={tab !== "gallery"}>
          <GalleryPanel
            categories={categories}
            images={images}
            loading={galleryLoading}
            offset={offset}
            onGoImport={() => setTab("manage")}
            onRefresh={onGalleryChanged}
            pageSize={pageSize}
            showStatus={showStatus}
          />
        </div>

        <div hidden={tab !== "manage"}>
          <div className="manage-grid">
            <ImageUploader
              categories={categories}
              onUploaded={onGalleryChanged}
              showStatus={showStatus}
            />
            <CategoryPanel
              categories={categories}
              onCategoriesChanged={onCategoriesChanged}
              showStatus={showStatus}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
