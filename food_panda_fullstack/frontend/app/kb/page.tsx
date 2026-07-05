"use client";

import Link from "next/link";
import React from "react";

const KB_API_BASE_URL = "http://127.0.0.1:8000";

type KbMetadata = {
  category?: string;
  type?: string;
  [key: string]: unknown;
};

type KbListResponse = {
  documents?: {
    ids?: string[];
    metadatas?: Array<KbMetadata | null>;
    documents?: string[];
  };
};

type KbDocument = {
  id: string;
  doc: string;
  metadata: KbMetadata | null;
};

type IngestResponse = {
  id: string;
  message: string;
  doc: string;
  metadata: KbMetadata;
};

function toDocumentList(payload: KbListResponse): KbDocument[] {
  const ids = payload.documents?.ids ?? [];
  const docs = payload.documents?.documents ?? [];
  const metadatas = payload.documents?.metadatas ?? [];

  return ids.map((id, index) => ({
    id,
    doc: docs[index] ?? "",
    metadata: metadatas[index] ?? null,
  }));
}

export default function KbPage() {
  const [doc, setDoc] = React.useState("");
  const [category, setCategory] = React.useState("");
  const [type, setType] = React.useState("");
  const [documents, setDocuments] = React.useState<KbDocument[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [deletingId, setDeletingId] = React.useState("");
  const [errorMessage, setErrorMessage] = React.useState("");
  const [successMessage, setSuccessMessage] = React.useState("");

  const loadDocuments = React.useCallback(async (showLoadingState = true) => {
    if (showLoadingState) {
      setIsLoading(true);
      setErrorMessage("");
    }

    try {
      const response = await fetch(`${KB_API_BASE_URL}/kb`, {
        method: "GET",
        headers: {
          Accept: "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data = (await response.json()) as KbListResponse;
      setDocuments(toDocumentList(data));
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to load KB documents right now.",
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void loadDocuments(false);
    }, 0);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [loadDocuments]);

  async function handleCreate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const response = await fetch(`${KB_API_BASE_URL}/kb/ingest`, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          doc,
          metadata: {
            category,
            type,
          },
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data = (await response.json()) as IngestResponse;
      setDoc("");
      setCategory("");
      setType("");
      setSuccessMessage(data.message || "Document ingested successfully.");
      await loadDocuments();
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to create the KB document right now.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    setDeletingId(id);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const response = await fetch(`${KB_API_BASE_URL}/kb/${id}`, {
        method: "DELETE",
        headers: {
          Accept: "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data = (await response.json()) as { message?: string };
      setSuccessMessage(
        data.message || `Document with ID ${id} deleted successfully.`,
      );
      await loadDocuments();
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to delete the KB document right now.",
      );
    } finally {
      setDeletingId("");
    }
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(249,115,22,0.18),_transparent_30%),linear-gradient(180deg,_#fff7ed_0%,_#fffbf5_45%,_#f5efe6_100%)] px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
        <section className="overflow-hidden rounded-[2rem] border border-stone-900/10 bg-white/80 shadow-[0_24px_80px_rgba(146,64,14,0.12)] backdrop-blur">
          <div className="border-b border-stone-900/10 px-6 py-6 sm:px-8">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.3em] text-orange-600">
                  Knowledge Base
                </p>
                <h1 className="mt-3 font-serif text-4xl tracking-tight text-stone-950 sm:text-5xl">
                  Manage KB docs
                </h1>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-stone-600 sm:text-base">
                  Add, review, and delete knowledge base documents from one
                  simple screen.
                </p>
              </div>

              <Link
                href="/chat"
                className="rounded-full border border-stone-200 bg-white px-4 py-2 text-sm font-medium text-stone-700 transition hover:border-orange-300 hover:text-orange-700"
              >
                Open chat
              </Link>
            </div>
          </div>

          <div className="grid gap-6 p-6 sm:p-8 lg:grid-cols-[minmax(0,380px)_minmax(0,1fr)]">
            <form
              onSubmit={(event) => void handleCreate(event)}
              className="rounded-[1.5rem] border border-stone-200 bg-stone-50/80 p-5 shadow-sm"
            >
              <div>
                <p className="text-sm font-semibold text-stone-900">
                  Add new document
                </p>
                <p className="mt-1 text-sm text-stone-500">
                  Fill in the text and metadata, then send it to the ingest API.
                </p>
              </div>

              <label className="mt-5 block text-sm font-medium text-stone-700">
                Document
                <textarea
                  value={doc}
                  onChange={(event) => setDoc(event.target.value)}
                  rows={8}
                  required
                  className="mt-2 w-full rounded-[1.25rem] border border-stone-200 bg-white px-4 py-3 text-sm text-stone-800 shadow-sm outline-none transition focus:border-orange-300 focus:ring-4 focus:ring-orange-500/20"
                  placeholder="Paste the KB document text here..."
                />
              </label>

              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <label className="block text-sm font-medium text-stone-700">
                  Category
                  <input
                    value={category}
                    onChange={(event) => setCategory(event.target.value)}
                    required
                    className="mt-2 w-full rounded-[1.25rem] border border-stone-200 bg-white px-4 py-3 text-sm text-stone-800 shadow-sm outline-none transition focus:border-orange-300 focus:ring-4 focus:ring-orange-500/20"
                    placeholder="refund"
                  />
                </label>

                <label className="block text-sm font-medium text-stone-700">
                  Type
                  <input
                    value={type}
                    onChange={(event) => setType(event.target.value)}
                    required
                    className="mt-2 w-full rounded-[1.25rem] border border-stone-200 bg-white px-4 py-3 text-sm text-stone-800 shadow-sm outline-none transition focus:border-orange-300 focus:ring-4 focus:ring-orange-500/20"
                    placeholder="general_question"
                  />
                </label>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="mt-5 w-full rounded-[1.25rem] bg-orange-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-orange-700 focus:outline-none focus:ring-4 focus:ring-orange-500/20 disabled:cursor-not-allowed disabled:bg-orange-300"
              >
                {isSubmitting ? "Saving..." : "Add document"}
              </button>
            </form>

            <div className="rounded-[1.5rem] border border-stone-200 bg-white p-5 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-stone-900">
                    All documents
                  </p>
                  <p className="mt-1 text-sm text-stone-500">
                    Loaded from the `GET /kb` endpoint.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => void loadDocuments()}
                  className="rounded-full border border-stone-200 bg-stone-50 px-4 py-2 text-sm font-medium text-stone-700 transition hover:border-orange-300 hover:bg-white hover:text-orange-700"
                >
                  Refresh
                </button>
              </div>

              {errorMessage ? (
                <div className="mt-5 rounded-[1.25rem] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {errorMessage}
                </div>
              ) : null}

              {successMessage ? (
                <div className="mt-5 rounded-[1.25rem] border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                  {successMessage}
                </div>
              ) : null}

              <div className="mt-5 space-y-4">
                {isLoading ? (
                  <div className="rounded-[1.25rem] border border-dashed border-stone-300 bg-stone-50 px-4 py-8 text-sm text-stone-500">
                    Loading KB documents...
                  </div>
                ) : null}

                {!isLoading && documents.length === 0 ? (
                  <div className="rounded-[1.25rem] border border-dashed border-stone-300 bg-stone-50 px-4 py-8 text-sm text-stone-500">
                    No KB documents found yet.
                  </div>
                ) : null}

                {!isLoading
                  ? documents.map((item) => (
                      <article
                        key={item.id}
                        className="rounded-[1.5rem] border border-stone-200 bg-stone-50/70 p-5"
                      >
                        <div className="flex flex-wrap items-start justify-between gap-4">
                          <div className="min-w-0 flex-1">
                            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
                              Document ID
                            </p>
                            <p className="mt-2 break-all text-sm font-medium text-stone-900">
                              {item.id}
                            </p>
                          </div>

                          <button
                            type="button"
                            onClick={() => void handleDelete(item.id)}
                            disabled={deletingId === item.id}
                            className="rounded-full bg-red-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-red-300"
                          >
                            {deletingId === item.id ? "Deleting..." : "Delete"}
                          </button>
                        </div>

                        <div className="mt-4 flex flex-wrap gap-2">
                          <span className="rounded-full bg-orange-100 px-3 py-1 text-xs font-semibold text-orange-700">
                            category: {String(item.metadata?.category ?? "-")}
                          </span>
                          <span className="rounded-full bg-stone-200 px-3 py-1 text-xs font-semibold text-stone-700">
                            type: {String(item.metadata?.type ?? "-")}
                          </span>
                        </div>

                        <p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-stone-700">
                          {item.doc}
                        </p>
                      </article>
                    ))
                  : null}
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
