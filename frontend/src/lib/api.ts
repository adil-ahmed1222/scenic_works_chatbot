export type ChatSource = {
  source_url?: string | null;
  title?: string | null;
  similarity?: number | null;
};

export type ChatResponse = {
  session_id: string;
  session_token?: string | null;
  answer: string;
  language: "en" | "ar" | string;
  sources: ChatSource[];
  show_lead_form: boolean;
  lead_prompt?: string | null;
};

export type LeadPayload = {
  name: string;
  email: string;
  phone?: string;
  company?: string;
  requirements?: string;
  session_id?: string;
  session_token?: string;
  language?: string;
  website?: string;
};

async function request<T>(
  path: string,
  body: unknown,
  signal?: AbortSignal
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export type ChatStreamEvent =
  | {
      type: "meta";
      session_id: string;
      session_token?: string | null;
      language?: string;
      sources?: ChatSource[];
    }
  | { type: "token"; text: string }
  | {
      type: "done";
      answer: string;
      show_lead_form?: boolean;
      lead_prompt?: string | null;
      sources?: ChatSource[];
    }
  | { type: "error"; detail?: string };

export async function streamChat(
  payload: {
    message: string;
    session_id?: string;
    session_token?: string;
    language?: "en" | "ar";
  },
  onEvent: (event: ChatStreamEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(payload),
    signal,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed (${response.status})`);
  }
  if (!response.body) {
    throw new Error("Streaming is not available.");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";
    for (const part of parts) {
      const line = part
        .split("\n")
        .find((item) => item.startsWith("data: "));
      if (!line) continue;
      onEvent(JSON.parse(line.slice(6)) as ChatStreamEvent);
    }
  }
}

export function sendChat(
  payload: {
    message: string;
    session_id?: string;
    session_token?: string;
    language?: "en" | "ar";
  },
  signal?: AbortSignal
) {
  return request<ChatResponse>("/chat", payload, signal);
}

export function requestVoice(
  payload: {
    text: string;
    language: string;
    session_id?: string;
    session_token?: string;
  },
  signal?: AbortSignal
) {
  return request<{ audio_url: string; language: string; voice_id: string }>(
    "/voice",
    {
      ...payload,
      text: payload.text.slice(0, 1500),
    },
    signal
  );
}

export function submitLead(payload: LeadPayload) {
  return request<{ id: string; status: string }>("/lead", payload);
}
