import { ChatWidget } from "@/components/chat-widget-lazy";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-adroit-black text-white">
      <div className="mx-auto max-w-5xl px-6 py-16">
        <p className="text-sm uppercase tracking-[0.3em] text-adroit-gold">
          Scenic Works
        </p>
        <h1 className="mt-4 text-4xl font-semibold md:text-6xl">
          Official AI chatbot demo
        </h1>
        <p className="mt-4 max-w-2xl text-adroit-muted">
          This page hosts the floating Scenic Works assistant. Embed the same widget
          on adroitiame.com with a single script tag — no website rebuild
          required.
        </p>
        <pre className="mt-8 overflow-x-auto rounded-xl border border-white/10 bg-adroit-charcoal p-4 text-sm text-adroit-gold-bright">
          {`<script src="https://chat.adroitiame.com/widget.js"></script>`}
        </pre>
        <p className="mt-8 text-sm text-adroit-gold">
          The assistant is open in the bottom-right corner. Ask about exhibitions, events, or fit-outs.
        </p>
      </div>
      <ChatWidget defaultOpen />
    </main>
  );
}
