import { ChatWidget } from "@/components/chat-widget-lazy";
import { ScenicWorksMark } from "@/components/scenic-works-mark";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-adroit-black text-white">
      <div className="mx-auto max-w-5xl px-6 py-16 md:py-20">
        <ScenicWorksMark className="h-14 w-auto max-w-[min(320px,88vw)] md:h-16" />
        <h1 className="mt-8 text-4xl font-semibold tracking-tight md:text-6xl">
          Official AI chatbot demo
        </h1>
        <p className="mt-4 max-w-2xl text-[16px] leading-relaxed text-adroit-muted">
          This page hosts the floating Scenic Works assistant. Embed the same widget
          on adroitiame.com with a single script tag — no website rebuild
          required.
        </p>
        <pre className="mt-8 overflow-x-auto rounded-card border border-white/10 bg-adroit-card p-4 text-sm text-scenic-orange-bright">
          {`<script src="https://chat.adroitiame.com/widget.js"></script>`}
        </pre>
        <p className="mt-8 text-sm font-medium tracking-wide text-scenic-orange">
          The assistant is open in the bottom-right corner. Ask about exhibitions, events, or fit-outs.
        </p>
      </div>
      <ChatWidget defaultOpen />
    </main>
  );
}
