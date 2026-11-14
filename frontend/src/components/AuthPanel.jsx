import { Eye, EyeOff, Images, Moon, ScanSearch, Sun, Wand2 } from "lucide-react";
import { useState } from "react";

import { api, jsonRequest } from "../api.js";

export default function AuthPanel({ onAuthenticated, showStatus, theme, onToggleTheme }) {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const registering = mode === "register";

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    try {
      const user = await api(
        `/api/auth/${registering ? "register" : "login"}`,
        jsonRequest("POST", { username, password }),
      );
      setPassword("");
      onAuthenticated(user);
      showStatus(registering ? "Compte créé avec succès." : "Connexion réussie.");
    } catch (error) {
      showStatus(error.message, true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-screen">
      <aside className="auth-hero">
        <div className="brand">
          <span className="brand-mark">G13</span>
          <span className="brand-name">Galerie CBIR</span>
        </div>
        <div className="auth-hero-body">
          <h1>Retrouvez vos images par leur contenu.</h1>
          <p>
            Gérez votre galerie et recherchez des images similaires grâce aux descripteurs de
            couleur et de texture, affinés par retour de pertinence FRE.
          </p>
          <ul className="feature-list">
            <li>
              <Images size={18} /> Galerie, catégories et transformations
            </li>
            <li>
              <ScanSearch size={18} /> Recherche CBIR sur 10 000 images
            </li>
            <li>
              <Wand2 size={18} /> Feature Relevance Estimation itérative
            </li>
          </ul>
        </div>
        <small>Projet universitaire · Groupe G13</small>
      </aside>

      <main className="auth-main">
        <button
          aria-label="Changer de thème"
          className="icon-btn auth-theme"
          onClick={onToggleTheme}
          type="button"
        >
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        <form className="auth-card" onSubmit={submit}>
          <h2>{registering ? "Créer un compte" : "Bon retour"}</h2>
          <p className="hint">
            {registering
              ? "Quelques secondes suffisent pour commencer."
              : "Connectez-vous pour accéder à votre galerie."}
          </p>

          <div className="segmented" role="tablist">
            <button
              aria-selected={!registering}
              className={!registering ? "is-active" : ""}
              onClick={() => setMode("login")}
              role="tab"
              type="button"
            >
              Connexion
            </button>
            <button
              aria-selected={registering}
              className={registering ? "is-active" : ""}
              onClick={() => setMode("register")}
              role="tab"
              type="button"
            >
              Inscription
            </button>
          </div>

          <label className="field">
            <span>Nom d’utilisateur</span>
            <input
              autoComplete="username"
              maxLength={32}
              minLength={3}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="ex. mohamed"
              required
              value={username}
            />
          </label>

          <label className="field">
            <span>Mot de passe</span>
            <div className="input-with-action">
              <input
                autoComplete={registering ? "new-password" : "current-password"}
                maxLength={256}
                minLength={12}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="12 caractères minimum"
                required
                type={showPassword ? "text" : "password"}
                value={password}
              />
              <button
                aria-label={showPassword ? "Masquer le mot de passe" : "Afficher le mot de passe"}
                onClick={() => setShowPassword((value) => !value)}
                type="button"
              >
                {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </div>
          </label>

          <button className="button button-primary button-block" disabled={loading} type="submit">
            {loading ? "Veuillez patienter…" : registering ? "Créer le compte" : "Se connecter"}
          </button>
        </form>
      </main>
    </div>
  );
}
