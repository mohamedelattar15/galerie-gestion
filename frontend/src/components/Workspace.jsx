import { FolderTree, Images, Layers3, LogOut, Moon, ScanSearch, Sun, UploadCloud } from "lucide-react";
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

function handleTabKeyDown(event) {
  const tabs = [...event.currentTarget.parentElement.querySelectorAll('[role="tab"]')];
  const index = tabs.indexOf(event.currentTarget);
  let next = index;
  if (event.key === "ArrowRight" || event.key === "ArrowDown") next = (index + 1) % tabs.length;
  else if (event.key === "ArrowLeft" || event.key === "ArrowUp") next = (index - 1 + tabs.length) % tabs.length;
  else if (event.key === "Home") next = 0;
  else if (event.key === "End") next = tabs.length - 1;
  else return;
  event.preventDefault();
  tabs[next].focus();
  tabs[next].click();
}

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
  const [galleryQuery, setGalleryQuery] = useState(null);
  const current = TABS.find((item) => item.id === tab);

  function searchWithGalleryImage(image) {
    setGalleryQuery(image);
    setTab("search");
  }

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
              onKeyDown={handleTabKeyDown}
              role="tab"
              tabIndex={tab === id ? 0 : -1}
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

        <div aria-hidden={tab !== "search"} className={`workspace-section${tab === "search" ? " is-active" : ""}`} hidden={tab !== "search"}>
          <SearchPanel
            galleryImage={galleryQuery}
            onClearGalleryImage={() => setGalleryQuery(null)}
            showStatus={showStatus}
          />
        </div>

        <div aria-hidden={tab !== "gallery"} className={`workspace-section${tab === "gallery" ? " is-active" : ""}`} hidden={tab !== "gallery"}>
          <GalleryPanel
            categories={categories}
            images={images}
            loading={galleryLoading}
            offset={offset}
            onGoImport={() => setTab("manage")}
            onRefresh={onGalleryChanged}
            onSearch={searchWithGalleryImage}
            pageSize={pageSize}
            showStatus={showStatus}
          />
        </div>

        <div aria-hidden={tab !== "manage"} className={`workspace-section${tab === "manage" ? " is-active" : ""}`} hidden={tab !== "manage"}>
          <section aria-labelledby="manage-intro-title" className="manage-intro">
            <div className="manage-intro-main">
              <span className="manage-intro-icon"><UploadCloud size={24} /></span>
              <p className="eyebrow">Importer & organiser</p>
              <h2 id="manage-intro-title">Construisez une galerie facile à explorer</h2>
              <p className="hint">Ajoutez vos photos, classez-les dans une arborescence de catégories et retrouvez-les ensuite dans la galerie ou par recherche visuelle.</p>
              <div className="manage-intro-badges">
                <span><Images size={15} /> Import par lot jusqu’à 32 images</span>
                <span><FolderTree size={15} /> {categories.length} catégorie{categories.length > 1 ? "s" : ""}</span>
              </div>
            </div>
            <div aria-hidden="true" className="manage-intro-art">
              <div className="manage-art-back"><Layers3 size={28} /></div>
              <div className="manage-art-front"><FolderTree size={28} /></div>
              <span className="manage-art-dot manage-art-dot-one" />
              <span className="manage-art-dot manage-art-dot-two" />
            </div>
            <div className="manage-steps">
              <article><span>01</span><strong>Ajoutez</strong><small>Sélectionnez une ou plusieurs photos.</small></article>
              <article><span>02</span><strong>Classez</strong><small>Choisissez une catégorie ou créez-en une.</small></article>
              <article><span>03</span><strong>Explorez</strong><small>Retrouvez vos images dans la galerie et la recherche.</small></article>
            </div>
          </section>
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
