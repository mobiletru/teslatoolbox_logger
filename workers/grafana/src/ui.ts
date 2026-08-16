export function renderDashboard(): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Grafana — tesla.mobileccs.com</title>
<link rel="icon" href="data:image/svg+xml,${encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='6' fill='#111217'/><path d='M8 22 L16 8 L24 22 Z' fill='#f38e2a'/></svg>`)}"/>
<style>
:root {
  --bg: #111217;
  --panel: #181b1f;
  --line: #22252b;
  --text: #d8d9da;
  --muted: #8e8e8e;
  --orange: #f38e2a;
  --green: #73bf69;
  --blue: #5794f2;
  --red: #f2495c;
  --yellow: #fade2a;
}
* { box-sizing: border-box; }
html, body { margin: 0; background: var(--bg); color: var(--text); font: 13px/1.45 Inter, "Helvetica Neue", Arial, sans-serif; }
a { color: var(--blue); text-decoration: none; }
header {
  display: flex; align-items: center; gap: 14px; padding: 0 16px;
  height: 48px; border-bottom: 1px solid var(--line); background: #0b0c0e;
}
.mark {
  width: 22px; height: 22px; background: var(--orange);
  clip-path: polygon(50% 8%, 92% 86%, 8% 86%);
}
h1 { font-size: 14px; font-weight: 600; margin: 0; letter-spacing: .01em; }
.grow { flex: 1; }
.chip {
  font-size: 11px; letter-spacing: .04em; text-transform: uppercase;
  border: 1px solid var(--line); background: #14161a; color: var(--muted);
  padding: 3px 8px; border-radius: 999px;
}
.chip.live { color: var(--green); border-color: #2b4a32; }
.chip.demo { color: var(--orange); border-color: #4a3518; }
.chip.down { color: var(--red); border-color: #4a1f26; }
main { padding: 14px 16px 32px; display: grid; gap: 12px; }
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }
.panel {
  background: var(--panel); border: 1px solid var(--line); border-radius: 2px;
  min-height: 88px;
}
.panel h2 {
  margin: 0; padding: 8px 10px 0; font-size: 12px; font-weight: 500; color: var(--muted);
}
.stat { padding: 4px 10px 10px; }
.stat .v { font-size: 28px; font-weight: 500; letter-spacing: -.03em; }
.stat .u { font-size: 12px; color: var(--muted); margin-left: 4px; }
.charts { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
@media (max-width: 900px) { .charts { grid-template-columns: 1fr; } }
.chart { min-height: 240px; display: flex; flex-direction: column; }
.chart canvas { width: 100%; height: 190px; display: block; }
.legend { display: flex; flex-wrap: wrap; gap: 10px; padding: 6px 10px 10px; color: var(--muted); }
.legend i { display: inline-block; width: 10px; height: 3px; margin-right: 5px; vertical-align: middle; }
.picker { padding: 10px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
select, button {
  background: #111217; color: var(--text); border: 1px solid var(--line);
  padding: 6px 8px; border-radius: 2px;
}
button { cursor: pointer; }
button:hover { border-color: var(--orange); }
footer { color: var(--muted); font-size: 12px; padding: 0 6px; }
</style>
</head>
<body>
<header>
  <div class="mark" aria-hidden="true"></div>
  <h1>Tesla Toolbox 3 — tesla.mobileccs.com</h1>
  <span class="chip" id="source">connecting</span>
  <span class="grow"></span>
  <a class="chip" href="https://tesla.mobileccs.com/" target="_blank" rel="noreferrer">Signal viewer</a>
  <a class="chip" href="/metrics" target="_blank" rel="noreferrer">/metrics</a>
</header>
<main>
  <section class="kpis" id="kpis"></section>
  <section class="charts">
    <article class="panel chart"><h2>SoC and charge limit</h2><canvas id="c-soc"></canvas><div class="legend" id="l-soc"></div></article>
    <article class="panel chart"><h2>Pack V / I</h2><canvas id="c-pack"></canvas><div class="legend" id="l-pack"></div></article>
    <article class="panel chart"><h2>Cabin and ambient</h2><canvas id="c-hvac"></canvas><div class="legend" id="l-hvac"></div></article>
    <article class="panel chart"><h2>Drive / DI current</h2><canvas id="c-di"></canvas><div class="legend" id="l-di"></div></article>
  </section>
  <article class="panel">
    <h2>Signal picker</h2>
    <div class="picker">
      <label>Group <select id="group"></select></label>
      <label>Signal <select id="signal"></select></label>
      <button type="button" id="add">Add to chart</button>
      <button type="button" id="clear">Clear extra</button>
    </div>
    <canvas id="c-pick" style="width:100%;height:220px;display:block"></canvas>
    <div class="legend" id="l-pick"></div>
  </article>
  <footer>Live via <code>tesla-signals</code> service binding. Source is demo until a Toolbox 3 gateway is configured. Refresh is SSE from <code>/api/stream</code>.</footer>
</main>
<script>
const COLORS = ["#5794f2","#73bf69","#f38e2a","#f2495c","#b877d9","#fade2a","#8ab8ff","#d0d0d0"];
const KPI = [
  ["BatteryLevel","%"],["PackVoltage","V"],["PackCurrent","A"],["HvacPower","kW"],
  ["InsideTemp","C"],["OutsideTemp","C"],["Speed","mph"],["Odometer","mi"]
];
const CHARTS = {
  soc: ["BatteryLevel","ChargeLimitSoc"],
  pack: ["PackVoltage","PackCurrent"],
  hvac: ["InsideTemp","OutsideTemp","HvacLeftVentTemp","HvacRightVentTemp"],
  di: ["Speed","PackCurrent","DIF_motorCurrent","DIREL_motorCurrent","DIRER_motorCurrent"]
};
const MAX = 180;
const hist = {};
let catalog = [];
let extra = [];
let last = { source: "", signals: {} };

function num(v) {
  if (v == null) return null;
  if (typeof v === "number") return Number.isFinite(v) ? v : null;
  if (typeof v === "object" && v.value != null && typeof v.value !== "string") {
    const n = Number(v.value);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}
function label(v) {
  if (v == null) return "—";
  if (typeof v === "object" && v.value != null) return String(v.value);
  return String(v);
}
function push(name, value, ts) {
  if (!hist[name]) hist[name] = [];
  hist[name].push({ t: ts, v: value });
  if (hist[name].length > MAX) hist[name].splice(0, hist[name].length - MAX);
}
function apply(payload) {
  last.source = payload.source || "";
  last.signals = payload.signals || {};
  const ts = payload.ts || Date.now();
  const chip = document.getElementById("source");
  const demo = String(last.source).includes("demo");
  chip.textContent = last.source || "unknown";
  chip.className = "chip " + (demo ? "demo" : "live");
  for (const [name, rec] of Object.entries(last.signals)) {
    const v = num(rec);
    if (v != null) push(name, v, ts);
  }
  renderKpis();
  draw("c-soc","l-soc", CHARTS.soc);
  draw("c-pack","l-pack", CHARTS.pack);
  draw("c-hvac","l-hvac", CHARTS.hvac);
  draw("c-di","l-di", CHARTS.di.filter((n) => hist[n] || last.signals[n]));
  draw("c-pick","l-pick", extra);
}
function renderKpis() {
  const root = document.getElementById("kpis");
  root.innerHTML = KPI.map(([name, unit]) => {
    const rec = last.signals[name];
    const v = num(rec);
    const shown = v == null ? label(rec) : (Math.abs(v) >= 100 ? v.toFixed(0) : v.toFixed(1));
    return '<article class="panel stat"><h2>'+name+'</h2><div class="v">'+shown+'<span class="u">'+unit+'</span></div></article>';
  }).join("");
}
function draw(canvasId, legendId, names) {
  const canvas = document.getElementById(canvasId);
  const legend = document.getElementById(legendId);
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth || 300;
  const h = canvas.clientHeight || 190;
  canvas.width = Math.floor(w * dpr);
  canvas.height = Math.floor(h * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "#14161a";
  ctx.fillRect(0, 0, w, h);
  const series = names.filter((n) => (hist[n] || []).length > 1);
  legend.innerHTML = names.map((n, i) =>
    '<span><i style="background:'+COLORS[i % COLORS.length]+'"></i>'+n+'</span>'
  ).join("");
  if (!series.length) {
    ctx.fillStyle = "#8e8e8e";
    ctx.fillText("Waiting for samples…", 12, 24);
    return;
  }
  let min = Infinity, max = -Infinity, t0 = Infinity, t1 = -Infinity;
  for (const n of series) {
    for (const p of hist[n]) {
      if (p.v < min) min = p.v;
      if (p.v > max) max = p.v;
      if (p.t < t0) t0 = p.t;
      if (p.t > t1) t1 = p.t;
    }
  }
  if (min === max) { min -= 1; max += 1; }
  if (t0 === t1) t1 = t0 + 1;
  const pad = { l: 8, r: 8, t: 8, b: 8 };
  ctx.strokeStyle = "#22252b";
  ctx.beginPath();
  for (let i = 1; i < 4; i++) {
    const y = pad.t + (h - pad.t - pad.b) * i / 4;
    ctx.moveTo(pad.l, y); ctx.lineTo(w - pad.r, y);
  }
  ctx.stroke();
  names.forEach((n, i) => {
    const pts = hist[n];
    if (!pts || pts.length < 2) return;
    ctx.strokeStyle = COLORS[i % COLORS.length];
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    pts.forEach((p, idx) => {
      const x = pad.l + (w - pad.l - pad.r) * (p.t - t0) / (t1 - t0);
      const y = pad.t + (h - pad.t - pad.b) * (1 - (p.v - min) / (max - min));
      if (idx === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
  });
}
function fillSelects() {
  const groups = ["all", ...Array.from(new Set(catalog.map((s) => s.group).filter(Boolean))).sort()];
  const g = document.getElementById("group");
  const s = document.getElementById("signal");
  g.innerHTML = groups.map((x) => '<option value="'+x+'">'+x+'</option>').join("");
  const paint = () => {
    const gv = g.value;
    const names = catalog.filter((c) => gv === "all" || c.group === gv).map((c) => c.name);
    s.innerHTML = names.map((n) => '<option value="'+n+'">'+n+'</option>').join("");
  };
  g.onchange = paint;
  paint();
}
document.getElementById("add").onclick = () => {
  const n = document.getElementById("signal").value;
  if (n && !extra.includes(n)) extra.push(n);
  draw("c-pick","l-pick", extra);
};
document.getElementById("clear").onclick = () => { extra = []; draw("c-pick","l-pick", extra); };

async function boot() {
  try {
    const [snap, cat] = await Promise.all([
      fetch("/api/signals").then((r) => r.json()),
      fetch("/api/signals/catalog").then((r) => r.json()),
    ]);
    catalog = Array.isArray(cat) ? cat : (cat.signals || []);
    fillSelects();
    apply(snap);
  } catch (e) {
    document.getElementById("source").textContent = "error";
    document.getElementById("source").className = "chip down";
  }
  const es = new EventSource("/api/stream");
  es.onmessage = (ev) => {
    try { apply(JSON.parse(ev.data)); } catch {}
  };
  es.onerror = () => {
    document.getElementById("source").classList.add("down");
  };
}
boot();
</script>
</body>
</html>`;
}
