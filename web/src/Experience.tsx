import { useEffect, useRef, useState } from "react";
import type { CSSProperties, FormEvent } from "react";
import ParticleScene from "./ParticleScene";
import { askChat } from "./api";
import type { ChatGroupResult, ChatResult } from "./api";

const MIN_THINKING_MS = 5000;
const LEGACY_HISTORY_KEY = "pulso:recent-questions:v1";
const MAX_RECENT_QUESTIONS = 6;

type Group = { label: string; percentages: Record<string, number | null> };
type ResultView = "total" | "sex" | "age";
type SavedQuestion = { id: string; question: string; answer: ChatResult };

const formatNumber = (value: number) =>
  new Intl.NumberFormat("es-ES", { maximumFractionDigits: 2 }).format(value);

function Percentages({
  values,
  labels = Object.keys(values),
}: {
  values: Record<string, number | null>;
  labels?: string[];
}) {
  return (
    <div className="percentages">
      {labels.map((label, index) => {
        const value = values[label] ?? null;
        return (
          <div
            className="percentage-row"
            key={label}
            style={{ "--bar-delay": `${180 + index * 95}ms` } as CSSProperties}
          >
            <div className="percentage-label">
              <span>{label}</span>
              <strong>
                {typeof value === "number"
                  ? `${formatNumber(value)} %`
                  : "Sin dato"}
              </strong>
            </div>
            <div className="percentage-track" aria-hidden="true">
              <span
                style={{ width: `${Math.min(100, Math.max(0, value ?? 0))}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function sortGroups(groups: Group[], view: "sex" | "age") {
  return groups.sort((first, second) =>
    view === "sex"
      ? ["Mujer", "Hombre"].indexOf(first.label) -
        ["Mujer", "Hombre"].indexOf(second.label)
      : Number.parseInt(first.label, 10) - Number.parseInt(second.label, 10),
  );
}

function chatGroups(
  data: Record<string, ChatGroupResult> | undefined,
  view: "sex" | "age",
) {
  return sortGroups(
    Object.entries(data ?? {})
      .filter(
        ([, result]) =>
          result.porcentajes && Object.keys(result.porcentajes).length > 0,
      )
      .map(([label, result]) => ({ label, percentages: result.porcentajes! })),
    view,
  );
}

function ScenarioViews({
  year,
  total,
  bySex,
  byAge,
  filtered = false,
  view,
  onViewChange,
}: {
  year: number;
  total: Record<string, number | null>;
  bySex: Group[];
  byAge: Group[];
  filtered?: boolean;
  view: ResultView;
  onViewChange: (view: ResultView) => void;
}) {
  const options = Object.keys(total);
  const hasGroups = bySex.length > 0 || byAge.length > 0;
  const activeGroups = view === "sex" ? bySex : byAge;

  return (
    <>
      {hasGroups && (
        <div className="result-view-switch" aria-label="Ver resultados">
          <button type="button" aria-pressed={view === "total"} onClick={() => onViewChange("total")}>General</button>
          {bySex.length > 0 && (
            <button type="button" aria-pressed={view === "sex"} onClick={() => onViewChange("sex")}>Por sexo</button>
          )}
          {byAge.length > 0 && (
            <button type="button" aria-pressed={view === "age"} onClick={() => onViewChange("age")}>Por edad</button>
          )}
        </div>
      )}
      {view === "total" ? (
        <>
          <span className="result-eyebrow">
            {filtered ? "Grupo consultado" : "Todos los perfiles"} · {year}
          </span>
          <div className="total-card">
            <Percentages values={total} labels={options} />
          </div>
        </>
      ) : (
        <>
          <span className="result-eyebrow">{view === "sex" ? "Por sexo" : "Por edad"} · {year}</span>
          <p className="result-scope">Porcentajes dentro de cada grupo. No se suman entre grupos.</p>
          <div className="subgroup-grid">
            {activeGroups.map((group) => (
              <section className="subgroup-card" key={group.label} aria-label={group.label}>
                <h3>{group.label}</h3>
                <Percentages values={group.percentages} labels={options} />
              </section>
            ))}
          </div>
        </>
      )}
      <p className="result-note">Escenario experimental sin validar. No es una encuesta real.</p>
    </>
  );
}

function Indicator({ evidence }: { evidence: Record<string, unknown> }) {
  const value = evidence.valor ?? evidence.valor_central;
  const unit =
    evidence.unidad === "porcentaje"
      ? " %"
      : ` ${String(evidence.unidad ?? "")}`;
  const projected = evidence.tipo_dato === "PROYECCION_HEURISTICA_NO_VALIDADA";
  const source = typeof evidence.fuente === "string" ? evidence.fuente : null;
  const url =
    typeof evidence.url === "string" && evidence.url.startsWith("https://")
      ? evidence.url
      : null;
  return (
    <div className="indicator-result">
      <span className="result-eyebrow">
        {projected ? "Proyección experimental" : "Dato observado"}
      </span>
      <strong className="indicator-value">
        {typeof value === "number" ? formatNumber(value) : "Sin dato"}
        {typeof value === "number" ? unit : ""}
      </strong>
      <p>
        {String(evidence.anio ?? "")} ·{" "}
        {source ??
          (projected ? "Estimación no validada" : "Fuente no disponible")}
      </p>
      {url && (
        <a href={url} target="_blank" rel="noreferrer">
          Ver fuente ↗
        </a>
      )}
    </div>
  );
}

function ThinkingStatus() {
  return (
    <div className="result-skeleton" role="status" aria-label="Preparando resultados">
      <div className="result-skeleton-heading">
        <div className="thinking-logo" aria-hidden="true">
          puls<span className="thinking-mark"><span /></span>
        </div>
        <p>Preparando resultados…</p>
      </div>
      <div className="skeleton-result-card" aria-hidden="true">
        {[0, 1, 2].map((index) => (
          <div className="skeleton-result-row" key={index}>
            <span className="skeleton-line skeleton-label" />
            <span className="skeleton-line skeleton-value" />
            <span className="skeleton-line skeleton-track" />
          </div>
        ))}
      </div>
    </div>
  );
}

function ResultContent({ data, view, onViewChange }: { data: ChatResult; view: ResultView; onViewChange: (view: ResultView) => void }) {
  const total = data.desgloses?.total;
  if (total?.porcentajes) {
    const query = data.consulta_interpretada;
    const hasFilters = Boolean(
      Object.keys(query?.filtros ?? {}).length ||
        query?.edad_min != null ||
        query?.edad_max != null,
    );
    return <ScenarioViews
      year={data.consulta_interpretada?.anio ?? 2026}
      total={total.porcentajes}
      bySex={chatGroups(data.desgloses?.por_sexo, "sex")}
      byAge={chatGroups(data.desgloses?.por_edad, "age")}
      filtered={hasFilters}
      view={view}
      onViewChange={onViewChange}
    />;
  }
  if (data.consulta_interpretada?.tipo === "indicador" && data.evidencias[0]) {
    return <Indicator evidence={data.evidencias[0]} />;
  }
  return <p className="plain-answer">{data.respuesta}</p>;
}

export default function Experience() {
  const [draft, setDraft] = useState("");
  const [history, setHistory] = useState<SavedQuestion[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [attemptedQuestion, setAttemptedQuestion] = useState<string | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [view, setView] = useState<ResultView>("total");
  const introRef = useRef<HTMLDivElement>(null);
  const submissionLock = useRef(false);
  const selected = history.find((item) => item.id === selectedId);
  const active = attemptedQuestion ?? selected?.question;
  const answer = busy || queryError ? null : selected?.answer;
  const previousQuestions = history
    .filter((item) => item.id !== selectedId)
    .slice(0, MAX_RECENT_QUESTIONS - 1)
    .reverse();

  useEffect(() => {
    try {
      sessionStorage.removeItem(LEGACY_HISTORY_KEY);
    } catch {
      // The in-memory history still works when browser storage is unavailable.
    }
  }, []);

  useEffect(() => {
    const intro = introRef.current;
    if (!intro) return;
    let frame = 0;
    const update = () => {
      const progress = Math.max(0, Math.min(1, -intro.getBoundingClientRect().top / (window.innerHeight * .55)));
      intro.style.opacity = String(1 - progress);
      intro.style.transform = `translateY(${progress * -35}px)`;
      frame = 0;
    };
    const scroll = () => { if (!frame) frame = requestAnimationFrame(update); };
    window.addEventListener("scroll", scroll, { passive: true });
    window.addEventListener("resize", scroll);
    update();
    return () => { window.removeEventListener("scroll", scroll); window.removeEventListener("resize", scroll); cancelAnimationFrame(frame); };
  }, []);

  function initialView(result: ChatResult, question: string): ResultView {
    if (/edad|jóven|joven|mayores|años/i.test(question) && chatGroups(result.desgloses?.por_edad, "age").length) return "age";
    if (/sexo|género|genero|mujer|hombre/i.test(question) && chatGroups(result.desgloses?.por_sexo, "sex").length) return "sex";
    return "total";
  }

  async function submitChatQuestion(text: string) {
    if (submissionLock.current || text.length < 8 || text.length > 900) return;
    submissionLock.current = true;
    const minimumWait = new Promise<void>((resolve) =>
      window.setTimeout(resolve, MIN_THINKING_MS),
    );
    setAttemptedQuestion(text);
    setSelectedId(null);
    setQueryError(null);
    setBusy(true);
    try {
      const result = await askChat(text);
      await minimumWait;
      const entry = {
        id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        question: text,
        answer: result,
      };
      setHistory((current) =>
        [entry, ...current].slice(0, MAX_RECENT_QUESTIONS),
      );
      setView(initialView(result, text));
      setSelectedId(entry.id);
      setAttemptedQuestion(null);
      setDraft("");
    } catch (error) {
      setQueryError(
        error instanceof Error
          ? error.message
          : "No se ha podido completar la consulta.",
      );
    } finally {
      submissionLock.current = false;
      setBusy(false);
    }
  }

  function submitChat(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitChatQuestion(draft.trim());
  }

  function selectQuestion(id: string) {
    if (busy) return;
    const item = history.find((entry) => entry.id === id);
    if (item) setView(initialView(item.answer, item.question));
    setSelectedId(id);
    setAttemptedQuestion(null);
    setQueryError(null);
  }

  return (
    <div className="site-shell">
      <header className="site-header wrap">
        <a
          className="wordmark"
          href="#inicio"
          aria-label="Pulso, volver al inicio"
        >
          pulso<span>.</span>
        </a>
      </header>
      <main id="inicio" className="experience-layout wrap">
        <div className="experience-copy">
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero-copy" ref={introRef}>
            <h1 id="hero-title">
              Pregúntale a una
              <br />
              <span>España sintética</span>
            </h1>
            <p>
              Pulso construye perfiles sintéticos con estadísticas del INE y del
              CIS. Haz una pregunta y compara las respuestas por edad, comunidad
              o año. Cada resultado indica cuánto puedes fiarte de él.
            </p>
            <a className="primary-link" href="#preguntar">
              Haz tu pregunta <span aria-hidden="true">↓</span>
            </a>
          </div>
        </section>
        <section
          className="ask-section"
          id="preguntar"
          aria-labelledby="chat-title"
        >
          <div>
            <div className="chat-area">
              <div className="chat-heading">
                <span className="chat-eyebrow">EL PULSO DE LA SOCIEDAD</span>
                <h2 id="chat-title">¿Qué quieres saber<br />de España?</h2>
                <p>Haz una pregunta. Descubre cómo cambia la respuesta entre generaciones y perfiles.</p>
              </div>
              <div className="chat-input-column">
                <form className="chat-form" onSubmit={submitChat}>
                  <label className="sr-only" htmlFor="question-input">
                    Tu pregunta
                  </label>
                  <textarea
                    id="question-input"
                    value={draft}
                    onChange={(event) => setDraft(event.target.value)}
                    onKeyDown={(event) => {
                      if (
                        event.key === "Enter" &&
                        !event.shiftKey &&
                        !event.nativeEvent.isComposing
                      ) {
                        event.preventDefault();
                        event.currentTarget.form?.requestSubmit();
                      }
                    }}
                    minLength={8}
                    maxLength={900}
                    rows={2}
                    required
                    disabled={busy}
                    placeholder="Escribe una pregunta sobre la sociedad española…"
                  />
                  <div className="chat-form-bottom">
                    <button
                      type="submit"
                      disabled={busy || draft.trim().length < 8}
                    >
                      Enviar <span aria-hidden="true">↗</span>
                    </button>
                  </div>
                </form>
              </div>
            </div>
            <section
              className="result-panel"
              aria-label="Resultado de la consulta"
              aria-busy={busy}
            >
              {active && (
                <div
                  className="question-stack"
                  style={{ "--stack-count": previousQuestions.length } as CSSProperties}
                >
                  {previousQuestions.map((item, index) => (
                    <button
                      className="history-card"
                      type="button"
                      key={item.id}
                      style={{ "--stack-index": index } as CSSProperties}
                      onClick={() => selectQuestion(item.id)}
                      disabled={busy}
                      aria-label={`Ver resultados de: ${item.question}`}
                    >
                      <span className="history-card-heading">
                        <span className="history-card-label">Anterior</span>
                        <span className="history-card-summary" aria-hidden="true">{item.question}</span>
                        <span className="history-card-arrow" aria-hidden="true">↗</span>
                      </span>
                      <span className="history-card-detail" aria-hidden="true">{item.question}</span>
                    </button>
                  ))}
                  <div className="foreground-result" key={active}>
                    <div className={`asked-question${busy ? " asked-question--loading" : ""}`} aria-live="polite">
                      <span>{busy ? "Tu pregunta · en curso" : "Tu pregunta"}</span>
                      <p>{active}</p>
                    </div>
                    <div className="result-body">
                      {busy && <ThinkingStatus />}
                      {queryError && (
                        <div className="query-error" role="alert">
                          <p>{queryError}</p>
                          <button
                            type="button"
                            onClick={() => void submitChatQuestion(active)}
                          >
                            Reintentar
                          </button>
                        </div>
                      )}
                      {answer && (
                        <div className="result-reveal">
                          <ResultContent key={selectedId} data={answer} view={view} onViewChange={setView} />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </section>
          </div>
        </section>
        </div>
        <aside className="experience-visual" aria-label="Visualización de la sociedad española">
          <div className="visual-sticky">
            <ParticleScene busy={busy} groups={busy || !answer?.desgloses?.total?.porcentajes ? [] : view === "sex" ? chatGroups(answer.desgloses.por_sexo, "sex") : view === "age" ? chatGroups(answer.desgloses.por_edad, "age") : [{ label: "General", percentages: answer.desgloses.total.porcentajes }]} title={view === "sex" ? "Respuestas por sexo" : view === "age" ? "Respuestas por edad" : "El pulso de España"} />
            {answer?.desgloses?.total?.porcentajes && !busy && <div className="scene-controls">
              <div className="result-view-switch" aria-label="Cambiar gráfico de puntos">
                <button type="button" aria-pressed={view === "total"} onClick={() => setView("total")}>General</button>
                {chatGroups(answer.desgloses.por_sexo, "sex").length > 0 && <button type="button" aria-pressed={view === "sex"} onClick={() => setView("sex")}>Por sexo</button>}
                {chatGroups(answer.desgloses.por_edad, "age").length > 0 && <button type="button" aria-pressed={view === "age"} onClick={() => setView("age")}>Por edad</button>}
              </div>
            </div>}
          </div>
        </aside>
      </main>
      <footer className="site-footer wrap">
        <span className="footer-brand">
          pulso<span>.</span>
        </span>
      </footer>
    </div>
  );
}
