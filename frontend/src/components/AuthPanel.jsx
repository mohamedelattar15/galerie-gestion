import { useState } from "react";

import { api, jsonRequest } from "../api.js";

export default function AuthPanel({ onAuthenticated, showStatus }) {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
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
    <section className="panel auth-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Espace personnel</p>
          <h2>{registering ? "Créer un compte" : "Connexion"}</h2>
        </div>
        <div className="mode-switch" aria-label="Mode d’authentification">
          <button
            className={`button button-small${!registering ? " is-active" : ""}`}
            onClick={() => setMode("login")}
            type="button"
          >
            Connexion
          </button>
          <button
            className={`button button-small${registering ? " is-active" : ""}`}
            onClick={() => setMode("register")}
            type="button"
          >
            Créer un compte
          </button>
        </div>
      </div>
      <form className="form-grid" onSubmit={submit}>
        <label>
          Nom d’utilisateur
          <input
            autoComplete="username"
            maxLength={32}
            minLength={3}
            onChange={(event) => setUsername(event.target.value)}
            required
            value={username}
          />
        </label>
        <label>
          Mot de passe
          <input
            autoComplete={registering ? "new-password" : "current-password"}
            maxLength={256}
            minLength={12}
            onChange={(event) => setPassword(event.target.value)}
            required
            type="password"
            value={password}
          />
        </label>
        <button className="button button-primary" disabled={loading} type="submit">
          {loading ? "Veuillez patienter…" : registering ? "Créer le compte" : "Se connecter"}
        </button>
      </form>
      <p className="hint">Mot de passe : 12 caractères minimum.</p>
    </section>
  );
}
