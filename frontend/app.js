/* Local demonstration only. No requests, model inference, or real population data. */
(() => {
  'use strict';
  const $ = (selector) => document.querySelector(selector);
  const canvas = $('#particles');
  const ctx = canvas.getContext('2d');
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const ages = ['18–29 años', '30–44 años', '45–54 años', '55–64 años', '65+ años'];
  const ageWeights = [.17, .25, .19, .17, .22];
  const profiles = [
    { key: 'vivienda', match: /vivienda|alquiler|casa|hipoteca|piso/i, name: 'el acceso a la vivienda', rates: [.86, .79, .62, .43, .29] },
    { key: 'empleo', match: /empleo|trabajo|paro|laboral|salario/i, name: 'el empleo', rates: [.77, .74, .63, .55, .25] },
    { key: 'sanidad', match: /sanidad|salud|hospital|m[eé]dic/i, name: 'la sanidad pública', rates: [.43, .52, .65, .77, .86] },
    { key: 'pensiones', match: /pensi[oó]n|pensiones|jubil/i, name: 'las pensiones', rates: [.31, .38, .61, .83, .88] },
    { key: 'clima', match: /clima|clim[aá]t|medioambiente|contamin/i, name: 'el medioambiente', rates: [.83, .73, .59, .49, .38] },
    { key: 'educacion', match: /educaci[oó]n|escuela|universidad|estudi/i, name: 'la educación', rates: [.77, .81, .72, .47, .36] },
    { key: 'economia', match: /econom[ií]a|inflaci[oó]n|precio|coste|compra/i, name: 'el coste de la vida', rates: [.73, .84, .79, .72, .63] }
  ];
  const state = { people: [], particles: [], mode: 'sex', result: null, busy: false, width: 0, height: 0, frame: 0, raf: 0, history: [], lastTime: 0, time: 0 };
  // Cache the glow once instead of running thousands of shadow filters each frame.
  const glow = document.createElement('canvas'); glow.width = glow.height = 32;
  const glowContext = glow.getContext('2d');
  const gradient = glowContext.createRadialGradient(16, 16, 0, 16, 16, 16);
  gradient.addColorStop(0, 'rgba(255,67,44,.4)'); gradient.addColorStop(.2, 'rgba(255,55,35,.16)'); gradient.addColorStop(1, 'rgba(255,40,20,0)');
  glowContext.fillStyle = gradient; glowContext.fillRect(0, 0, 32, 32);
  try { const saved = JSON.parse(localStorage.getItem('pulso-history-v1') || '[]'); state.history = Array.isArray(saved) ? saved.filter(x => typeof x === 'string').slice(0, 8) : []; } catch (_) { /* Storage can be unavailable. */ }
  function randomSeed(text) { let value = 2166136261; for (const character of text) value = Math.imul(value ^ character.charCodeAt(0), 16777619); return () => { value += 0x6D2B79F5; let t = value; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  const number = n => n.toLocaleString('es-ES');
  const percent = n => `${Math.round(n * 100)}%`;
  function generatePeople() {
    const rng = randomSeed('pulso-population-v1');
    const count = Number($('#population').value);
    state.people = Array.from({ length: count }, (_, id) => {
      const roll = rng(); let cumulative = 0; let age = 4;
      for (let i = 0; i < ageWeights.length; i++) { cumulative += ageWeights[i]; if (roll < cumulative) { age = i; break; } }
      return { id, sex: rng() < .51 ? 0 : 1, age, concerned: false };
    });
    const previous = state.particles;
    state.particles = state.people.map((person, i) => {
      const particle = { x: 0, y: 0, tx: 0, ty: 0, phase: rng() * Math.PI * 2, size: .65 + rng() * .85, depth: 0, alpha: .65, displaySize: 1, person, i };
      sphereTarget(particle, state.time);
      const origin = previous[i] || previous[i % previous.length];
      particle.x = origin ? origin.x : particle.tx; particle.y = origin ? origin.y : particle.ty;
      return particle;
    });
    $('#person-count').textContent = number(count);
  }
  function resize() {
    const rect = canvas.getBoundingClientRect(); const ratio = Math.min(devicePixelRatio || 1, 2);
    state.width = rect.width; state.height = rect.height;
    if (canvas.width !== Math.round(rect.width * ratio)) canvas.width = Math.round(rect.width * ratio);
    if (canvas.height !== Math.round(rect.height * ratio)) canvas.height = Math.round(rect.height * ratio);
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    if (state.result && !state.busy) layoutGroups();
    // Paint immediately when resizing the buffer, so no empty frame is presented.
    if (state.raf) cancelAnimationFrame(state.raf);
    draw(performance.now());
  }
  function sphereTarget(particle, time) {
    const i = particle.i; const count = state.people.length;
    const y = 1 - (i / (count - 1)) * 2; const ring = Math.sqrt(Math.max(0, 1 - y * y));
    const angle = i * 2.3999632297 + time * .000075;
    const x = Math.cos(angle) * ring; const z = Math.sin(angle) * ring;
    const tilt = -.22; const yt = y * Math.cos(tilt) - z * Math.sin(tilt); const zt = y * Math.sin(tilt) + z * Math.cos(tilt);
    const radius = Math.min(state.width * .285, state.height * .46, 190);
    const ripple = state.busy ? 1 + .045 * Math.sin(time * .004 + y * 8) : 1;
    const perspective = 1 + zt * .13;
    particle.tx = state.width / 2 + x * radius * perspective * ripple;
    particle.ty = state.height / 2 + yt * radius * perspective * ripple - 3;
    particle.depth = zt;
  }
  function draw(timestamp = performance.now()) {
    state.raf = 0;
    const dt = Math.min(Math.max((timestamp - state.lastTime) / 1000, 0), 1 / 30);
    state.lastTime = timestamp; state.time += dt * 1000;
    const time = state.time;
    ctx.clearRect(0, 0, state.width, state.height);
    const grouped = !!state.result && !state.busy;
    let moving = false;
    const buckets = Array.from({ length: 24 }, () => []);
    for (const p of state.particles) {
      if (!grouped) sphereTarget(p, reducedMotion.matches ? 0 : time);
      const easing = reducedMotion.matches ? 1 : 1 - Math.exp(-dt * (grouped ? 3.2 : 2.4));
      const driftX = grouped && !reducedMotion.matches ? Math.sin(time * .00065 + p.phase) * 1.25 : 0;
      const driftY = grouped && !reducedMotion.matches ? Math.cos(time * .0008 + p.phase * 1.3) * 1.4 : 0;
      p.x += (p.tx + driftX - p.x) * easing; p.y += (p.ty + driftY - p.y) * easing;
      if (Math.abs(p.tx - p.x) + Math.abs(p.ty - p.y) > .2) moving = true;
      const alpha = grouped ? (p.person.concerned ? .9 : .15) : .22 + (p.depth + 1) * .32;
      const size = grouped ? p.size * .85 : p.size * (.8 + (p.depth + 1) * .3);
      p.alpha += (alpha - p.alpha) * easing; p.displaySize += (size - p.displaySize) * easing;
      buckets[Math.min(23, Math.floor(p.alpha * 24))].push(p);
    }
    // Batch points by opacity; avoid one canvas fill/composite per simulated person.
    buckets.forEach((bucket, index) => {
      if (!bucket.length) return;
      ctx.fillStyle = `rgba(255,65,53,${(index + .5) / 24})`;
      ctx.beginPath();
      for (const p of bucket) { ctx.moveTo(p.x + p.displaySize, p.y); ctx.arc(p.x, p.y, p.displaySize, 0, Math.PI * 2); }
      ctx.fill();
    });
    for (let i = 0; i < state.particles.length; i += 24) {
      const p = state.particles[i]; ctx.globalAlpha = p.alpha;
      const halo = p.displaySize * 10; ctx.drawImage(glow, p.x - halo / 2, p.y - halo / 2, halo, halo);
    }
    ctx.globalAlpha = 1;
    if (!document.hidden && (!reducedMotion.matches || moving)) state.raf = requestAnimationFrame(draw);
  }
  function requestDraw() { if (!state.raf && !document.hidden) state.raf = requestAnimationFrame(draw); }
  function getGroups() {
    const specs = state.mode === 'sex' ? [{ name: 'Mujeres', sex: 0 }, { name: 'Hombres', sex: 1 }]
      : state.mode === 'age' ? ages.map((name, age) => ({ name, age }))
      : [0, 1].flatMap(sex => ages.map((name, age) => ({ name: `${sex === 0 ? 'Mujeres' : 'Hombres'} · ${name.replace(' años', '')}`, sex, age })));
    return specs.map(group => { const people = state.people.filter(p => (group.sex === undefined || p.sex === group.sex) && (group.age === undefined || p.age === group.age)); const concerned = people.filter(p => p.concerned).length; return { ...group, people, concerned, rate: concerned / people.length }; });
  }
  function layoutGroups() {
    if (!state.result) return;
    const groups = getGroups(); const mobile = state.width < 520;
    const columns = state.mode === 'sex' ? 2 : mobile ? (state.mode === 'cross' ? 2 : 3) : 5;
    const rows = Math.ceil(groups.length / columns);
    const desiredHeight = state.mode === 'cross' ? (mobile ? 790 : 395) : state.mode === 'age' && mobile ? 375 : (innerWidth >= 1500 ? 340 : 290);
    const wrap = $('#canvas-wrap');
    if (Math.abs(wrap.getBoundingClientRect().height - desiredHeight) > 1) wrap.style.height = `${desiredHeight}px`;
    const width = state.width / columns; const rowHeight = state.height / rows;
    const labels = $('#group-labels'); labels.replaceChildren();
    groups.forEach((group, index) => {
      const column = index % columns; const row = Math.floor(index / columns); const centerX = (column + .5) * width;
      const top = row * rowHeight + 20; const graphHeight = Math.max(45, rowHeight - 96);
      const gridColumns = Math.max(8, Math.floor((width - 30) / (state.mode === 'sex' ? 7 : 5)));
      const gridRows = Math.ceil(group.people.length / gridColumns);
      const gapX = Math.min(state.mode === 'sex' ? 7 : 5, (width - 25) / gridColumns);
      const gapY = Math.min(5, graphHeight / gridRows);
      const particles = group.people.map(person => state.particles[person.id]).sort((a, b) => Number(b.person.concerned) - Number(a.person.concerned));
      particles.forEach((particle, slot) => { particle.tx = centerX + ((slot % gridColumns) - (gridColumns - 1) / 2) * gapX; particle.ty = top + graphHeight - Math.floor(slot / gridColumns) * gapY; });
      const label = document.createElement('div'); label.className = 'group-label'; label.style.left = `${centerX}px`; label.style.top = `${top + graphHeight + 15}px`;
      const rate = document.createElement('strong'); rate.textContent = percent(group.rate);
      const title = document.createElement('span'); title.textContent = group.name;
      const sample = document.createElement('small'); sample.textContent = `${number(group.concerned)} de ${number(group.people.length)} personas`;
      label.append(rate, title, sample); labels.append(label);
    });
    $('#legend-text').textContent = 'Rojo brillante: expresa preocupación · tenue: resto';
    $('#viz-caption').textContent = 'Porcentaje dentro de cada grupo';
    canvas.setAttribute('aria-label', groups.map(g => `${g.name}: ${percent(g.rate)}, ${g.concerned} de ${g.people.length} personas`).join('. '));
    const highest = groups.reduce((a, b) => a.rate > b.rate ? a : b);
    const total = state.people.filter(p => p.concerned).length / state.people.length;
    const topic = state.result.profile ? state.result.profile.name : 'el tema planteado';
    $('#answer').textContent = `En esta simulación, ${percent(total)} de las personas expresa preocupación por ${topic}. El grupo con mayor porcentaje es ${highest.name.toLowerCase()} (${percent(highest.rate)}).`;
    $('#total-rate').textContent = percent(total);
    $('#total-rate').setAttribute('aria-label', `Preocupación total: ${percent(total)}`);
    requestDraw();
  }
  function applySimulation(question) {
    const profile = profiles.find(profile => profile.match.test(question)); const rng = randomSeed(question.trim().toLocaleLowerCase('es'));
    const rates = profile ? profile.rates : ages.map(() => .25 + rng() * .55);
    for (const person of state.people) person.concerned = rng() < Math.min(.96, Math.max(.08, rates[person.age] + (person.sex === 0 ? .035 : -.035)));
    state.result = { question, profile, generatedAt: new Date().toISOString() };
  }
  function renderHistory() {
    const history = $('#history'); history.replaceChildren();
    if (!state.history.length) { const empty = document.createElement('p'); empty.className = 'empty-history'; empty.textContent = 'Tus preguntas abren nuevas perspectivas.'; history.append(empty); }
    state.history.forEach(question => { const button = document.createElement('button'); button.className = 'history-item'; button.textContent = question; button.title = question; button.addEventListener('click', () => ask(question)); history.append(button); });
  }
  function saveHistory(question) {
    state.history = [question, ...state.history.filter(item => item !== question)].slice(0, 8);
    try { localStorage.setItem('pulso-history-v1', JSON.stringify(state.history)); } catch (_) { /* Optional browser storage. */ }
    renderHistory();
  }
  const delay = duration => new Promise(resolve => setTimeout(resolve, duration));
  async function ask(rawQuestion) {
    const question = rawQuestion.trim().slice(0, 500); if (!question || state.busy) return;
    state.busy = true; $('#submit').disabled = true; $('#population').disabled = true; $('#new-chat').disabled = true;
    $('#question').value = ''; $('#question').style.height = ''; $('#results').hidden = true; $('#suggestions').hidden = true; $('#ask-heading').hidden = true;
    $('#question-display').hidden = false; $('#question-display').textContent = question;
    $('#group-labels').replaceChildren(); $('#thinking').hidden = false; $('#thinking-text').textContent = 'Escuchando a la sociedad…';
    $('#viz-state').textContent = 'EXPLORANDO TU PREGUNTA'; document.body.classList.remove('analyzed'); $('#canvas-wrap').style.height = '';
    requestDraw(); await delay(reducedMotion.matches ? 100 : 800);
    $('#thinking-text').textContent = 'Encontrando patrones entre las personas…';
    await delay(reducedMotion.matches ? 100 : 1000);
    applySimulation(question); state.busy = false; document.body.classList.add('analyzed');
    $('#thinking').hidden = true; $('#results').hidden = false; $('#viz-state').textContent = 'UNA SOCIEDAD, DISTINTAS PERSPECTIVAS';
    $('#submit').disabled = false; $('#population').disabled = false; $('#new-chat').disabled = false;
    $('#question').placeholder = 'Haz otra pregunta a esta sociedad…';
    saveHistory(question); layoutGroups();
  }
  function reset() {
    if (state.busy) return;
    state.result = null; document.body.classList.remove('analyzed'); $('#canvas-wrap').style.height = '';
    $('#results').hidden = true; $('#suggestions').hidden = false; $('#ask-heading').hidden = false; $('#question-display').hidden = true; $('#group-labels').replaceChildren();
    $('#question').value = ''; $('#question').placeholder = '¿A quién le preocupa más el acceso a la vivienda?';
    $('#legend-text').textContent = 'Cada punto es una persona simulada'; $('#viz-caption').textContent = 'Diferentes historias. Un mismo espacio.'; $('#viz-state').textContent = 'SOCIEDAD EN MOVIMIENTO';
    canvas.setAttribute('aria-label', 'Nube animada de personas simuladas'); requestDraw(); $('#question').focus();
  }
  $('#chat-form').addEventListener('submit', event => { event.preventDefault(); ask($('#question').value); });
  $('#question').addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); $('#chat-form').requestSubmit(); } });
  $('#question').addEventListener('input', event => { event.target.style.height = 'auto'; event.target.style.height = `${Math.min(120, event.target.scrollHeight)}px`; });
  document.querySelectorAll('[data-question]').forEach(button => button.addEventListener('click', () => ask(button.dataset.question)));
  const tabs = [...document.querySelectorAll('[data-mode]')];
  function selectTab(button) { state.mode = button.dataset.mode; tabs.forEach(tab => { const selected = tab === button; tab.setAttribute('aria-selected', String(selected)); tab.tabIndex = selected ? 0 : -1; }); layoutGroups(); }
  tabs.forEach((button, index) => { button.tabIndex = index === 0 ? 0 : -1; button.addEventListener('click', () => selectTab(button)); button.addEventListener('keydown', event => { if (['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) { event.preventDefault(); const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length; selectTab(tabs[next]); tabs[next].focus(); } }); });
  $('#new-chat').addEventListener('click', reset); $('#explore').addEventListener('click', reset);
  $('#population').addEventListener('change', () => { generatePeople(); if (state.result) { applySimulation(state.result.question); layoutGroups(); } requestDraw(); });
  $('#replay').addEventListener('click', async () => { if (state.busy) return; if (state.result) { const question = state.result.question; await ask(question); } else { state.time += 1200; requestDraw(); } });
  const dialog = $('#about-dialog'); $('#about').addEventListener('click', () => dialog.showModal()); $('#demo-info').addEventListener('click', () => dialog.showModal()); $('#close-about').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) { const rect = dialog.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close(); } });
  $('#clear-history').addEventListener('click', () => { state.history = []; try { localStorage.removeItem('pulso-history-v1'); } catch (_) { /* Optional browser storage. */ } renderHistory(); dialog.close(); });
  $('#export').addEventListener('click', () => {
    if (!state.result) return;
    const data = { demo: true, source: 'Fictitious data generated locally; not a real prediction or survey.', question: state.result.question, generatedAt: state.result.generatedAt, population: state.people.length, grouping: state.mode, totalConcerned: state.people.filter(p => p.concerned).length, groups: getGroups().map(g => ({ name: g.name, people: g.people.length, concerned: g.concerned, percent: Math.round(g.rate * 10000) / 100 })) };
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a'); link.href = url; link.download = `pulso-simulacion-${state.result.generatedAt.slice(0, 10)}.json`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  document.addEventListener('visibilitychange', () => { if (document.hidden) { cancelAnimationFrame(state.raf); state.raf = 0; } else requestDraw(); });
  reducedMotion.addEventListener('change', requestDraw);
  new ResizeObserver(resize).observe($('#canvas-wrap'));
  resize(); generatePeople(); renderHistory(); requestDraw();
})();
