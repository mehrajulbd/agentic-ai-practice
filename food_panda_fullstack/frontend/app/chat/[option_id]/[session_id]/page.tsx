"use client";

import Link from "next/link";
import React from "react";

type ChatMessage = [sender: "human" | "ai" | string, text: string];

type ChatHistoryResponse = {
  session_id: string;
  chat_history: ChatMessage[];
  message?: string;
  is_completed?: boolean;
};

type ChatPageProps = {
  params: Promise<{
    option_id: string;
    session_id: string;
  }>;
};

const ChatPage = ({ params }: ChatPageProps) => {
  const { option_id, session_id } = React.use(params);
  const [chatHistory, setChatHistory] = React.useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [errorMessage, setErrorMessage] = React.useState("");
  const [user_message, setUserMessage] = React.useState("");
  const [isSending, setIsSending] = React.useState(false);
  const [isCompleted, setIsCompleted] = React.useState(false);

  React.useEffect(() => {
    const controller = new AbortController();

    const loadChatHistory = async () => {
      setIsLoading(true);
      setErrorMessage("");

      try {
        const response = await fetch(
          `http://127.0.0.1:8000/chat/history/${session_id}`,
          {
            method: "GET",
            headers: {
              Accept: "application/json",
            },
            signal: controller.signal,
          },
        );

        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }

        const data = (await response.json()) as ChatHistoryResponse;
        setChatHistory(
          Array.isArray(data.chat_history) ? data.chat_history : [],
        );
      } catch (error) {
        if (error instanceof Error && error.name === "AbortError") {
          return;
        }

        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Unable to load chat history right now.",
        );
      } finally {
        setIsLoading(false);
      }
    };

    void loadChatHistory();

    return () => {
      controller.abort();
    };
  }, [session_id]);

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(249,115,22,0.18),_transparent_30%),linear-gradient(180deg,_#fff7ed_0%,_#fffbf5_45%,_#f5efe6_100%)] px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-6">
        <section className="overflow-hidden rounded-[2rem] border border-stone-900/10 bg-white/80 shadow-[0_24px_80px_rgba(146,64,14,0.12)] backdrop-blur">
          <div className="border-b border-stone-900/10 px-6 py-6 sm:px-8">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-orange-600">
              Chat History
            </p>
            <h1 className="mt-3 font-serif text-4xl tracking-tight text-stone-950 sm:text-5xl">
              Session #{session_id}
            </h1>
            <p className="mt-3 text-sm leading-6 text-stone-600 sm:text-base">
              Showing support conversation for option #{option_id}.
            </p>
          </div>

          <div className="space-y-4 p-6 sm:p-8">
            {isLoading ? (
              <div className="rounded-[1.5rem] border border-dashed border-stone-300 bg-stone-50 px-5 py-8 text-sm text-stone-500">
                Loading chat history...
              </div>
            ) : null}

            {!isLoading && errorMessage ? (
              <div className="rounded-[1.5rem] border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
                {errorMessage}
              </div>
            ) : null}

            {!isLoading && !errorMessage && chatHistory.length === 0 ? (
              <div className="rounded-[1.5rem] border border-dashed border-stone-300 bg-stone-50 px-5 py-8 text-sm text-stone-500">
                No chat history found for this session yet.
              </div>
            ) : null}

            {!isLoading && !errorMessage
              ? chatHistory.map(([sender, text], index) => {
                  const isHuman = sender === "human";

                  return (
                    <article
                      key={`${sender}-${index}`}
                      className={`rounded-[1.5rem] border px-5 py-4 shadow-sm ${
                        isHuman
                          ? "border-orange-200 bg-orange-50/80 text-stone-800"
                          : "border-stone-200 bg-white text-stone-800"
                      }`}
                    >
                      <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
                        {isHuman ? "Customer" : "Assistant"}
                      </p>
                      <p className="mt-3 whitespace-pre-wrap text-sm leading-6 sm:text-base">
                        {text}
                      </p>
                    </article>
                  );
                })
              : null}
          </div>
          {isCompleted ? (
            <div className="border-t border-stone-900/10 px-6 py-6 sm:px-8">
              <div className="text-sm text-stone-500">
                This conversation has been completed.
              </div>
              <Link href="/chat" className="mt-4 inline-block text-sm font-medium text-orange-600 hover:text-orange-700">
                Start a new conversation
              </Link>
            </div>
          ) : (
            <form
              onSubmit={(e: { preventDefault: () => void }) => {
                e.preventDefault();
                setIsSending(true);
                fetch(`http://127.0.0.1:8000/chat`, {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                  },
                  body: JSON.stringify({
                    session_id: session_id,
                    message: user_message,
                    option_id: option_id,
                  }),
                })
                  .then((response) => {
                    if (!response.ok) {
                      throw new Error(
                        `Request failed with status ${response.status}`,
                      );
                    }
                    return response.json();
                  })
                  .then((data: ChatHistoryResponse) => {
                    setChatHistory(
                      Array.isArray(data.chat_history) ? data.chat_history : [],
                    );
                    if (data.is_completed) {
                      setIsCompleted(true);
                    }
                  })
                  .catch((error) => {
                    setErrorMessage(
                      error instanceof Error
                        ? error.message
                        : "Unable to send message right now.",
                    );
                  })
                  .finally(() => {
                    setIsSending(false);
                  });
                setUserMessage("");
              }}
              className="border-t border-stone-900/10 px-6 py-6 sm:px-8"
            >
              <div>
                <textarea
                  className="w-full rounded-[1.5rem] border border-stone-200 bg-white px-5 py-4 text-sm text-stone-800 shadow-sm focus:border-orange-300 focus:ring-4 focus:ring-orange-500/20 sm:text-base"
                  placeholder="Type your message here..."
                  rows={3}
                  value={user_message}
                  onChange={(e) => setUserMessage(e.target.value)}
                />
              </div>
              <div className="mt-4 flex justify-end">
                {isSending ? (
                  <button
                    type="button"
                    className="rounded-[1.5rem] bg-orange-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition duration-200 hover:bg-orange-700 focus:outline-none focus:ring-4 focus:ring-orange-500/20 sm:text-base"
                    disabled
                  >
                    Sending...
                  </button>
                ) : (
                  <button
                    type="submit"
                    className="rounded-[1.5rem] bg-orange-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition duration-200 hover:bg-orange-700 focus:outline-none focus:ring-4 focus:ring-orange-500/20 sm:text-base"
                    disabled={isSending}
                  >
                    Send
                  </button>
                )}
              </div>
            </form>
          )}
        </section>
      </div>
    </main>
  );
};

export default ChatPage;
