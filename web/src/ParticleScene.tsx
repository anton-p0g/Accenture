import { useEffect, useMemo, useRef, useState } from "react";
import dotsSvg from "./assets/spain-dots.svg?raw";

export type ParticleGroup = { label: string; percentages: Record<string, number | null> };
const COLORS = ["#f0442e", "#263458", "#d59737", "#63887c", "#9c6087", "#6975b5"];
const DRAW_COLORS = [...COLORS, "#b2a69d"];
const OPACITY_STEPS = 24;
// Keep stable identities from the map through every subsequent chart.
const original = [...dotsSvg.matchAll(/<circle cx="([\d.]+)" cy="([\d.]+)"/g)]
  .map((match) => ({ x: Number(match[1]), y: Number(match[2]) }));
const random = (seed: number) => {
  const value = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return value - Math.floor(value);
};
const mapSamples = original.flatMap((point, index) => {
  const neighbor = original.find((other, otherIndex) => otherIndex !== index &&
    Math.hypot(other.x - point.x, other.y - point.y) > 4 &&
    Math.hypot(other.x - point.x, other.y - point.y) < 12);
  return neighbor ? [point, { x: (point.x + neighbor.x) / 2, y: (point.y + neighbor.y) / 2 }] : [point];
});
const MAP = mapSamples.flatMap((point, index) => [0, 1].map((layer) => {
  const seed = index * 2 + layer;
  const angle = random(seed + 1) * Math.PI * 2;
  const offset = Math.sqrt(random(seed + 7)) * (layer ? 4.8 : 2.8);
  return {
    x: point.x + Math.cos(angle) * offset,
    y: point.y + Math.sin(angle) * offset,
    size: layer ? .4 + random(seed + 19) * .7 : .65 + Math.pow(random(seed + 19), 2.4) * 2.1,
  };
}));

type Target = { x: number; y: number; color: string; opacity: number; size?: number };
type ChartRow = { label: string; value: number | null; option: string; color: string; x: number; y: number; width: number; labelX: number; labelWidth: number; textWidth: number; height: number };

export default function ParticleScene({ busy, groups, title, orientation = "horizontal" }: {
  busy: boolean; groups: ParticleGroup[]; title: string; orientation?: "horizontal" | "vertical";
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [dimensions, setDimensions] = useState({ width: 640, height: 400 });
  const stateRef = useRef({ busy, chart: false, targets: [] as Target[], ...dimensions });
  const layout = useMemo(() => {
    const options = [...new Set(groups.flatMap((group) => Object.keys(group.percentages)))];
    const rows: ChartRow[] = [];
    const { width, height } = dimensions;
    const vertical = orientation === "vertical";
    const groupColumns = vertical
      ? Math.min(Math.max(1, groups.length), width >= 1100 ? (groups.length <= 4 ? 4 : 3) : width >= 620 ? 2 : 1)
      : width >= 1100 && groups.length >= 5 ? 3 : width >= 620 && groups.length > 1 ? 2 : 1;
    const groupRows = Math.max(1, Math.ceil(groups.length / groupColumns));
    const gutter = groupColumns > 1 ? 52 : 0;
    const padding = width >= 620 ? 28 : 12;
    const cellWidth = (width - padding * 2 - gutter * (groupColumns - 1)) / groupColumns;
    const sideLabels = !vertical && cellWidth >= 360;
    const minimumHeight = groups.length ? groupRows * (vertical ? 240 : (sideLabels ? 48 : 58) + options.length * (sideLabels ? 30 : 48)) + 18 : 0;
    const cellHeight = (height - 18) / groupRows;
    const optionPitch = Math.min(125, (cellHeight - 48) / Math.max(1, options.length));
    const textWidth = sideLabels ? Math.min(170, Math.max(104, cellWidth * .23)) : 0;
    const barHeight = Math.max(8, Math.min(54, optionPitch * (sideLabels ? .58 : .42)));
    const headings = groups.map((group, index) => ({
      label: group.label,
      x: padding + (index % groupColumns) * (cellWidth + gutter),
      y: 9 + Math.floor(index / groupColumns) * cellHeight,
      width: cellWidth,
    }));
    groups.forEach((group, groupIndex) => {
      options.forEach((option, optionIndex) => {
        const slotWidth = cellWidth / Math.max(1, options.length);
        const columnWidth = Math.min(70, slotWidth * .58);
        const slotX = headings[groupIndex].x + optionIndex * slotWidth;
        rows.push({ label: group.label, option, value: group.percentages[option] ?? null,
          color: COLORS[optionIndex % COLORS.length],
          x: vertical ? slotX + (slotWidth - columnWidth) / 2 : headings[groupIndex].x + (sideLabels ? textWidth + 12 : 0),
          width: vertical ? columnWidth : cellWidth - (sideLabels ? textWidth + 80 : 0),
          y: vertical ? headings[groupIndex].y + 66 : headings[groupIndex].y + (sideLabels ? 40 : 66) + optionIndex * optionPitch,
          labelX: vertical ? slotX : headings[groupIndex].x,
          labelWidth: vertical ? slotWidth : cellWidth,
          textWidth,
          height: vertical ? Math.max(80, cellHeight - 110) : barHeight,
        });
      });
    });
    const mapScale = Math.min((width - 32) / 640, (height - 12) / 523, 1.4);
    // Independent 0–100% axes: response options may be multiple choice, so never normalize their sum.
    const capacity = Math.max(1, Math.floor(MAP.length / Math.max(1, rows.length)));
    const targets = MAP.map((point, index): Target => {
      if (!rows.length) return {
        x: (width - 640 * mapScale) / 2 + point.x * mapScale,
        y: (height - 523 * mapScale) / 2 + point.y * mapScale,
        size: point.size * Math.max(.7, mapScale), color: COLORS[0], opacity: 1,
      };
      const rowIndex = Math.min(rows.length - 1, Math.floor(index / capacity));
      const row = rows[rowIndex];
      const slot = index - rowIndex * capacity;
      const count = rowIndex === rows.length - 1 ? MAP.length - rowIndex * capacity : capacity;
      // Distribute people across a dense band, without any aligned rows or columns.
      // Stratified horizontal positions preserve coverage; vertical positions are individual.
      // Stable seeds avoid reshuffling when React renders the same result again.
      const fraction = (slot + .15 + random(index + 211) * .7) / count;
      const crowdHeight = row.height;
      const crowdY = random(index + 239) * crowdHeight
        + Math.sin(fraction * 17 + rowIndex * 1.7) * 1.1;
      const highlighted = row.value !== null && row.value > 0 && fraction <= row.value / 100;
      return {
        x: row.x + (vertical ? random(index + 239) * row.width + Math.sin(fraction * 17) * .7 : fraction * row.width),
        y: row.y + (vertical ? (1 - fraction) * row.height : crowdY),
        size: (.85 + random(index + 191) * .85) * Math.max(.75, Math.min(2.1, Math.sqrt(row.width * crowdHeight / count) / 3.8)),
        color: row.value === null ? "#b2a69d" : row.color,
        opacity: highlighted ? 1 : .13,
      };
    });
    return { rows, targets, headings, sideLabels, minimumHeight, vertical };
  }, [groups, dimensions, orientation]);

  useEffect(() => {
    stateRef.current = { busy, chart: layout.rows.length > 0, targets: layout.targets, ...dimensions };
  }, [busy, layout, dimensions]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const initialScale = Math.min((canvas.clientWidth - 32) / 640, (canvas.clientHeight - 12) / 523, 1.4);
    const particles = MAP.map((point, index) => {
      const x = (canvas.clientWidth - 640 * initialScale) / 2 + point.x * initialScale;
      const y = (canvas.clientHeight - 523 * initialScale) / 2 + point.y * initialScale;
      return {
      ...point, x, y, color: COLORS[0], opacity: 1,
      baseX: x, baseY: y, fromX: x, fromY: y,
      goalX: x, goalY: y, travelAt: -10000, duration: 1,
      journeyDistance: 0, radius: point.size, halo: index % 12 === 0,
      phase: random(index + 43) * Math.PI * 2,
      pace: .65 + random(index + 71) * 1.1,
      patience: random(index + 101),
      bendX: random(index + 137) * 2 - 1,
      bendY: random(index + 163) * 2 - 1,
      crowdSize: .85 + random(index + 191) * .85,
      wander: 1,
      };
    });
    // Reuse paths grouped by color/opacity instead of filling thousands of individual circles.
    const buckets = Array.from({ length: DRAW_COLORS.length * OPACITY_STEPS }, () => [] as typeof particles);
    let frame = 0;
    let previousTime = 0;
    let visible = true;
    let energy = 0;
    let pulsePhase = 0;
    let strollTime = 0;
    const resize = () => {
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      const width = Math.max(1, canvas.clientWidth);
      const height = Math.max(1, canvas.clientHeight);
      const pixelWidth = Math.round(width * ratio);
      const pixelHeight = Math.round(height * ratio);
      if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) {
        canvas.width = pixelWidth;
        canvas.height = pixelHeight;
      }
      setDimensions((current) => current.width === width && current.height === height ? current : { width, height });
    };
    const observer = new ResizeObserver(resize);
    observer.observe(canvas);
    const visibility = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
    });
    visibility.observe(canvas);
    const draw = (time: number) => {
      frame = requestAnimationFrame(draw);
      const delta = Math.min(1000, time - previousTime || 16);
      previousTime = time;
      if (!visible || document.hidden) return;
      const animationDelta = Math.min(delta, 50);
      const ease = motion.matches ? 1 : 1 - Math.exp(-animationDelta / 340);
      energy += ((stateRef.current.busy ? 1 : 0) - energy) * (1 - Math.exp(-animationDelta / 650));
      // Integrate the phase: changing loading intensity must never jump the heartbeat's phase.
      pulsePhase += animationDelta * (.00165 + energy * .00035);
      strollTime += animationDelta;
      // A shared loading beat is visible across the map instead of cancelling out
      // between thousands of independently phased particles.
      const heartbeat = motion.matches ? 0 : Math.pow((1 + Math.sin(pulsePhase)) / 2, 1.5);
      const mapBreath = stateRef.current.chart ? 1 : 1 + energy * heartbeat * .03;
      for (const bucket of buckets) bucket.length = 0;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.setTransform(canvas.width / stateRef.current.width, 0, 0, canvas.height / stateRef.current.height, 0, 0);
      particles.forEach((particle, index) => {
        const target = stateRef.current.targets[index] ?? { ...MAP[index], color: COLORS[0], opacity: 1 };
        if (target.x !== particle.goalX || target.y !== particle.goalY) {
          // Each person departs at their own pace and follows an individual curved route.
          // Start from the current position even if a new view interrupts a journey.
          particle.fromX = particle.baseX;
          particle.fromY = particle.baseY;
          particle.goalX = target.x;
          particle.goalY = target.y;
          particle.travelAt = time + particle.patience * 260;
          particle.journeyDistance = Math.hypot(target.x - particle.fromX, target.y - particle.fromY);
          particle.duration = 1050 + 1350 / particle.pace + particle.journeyDistance * .7;
        }
        const progress = motion.matches ? 1 : Math.max(0, Math.min(1, (time - particle.travelAt) / particle.duration));
        if (progress < 1) {
          const step = progress * progress * (3 - 2 * progress);
          const detour = Math.min(85, particle.journeyDistance * .3) * Math.sin(Math.PI * step);
          particle.baseX = particle.fromX + (particle.goalX - particle.fromX) * step
            + detour * (particle.bendX + .28 * Math.sin(step * 14 + particle.phase));
          particle.baseY = particle.fromY + (particle.goalY - particle.fromY) * step
            + detour * (particle.bendY + .28 * Math.cos(step * 12 + particle.phase));
        } else {
          particle.baseX = particle.goalX;
          particle.baseY = particle.goalY;
        }
        const stroll = strollTime * .00045 * particle.pace;
        const drift = motion.matches ? 0 : stateRef.current.chart ? .35 + particle.patience * .22 : 2.3 + particle.patience * 1.7 + energy * .8;
        particle.wander += (drift - particle.wander) * ease;
        const wander = motion.matches ? 0 : particle.wander;
        particle.x = particle.baseX + (Math.sin(stroll + particle.phase) + .35 * Math.sin(stroll * 2.3 + particle.phase * 1.7)) * wander;
        particle.y = particle.baseY + (Math.cos(stroll * .83 + particle.phase * 1.3) + .35 * Math.sin(stroll * 1.9 + particle.phase)) * wander;
        particle.x = stateRef.current.width / 2 + (particle.x - stateRef.current.width / 2) * mapBreath;
        particle.y = stateRef.current.height / 2 + (particle.y - stateRef.current.height / 2) * mapBreath;
        particle.opacity += (target.opacity - particle.opacity) * ease;
        const pulse = motion.matches ? 0 : (1 + Math.sin(pulsePhase + particle.phase)) / 2;
        const targetSize = target.size ?? (stateRef.current.chart ? particle.crowdSize : MAP[index].size);
        particle.size += (targetSize - particle.size) * ease;
        particle.radius = particle.size * (stateRef.current.chart ? 1 + pulse * .12 : .85 + pulse * .55 + energy * heartbeat * 2);
        const brightness = stateRef.current.chart ? .65 + pulse * .35
          : Math.min(1, (.65 + pulse * .35) * (1 - energy * .4) + energy * heartbeat * .5);
        const alpha = brightness * particle.opacity;
        const opacityIndex = Math.min(OPACITY_STEPS - 1, Math.floor(alpha * OPACITY_STEPS));
        const colorIndex = Math.max(0, DRAW_COLORS.indexOf(target.color));
        buckets[colorIndex * OPACITY_STEPS + opacityIndex].push(particle);
      });
      buckets.forEach((bucket, index) => {
        if (!bucket.length) return;
        const alpha = ((index % OPACITY_STEPS) + .5) / OPACITY_STEPS;
        ctx.fillStyle = DRAW_COLORS[Math.floor(index / OPACITY_STEPS)];
        if (energy > .04 && !motion.matches) {
          ctx.globalAlpha = alpha * energy * (.045 + heartbeat * .2);
          ctx.beginPath();
          for (const particle of bucket) {
            if (!particle.halo) continue;
            const radius = particle.radius * 3.2;
            ctx.moveTo(particle.x + radius, particle.y);
            ctx.arc(particle.x, particle.y, radius, 0, Math.PI * 2);
          }
          ctx.fill();
        }
        ctx.globalAlpha = alpha;
        ctx.beginPath();
        for (const particle of bucket) {
          ctx.moveTo(particle.x + particle.radius, particle.y);
          ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
        }
        ctx.fill();
      });
      ctx.globalAlpha = 1;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
    };
    frame = requestAnimationFrame(draw);
    return () => { cancelAnimationFrame(frame); observer.disconnect(); visibility.disconnect(); };
  }, []);

  return <figure className={`particle-scene${layout.rows.length ? " particle-scene--chart" : ""}`} aria-label={title}>
    {busy && <figcaption className="scene-caption" role="status">
      <span className="scene-status scene-status--busy" /> Escuchando a la España sintética…
    </figcaption>}
    <div className="particle-stage" style={layout.minimumHeight ? { minHeight: layout.minimumHeight } : undefined}>
      <canvas ref={canvasRef} role="img" aria-label={busy ? "Mapa de España con un latido más intenso mientras se prepara la respuesta" : layout.rows.length ? `Gráfico de puntos: ${title}. Datos detallados en Cifras y fuentes.` : `Mapa de España formado por ${MAP.length} puntos animados`} />
      <div className="particle-labels" aria-hidden="true">
        {layout.headings.map((group) => <div className="particle-group-heading" key={group.label} style={{ top: group.y, left: group.x, width: group.width }}>{group.label}</div>)}
        {layout.rows.map((row) => <div className={`particle-row-label${layout.sideLabels ? " particle-row-label--side" : ""}${layout.vertical ? " particle-row-label--vertical" : ""}`} key={`${row.label}-${row.option}`} style={{ top: row.y + (layout.vertical ? row.height + 10 : layout.sideLabels ? row.height / 2 : 0), left: row.labelX, width: row.labelWidth, ...(layout.sideLabels ? { gridTemplateColumns: `${row.textWidth}px minmax(0, 1fr) 56px` } : {}) }}>
          <span title={row.option.replaceAll("_", " ")}>{row.option.replaceAll("_", " ")}</span>
          <strong style={{ color: row.color, ...(layout.vertical ? { top: -row.height - 32 } : {}) }}>{row.value === null ? "Sin dato" : `${new Intl.NumberFormat("es-ES", { maximumFractionDigits: 1 }).format(row.value)} %`}</strong>
        </div>)}
      </div>
    </div>
    {layout.rows.length > 0 && <p className="scene-footnote"><span className="legend-dot" /> Color intenso: respuesta · Tenue: resto del grupo. Porcentajes dentro de cada grupo.</p>}
  </figure>;
}
