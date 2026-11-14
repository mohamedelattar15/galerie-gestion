const authPanel = document.querySelector("#auth-panel");
const workspace = document.querySelector("#workspace");
const statusMessage = document.querySelector("#status-message");
const authForm = document.querySelector("#auth-form");
const accountBar = document.querySelector("#account-bar");
const categoryParent = document.querySelector("#category-parent");
const uploadCategory = document.querySelector("#upload-category");
const galleryGrid = document.querySelector("#gallery-grid");
const searchResults = document.querySelector("#search-results");
const feedbackButton = document.querySelector("#feedback-button");

let authMode = "login";
let searchSessionId = null;
let currentSearchResults = [];

async function api(path, options = {}) {
  const response = await fetch(path, {
    credentials: "same-origin",
    ...options,
  });
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json")
    ? await response.json()
    : null;
  if (!response.ok) {
    throw new Error(body?.error || `La requête a échoué (${response.status}).`);
  }
  return body;
}

function showStatus(message, isError = false) {
  statusMessage.textContent = message;
  statusMessage.classList.toggle("is-error", isError);
}

function setAuthenticated(username) {
  authPanel.hidden = true;
  workspace.hidden = false;
  accountBar.hidden = false;
  document.querySelector("#account-name").textContent = username;
  loadWorkspace();
}

function setLoggedOut() {
  authPanel.hidden = false;
  workspace.hidden = true;
  accountBar.hidden = true;
  galleryGrid.replaceChildren();
  searchResults.replaceChildren();
  feedbackButton.hidden = true;
  searchSessionId = null;
}

function setAuthMode(mode) {
  authMode = mode;
  const register = mode === "register";
  document.querySelector("#auth-title").textContent = register ? "Créer un compte" : "Connexion";
  document.querySelector("#auth-submit").textContent = register ? "Créer le compte" : "Se connecter";
  document.querySelector("#password").autocomplete = register ? "new-password" : "current-password";
  document.querySelector("#login-mode").classList.toggle("is-active", !register);
  document.querySelector("#register-mode").classList.toggle("is-active", register);
}

async function loadWorkspace() {
  try {
    await Promise.all([loadCategories(), loadGallery()]);
    showStatus("Galerie prête.");
  } catch (error) {
    showStatus(error.message, true);
  }
}

async function loadCategories() {
  const categories = await api("/api/categories");
  categoryParent.replaceChildren(new Option("Aucune — catégorie racine", ""));
  uploadCategory.replaceChildren(new Option("Sans catégorie", ""));
  const list = document.querySelector("#category-list");
  list.replaceChildren();

  const namesById = new Map(categories.map((category) => [category.id, category.name]));
  for (const category of categories) {
    const prefix = category.parent_id ? `${namesById.get(category.parent_id)} / ` : "";
    categoryParent.add(new Option(`${prefix}${category.name}`, category.id));
    uploadCategory.add(new Option(`${prefix}${category.name}`, category.id));
    const item = document.createElement("li");
    const name = document.createElement("span");
    name.textContent = `${prefix}${category.name}`;
    const deleteButton = makeButton("×", "button button-small");
    deleteButton.setAttribute("aria-label", `Supprimer la catégorie ${category.name}`);
    deleteButton.addEventListener("click", async () => {
      try {
        await api(`/api/categories/${category.id}`, { method: "DELETE" });
        await loadCategories();
        showStatus("Catégorie supprimée.");
      } catch (error) {
        showStatus(error.message, true);
      }
    });
    item.append(name, deleteButton);
    list.append(item);
  }
  if (categories.length === 0) {
    const item = document.createElement("li");
    item.textContent = "Aucune catégorie pour le moment.";
    list.append(item);
  }
}

async function loadGallery() {
  const result = await api("/api/images?limit=100");
  galleryGrid.replaceChildren();
  if (result.images.length === 0) {
    galleryGrid.append(emptyState("Votre galerie est vide. Importez quelques images pour commencer."));
    return;
  }
  for (const image of result.images) {
    galleryGrid.append(createGalleryCard(image));
  }
}

function emptyState(message) {
  const element = document.createElement("p");
  element.className = "empty-state";
  element.textContent = message;
  return element;
}

function createGalleryCard(image) {
  const card = document.createElement("article");
  card.className = "image-card";
  const preview = document.createElement("img");
  preview.src = image.file_url;
  preview.alt = image.filename;
  preview.loading = "lazy";

  const body = document.createElement("div");
  body.className = "image-card-body";
  const title = document.createElement("h3");
  title.textContent = image.filename;
  const meta = document.createElement("p");
  meta.className = "image-meta";
  meta.textContent = `${image.width} × ${image.height}`;
  const actions = document.createElement("div");
  actions.className = "card-actions";

  const descriptorsButton = makeButton("Descripteurs", "button button-secondary");
  const deleteButton = makeButton("Supprimer", "button button-quiet");
  const downloadLink = document.createElement("a");
  downloadLink.className = "button button-quiet";
  downloadLink.href = `${image.file_url}?download=1`;
  downloadLink.download = image.filename;
  downloadLink.textContent = "Télécharger";
  actions.append(descriptorsButton, downloadLink, deleteButton);
  body.append(title, meta, actions);
  const descriptorPanel = document.createElement("div");
  descriptorPanel.className = "descriptor-panel";
  descriptorPanel.hidden = true;
  const transformBox = createTransformControls(image);
  body.append(descriptorPanel, transformBox);
  card.append(preview, body);

  descriptorsButton.addEventListener("click", async () => {
    if (!descriptorPanel.hidden) {
      descriptorPanel.hidden = true;
      return;
    }
    descriptorsButton.disabled = true;
    try {
      const response = await api(`/api/images/${image.id}/descriptors`);
      renderDescriptors(descriptorPanel, response.descriptors);
      descriptorPanel.hidden = false;
    } catch (error) {
      showStatus(error.message, true);
    } finally {
      descriptorsButton.disabled = false;
    }
  });

  deleteButton.addEventListener("click", async () => {
    if (!window.confirm(`Supprimer « ${image.filename} » ?`)) return;
    try {
      await api(`/api/images/${image.id}`, { method: "DELETE" });
      showStatus("Image supprimée.");
      await loadGallery();
    } catch (error) {
      showStatus(error.message, true);
    }
  });
  return card;
}

function makeButton(text, className) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = className;
  button.textContent = text;
  return button;
}

function createTransformControls(image) {
  const details = document.createElement("details");
  details.className = "transform-box";
  const summary = document.createElement("summary");
  summary.textContent = "Créer une image transformée";
  const form = document.createElement("form");
  form.className = "transform-form";
  const operation = document.createElement("select");
  operation.setAttribute("aria-label", "Transformation");
  for (const [value, label] of [
    ["rotate", "Rotation 90°"],
    ["flip", "Miroir horizontal"],
    ["resize", "Redimensionner"],
    ["crop", "Recadrer"],
  ]) {
    operation.add(new Option(label, value));
  }
  const options = document.createElement("div");
  options.className = "transform-parameters";
  const submit = makeButton("Créer une copie", "button button-secondary");
  submit.type = "submit";
  form.append(operation, options, submit);
  details.append(summary, form);

  function renderOptions() {
    options.replaceChildren();
    if (operation.value === "rotate") return;
    if (operation.value === "flip") {
      const direction = document.createElement("select");
      direction.name = "direction";
      direction.add(new Option("Horizontal", "horizontal"));
      direction.add(new Option("Vertical", "vertical"));
      options.append(direction);
      return;
    }
    const fields = operation.value === "resize"
      ? [["width", "Largeur", 512], ["height", "Hauteur", 512]]
      : [["left", "Gauche", 0], ["upper", "Haut", 0], ["right", "Droite", image.width], ["lower", "Bas", image.height]];
    for (const [name, label, value] of fields) {
      const wrapper = document.createElement("label");
      wrapper.textContent = label;
      const input = document.createElement("input");
      input.type = "number";
      input.name = name;
      input.min = name === "left" || name === "upper" ? "0" : "1";
      input.value = String(value);
      input.required = true;
      wrapper.append(input);
      options.append(wrapper);
    }
  }
  operation.addEventListener("change", renderOptions);
  renderOptions();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const body = { operation: operation.value };
    if (operation.value === "rotate") body.degrees = 90;
    if (operation.value === "flip") body.direction = data.get("direction");
    if (operation.value === "resize") {
      body.width = Number(data.get("width"));
      body.height = Number(data.get("height"));
    }
    if (operation.value === "crop") {
      body.box = ["left", "upper", "right", "lower"].map((key) => Number(data.get(key)));
    }
    try {
      await api(`/api/images/${image.id}/transform`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      showStatus("Image dérivée créée; l’originale est conservée.");
      await loadGallery();
    } catch (error) {
      showStatus(error.message, true);
    }
  });
  return details;
}

function renderDescriptors(container, descriptors) {
  container.replaceChildren();
  const histogramTitle = document.createElement("h4");
  histogramTitle.textContent = "Histogrammes HSV";
  container.append(histogramTitle);
  for (const [name, values, color] of [
    ["Teinte", descriptors.color_histogram.slice(0, 16), "#287b78"],
    ["Saturation", descriptors.color_histogram.slice(16, 32), "#4184a5"],
    ["Valeur", descriptors.color_histogram.slice(32, 48), "#d18b37"],
    ["LBP", descriptors.lbp_histogram, "#6d67a8"],
  ]) {
    const title = document.createElement("h4");
    title.textContent = name;
    const canvas = document.createElement("canvas");
    canvas.className = "descriptor-chart";
    canvas.width = 320;
    canvas.height = 100;
    drawHistogram(canvas, values, color);
    container.append(title, canvas);
  }

  const numericTitle = document.createElement("h4");
  numericTitle.textContent = "Moments et texture GLCM";
  const values = document.createElement("dl");
  values.className = "descriptor-values";
  const entries = [
    ...descriptors.color_moments.map((value, index) => [`Moment ${index + 1}`, value]),
    ...descriptors.glcm.map((value, index) => [["Contraste", "Corrélation", "Énergie", "Homogénéité"][index], value]),
  ];
  for (const [label, value] of entries) {
    const term = document.createElement("dt");
    term.textContent = label;
    const description = document.createElement("dd");
    description.textContent = Number(value).toFixed(4);
    values.append(term, description);
  }
  container.append(numericTitle, values);
}

function drawHistogram(canvas, values, color) {
  const context = canvas.getContext("2d");
  if (!context) return;
  const width = canvas.width;
  const height = canvas.height;
  const max = Math.max(...values, 1e-8);
  const barWidth = width / values.length;
  context.clearRect(0, 0, width, height);
  context.fillStyle = "#edf3f5";
  context.fillRect(0, 0, width, height);
  context.fillStyle = color;
  values.forEach((value, index) => {
    const barHeight = (value / max) * (height - 8);
    context.fillRect(index * barWidth + 1, height - barHeight, Math.max(1, barWidth - 2), barHeight);
  });
}

function renderSearchResults(results) {
  currentSearchResults = results;
  searchResults.replaceChildren();
  feedbackButton.hidden = results.length === 0;
  if (results.length === 0) {
    searchResults.append(emptyState("Aucun résultat disponible."));
    return;
  }
  for (const result of results) {
    const card = document.createElement("article");
    card.className = "image-card";
    const preview = document.createElement("img");
    preview.src = `/api/indexed-images/${result.id}/file`;
    preview.alt = `Résultat ${result.id}`;
    preview.loading = "lazy";
    const body = document.createElement("div");
    body.className = "image-card-body";
    const title = document.createElement("h3");
    title.textContent = result.path;
    const meta = document.createElement("p");
    meta.className = "image-meta";
    meta.textContent = `${result.category} · distance ${Number(result.distance).toFixed(4)}`;
    const options = document.createElement("div");
    options.className = "feedback-options";
    for (const [value, label] of [["relevant", "Pertinente"], ["non_relevant", "Non pertinente"]]) {
      const wrapper = document.createElement("label");
      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = `feedback-${result.id}`;
      radio.value = value;
      wrapper.append(radio, document.createTextNode(label));
      options.append(wrapper);
    }
    body.append(title, meta, options);
    card.append(preview, body);
    searchResults.append(card);
  }
}

document.querySelector("#login-mode").addEventListener("click", () => setAuthMode("login"));
document.querySelector("#register-mode").addEventListener("click", () => setAuthMode("register"));

authForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    username: document.querySelector("#username").value,
    password: document.querySelector("#password").value,
  };
  try {
    const user = await api(`/api/auth/${authMode === "register" ? "register" : "login"}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    document.querySelector("#password").value = "";
    setAuthenticated(user.username);
    showStatus("Connexion réussie.");
  } catch (error) {
    showStatus(error.message, true);
  }
});

document.querySelector("#logout-button").addEventListener("click", async () => {
  try {
    await api("/api/auth/logout", { method: "POST" });
    setLoggedOut();
    showStatus("Vous êtes déconnecté.");
  } catch (error) {
    showStatus(error.message, true);
  }
});

document.querySelector("#category-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await api("/api/categories", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: document.querySelector("#category-name").value,
        parent_id: categoryParent.value ? Number(categoryParent.value) : null,
      }),
    });
    document.querySelector("#category-name").value = "";
    await loadCategories();
    showStatus("Catégorie créée.");
  } catch (error) {
    showStatus(error.message, true);
  }
});

document.querySelector("#upload-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const files = document.querySelector("#image-files").files;
  const formData = new FormData();
  for (const file of files) formData.append("images", file);
  if (uploadCategory.value) formData.append("category_id", uploadCategory.value);
  try {
    const result = await api("/api/images", { method: "POST", body: formData });
    document.querySelector("#image-files").value = "";
    await loadGallery();
    showStatus(`${result.created} image(s) importée(s), ${result.failed} échec(s).`);
  } catch (error) {
    showStatus(error.message, true);
  }
});

document.querySelector("#refresh-gallery").addEventListener("click", loadGallery);

document.querySelector("#search-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData();
  formData.append("query", document.querySelector("#query-file").files[0]);
  formData.append("top_k", document.querySelector("#top-k").value);
  try {
    const result = await api("/api/search", { method: "POST", body: formData });
    searchSessionId = result.session_id;
    renderSearchResults(result.results);
    showStatus(`${result.results.length} résultat(s) affiché(s).`);
  } catch (error) {
    showStatus(error.message, true);
  }
});

feedbackButton.addEventListener("click", async () => {
  const relevantIds = [];
  const nonRelevantIds = [];
  for (const result of currentSearchResults) {
    const choice = document.querySelector(`input[name="feedback-${result.id}"]:checked`);
    if (choice?.value === "relevant") relevantIds.push(result.id);
    if (choice?.value === "non_relevant") nonRelevantIds.push(result.id);
  }
  try {
    const result = await api("/api/search/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: searchSessionId,
        relevant_ids: relevantIds,
        non_relevant_ids: nonRelevantIds,
        top_k: Number(document.querySelector("#top-k").value),
      }),
    });
    renderSearchResults(result.results);
    showStatus(`Résultats FRE — itération ${result.iteration}.`);
  } catch (error) {
    showStatus(error.message, true);
  }
});

api("/api/auth/me")
  .then((user) => setAuthenticated(user.username))
  .catch(() => setLoggedOut());
