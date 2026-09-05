import { ChatWidget } from "@/components/chat-widget-lazy";

export default function EmbedPage() {
  return (
    <main className="h-screen w-screen overflow-hidden bg-transparent">
      <ChatWidget embedded defaultOpen={false} />
    </main>
  );
}
