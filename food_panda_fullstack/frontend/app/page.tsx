"use client";

import { FormEvent, useRef, useState } from "react";

type StreamEventName =
  | "start"
  | "node"
  | "tool_call"
  | "text"
  | "tool_output"
  | "done";

type EventLog = {
  id: number;
  event: StreamEventName | "unknown";
  payload: string;
};

type ToolCallMap = Record<
  string,
  {
    name: string;
    args: string;
  }
>;

// These defaults make the page demo-ready as soon as it opens.
const DEFAULT_MESSAGE =
  "What is the weather in San Francisco? Use the tool if needed, then tell me something fun about the city.";

const DEFAULT_API_URL = "http://localhost:8000/chat/stream";
const DEFAULT_DELAY_SECONDS = 0.12;

function prettyJson(value: unknown) {
  return JSON.stringify(value, null, 2);
}

// SSE messages are separated by a blank line, but a network chunk may contain
// only part of one message. We keep the unfinished remainder for the next read.
function splitSseMessages(buffer: string) {
  // Normalize line endings to Unix style ("\n") so we can reliably
  // split Server-Sent Events (SSE) messages. SSE uses \n as the
  // delimiter between lines; however, network transports or some
  // servers may emit CRLF ("\r\n"). Converting CRLF -> LF ensures
  // consistent behavior across platforms.
  //
  // Learn more about SSE and the wire format here:
  // https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events
  const normalized = buffer.replace(/\r\n/g, "\n");
  const parts = normalized.split("\n\n");

  return {
    complete: parts.slice(0, -1),
    remainder: parts.at(-1) ?? "",
  };
}

// Each SSE message has an "event:" line plus one or more "data:" lines.
// We turn that wire format back into a small JavaScript object for the UI.
function parseSseMessage(message: string) {
  let event = "message";
  const dataLines: string[] = [];

  for (const line of message.split("\n")) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
      continue;
    }

    if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trim());
    }
  }

  const rawData = dataLines.join("\n");

  return {
    event,
    data: rawData ? JSON.parse(rawData) : null,
  };
}

export default function Home() {
  const abortRef = useRef<AbortController | null>(null);
  const logIdRef = useRef(0);

  // These state values mirror what the backend is streaming so students can
  // see the request lifecycle and the UI state evolve together.
  const [apiUrl, setApiUrl] = useState(DEFAULT_API_URL);
  const [message, setMessage] = useState(DEFAULT_MESSAGE);
  const [delaySeconds, setDelaySeconds] = useState(DEFAULT_DELAY_SECONDS);
  const [status, setStatus] = useState("Idle");
  const [isStreaming, setIsStreaming] = useState(false);
  const [modelNode, setModelNode] = useState("");
  const [assistantText, setAssistantText] = useState("");
  const [toolOutput, setToolOutput] = useState("");
  const [toolCalls, setToolCalls] = useState<ToolCallMap>({});
  const [eventLogs, setEventLogs] = useState<EventLog[]>([]);
  const [errorMessage, setErrorMessage] = useState("");

  // The event log is a teaching/debugging panel that shows the raw structured
  // events exactly as the frontend receives them.
  function appendLog(event: EventLog["event"], payload: unknown) {
    logIdRef.current += 1;
    setEventLogs((current) => [
      {
        id: logIdRef.current,
        event,
        payload: typeof payload === "string" ? payload : prettyJson(payload),
      },
      ...current,
    ]);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    // Stop any older stream before starting a new one so the UI only reflects
    // the latest request.
    abortRef.current?.abort();

    const controller = new AbortController();
    abortRef.current = controller;

    // Reset the UI so each demo starts from a clean state.
    setIsStreaming(true);
    setStatus("Connecting");
    setModelNode("");
    setAssistantText("");
    setToolOutput("");
    setToolCalls({});
    setEventLogs([]);
    setErrorMessage("");

    try {
      // We use fetch instead of EventSource because this stream needs POST
      // with a JSON body, not a simple GET request.
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({
          message,
          delay_seconds: delaySeconds,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      if (!response.body) {
        throw new Error("Streaming is not available because the response body is missing.");
      }

      setStatus("Streaming");

      // Streaming responses arrive as bytes, so we read them chunk by chunk and
      // decode them back into text.
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });

        // One network chunk can contain multiple SSE messages or only half of
        // one, so we split carefully and keep the unfinished tail in `buffer`.
        const { complete, remainder } = splitSseMessages(buffer);
        buffer = remainder;

        for (const rawMessage of complete) {
          if (!rawMessage.trim()) {
            continue;
          }

          const parsed = parseSseMessage(rawMessage);
          const eventName = parsed.event as StreamEventName;

          // This panel helps students compare the backend event protocol with
          // the richer UI state below.
          appendLog(
            ["start", "node", "tool_call", "text", "tool_output", "done"].includes(eventName)
              ? eventName
              : "unknown",
            parsed.data,
          );

          // The backend reports which part of the agent pipeline is active
          // ("model", "tools", etc.), so we surface that as a simple badge.
          if (eventName === "node" && parsed.data?.node) {
            setModelNode(parsed.data.node);
          }

          // Text events stream the assistant answer progressively.
          if (eventName === "text") {
            setAssistantText(parsed.data?.full_text ?? "");
          }

          // Tool calls can arrive in pieces, so we rebuild the current argument
          // string by tool-call id and show it live.
          if (eventName === "tool_call") {
            const id = parsed.data?.id ?? "tool_call";
            setToolCalls((current) => ({
              ...current,
              [id]: {
                name: parsed.data?.name ?? id,
                args: parsed.data?.args_so_far ?? "",
              },
            }));
          }

          // Tool output is separate from the final assistant text, which makes
          // the agent's tool usage easier to explain during the demo.
          if (eventName === "tool_output") {
            setToolOutput((current) =>
              current
                ? `${current}\n${parsed.data?.text ?? ""}`
                : (parsed.data?.text ?? ""),
            );
          }

          // The "done" event is the backend's signal that no more chunks are coming.
          if (eventName === "done") {
            setStatus("Complete");
          }
        }
      }

      setStatus("Complete");
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        setStatus("Stopped");
      } else {
        const message =
          error instanceof Error ? error.message : "An unknown streaming error occurred.";
        setErrorMessage(message);
        setStatus("Error");
      }
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }

  function stopStreaming() {
    abortRef.current?.abort();
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(249,115,22,0.22),_transparent_28%),linear-gradient(180deg,_#fff8ef_0%,_#fffdf8_46%,_#f6efe5_100%)] px-4 py-8 text-stone-900 sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
        <section className="overflow-hidden rounded-[2rem] border border-stone-900/10 bg-white/75 shadow-[0_24px_80px_rgba(146,64,14,0.12)] backdrop-blur">
          <div className="border-b border-stone-900/10 px-6 py-5 sm:px-8">
            <p className="text-xs font-semibold uppercase tracking-[0.32em] text-orange-600">
              Food Panda Agent Stream
            </p>
            <div className="mt-3 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <h1 className="font-serif text-4xl tracking-tight text-stone-950 sm:text-5xl">
                  Watch chat and tool calls arrive in real time
                </h1>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-stone-600 sm:text-base">
                  This page posts to your FastAPI stream endpoint, parses SSE chunks from the
                  response body, and keeps the assistant answer, tool arguments, and tool output
                  visible side by side.
                </p>
              </div>
              <div className="rounded-full border border-stone-900/10 bg-stone-950 px-4 py-2 text-sm font-medium text-stone-50">
                Status: {status}
              </div>
            </div>
          </div>

          <form className="grid gap-5 px-6 py-6 sm:px-8" onSubmit={handleSubmit}>
            <label className="grid gap-2">
              <span className="text-sm font-medium text-stone-700">Backend stream URL</span>
              <input
                className="rounded-2xl border border-stone-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-orange-500 focus:ring-4 focus:ring-orange-500/15"
                value={apiUrl}
                onChange={(event) => setApiUrl(event.target.value)}
                placeholder="http://localhost:8000/chat/stream"
              />
            </label>

            <label className="grid gap-2">
              <span className="text-sm font-medium text-stone-700">Message</span>
              <textarea
                className="min-h-32 rounded-[1.5rem] border border-stone-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-orange-500 focus:ring-4 focus:ring-orange-500/15"
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                placeholder="Ask something that triggers a tool call"
              />
            </label>

            <label className="grid gap-2">
              <span className="text-sm font-medium text-stone-700">Stream delay in seconds</span>
              <input
                className="rounded-2xl border border-stone-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-orange-500 focus:ring-4 focus:ring-orange-500/15"
                type="number"
                min="0"
                max="2"
                step="0.01"
                value={delaySeconds}
                onChange={(event) => setDelaySeconds(Number(event.target.value) || 0)}
              />
            </label>

            <div className="flex flex-col gap-3 sm:flex-row">
              <button
                type="submit"
                disabled={isStreaming}
                className="rounded-full bg-stone-950 px-6 py-3 text-sm font-semibold text-white transition hover:bg-orange-600 disabled:cursor-not-allowed disabled:bg-stone-400"
              >
                {isStreaming ? "Streaming..." : "Start Stream"}
              </button>
              <button
                type="button"
                onClick={stopStreaming}
                disabled={!isStreaming}
                className="rounded-full border border-stone-300 bg-white px-6 py-3 text-sm font-semibold text-stone-700 transition hover:border-stone-950 hover:text-stone-950 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Stop
              </button>
            </div>

            {errorMessage ? (
              <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {errorMessage}
              </div>
            ) : null}
          </form>
        </section>

        {/* The lower half of the page is intentionally split into "final UX"
            panels and a raw event/debug panel so students can connect protocol
            events to visible UI updates. */}
        <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="grid gap-6">
            <article className="rounded-[1.75rem] border border-stone-900/10 bg-white/80 p-6 shadow-[0_20px_50px_rgba(28,25,23,0.08)]">
              <div className="flex items-center justify-between gap-4">
                <h2 className="text-lg font-semibold text-stone-950">Assistant Response</h2>
                <span className="rounded-full bg-orange-100 px-3 py-1 text-xs font-medium text-orange-700">
                  Node: {modelNode || "waiting"}
                </span>
              </div>
              <pre className="mt-4 min-h-52 whitespace-pre-wrap break-words rounded-[1.25rem] bg-stone-950 p-5 font-mono text-sm leading-6 text-stone-100">
                {assistantText || "Assistant text chunks will appear here."}
              </pre>
            </article>

            <article className="rounded-[1.75rem] border border-stone-900/10 bg-white/80 p-6 shadow-[0_20px_50px_rgba(28,25,23,0.08)]">
              <h2 className="text-lg font-semibold text-stone-950">Event Feed</h2>
              <div className="mt-4 max-h-[30rem] space-y-3 overflow-auto pr-1">
                {eventLogs.length === 0 ? (
                  <div className="rounded-[1.25rem] border border-dashed border-stone-300 px-4 py-6 text-sm text-stone-500">
                    Stream events will be listed here as soon as the backend starts sending them.
                  </div>
                ) : (
                  eventLogs.map((entry) => (
                    <div
                      key={entry.id}
                      className="rounded-[1.25rem] border border-stone-200 bg-stone-50 p-4"
                    >
                      <div className="text-xs font-semibold uppercase tracking-[0.22em] text-stone-500">
                        {entry.event}
                      </div>
                      <pre className="mt-3 whitespace-pre-wrap break-words font-mono text-xs leading-5 text-stone-700">
                        {entry.payload}
                      </pre>
                    </div>
                  ))
                )}
              </div>
            </article>
          </div>

          <div className="grid gap-6">
            <article className="rounded-[1.75rem] border border-stone-900/10 bg-white/80 p-6 shadow-[0_20px_50px_rgba(28,25,23,0.08)]">
              <h2 className="text-lg font-semibold text-stone-950">Tool Call Arguments</h2>
              <div className="mt-4 grid gap-4">
                {Object.keys(toolCalls).length === 0 ? (
                  <div className="rounded-[1.25rem] border border-dashed border-stone-300 px-4 py-6 text-sm text-stone-500">
                    Tool call chunks will collect here once the model starts building arguments.
                  </div>
                ) : (
                  Object.entries(toolCalls).map(([id, toolCall]) => (
                    <div key={id} className="rounded-[1.25rem] bg-amber-50 p-4 ring-1 ring-amber-200">
                      <div className="text-sm font-semibold text-amber-900">{toolCall.name}</div>
                      <div className="mt-1 text-xs text-amber-700">Call ID: {id}</div>
                      <pre className="mt-3 whitespace-pre-wrap break-words font-mono text-xs leading-5 text-amber-950">
                        {toolCall.args || "Waiting for arguments..."}
                      </pre>
                    </div>
                  ))
                )}
              </div>
            </article>

            <article className="rounded-[1.75rem] border border-stone-900/10 bg-white/80 p-6 shadow-[0_20px_50px_rgba(28,25,23,0.08)]">
              <h2 className="text-lg font-semibold text-stone-950">Tool Output</h2>
              <pre className="mt-4 min-h-52 whitespace-pre-wrap break-words rounded-[1.25rem] bg-stone-900 p-5 font-mono text-sm leading-6 text-emerald-200">
                {toolOutput || "Tool output will appear here after the tool node runs."}
              </pre>
            </article>
          </div>
        </section>
      </div>
    </main>
  );
}
