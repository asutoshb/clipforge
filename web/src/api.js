// Thin client for the ClipForge API.

async function post(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error((await res.json()).detail || res.statusText);
  return res.json();
}

export const downloadVideo = (url, start, end) =>
  post("/api/youtube/download", { url, start, end });

export const makeShorts = (url, count, platform, niche) =>
  post("/api/youtube/shorts", { url, count, platform, niche });

export const makeCaption = (text, platform, niche) =>
  post("/api/caption", { text, platform, niche });

export async function makeReel(formData) {
  const res = await fetch("/api/reel", { method: "POST", body: formData });
  if (!res.ok) throw new Error((await res.json()).detail || res.statusText);
  return res.json();
}

export const fileUrl = (path) => `/api/file?path=${encodeURIComponent(path)}`;
