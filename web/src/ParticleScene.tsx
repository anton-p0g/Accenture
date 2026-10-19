import { useEffect, useMemo, useRef } from "react";
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

type Target = { x: number; y: number; color: string; opacity: number };
type ChartRow = { label: string; value: number | null; option: string; color: string; x: number; y: number; width: number };

export default function ParticleScene({ busy, groups, title }: {
  busy: boolean; groups: ParticleGroup[]; title: string;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef({ busy, chart: false, targets: [] as Target[] });
  const layout = useMemo(() => {
    const options = [...new Set(groups.flatMap((group) => Object.keys(group.percentages)))];
    const rows: ChartRow[] = [];
    const groupColumns = groups.length > 2 ? 2 : 1;
    const groupRows = Math.ceil(groups.length / groupColumns);
    const cellWidth = groupColumns === 2 ? 280 : 605;
    groups.forEach((group, groupIndex) => {
      options.forEach((option, optionIndex) => {
        rows.push({ label: group.label, option, value: group.percentages[option] ?? null,
          color: COLORS[optionIndex % COLORS.length],
          x: 16 + (groupIndex % groupColumns) * 330,
          width: cellWidth,
          y: 45 + Math.floor(groupIndex / groupColumns) * (460 / groupRows) + optionIndex * (395 / groupRows / Math.max(1, options.length)),
        });
      });
    });
    // Independent 0–100% axes: response options may be multiple choice, so never normalize their sum.
    const capacity = Math.max(1, Math.floor(MAP.length / Math.max(1, rows.length)));
    const targets = MAP.map((point, index): Target => {
      if (!rows.length) return { ...point, color: COLORS[0], opacity: 1 };
      const rowIndex = Math.min(rows.length - 1, Math.floor(index / capacity));
      const row = rows[rowIndex];
      const slot = index - rowIndex * capacity;
      const count = rowIndex === rows.length - 1 ? MAP.length - rowIndex * capacity : capacity;
      // Similar horizontal and vertical spacing prevents the sparse vertical stripes.
      const availableHeight = Math.min(36, 395 / Math.max(1, groupRows) / Math.max(1, options.length) - 24);
      const dotRows = Math.max(3, Math.min(Math.floor(availableHeight / 3.8) + 1, Math.round(count * 4 / row.width)));
      // Distribute people across a dense band, without any aligned rows or columns.
      // Stratified horizontal positions preserve coverage; vertical positions are individual.
      // Stable seeds avoid reshuffling when React renders the same result again.
      const fraction = (slot + .15 + random(index + 211) * .7) / count;
      const crowdHeight = Math.max(7.6, (dotRows - 1) * 3.8);
      const crowdY = random(index + 239) * crowdHeight
        + Math.sin(fraction * 17 + rowIndex * 1.7) * 1.1;
      const highlighted = row.value !== null && row.value > 0 && fraction <= row.value / 100;
      return {
        x: row.x + fraction * row.width,
        y: row.y + crowdY,
        color: row.value === null ? "#b2a69d" : row.color,
        opacity: highlighted ? 1 : .13,
      };
    });
    return { rows, targets };
  }, [groups]);

  useEffect(() => {
    stateRef.current = { busy, chart: layout.rows.length > 0, targets: layout.targets };
  }, [busy, layout]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const particles = MAP.map((point, index) => ({
      ...point, color: COLORS[0], opacity: 1,
      baseX: point.x, baseY: point.y, fromX: point.x, fromY: point.y,
      goalX: point.x, goalY: point.y, travelAt: -10000, duration: 1,
      journeyDistance: 0, radius: point.size, halo: index % 12 === 0,
      phase: random(index + 43) * Math.PI * 2,
      pace: .65 + random(index + 71) * 1.1,
      patience: random(index + 101),
      bendX: random(index + 137) * 2 - 1,
      bendY: random(index + 163) * 2 - 1,
      crowdSize: .85 + random(index + 191) * .85,
      wander: 1,
    }));
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
      canvas.width = Math.round(canvas.clientWidth * ratio);
      canvas.height = Math.round(canvas.clientHeight * ratio);
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
      ctx.setTransform(canvas.width / 640, 0, 0, canvas.height / 523, 0, 0);
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
        particle.x = 320 + (particle.x - 320) * mapBreath;
        particle.y = 261.5 + (particle.y - 261.5) * mapBreath;
        particle.opacity += (target.opacity - particle.opacity) * ease;
        const pulse = motion.matches ? 0 : (1 + Math.sin(pulsePhase + particle.phase)) / 2;
        const targetSize = stateRef.current.chart ? particle.crowdSize : MAP[index].size;
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

  return <figure className={`particle-scene${layout.rows.length ? " particle-scene--chart" : ""}`}>
    <figcaption className="scene-caption" aria-live="polite">
      <span className={`scene-status${busy ? " scene-status--busy" : ""}`} />
      {busy ? "Escuchando a la España sintética…" : layout.rows.length ? title : "Una sociedad. Miles de perspectivas."}
    </figcaption>
    <div className="particle-stage">
      <canvas ref={canvasRef} role="img" aria-label={busy ? "Mapa de España con un latido más intenso mientras se prepara la respuesta" : layout.rows.length ? `Gráfico de puntos: ${title}. Datos detallados debajo de la pregunta.` : `Mapa de España formado por ${MAP.length} puntos animados`} />
      <div className="particle-labels" aria-hidden="true">
        {layout.rows.map((row, index) => <div className="particle-row-label" key={`${row.label}-${row.option}`} style={{ top: `${row.y / 523 * 100}%`, left: `${row.x / 640 * 100}%`, width: `${row.width / 640 * 100}%` }}>
          <span>{index === 0 || layout.rows[index - 1].label !== row.label ? <b>{row.label} · </b> : null}{row.option}</span>
          <strong style={{ color: row.color }}>{row.value === null ? "Sin dato" : `${new Intl.NumberFormat("es-ES", { maximumFractionDigits: 1 }).format(row.value)} %`}</strong>
        </div>)}
      </div>
    </div>
    <p className="scene-footnote">{layout.rows.length ? "Color intenso: porcentaje de respuesta · Tenue: resto del grupo. Escenario experimental sin validar." : "Perfiles sintéticos · Ilustración de la población"}</p>
  </figure>;
}
