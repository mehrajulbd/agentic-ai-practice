"use client";
import Link from 'next/link';
import React from 'react'

const generate_session_id = () => {
    return Math.floor(Math.random() * 1000000).toString();
}

const ChatHomePage = () => {
    const [sessionId] = React.useState<string>(generate_session_id());
    const options = [
        {id: 1, text: "What is the refund turnaround time?"},
        {id: 2, text: "Check refund status"},
        {id: 3, text: "I have been overcharged"},
        {id: 4, text: "I didn't receive invoice"},
        {id: 5, text: "General Questions"},
        {id: 6, text: "General feedback"}
    ];
    
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(249,115,22,0.18),_transparent_30%),linear-gradient(180deg,_#fff7ed_0%,_#fffbf5_45%,_#f5efe6_100%)] px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-8">
        <section className="overflow-hidden rounded-[2rem] border border-stone-900/10 bg-white/80 shadow-[0_24px_80px_rgba(146,64,14,0.12)] backdrop-blur">
          <div className="border-b border-stone-900/10 px-6 py-6 sm:px-8">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.3em] text-orange-600">
                  Chat Support
                </p>
                <h1 className="mt-3 font-serif text-4xl tracking-tight text-stone-950 sm:text-5xl">
                  Select an option
                </h1>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-stone-600 sm:text-base">
                  Start a support conversation by choosing the topic that best matches your issue.
                </p>
              </div>

              <Link
                href="/kb"
                className="rounded-full border border-stone-200 bg-white px-4 py-2 text-sm font-medium text-stone-700 transition hover:border-orange-300 hover:text-orange-700"
              >
                Manage KB docs
              </Link>
            </div>
          </div>

          <div className="grid gap-4 p-6 sm:grid-cols-2 sm:p-8">
        {options.map(option => (
              <Link
                key={option.id}
                href={`/chat/${option.id}/${sessionId}`}
                className="group rounded-[1.5rem] border border-stone-200 bg-stone-50/80 px-5 py-5 text-sm font-medium text-stone-700 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-orange-300 hover:bg-white hover:text-stone-950 hover:shadow-[0_16px_40px_rgba(249,115,22,0.16)] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-orange-500/20"
              >
                <span className="flex items-start justify-between gap-4">
                  <span className="leading-6">{option.text}</span>
                  <span className="rounded-full bg-orange-100 px-3 py-1 text-xs font-semibold text-orange-700 transition group-hover:bg-orange-500 group-hover:text-white">
                    #{option.id}
                  </span>
                </span>
              </Link>
        ))}
          </div>
        </section>
      </div>
    </main>
  )
}

export default ChatHomePage
