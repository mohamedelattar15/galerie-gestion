import { useState } from "react";

import { api } from "../api.js";
import CategoryPanel from "./CategoryPanel.jsx";
import GalleryPanel from "./GalleryPanel.jsx";
import ImageUploader from "./ImageUploader.jsx";
import SearchPanel from "./SearchPanel.jsx";

const TABS = [
  { id: "search", label: "Recherche FRE" },
  { id: "gallery", label: "Ma galerie" },
  { id: "manage", label: "Importer & organiser" },
];

export default function Workspace({
  categories,
  images,
  offset,
  pageSize,
  onCategoriesChanged,
  onGalleryChanged,
  showStatus,
}) {
  const [tab, setTab] = useState("search");

  return (
    <div className="workspace-shell">
      <nav aria-label="Sections de l’application" className="tab-bar" role="tablist">
        {TABS.map((item) => (
          <button
            aria-selected={tab === item.id}
            className={`tab${tab === item.id ? " is-active" : ""}`}
            key={item.id}
            onClick={() => setTab(item.id)}
            role="tab"
            type="button"
          >
            {item.label}
          </button>
        ))}
      </nav>

      <div className="tab-panels">
        <div className="tab-panel" hidden={tab !== "search"}>
          <SearchPanel showStatus={showStatus} />
        </div>

        <div className="tab-panel" hidden={tab !== "gallery"}>
          <GalleryPanel
            categories={categories}
            images={images}
            offset={offset}
            pageSize={pageSize}
            onRefresh={onGalleryChanged}
            showStatus={showStatus}
          />
        </div>

        <div className="tab-panel" hidden={tab !== "manage"}>
          <div className="manage-grid">
            <CategoryPanel
              categories={categories}
              onCategoriesChanged={onCategoriesChanged}
              showStatus={showStatus}
            />
            <ImageUploader
              categories={categories}
              onUploaded={onGalleryChanged}
              showStatus={showStatus}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
