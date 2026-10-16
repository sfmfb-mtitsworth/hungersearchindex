import csv, json, math
from collections import defaultdict

# ── load ─────────────────────────────────────────────────────
rows = list(csv.DictReader(open('food_bank_trends_california_dma.csv')))
raw = {}
for r in rows:
    n = r['dma_name']
    if n not in raw:
        raw[n] = {'code': r['dma_code'], 'vals': [], 'dates': []}
    raw[n]['vals'].append(int(r['search_interest']))
    raw[n]['dates'].append(r['week_start'][:10])

weeks_list = raw['San Francisco-Oakland-San Jose']['dates']
n_weeks = len(weeks_list)

DMAS = [
    ('San Francisco-Oakland-San Jose', '807', 'SF Bay Area',        37.77, -122.42),
    ('Sacramento-Stockton-Modesto',    '862', 'Sacramento',         38.58, -121.49),
    ('Los Angeles',                    '803', 'Los Angeles',         34.05, -118.24),
    ('San Diego',                      '825', 'San Diego',           32.72, -117.16),
    ('Fresno-Visalia',                 '866', 'Fresno–Visalia',      36.74, -119.77),
    ('Monterey-Salinas',               '828', 'Monterey–Salinas',    36.60, -121.89),
    ('Eureka',                         '855', 'Eureka',              40.80, -124.16),
    ('Chico-Redding',                  '813', 'Chico–Redding',       40.58, -122.39),
    ('Bakersfield',                    '800', 'Bakersfield',         35.37, -119.02),
    ('Santa Barbara-Santa Maria-San Luis Obispo', '868', 'Santa Barbara', 34.42, -119.70),
]

def cx(lon): return round((lon + 124.5) / 10.4 * 300, 1)
def cy(lat): return round((42.0 - lat) / 9.5  * 400, 1)

def stats(key):
    d = raw[key]
    vals = d['vals']
    total = sum(vals)
    mx = max(vals)
    peak_i = vals.index(mx)
    recent = sum(vals[-13:])
    prior  = sum(vals[-26:-13])
    yoy = round((recent - prior) / prior * 100, 1) if prior > 0 else 0
    return {'total': total, 'max': mx, 'peak': d['dates'][peak_i], 'yoy': yoy}

# statewide aggregate per week
agg = [0] * n_weeks
for csv_name, *_ in DMAS:
    for i, v in enumerate(raw[csv_name]['vals']):
        agg[i] += v

dma_data = []
for csv_name, code, label, lat, lon in DMAS:
    s = stats(csv_name)
    dma_data.append({
        'code': code, 'label': label,
        'cx': cx(lon), 'cy': cy(lat),
        'total': s['total'], 'max': s['max'],
        'peak': s['peak'], 'yoy': s['yoy'],
        'vals': raw[csv_name]['vals']
    })

grand_total  = sum(agg)
avg_yoy      = round(sum(d['yoy'] for d in dma_data) / len(dma_data), 1)
peak_agg_i   = agg.index(max(agg))
peak_agg_wk  = weeks_list[peak_agg_i]

DATA_JSON = json.dumps({
    'weeks': weeks_list, 'dmas': dma_data, 'agg': agg,
    'grandTotal': grand_total, 'avgYoy': avg_yoy,
    'peakWeek': peak_agg_wk, 'peakIdx': peak_agg_i,
}, separators=(',', ':'))

# California outline  viewBox="0 0 300 400"
# x = (lon + 124.5) / 10.4 * 300   y = (42 - lat) / 9.5 * 400
CA_PATH = (
    "M9,0 L3,57 8,105 18,148 42,165 61,177 66,195 78,221 "
    "91,238 107,276 115,294 136,323 173,337 193,355 211,388 "
    "240,396 286,393 286,295 300,291 286,244 271,228 216,211 "
    "173,195 159,168 130,126 130,0 Z"
)

# ── design tokens ─────────────────────────────────────────────
GROUND  = "#FFFFFF"
SURFACE = "#F5F6F8"
BORDER  = "#E2E5EA"
TEXT    = "#111827"
MUTED   = "#6B7280"
ACCENT  = "#E8622A"
OCEAN   = "#1A6B9A"

# ── HTML ──────────────────────────────────────────────────────
html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>California Hunger Signal</title>
<style>
:root {{
  --ground:   #FFFFFF;
  --surface:  #F5F6F8;
  --border:   #E2E5EA;
  --text:     #111827;
  --muted:    #6B7280;
  --accent:   #E8622A;
  --ocean:    #1A6B9A;
}}

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  background: var(--ground);
  color: var(--text);
  font-family: system-ui, -apple-system, 'Helvetica Neue', Arial, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}}

/* numbers always tabular */
.kpi-num, .rank-yoy, .card-meta, .card-yoy, .chart-axis, footer {{
  font-variant-numeric: tabular-nums;
}}

.page {{ max-width: 1080px; margin: 0 auto; padding: 0 40px 80px; }}

/* ── hero ─────────────────────────────────────────────── */
.hero {{
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 48px;
  align-items: end;
  padding: 64px 0 0;
  margin-bottom: 0;
}}
.hero-title {{
  padding-bottom: 12px;
}}
.eyebrow {{
  font-size: 11px;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 20px;
  line-height: 1.6;
}}
h1 {{
  font-size: clamp(32px, 4.5vw, 52px);
  font-weight: 800;
  letter-spacing: -.03em;
  line-height: 1.0;
  color: var(--text);
}}
h1 span {{ color: var(--accent); }}
.hero-chart-wrap {{
  position: relative;
}}
#heroCanvas {{
  display: block;
  width: 100%;
  height: 180px;
}}
.chart-axis {{
  display: flex;
  justify-content: space-between;
  padding-top: 6px;
  font-family: var(--mono);
  font-size: 10px;
  color: var(--muted);
  letter-spacing: .04em;
}}

/* ── divider ── */
.divider {{
  height: 1px;
  background: var(--border);
  margin: 32px 0;
}}

/* ── kpi bar ─────────────────────────────────────────── */
.kpi-bar {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0;
  border: 1px solid var(--border);
  margin-bottom: 56px;
}}
.kpi {{
  padding: 24px 24px 20px;
  border-right: 1px solid var(--border);
}}
.kpi:last-child {{ border-right: none; }}
.kpi-num {{
  display: block;
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -.02em;
  margin-bottom: 8px;
  color: var(--text);
}}
.kpi-num.signal {{ color: var(--accent); }}
.kpi-num.ocean  {{ color: var(--ocean); }}
.kpi-label {{
  font-size: 11px;
  color: var(--muted);
  letter-spacing: .04em;
  text-transform: uppercase;
}}

/* ── two-col: map + rank ────────────────────────────── */
.map-row {{
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 56px;
  align-items: start;
  margin-bottom: 64px;
}}
.map-wrap {{
  position: relative;
}}
.map-wrap svg {{
  display: block;
  width: 100%;
  height: auto;
  overflow: visible;
}}
#caOutline {{
  fill: var(--surface);
  stroke: var(--border);
  stroke-width: 1;
  stroke-linejoin: round;
}}
.dma-bubble {{
  cursor: pointer;
}}
.dma-bubble circle {{
  fill: var(--accent);
  fill-opacity: .15;
  stroke: var(--accent);
  stroke-width: 1;
  transition: fill-opacity .12s;
}}
.dma-bubble:hover circle,
.dma-bubble.active circle {{
  fill-opacity: .32;
  stroke-width: 1.5;
}}
.bubble-label {{
  font-size: 8.5px;
  fill: var(--text);
  font-family: system-ui, sans-serif;
  pointer-events: none;
  text-anchor: middle;
  dominant-baseline: middle;
}}
#mapTip {{
  position: absolute;
  background: var(--text);
  color: #fff;
  font-size: 11px;
  padding: 8px 12px;
  pointer-events: none;
  opacity: 0;
  transition: opacity .1s;
  white-space: nowrap;
  z-index: 10;
  line-height: 1.6;
}}
#mapTip.show {{ opacity: 1; }}

/* rank panel */
.rank-panel h2 {{
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: .12em;
  color: var(--muted);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}}
.rank-row {{
  display: grid;
  grid-template-columns: 1fr 80px 60px;
  align-items: center;
  gap: 16px;
  padding: 11px 8px;
  cursor: pointer;
  border-bottom: 1px solid var(--border);
  transition: background .1s;
}}
.rank-row:hover {{ background: var(--surface); margin: 0 -8px; padding: 11px 8px; }}
.rank-row.active .rank-name {{ color: var(--accent); }}
.rank-name {{
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
.rank-bar-track {{
  height: 3px;
  background: var(--border);
  border-radius: 2px;
  overflow: hidden;
}}
.rank-bar-fill {{
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
}}
.rank-yoy {{
  font-size: 11px;
  text-align: right;
}}
.rank-yoy.up   {{ color: var(--accent); }}
.rank-yoy.down {{ color: var(--ocean); }}

/* ── sparkline grid ──────────────────────────────────── */
.grid-head {{
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 16px;
}}
.grid-head h2 {{
  font-size: 10px;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: var(--muted);
}}
.grid-head .hint {{
  font-size: 11px;
  color: var(--muted);
}}
.dma-grid {{
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
  margin-bottom: 64px;
}}
.dma-card {{
  background: var(--ground);
  padding: 18px 16px 14px;
  cursor: pointer;
  transition: background .1s;
}}
.dma-card:hover,
.dma-card.active {{ background: var(--surface); }}
.dma-card.active .card-name {{ color: var(--accent); }}
.card-name {{
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 1px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
.card-meta {{
  font-size: 10px;
  color: var(--muted);
  margin-bottom: 10px;
}}
.card-canvas {{
  display: block;
  width: 100%;
  height: 48px;
}}
.card-yoy {{
  font-size: 10px;
  margin-top: 7px;
}}
.card-yoy .val {{ font-weight: 700; }}
.card-yoy .up   {{ color: var(--accent); }}
.card-yoy .down {{ color: var(--ocean); }}

/* ── footer ──────────────────────────────────────────── */
footer {{
  border-top: 1px solid var(--border);
  padding-top: 20px;
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--muted);
  letter-spacing: .04em;
  flex-wrap: wrap;
  gap: 8px;
}}

@media (max-width: 820px) {{
  .hero         {{ grid-template-columns: 1fr; gap: 32px; }}
  .hero-title   {{ padding-bottom: 0; }}
  .map-row      {{ grid-template-columns: 1fr; }}
  .dma-grid     {{ grid-template-columns: repeat(2, 1fr); }}
  .kpi-bar      {{ grid-template-columns: repeat(2, 1fr); }}
  .kpi:nth-child(2) {{ border-right: none; }}
}}

@media (prefers-reduced-motion: reduce) {{
  * {{ animation: none !important; transition-duration: 0ms !important; }}
}}
</style>
</head>
<body>
<div class="page">

<!-- ── hero ─────────────────────────────────────────── -->
<div class="hero">
  <div class="hero-title">
    <p class="eyebrow">Google Trends API · 2024 – 2026</p>
    <h1>California<br><span>Hunger</span><br>Signal</h1>
  </div>
  <div class="hero-chart-wrap">
    <canvas id="heroCanvas"></canvas>
    <div class="chart-axis" id="chartAxis"></div>
  </div>
</div>

<div class="divider"></div>

<!-- ── kpi bar ──────────────────────────────────────── -->
<div class="kpi-bar">
  <div class="kpi">
    <span class="kpi-num signal" id="kpiTotal">—</span>
    <span class="kpi-label">Total searches, statewide</span>
  </div>
  <div class="kpi">
    <span class="kpi-num signal" id="kpiYoy">—</span>
    <span class="kpi-label">Avg YoY change, all markets</span>
  </div>
  <div class="kpi">
    <span class="kpi-num" id="kpiWeeks">129 wks</span>
    <span class="kpi-label">Coverage per market</span>
  </div>
  <div class="kpi">
    <span class="kpi-num ocean" id="kpiPeak">—</span>
    <span class="kpi-label">Statewide peak week</span>
  </div>
</div>

<!-- ── map + rank ───────────────────────────────────── -->
<div class="map-row">
  <div class="map-wrap" id="mapWrap">
    <svg id="mapSvg" viewBox="0 0 300 400" xmlns="http://www.w3.org/2000/svg">
      <path id="caOutline" d="{CA_PATH}"/>
      <g id="bubbleLayer"></g>
    </svg>
    <div id="mapTip"></div>
  </div>

  <div class="rank-panel">
    <h2>Markets ranked by total search volume</h2>
    <div id="rankList"></div>
  </div>
</div>

<!-- ── sparkline grid ───────────────────────────────── -->
<div class="grid-head">
  <h2>Weekly trend · all markets</h2>
  <span class="hint">Click a market to highlight across views</span>
</div>
<div class="dma-grid" id="dmaGrid"></div>

<!-- ── footer ───────────────────────────────────────── -->
<footer>
  <span>Source: Google Trends API (alpha) · term: "food bank" · resolution: GEO_TYPE_DESIGNATED_MARKET_AREA · WEEK</span>
  <span id="footDates">—</span>
</footer>

</div><!-- .page -->

<script>
const DATA = {DATA_JSON};

const ACCENT  = '#E8622A';
const OCEAN   = '#1A6B9A';
const GROUND  = '#FFFFFF';
const SURFACE = '#F5F6F8';
const BORDER  = '#E2E5EA';
const TEXT    = '#0D1B2A';
const MUTED   = '#7089A3';

let active = null;

function fmt(n) {{
  if (n >= 1e6) return (n / 1e6).toFixed(1).replace(/\\.0$/, '') + 'M';
  if (n >= 1e3) return Math.round(n / 1e3) + 'K';
  return String(n);
}}
function fmtYoy(v) {{
  return (v >= 0 ? '+' : '') + v.toFixed(1) + '%';
}}
function fmtDate(s) {{
  const d = new Date(s + 'T00:00:00Z');
  return d.toLocaleDateString('en-US', {{ month: 'short', year: 'numeric', timeZone: 'UTC' }});
}}

// ── KPI bar ──────────────────────────────────────────────────
document.getElementById('kpiTotal').textContent  = fmt(DATA.grandTotal);
document.getElementById('kpiYoy').textContent    = fmtYoy(DATA.avgYoy);
document.getElementById('kpiPeak').textContent   = fmtDate(DATA.peakWeek);
document.getElementById('footDates').textContent =
  DATA.weeks[0] + ' → ' + DATA.weeks[DATA.weeks.length - 1];

// ── Hero aggregate chart ──────────────────────────────────────
(function () {{
  const canvas = document.getElementById('heroCanvas');
  const axisEl = document.getElementById('chartAxis');
  const vals   = DATA.agg;
  const n      = vals.length;
  const max    = Math.max(...vals);

  // axis labels: ~6 evenly spaced dates
  const axisDates = [];
  const step = Math.floor(n / 5);
  for (let i = 0; i <= 5; i++) {{
    const idx = Math.min(i * step, n - 1);
    const d   = new Date(DATA.weeks[idx] + 'T00:00:00Z');
    axisDates.push(d.toLocaleDateString('en-US', {{ month: 'short', year: '2-digit', timeZone: 'UTC' }}));
  }}
  axisEl.innerHTML = axisDates.map(s => `<span>${{s}}</span>`).join('');

  function draw() {{
    const dpr = window.devicePixelRatio || 1;
    const W   = canvas.offsetWidth  * dpr;
    const H   = canvas.offsetHeight * dpr;
    if (W === 0) return;
    canvas.width  = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, W, H);

    const padL = 0, padR = 0, padT = 12 * dpr, padB = 4 * dpr;
    const uw = (W - padL - padR) / (n - 1);
    const uh = H - padT - padB;

    const px = i  => padL + i * uw;
    const py = v  => H - padB - (v / max) * uh;

    // grid lines (subtle)
    ctx.strokeStyle = BORDER;
    ctx.lineWidth   = dpr;
    [0.25, 0.5, 0.75, 1.0].forEach(f => {{
      const y = H - padB - f * uh;
      ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(W - padR, y); ctx.stroke();
    }});

    // filled area — draw full extent
    const grad = ctx.createLinearGradient(0, 0, 0, H);
    grad.addColorStop(0, 'rgba(232,98,42,.22)');
    grad.addColorStop(1, 'rgba(232,98,42,0)');

    ctx.beginPath();
    ctx.moveTo(px(0), H - padB);
    for (let i = 0; i < n; i++) ctx.lineTo(px(i), py(vals[i]));
    ctx.lineTo(px(n - 1), H - padB);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // line
    ctx.beginPath();
    for (let i = 0; i < n; i++) {{
      if (i === 0) ctx.moveTo(px(i), py(vals[i]));
      else         ctx.lineTo(px(i), py(vals[i]));
    }}
    ctx.strokeStyle = ACCENT;
    ctx.lineWidth   = 1.5 * dpr;
    ctx.lineJoin    = 'round';
    ctx.stroke();

    // peak annotation
    const pi  = DATA.peakIdx;
    const ppx = px(pi);
    const ppy = py(vals[pi]);
    ctx.beginPath();
    ctx.arc(ppx, ppy, 4 * dpr, 0, Math.PI * 2);
    ctx.fillStyle = ACCENT;
    ctx.fill();

    // annotation label
    ctx.font      = `${{600}} ${{10 * dpr}}px system-ui, sans-serif`;
    ctx.fillStyle = TEXT;
    ctx.textAlign = ppx > W * 0.7 ? 'right' : 'left';
    const lx = ppx > W * 0.7 ? ppx - 8 * dpr : ppx + 8 * dpr;
    ctx.fillText('PEAK · ' + fmtDate(DATA.peakWeek).toUpperCase(), lx, ppy - 6 * dpr);
  }}

  draw();
  window.addEventListener('resize', draw);
}})();

// ── California map ────────────────────────────────────────────
const maxTotal = Math.max(...DATA.dmas.map(d => d.total));

function buildMap() {{
  const layer = document.getElementById('bubbleLayer');
  layer.innerHTML = '';
  const tip  = document.getElementById('mapTip');
  const wrap = document.getElementById('mapWrap');

  DATA.dmas.forEach((d, i) => {{
    const r  = 5 + Math.sqrt(d.total / maxTotal) * 22;
    const g  = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.setAttribute('class', 'dma-bubble' + (active === i ? ' active' : ''));

    const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    c.setAttribute('cx', d.cx);
    c.setAttribute('cy', d.cy);
    c.setAttribute('r',  r.toFixed(1));
    g.appendChild(c);

    if (r > 12) {{
      const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      t.setAttribute('x', d.cx);
      t.setAttribute('y', d.cy);
      t.setAttribute('class', 'bubble-label');
      t.textContent = d.label.split('–')[0].split(' ')[0];
      g.appendChild(t);
    }}

    g.addEventListener('mouseenter', e => {{
      const yoyStr = fmtYoy(d.yoy);
      tip.innerHTML = `<strong style="color:#fff">${{d.label}}</strong><br>${{fmt(d.total)}} searches · ${{yoyStr}} YoY`;
      tip.classList.add('show');
    }});
    g.addEventListener('mousemove', e => {{
      const rect = wrap.getBoundingClientRect();
      let lx = e.clientX - rect.left + 14;
      let ly = e.clientY - rect.top  - 14;
      tip.style.left = lx + 'px';
      tip.style.top  = ly + 'px';
    }});
    g.addEventListener('mouseleave', () => tip.classList.remove('show'));
    g.addEventListener('click', () => setActive(i));

    layer.appendChild(g);
  }});
}}

// ── Rank list ─────────────────────────────────────────────────
function buildRank() {{
  const sorted = [...DATA.dmas].sort((a, b) => b.total - a.total);
  const el     = document.getElementById('rankList');
  el.innerHTML = '';
  const maxT   = sorted[0].total;

  sorted.forEach(d => {{
    const i   = DATA.dmas.indexOf(d);
    const pct = Math.round(d.total / maxT * 100);
    const row = document.createElement('div');
    row.className = 'rank-row' + (active === i ? ' active' : '');
    const yoyClass = d.yoy >= 0 ? 'up' : 'down';
    row.innerHTML = `
      <span class="rank-name">${{d.label}}</span>
      <div class="rank-bar-track"><div class="rank-bar-fill" style="width:${{pct}}%"></div></div>
      <span class="rank-yoy ${{yoyClass}}">${{fmtYoy(d.yoy)}}</span>
    `;
    row.addEventListener('click', () => setActive(i));
    el.appendChild(row);
  }});
}}

// ── Sparkline drawing ─────────────────────────────────────────
function drawSparkline(canvas, vals, isActive) {{
  const dpr = window.devicePixelRatio || 1;
  const W   = canvas.offsetWidth  * dpr;
  const H   = canvas.offsetHeight * dpr;
  if (W === 0) return;
  canvas.width  = W;
  canvas.height = H;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, W, H);

  const n   = vals.length;
  const max = Math.max(...vals) || 1;
  const pad = 2 * dpr;
  const uw  = (W - pad * 2) / (n - 1);
  const uh  = H - pad * 2;
  const px  = i => pad + i * uw;
  const py  = v => H - pad - (v / max) * uh;

  // fill
  const grad = ctx.createLinearGradient(0, 0, 0, H);
  grad.addColorStop(0, isActive ? 'rgba(232,98,42,.3)' : 'rgba(232,98,42,.15)');
  grad.addColorStop(1, 'rgba(232,98,42,0)');
  ctx.beginPath();
  ctx.moveTo(px(0), H - pad);
  for (let i = 0; i < n; i++) ctx.lineTo(px(i), py(vals[i]));
  ctx.lineTo(px(n - 1), H - pad);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  // line
  ctx.beginPath();
  for (let i = 0; i < n; i++) {{
    if (i === 0) ctx.moveTo(px(i), py(vals[i]));
    else         ctx.lineTo(px(i), py(vals[i]));
  }}
  ctx.strokeStyle = isActive ? ACCENT : 'rgba(232,98,42,.55)';
  ctx.lineWidth   = isActive ? 1.8 * dpr : 1.2 * dpr;
  ctx.lineJoin    = 'round';
  ctx.stroke();

  // peak dot
  const pi = vals.indexOf(Math.max(...vals));
  ctx.beginPath();
  ctx.arc(px(pi), py(vals[pi]), 2.5 * dpr, 0, Math.PI * 2);
  ctx.fillStyle = ACCENT;
  ctx.fill();
}}

// ── Grid ──────────────────────────────────────────────────────
function buildGrid() {{
  const grid = document.getElementById('dmaGrid');
  grid.innerHTML = '';

  DATA.dmas.forEach((d, i) => {{
    const isActive = active === i;
    const card     = document.createElement('div');
    card.className = 'dma-card' + (isActive ? ' active' : '');
    const yoyClass = d.yoy >= 0 ? 'up' : 'down';
    card.innerHTML = `
      <div class="card-name">${{d.label}}</div>
      <div class="card-meta">${{fmt(d.total)}} total searches</div>
      <canvas class="card-canvas"></canvas>
      <div class="card-yoy"><span class="val ${{yoyClass}}">${{fmtYoy(d.yoy)}}</span> vs prior 13 wks</div>
    `;
    card.addEventListener('click', () => setActive(i));
    grid.appendChild(card);
  }});

  requestAnimationFrame(() => {{
    document.querySelectorAll('.dma-card').forEach((card, i) => {{
      drawSparkline(card.querySelector('canvas'), DATA.dmas[i].vals, active === i);
    }});
  }});
}}

// ── Active state ──────────────────────────────────────────────
function setActive(i) {{
  active = (active === i) ? null : i;
  buildMap();
  buildRank();
  buildGrid();
}}

// ── Init ──────────────────────────────────────────────────────
buildMap();
buildRank();
buildGrid();

let resizeT;
window.addEventListener('resize', () => {{
  clearTimeout(resizeT);
  resizeT = setTimeout(() => {{
    document.querySelectorAll('.dma-card').forEach((card, i) => {{
      drawSparkline(card.querySelector('canvas'), DATA.dmas[i].vals, active === i);
    }});
  }}, 120);
}});
</script>
</body>
</html>"""

with open('hunger_signal_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Written: {len(html):,} bytes")
print(f"Grand total: {grand_total:,}  |  Avg YoY: {avg_yoy:+.1f}%  |  Peak: {peak_agg_wk}")
