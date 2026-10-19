export type QuestionId = "P1" | "P2" | "P3" | "P4";

export type ChatResult = {
  pregunta: string;
  respuesta: string;
  consulta_interpretada?: {
    tipo: "escenario" | "indicador" | "no_disponible";
    anio: number;
    pregunta_id?: QuestionId | null;
    filtros?: Record<string, string>;
    edad_min?: number | null;
    edad_max?: number | null;
  } | null;
  desgloses?: {
    total: {
      porcentajes: Record<string, number | null>;
      registros_sinteticos: number;
    };
    por_sexo?: Record<string, ChatGroupResult>;
    por_edad?: Record<string, ChatGroupResult>;
  };
  evidencias: Record<string, unknown>[];
  fiabilidad: string;
  procedencia?: string;
};

export type ChatGroupResult = {
  porcentajes?: Record<string, number | null>;
  registros_sinteticos?: number;
  error?: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

async function request(path: string, init?: RequestInit): Promise<unknown> {
  const response = await fetch(path, init);
  let data: unknown;

  try {
    data = await response.json();
  } catch {
    throw new Error("La API no ha devuelto una respuesta válida.");
  }

  if (!response.ok) {
    const detail = isRecord(data) ? data.detail : undefined;
    throw new Error(
      response.status === 404 && detail === "Not Found"
        ? "La API conectada no tiene esta ruta. Comprueba el puerto del backend."
        :
      typeof detail === "string"
        ? detail
        : "No se ha podido completar la consulta.",
    );
  }

  return data;
}

export async function askChat(question: string): Promise<ChatResult> {
  const data = await request("/escenarios/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pregunta: question }),
  });
  if (
    !isRecord(data) ||
    typeof data.respuesta !== "string" ||
    !Array.isArray(data.evidencias)
  ) {
    throw new Error("La respuesta recibida no tiene el formato esperado.");
  }
  return data as ChatResult;
}
