import { useEffect, useRef, useState } from "react";
import type { CSSProperties, FormEvent } from "react";
import spainDots from "./assets/spain-dots.svg";
import { askChat } from "./api";
import type { ChatGroupResult, ChatResult } from "./api";

const MIN_THINKING_MS = 2200;

type Group = { label: string; percentages: Record<string, number | null> };
type ResultView = "total" | "sex" | "age";
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
}: {
  year: number;
  total: Record<string, number | null>;
  bySex: Group[];
  byAge: Group[];
  filtered?: boolean;
}) {
  const [view, setView] = useState<ResultView>("total");
  const options = Object.keys(total);
  const hasGroups = bySex.length > 0 || byAge.length > 0;
  const activeGroups = view === "sex" ? bySex : byAge;

  return (
    <>
      {hasGroups && (
        <div className="result-view-switch" aria-label="Ver resultados">
          <button type="button" aria-pressed={view === "total"} onClick={() => setView("total")}>General</button>
          {bySex.length > 0 && (
            <button type="button" aria-pressed={view === "sex"} onClick={() => setView("sex")}>Por sexo</button>
          )}
          {byAge.length > 0 && (
            <button type="button" aria-pressed={view === "age"} onClick={() => setView("age")}>Por edad</button>
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
    <div className="thinking-status" role="status" aria-label="Preparando resultados">
      <div className="thinking-logo" aria-hidden="true">
        puls<span className="thinking-mark"><span /></span>
      </div>
    </div>
  );
}

function ResultContent({ data }: { data: ChatResult }) {
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
    />;
  }
  if (data.consulta_interpretada?.tipo === "indicador" && data.evidencias[0]) {
    return <Indicator evidence={data.evidencias[0]} />;
  }
  return <p className="plain-answer">{data.respuesta}</p>;
}

export default function Experience() {
  const [draft, setDraft] = useState("");
  const [active, setActive] = useState<string | null>(null);
  const [answer, setAnswer] = useState<ChatResult | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const resultRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (answer || queryError)
      resultRef.current?.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "instant"
          : "smooth",
        block: "start",
      });
  }, [answer, queryError]);

  async function submitChatQuestion(text: string) {
    if (busy || text.length < 8 || text.length > 900) return;
    const minimumWait = new Promise<void>((resolve) =>
      window.setTimeout(resolve, MIN_THINKING_MS),
    );
    setActive(text);
    setAnswer(null);
    setQueryError(null);
    setBusy(true);
    try {
      const result = await askChat(text);
      await minimumWait;
      setAnswer(result);
      setDraft("");
    } catch (error) {
      setQueryError(
        error instanceof Error
          ? error.message
          : "No se ha podido completar la consulta.",
      );
    } finally {
      setBusy(false);
    }
  }

  function submitChat(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitChatQuestion(draft.trim());
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
      <main id="inicio">
        <section className="hero wrap" aria-labelledby="hero-title">
          <div className="hero-copy">
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
          <figure className="hero-map">
            <img
              src={spainDots}
              alt="Ilustración de España formada por puntos"
            />
          </figure>
        </section>
        <section
          className="ask-section"
          id="preguntar"
          aria-labelledby="chat-title"
        >
          <div className="wrap">
            <div className="chat-area">
              <div className="chat-heading">
                <h2 id="chat-title">Haz tu pregunta</h2>
                <p>Explora respuestas basadas en los datos disponibles.</p>
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
                <div className="thinking-space">
                  {busy && <ThinkingStatus />}
                </div>
              </div>
            </div>
            <section
              className="result-panel"
              ref={resultRef}
              aria-label="Resultado de la consulta"
              aria-live="polite"
            >
              {active && !busy && (
                <>
                  <div className="asked-question">
                    <span>Tu pregunta</span>
                    <p>{active}</p>
                  </div>
                  <div className="result-body">
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
                        <ResultContent data={answer} />
                      </div>
                    )}
                  </div>
                </>
              )}
            </section>
          </div>
        </section>
      </main>
      <footer className="site-footer wrap">
        <span className="footer-brand">
          pulso<span>.</span>
        </span>
      </footer>
    </div>
  );
}
