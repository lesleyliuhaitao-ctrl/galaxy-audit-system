import { useEffect, useMemo, useRef, useState } from "react";
import { mockGalaxies } from "./data/mockAudit";
import { copy } from "./i18n";
import { AuditMode, GalaxyRecord, Lang, PathologyTag, ViewMode } from "./types";

const dataUrl = (relativePath: string) =>
  `${import.meta.env.BASE_URL}${relativePath.replace(/^\/+/, "")}`;

const tagOptions: PathologyTag[] = [
  "acm-recovered",
  "distance-sensitive",
  "geometry-fragile",
  "MOND-resistant",
  "gas-flat",
  "stellar-hostage",
];

function humanizeTag(tag: PathologyTag | "all", t: Record<string, string>) {
  const map: Record<PathologyTag | "all", string> = {
    all: t.tag_all,
    "acm-recovered": t.tag_acmRecovered,
    "distance-sensitive": t.tag_distanceSensitive,
    "geometry-fragile": t.tag_geometryFragile,
    "MOND-resistant": t.tag_mondResistant,
    "gas-flat": t.tag_gasFlat,
    "stellar-hostage": t.tag_stellarHostage,
  };
  return map[tag];
}

type PathologyPoint = {
  id: string;
  group: string;
  distanceRelErrPct: number;
  deltaCppMondMinusAcm: number;
  l36: number;
  gasToLightProxy: number;
  outerGasSlope: number;
  outerToInnerGasRatio: number;
  outerGasCurvature: number;
  vgasHighFreqPowerFrac: number;
};

function polylinePoints(values: number[], width: number, height: number) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = Math.max(max - min, 1);
  return values
    .map((v, i) => {
      const x = (i / Math.max(values.length - 1, 1)) * width;
      const y = height - ((v - min) / span) * height;
      return `${x},${y}`;
    })
    .join(" ");
}

function Chart({
  title,
  note,
  series,
  xLabel,
  yLabel,
}: {
  title: string;
  note?: string;
  series: Array<{ label: string; color: string; values: number[] }>;
  xLabel?: string;
  yLabel?: string;
}) {
  const all = series.flatMap((s) => s.values);
  const min = Math.min(...all);
  const max = Math.max(...all);
  const width = 580;
  const height = 220;
  const padL = 40;
  const padB = 28;

  return (
    <div className="chart-block">
      <div className="chart-head">
        <h3>{title}</h3>
        <div className="chart-range">
          {min.toFixed(1)} – {max.toFixed(1)}
        </div>
      </div>
      {note && <p className="chart-note">{note}</p>}
      <svg
        viewBox={`0 0 ${width + padL} ${height + padB}`}
        className="chart-svg"
        role="img"
      >
        {/* y-axis label */}
        {yLabel && (
          <text
            x="10"
            y={height / 2}
            transform={`rotate(-90, 10, ${height / 2})`}
            className="axis-label"
            textAnchor="middle"
          >
            {yLabel}
          </text>
        )}
        {/* grid lines */}
        <g transform={`translate(${padL}, 0)`}>
          {[0.2, 0.4, 0.6, 0.8].map((fraction) => (
            <line
              key={fraction}
              x1="0"
              y1={height * fraction}
              x2={width}
              y2={height * fraction}
              className="grid-line"
            />
          ))}
          {series.map((item) => (
            <polyline
              key={item.label}
              points={polylinePoints(item.values, width, height)}
              fill="none"
              stroke={item.color}
              strokeWidth="2.5"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          ))}
          {/* x-axis label */}
          {xLabel && (
            <text
              x={width / 2}
              y={height + 22}
              className="axis-label"
              textAnchor="middle"
            >
              {xLabel}
            </text>
          )}
        </g>
      </svg>
      <div className="chart-legend">
        {series.map((item) => (
          <span key={item.label} className="legend-item">
            <span className="legend-dot" style={{ backgroundColor: item.color }} />
            {item.label}
          </span>
        ))}
      </div>
    </div>
  );
}

function scatterPoints(
  points: PathologyPoint[],
  xKey: keyof PathologyPoint,
  yKey: keyof PathologyPoint,
  width: number,
  height: number,
) {
  const xs = points.map((p) => Number(p[xKey])).filter((v) => Number.isFinite(v));
  const ys = points.map((p) => Number(p[yKey])).filter((v) => Number.isFinite(v));
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const spanX = Math.max(maxX - minX, 1e-6);
  const spanY = Math.max(maxY - minY, 1e-6);

  return points.map((p) => {
    const x = ((Number(p[xKey]) - minX) / spanX) * width;
    const y = height - ((Number(p[yKey]) - minY) / spanY) * height;
    const color =
      p.group === "acm_better_102"
        ? "#7bc3ff"
        : p.group === "geom_hostage_22"
          ? "#dd614a"
          : p.group === "stellar_hostage_9"
            ? "#ffb347"
            : "#71b340";
    return { id: p.id, x, y, color };
  });
}

function PathologyMiniMap({
  title,
  subtitle,
  points,
  xKey,
  yKey,
}: {
  title: string;
  subtitle: string;
  points: PathologyPoint[];
  xKey: keyof PathologyPoint;
  yKey: keyof PathologyPoint;
}) {
  const width = 220;
  const height = 118;
  const dots = scatterPoints(points, xKey, yKey, width, height);

  return (
    <div className="mini-map">
      <div className="mini-map-head">
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="mini-map-svg" role="img">
        {[0.25, 0.5, 0.75].map((f) => (
          <line key={`h-${f}`} x1="0" y1={height * f} x2={width} y2={height * f} className="grid-line" />
        ))}
        {[0.25, 0.5, 0.75].map((f) => (
          <line key={`v-${f}`} x1={width * f} y1="0" x2={width * f} y2={height} className="grid-line" />
        ))}
        {dots.map((dot) => (
          <circle key={dot.id} cx={dot.x} cy={dot.y} r="2.9" fill={dot.color} opacity="0.84" />
        ))}
      </svg>
    </div>
  );
}

// ── Popular (simple) view ────────────────────────────────────────────────────
function PopularView({
  galaxies,
  selected,
  selectedId,
  setSelectedId,
  query,
  setQuery,
  adjusted,
  lang,
}: {
  galaxies: GalaxyRecord[];
  selected: GalaxyRecord;
  selectedId: string;
  setSelectedId: (id: string) => void;
  query: string;
  setQuery: (q: string) => void;
  adjusted: { obs: number[]; acm: number[]; mond: number[] };
  lang: Lang;
}) {
  const t = copy[lang];

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return galaxies.filter(
      (g) => !q || g.displayName.toLowerCase().includes(q) || g.id.toLowerCase().includes(q),
    );
  }, [galaxies, query]);

  const confidenceText =
    selected.confidence === "high"
      ? t.popularConfidenceHigh
      : selected.confidence === "medium"
        ? t.popularConfidenceMedium
        : t.popularConfidenceFragile;

  const sensitivityText =
    selected.primarySensitivity === "distance"
      ? t.popularSensitivityDistance
      : selected.primarySensitivity === "inclination"
        ? t.popularSensitivityInclination
        : selected.primarySensitivity === "shape-depth"
          ? t.popularSensitivityShape
          : t.popularSensitivityMass;

  const tagExplainMap: Record<string, string> = {
    "acm-recovered": t.popularTagExplain_acmRecovered,
    "distance-sensitive": t.popularTagExplain_distanceSensitive,
    "geometry-fragile": t.popularTagExplain_geometryFragile,
    "MOND-resistant": t.popularTagExplain_mondResistant,
    "gas-flat": t.popularTagExplain_gasFlat,
    "stellar-hostage": t.popularTagExplain_stellarHostage,
  };

  return (
    <div className="popular-shell">
      {/* intro cards */}
      <div className="popular-intro-grid">
        <div className="intro-card">
          <div className="intro-card-label">{t.popularSectionWhat}</div>
          <p>{t.popularBodyWhat}</p>
        </div>
        <div className="intro-card">
          <div className="intro-card-label">ACM</div>
          <p>{t.popularWhatIsACM}</p>
        </div>
        <div className="intro-card">
          <div className="intro-card-label">MOND</div>
          <p>{t.popularWhatIsMOND}</p>
        </div>
        <div className="intro-card">
          <div className="intro-card-label">{t.popularSectionWhy}</div>
          <p>{t.popularBodyWhy}</p>
        </div>
      </div>

      <div className="popular-layout">
        {/* galaxy list */}
        <aside className="popular-sidebar">
          <input
            className="search-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t.search}
          />
          <div className="galaxy-list">
            {filtered.map((g) => (
              <button
                key={g.id}
                className={g.id === selectedId ? "galaxy-item active" : "galaxy-item"}
                onClick={() => setSelectedId(g.id)}
              >
                <span>{g.displayName}</span>
                <span className={`winner-pill ${g.winner}`}>{g.winner.toUpperCase()}</span>
              </button>
            ))}
          </div>
        </aside>

        {/* detail */}
        <div className="popular-detail">
          {/* result card */}
          <div className="popular-result-card">
            <div className="popular-galaxy-name">{selected.displayName}</div>
            <div className="popular-winner-row">
              <span className="popular-winner-label">{t.popularWinnerPrefix}</span>
              <span className={`popular-winner-badge ${selected.winner}`}>
                {selected.winner.toUpperCase()}
              </span>
            </div>
            <p className="popular-confidence-text">{confidenceText}</p>
            <div className="popular-sensitivity-pill">{sensitivityText}</div>
            <div className="popular-tags">
              {selected.pathologyTags.map((tag) => (
                <div key={tag} className="popular-tag-row">
                  <span className="popular-tag-dot" />
                  <span>{tagExplainMap[tag] ?? tag}</span>
                </div>
              ))}
            </div>
          </div>

          {/* chart */}
          <Chart
            title={t.popularChartTitle}
            note={t.popularChartNote}
            xLabel={t.axisRadius}
            yLabel={t.axisVelocity}
            series={[
              { label: t.legendObserved, color: "#f4f1de", values: adjusted.obs },
              { label: t.legendAcm, color: "#dd614a", values: adjusted.acm },
              { label: t.legendMond, color: "#4ea699", values: adjusted.mond },
            ]}
          />
        </div>
      </div>
    </div>
  );
}

// ── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const atlasRef = useRef<HTMLElement | null>(null);
  const [galaxies, setGalaxies] = useState<GalaxyRecord[]>(mockGalaxies);
  const [pathologyPoints, setPathologyPoints] = useState<PathologyPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [lang, setLang] = useState<Lang>("en");
  const [viewMode, setViewMode] = useState<ViewMode>("popular");
  const [query, setQuery] = useState("");
  const [activeTag, setActiveTag] = useState<PathologyTag | "all">("all");
  const [selectedId, setSelectedId] = useState(mockGalaxies[0].id);
  const [mode, setMode] = useState<AuditMode>("official");
  const [showResiduals, setShowResiduals] = useState(true);
  const [showBaryons, setShowBaryons] = useState(true);
  const [normalizeByError, setNormalizeByError] = useState(false);
  const [distanceScale, setDistanceScale] = useState(1);
  const [inclinationDelta, setInclinationDelta] = useState(0);

  const t = copy[lang];

  useEffect(() => {
    let alive = true;
    fetch(dataUrl("data/audit-bundle.json"))
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error("bundle fetch failed"))))
      .then((bundle) => {
        if (!alive || !bundle?.galaxies?.length) return;
        setGalaxies(bundle.galaxies as GalaxyRecord[]);
        setPathologyPoints((bundle.pathologyMap?.points ?? []) as PathologyPoint[]);
        if (bundle.summary?.defaultGalaxyId) setSelectedId(String(bundle.summary.defaultGalaxyId));
      })
      .catch(() => { if (!alive) return; setGalaxies(mockGalaxies); setPathologyPoints([]); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return galaxies.filter((galaxy) => {
      const tagPass = activeTag === "all" || galaxy.pathologyTags.includes(activeTag);
      const queryPass = !q || galaxy.displayName.toLowerCase().includes(q) || galaxy.id.toLowerCase().includes(q);
      return tagPass && queryPass;
    });
  }, [activeTag, galaxies, query]);

  const selected =
    filtered.find((g) => g.id === selectedId) ??
    galaxies.find((g) => g.id === selectedId) ??
    galaxies[0];

  const adjusted = useMemo(() => {
    const distanceFactor = distanceScale;
    const modeFactor = mode === "official" ? 1 : mode === "fragile" ? 0.93 : 1.04;
    const acmBoost = distanceFactor * modeFactor;
    const mondBoost = 1 + (distanceFactor - 1) * 0.45;
    const obs = selected.profile.vObs;
    const err = selected.profile.vObsErr;
    const acm = selected.profile.vAcm.map((v) => v * acmBoost * (1 + inclinationDelta * 0.002));
    const mond = selected.profile.vMond.map((v) => v * mondBoost * (1 + inclinationDelta * 0.001));
    const residualAcm = obs.map((v, i) => { const raw = v - acm[i]; return normalizeByError ? raw / Math.max(err[i], 1) : raw; });
    const residualMond = obs.map((v, i) => { const raw = v - mond[i]; return normalizeByError ? raw / Math.max(err[i], 1) : raw; });
    return { obs, acm, mond, residualAcm, residualMond };
  }, [distanceScale, inclinationDelta, mode, normalizeByError, selected]);

  const autoNote =
    mode === "audit" ? t.autoNoteAudit : distanceScale > 1.03 ? t.autoNoteDistance : t.autoNoteInclination;

  const handleStartFlagged = () => {
    const flagged =
      galaxies.find((g) => g.pathologyTags.includes("distance-sensitive")) ??
      galaxies.find((g) => g.pathologyTags.includes("MOND-resistant")) ??
      galaxies[0];
    if (flagged) { setSelectedId(flagged.id); setActiveTag("all"); setQuery(""); }
  };

  const handleBrowseAll = () => {
    setViewMode("expert");
    setActiveTag("all");
    setQuery("");
    atlasRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero-copy">
          <div className="eyebrow">{t.heroEyebrow}</div>
          <h1>{t.title}</h1>
          <p>{t.subtitle}</p>
          <div className="hero-actions">
            <button className="primary-btn" onClick={handleStartFlagged}>{t.startFlagged}</button>
            <button className="ghost-btn" onClick={handleBrowseAll}>{t.browseAll}</button>
          </div>
        </div>
        <div className="hero-controls">
          {/* view mode */}
          <div className="switch-group">
            <button
              className={viewMode === "popular" ? "mode-btn active" : "mode-btn"}
              onClick={() => setViewMode("popular")}
            >
              {t.popularMode}
            </button>
            <button
              className={viewMode === "expert" ? "mode-btn active" : "mode-btn"}
              onClick={() => setViewMode("expert")}
            >
              {t.expertMode}
            </button>
          </div>
          {/* language */}
          <div className="switch-group">
            <button className={lang === "en" ? "mode-btn active" : "mode-btn"} onClick={() => setLang("en")}>EN</button>
            <button className={lang === "zh" ? "mode-btn active" : "mode-btn"} onClick={() => setLang("zh")}>中</button>
          </div>
        </div>
      </header>

      {viewMode === "popular" ? (
        <PopularView
          galaxies={galaxies}
          selected={selected}
          selectedId={selectedId}
          setSelectedId={setSelectedId}
          query={query}
          setQuery={setQuery}
          adjusted={adjusted}
          lang={lang}
        />
      ) : (
        <>
          <section className="overview-panel" ref={atlasRef}>
            <div className="panel-header">{t.atlasLabel}</div>
            <div className="overview-copy">
              <h2>{t.atlasHeadline}</h2>
              <p>{t.atlasBody}</p>
            </div>
            <div className="mini-map-grid">
              <PathologyMiniMap title={t.geometryPlaneTitle} subtitle={t.geometryPlaneSubtitle} points={pathologyPoints} xKey="distanceRelErrPct" yKey="deltaCppMondMinusAcm" />
              <PathologyMiniMap title={t.massPlaneTitle} subtitle={t.massPlaneSubtitle} points={pathologyPoints} xKey="l36" yKey="gasToLightProxy" />
              <PathologyMiniMap title={t.gasShapeTitle} subtitle={t.gasShapeSubtitle} points={pathologyPoints} xKey="outerGasSlope" yKey="outerToInnerGasRatio" />
              <PathologyMiniMap title={t.spectrumPlaneTitle} subtitle={t.spectrumPlaneSubtitle} points={pathologyPoints} xKey="outerGasCurvature" yKey="vgasHighFreqPowerFrac" />
            </div>
          </section>

          <main className="layout">
            <aside className="selector-panel">
              <div className="panel-header">{t.selectorTitle}</div>
              <input className="search-input" value={query} onChange={(e) => setQuery(e.target.value)} placeholder={t.search} />
              <div className="tag-row">
                <button className={activeTag === "all" ? "tag active" : "tag"} onClick={() => setActiveTag("all")}>
                  {humanizeTag("all", t)}
                </button>
                {tagOptions.map((tag) => (
                  <button key={tag} className={activeTag === tag ? "tag active" : "tag"} onClick={() => setActiveTag(tag)}>
                    {humanizeTag(tag, t)}
                  </button>
                ))}
              </div>
              <div className="galaxy-list">
                {filtered.map((galaxy) => (
                  <button key={galaxy.id} className={selected.id === galaxy.id ? "galaxy-item active" : "galaxy-item"} onClick={() => setSelectedId(galaxy.id)}>
                    <span>{galaxy.displayName}</span>
                    <span className={`winner-pill ${galaxy.winner}`}>{galaxy.winner}</span>
                  </button>
                ))}
              </div>
            </aside>

            <section className="content-shell">
              <section className="main-panel">
                <div className="panel-header">{t.comparisonTitle}</div>
                {loading && <div className="auto-note">{t.loadingBundle}</div>}
                <Chart
                  title={t.chartRotation}
                  xLabel={t.axisRadius}
                  yLabel={t.axisVelocity}
                  series={[
                    { label: t.legendObserved, color: "#f4f1de", values: adjusted.obs },
                    { label: t.legendAcm, color: "#dd614a", values: adjusted.acm },
                    { label: t.legendMond, color: "#4ea699", values: adjusted.mond },
                    ...(showBaryons
                      ? [
                          { label: t.legendGas, color: "#d4b483", values: selected.profile.vGas },
                          { label: t.legendDisk, color: "#8093f1", values: selected.profile.vDisk },
                        ]
                      : []),
                  ]}
                />
                {showResiduals && (
                    <Chart
                      title={t.residualTitle}
                      xLabel={t.axisRadius}
                      yLabel={normalizeByError ? t.axisResidualNorm : t.axisResidual}
                      series={[
                      { label: t.legendAcmResidual, color: "#dd614a", values: adjusted.residualAcm },
                      { label: t.legendMondResidual, color: "#4ea699", values: adjusted.residualMond },
                    ]}
                  />
                )}
              </section>

              <div className="side-stack">
                <section className="controls-panel">
                  <div className="panel-header">{t.controlsTitle}</div>
                  <label className="control-block">
                    <span>{t.distanceScale}: {distanceScale.toFixed(2)}x</span>
                    <input type="range" min="0.85" max="1.15" step="0.01" value={distanceScale} onChange={(e) => setDistanceScale(Number(e.target.value))} />
                  </label>
                  <label className="control-block">
                    <span>{t.inclination}: {inclinationDelta > 0 ? "+" : ""}{inclinationDelta}°</span>
                    <input type="range" min="-12" max="12" step="1" value={inclinationDelta} onChange={(e) => setInclinationDelta(Number(e.target.value))} />
                  </label>
                  <label className="control-block">
                    <span>{t.mode}</span>
                    <select value={mode} onChange={(e) => setMode(e.target.value as AuditMode)}>
                      <option value="official">{t.official}</option>
                      <option value="fragile">{t.fragile}</option>
                      <option value="audit">{t.audit}</option>
                    </select>
                  </label>
                  <label className="toggle"><input type="checkbox" checked={showResiduals} onChange={() => setShowResiduals((v) => !v)} />{t.showResiduals}</label>
                  <label className="toggle"><input type="checkbox" checked={showBaryons} onChange={() => setShowBaryons((v) => !v)} />{t.showBaryons}</label>
                  <label className="toggle"><input type="checkbox" checked={normalizeByError} onChange={() => setNormalizeByError((v) => !v)} />{t.normalizeByError}</label>
                  <div className="auto-note">{autoNote}</div>
                </section>

                <section className="verdict-panel">
                  <div className="panel-header">{t.verdictTitle}</div>
                  <div className="verdict-card">
                    <div className="verdict-row">
                      <span>{t.currentWinner}</span>
                      <strong className={`winner-text ${selected.winner}`}>{selected.winner.toUpperCase()}</strong>
                    </div>
                    <div className="verdict-row">
                      <span>{t.sensitivity}</span>
                      <strong>{selected.primarySensitivity}</strong>
                    </div>
                    <div className="verdict-row">
                      <span>{t.confidence}</span>
                      <strong>{selected.confidence}</strong>
                    </div>
                    <div className="verdict-row">
                      <span>{t.tags}</span>
                      <div className="tag-cluster">
                        {selected.pathologyTags.map((tag) => (
                          <span key={tag} className="mini-tag">{humanizeTag(tag, t)}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="metadata-card">
                    <div className="panel-header">{t.metadata}</div>
                    <div className="meta-line"><span>{t.obsStructure}</span></div>
                    <div className="meta-grid">
                      <div><span>D</span><strong>{selected.distanceMpc.toFixed(2)} Mpc</strong></div>
                      <div><span>eD</span><strong>{selected.distanceErrorMpc.toFixed(2)} Mpc</strong></div>
                      <div><span>i</span><strong>{selected.inclinationDeg.toFixed(0)}°</strong></div>
                      <div><span>QC</span><strong>{selected.geometryFlag}</strong></div>
                      <div><span>ACM CPP</span><strong>{selected.acmCpp.toFixed(2)}</strong></div>
                      <div><span>MOND CPP</span><strong>{selected.mondCpp.toFixed(2)}</strong></div>
                      <div><span>L3.6</span><strong>{selected.structure.l36.toFixed(2)}</strong></div>
                      <div><span>Gas/L</span><strong>{selected.structure.gasToLightProxy.toFixed(2)}</strong></div>
                      <div><span>Slope</span><strong>{selected.structure.outerGasSlope.toFixed(2)}</strong></div>
                      <div><span>Curvature</span><strong>{selected.structure.outerGasCurvature.toFixed(2)}</strong></div>
                    </div>
                  </div>
                </section>
              </div>
            </section>
          </main>
        </>
      )}
    </div>
  );
}
