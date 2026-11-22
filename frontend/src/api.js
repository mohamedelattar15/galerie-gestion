export async function api(path, options = {}) {
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

export function uploadWithProgress(path, body, onProgress) {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open("POST", path);
    request.withCredentials = true;
    request.responseType = "json";
    request.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable) {
        onProgress?.(Math.round((event.loaded / event.total) * 100));
      }
    });
    request.addEventListener("load", () => {
      let payload = request.response;
      if (!payload) {
        try {
          payload = JSON.parse(request.responseText);
        } catch {
          payload = null;
        }
      }
      if (request.status < 200 || request.status >= 300) {
        reject(new Error(payload?.error || `L’import a échoué (${request.status}).`));
        return;
      }
      resolve(payload);
    });
    request.addEventListener("error", () => reject(new Error("La connexion a échoué pendant l’import.")));
    request.addEventListener("abort", () => reject(new Error("L’import a été interrompu.")));
    request.send(body);
  });
}

export function jsonRequest(method, body) {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}
