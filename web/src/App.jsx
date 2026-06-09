import { useState } from "react";
import * as api from "./api.js";

const TABS = [
  { id: "download", label: "YouTube → Download" },
  { id: "shorts", label: "YouTube → Shorts" },
  { id: "reel", label: "Media + Prompt → Short" },
];

export default function App() {
  const [tab, setTab] = useState("download");
  return (
    <div className="app">
      <header>
        <h1>ClipForge</h1>
        <p>Turn links & raw media into ready-to-post shorts, reels and copy.</p>
      </header>
      <nav className="tabs">
        {TABS.map((t) => (
          <button key={t.id} className={tab === t.id ? "active" : ""}
            onClick={() => setTab(t.id)}>{t.label}</button>
        ))}
      </nav>
      <main>
        {tab === "download" && <DownloadPane />}
        {tab === "shorts" && <ShortsPane />}
        {tab === "reel" && <ReelPane />}
      </main>
      <footer>Open-source · runs locally · use rights-cleared media only.</footer>
    </div>
  );
}

function useAsync(fn) {
  const [state, set] = useState({ loading: false, error: "", data: null });
  const run = async (...args) => {
    set({ loading: true, error: "", data: null });
    try { set({ loading: false, error: "", data: await fn(...args) }); }
    catch (e) { set({ loading: false, error: e.message, data: null }); }
  };
  return [state, run];
}

function DownloadPane() {
  const [url, setUrl] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [s, run] = useAsync(api.downloadVideo);
  return (
    <section className="pane">
      <input placeholder="Video URL" value={url} onChange={(e) => setUrl(e.target.value)} />
      <div className="row">
        <input placeholder="start (s)" value={start} onChange={(e) => setStart(e.target.value)} />
        <input placeholder="end (s)" value={end} onChange={(e) => setEnd(e.target.value)} />
      </div>
      <button onClick={() => run(url, start || null, end || null)} disabled={s.loading}>
        {s.loading ? "Working…" : "Download"}
      </button>
      <Status s={s} />
      {s.data && <a className="dl" href={api.fileUrl(s.data.file)}>⬇ Download file</a>}
    </section>
  );
}

function ShortsPane() {
  const [url, setUrl] = useState("");
  const [count, setCount] = useState(3);
  const [platform, setPlatform] = useState("youtube");
  const [s, run] = useAsync(api.makeShorts);
  return (
    <section className="pane">
      <input placeholder="Video URL" value={url} onChange={(e) => setUrl(e.target.value)} />
      <div className="row">
        <input type="number" value={count} onChange={(e) => setCount(+e.target.value)} />
        <PlatformPicker value={platform} onChange={setPlatform} />
      </div>
      <button onClick={() => run(url, count, platform)} disabled={s.loading}>
        {s.loading ? "Generating…" : "Make shorts"}
      </button>
      <Status s={s} />
      {s.data?.shorts?.map((sh, i) => (
        <div className="card" key={i}>
          <a className="dl" href={api.fileUrl(sh.file)}>⬇ Short {i + 1}</a>
          <Copy copy={sh.copy} />
        </div>
      ))}
    </section>
  );
}

function ReelPane() {
  const [prompt, setPrompt] = useState("");
  const [files, setFiles] = useState(null);
  const [s, run] = useAsync(async () => {
    const fd = new FormData();
    fd.append("prompt", prompt);
    [...files].forEach((f) => fd.append("files", f));
    return api.makeReel(fd);
  });
  return (
    <section className="pane">
      <input type="file" multiple onChange={(e) => setFiles(e.target.files)} />
      <textarea placeholder="Describe the short you want…" value={prompt}
        onChange={(e) => setPrompt(e.target.value)} />
      <button onClick={run} disabled={s.loading || !files}>
        {s.loading ? "Editing…" : "Generate short"}
      </button>
      <Status s={s} />
      {s.data && (
        <div className="card">
          <a className="dl" href={api.fileUrl(s.data.file)}>⬇ Download reel</a>
          <Copy copy={s.data.copy} />
        </div>
      )}
    </section>
  );
}

function PlatformPicker({ value, onChange }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="youtube">YouTube</option>
      <option value="instagram">Instagram</option>
      <option value="linkedin">LinkedIn</option>
    </select>
  );
}

function Copy({ copy }) {
  if (!copy) return null;
  return (
    <div className="copy">
      <strong>Titles</strong>
      <ul>{copy.titles?.map((t, i) => <li key={i}>{t}</li>)}</ul>
      <p>{copy.caption}</p>
      <small>{copy.hashtags?.map((h) => `#${h}`).join(" ")}</small>
    </div>
  );
}

function Status({ s }) {
  if (s.error) return <p className="err">⚠ {s.error}</p>;
  return null;
}
