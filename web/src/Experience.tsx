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
  const submissionLock = useRef(false);
  const selected = history.find((item) => item.id === selectedId);
  const active = attemptedQuestion ?? selected?.question;
  const answer = busy || queryError ? null : selected?.answer;

  useEffect(() => {
    try {
      sessionStorage.removeItem(LEGACY_HISTORY_KEY);
    } catch {
      // The in-memory history still works when browser storage is unavailable.
    }
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

  const total = answer?.desgloses?.total?.porcentajes;
  const bySex = chatGroups(answer?.desgloses?.por_sexo, "sex");
  const byAge = chatGroups(answer?.desgloses?.por_edad, "age");
  const groups = !total ? [] : view === "sex" ? bySex : view === "age" ? byAge : [{ label: "General", percentages: total }];

  function resetScene() {
    if (busy) return;
    setSelectedId(null);
    setAttemptedQuestion(null);
    setQueryError(null);
    setView("total");
    setDraft("");
  }

  return (
    <div className="site-shell immersive-shell">
      <header className="scene-header">
        <button className="wordmark" type="button" onClick={resetScene} disabled={busy} aria-label="Pulso, volver al mapa">
          pulso<span>.</span>
        </button>
        {history.length > 0 && <details className="history-menu">
          <summary>Consultas anteriores <span aria-hidden="true">↗</span></summary>
          <div className="history-menu-list">
            {history.map((item) => <button type="button" key={item.id} disabled={busy} aria-current={selectedId === item.id ? "true" : undefined} onClick={(event) => {
              selectQuestion(item.id);
              event.currentTarget.closest("details")?.removeAttribute("open");
            }}>{item.question}</button>)}
          </div>
        </details>}
      </header>
      <main id="inicio" className={`scene-experience${total ? " scene-experience--results" : ""}`}>
        <section className="scene-workspace" aria-label="Explora la sociedad española">
          <div className="scene-toolbar">
            {active && <h1 className="scene-question" title={active}>{active}</h1>}
            {total && <div className="scene-result-tools">
              <div className="result-view-switch" aria-label="Cambiar gráfico de puntos">
                <button type="button" aria-pressed={view === "total"} onClick={() => setView("total")}>General</button>
                {bySex.length > 0 && <button type="button" aria-pressed={view === "sex"} onClick={() => setView("sex")}>Por sexo</button>}
                {byAge.length > 0 && <button type="button" aria-pressed={view === "age"} onClick={() => setView("age")}>Por edad</button>}
              </div>
              <span className="scene-year">{answer?.consulta_interpretada?.anio ?? 2026}</span>
            </div>}
          </div>
          <ParticleScene busy={busy} groups={groups} orientation="horizontal" title={view === "sex" ? "Respuestas por sexo" : view === "age" ? "Respuestas por edad" : "El pulso de España"} />
          {answer && !total && <div className="scene-text-answer" aria-live="polite">
            <ResultContent data={answer} view={view} onViewChange={setView} />
          </div>}
        </section>
        <section className="scene-composer" id="preguntar" aria-label="Haz una pregunta">
          {queryError && <div className="query-error" role="alert">
            <p>{queryError}</p>
            <button type="button" onClick={() => void submitChatQuestion(active ?? draft.trim())}>Reintentar</button>
          </div>}
          <form className="chat-form" onSubmit={submitChat}>
            <label className="sr-only" htmlFor="question-input">Tu pregunta</label>
            <textarea id="question-input" value={draft} onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
              minLength={8} maxLength={900} rows={1} required disabled={busy}
              placeholder="Pregunta algo sobre la sociedad española…"
            />
            <button className="scene-send" type="submit" disabled={busy || draft.trim().length < 8} aria-label={busy ? "Preparando respuesta" : "Enviar pregunta"}>
              <span className={busy ? "send-spinner" : ""} aria-hidden="true">{busy ? "" : "↑"}</span>
            </button>
          </form>
          <div className="composer-meta">
            <span>Perfiles sintéticos · Resultados experimentales</span>
            {total && <button type="button" className="details-link" onClick={() => { const detail = document.getElementById("detalle") as HTMLDetailsElement | null; if (detail) { detail.open = !detail.open; if (detail.open) detail.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth", block: "start" }); } }}>Ver cifras y fuentes ↓</button>}
          </div>
        </section>
        {total && answer && <details className="answer-details" id="detalle">
          <summary>Cifras y fuentes de la respuesta</summary>
          <ResultContent data={answer} view={view} onViewChange={setView} />
        </details>}
      </main>
    </div>
  );
}
