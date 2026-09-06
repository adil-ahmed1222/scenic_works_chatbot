"use client";

import { AnimatePresence, motion } from "framer-motion";
import { FormEvent, useEffect, useRef, useState } from "react";
import {
  Eraser,
  MessageCircle,
  Mic,
  Moon,
  Send,
  Sun,
  Volume2,
  X,
} from "lucide-react";

import { ScenicWorksMark } from "@/components/scenic-works-mark";
import { LeadForm } from "@/components/lead-form";
import {
  MessageBubble,
  ThinkingIndicator,
  type ChatMessage,
} from "@/components/message-bubble";
import { Button } from "@/components/ui/button";
import { WelcomeHero } from "@/components/welcome-hero";
import { requestVoice, streamChat } from "@/lib/api";
import { copy, detectBrowserLanguage, type Lang } from "@/lib/i18n";
import { cn } from "@/lib/utils";

const LANG_KEY = "scenic_works_chat_lang";
const STALE_KEYS = [
  "scenic_works_chat_session",
  "scenic_works_chat_session_token",
  "scenic_works_chat_history_v3",
  "scenic_works_chat_history",
  "scenic-works_chat_history",
];

function purgeStaleChatStorage() {
  STALE_KEYS.forEach((key) => localStorage.removeItem(key));
}

function readPreferredLanguage(): Lang {
  const stored = localStorage.getItem(LANG_KEY);
  if (stored === "en" || stored === "ar") return stored;
  return detectBrowserLanguage();
}

function notifyParent(open: boolean) {
  if (typeof window === "undefined") return;
  window.parent?.postMessage({ source: "scenic-works-widget", open }, "*");
}

export function ChatWidget({
  embedded = false,
  defaultOpen = false,
}: {
  embedded?: boolean;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const [mounted, setMounted] = useState(false);
  const [dark, setDark] = useState(true);
  const [language, setLanguage] = useState<Lang>("en");
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [showLead, setShowLead] = useState(false);
  const [leadHint, setLeadHint] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [sessionToken, setSessionToken] = useState<string | undefined>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [playingLast, setPlayingLast] = useState(false);
  const scroller = useRef<HTMLDivElement>(null);
  const epochRef = useRef(0);
  const requestRef = useRef(0);
  const abortRef = useRef<AbortController | null>(null);
  const sessionRef = useRef<{ id?: string; token?: string }>({});
  const t = copy[language];
  const arabic = language === "ar";

  function resetActiveSession() {
    epochRef.current += 1;
    requestRef.current += 1;
    abortRef.current?.abort();
    abortRef.current = null;
    sessionRef.current = {};
    setMessages([]);
    setSessionId(undefined);
    setSessionToken(undefined);
    setShowLead(false);
    setLeadHint(null);
    setInput("");
    setPending(false);
    setPlayingLast(false);
    purgeStaleChatStorage();
  }

  function closeChat() {
    resetActiveSession();
    setOpen(false);
  }

  function openChat() {
    resetActiveSession();
    setOpen(true);
  }

  function toggleChat() {
    if (open) closeChat();
    else openChat();
  }

  useEffect(() => {
    purgeStaleChatStorage();
    setLanguage(readPreferredLanguage());
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    localStorage.setItem(LANG_KEY, language);
  }, [language, mounted]);

  useEffect(() => {
    scroller.current?.scrollTo({
      top: scroller.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, pending, showLead]);

  useEffect(() => {
    if (embedded) notifyParent(open);
  }, [embedded, open]);

  async function ask(text: string) {
    const trimmed = text.trim();
    if (!trimmed || pending) return;
    const epoch = epochRef.current;
    const requestId = ++requestRef.current;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setInput("");
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
      language,
    };
    setMessages((current) => [...current, userMessage]);
    setPending(true);
    const assistantId = crypto.randomUUID();
    let started = false;
    const timeout = window.setTimeout(() => controller.abort(), 120_000);
    try {
      await streamChat(
        {
          message: trimmed,
          session_id: sessionRef.current.id,
          session_token: sessionRef.current.token,
          language,
        },
        (event) => {
          if (epoch !== epochRef.current || requestId !== requestRef.current) return;
          if (event.type === "meta") {
            sessionRef.current = {
              id: event.session_id,
              token: event.session_token || undefined,
            };
            setSessionId(event.session_id);
            if (event.session_token) setSessionToken(event.session_token);
            if (event.language === "ar" || event.language === "en") {
              setLanguage(event.language);
            }
            return;
          }
          if (event.type === "token") {
            if (!started) {
              started = true;
              setPending(false);
              setMessages((current) => [
                ...current,
                {
                  id: assistantId,
                  role: "assistant",
                  content: event.text,
                  language,
                  streaming: true,
                },
              ]);
              return;
            }
            setMessages((current) =>
              current.map((item) =>
                item.id === assistantId
                  ? { ...item, content: item.content + event.text }
                  : item
              )
            );
            return;
          }
          if (event.type === "done") {
            setPending(false);
            setMessages((current) =>
              current.map((item) =>
                item.id === assistantId
                  ? {
                      ...item,
                      content: event.answer || item.content,
                      sources: event.sources,
                      streaming: false,
                    }
                  : item
              )
            );
            if (event.show_lead_form) {
              setShowLead(true);
              setLeadHint(event.lead_prompt || null);
            } else {
              setShowLead(false);
              setLeadHint(null);
            }
            return;
          }
          if (event.type === "error") {
            throw new Error(event.detail || t.error);
          }
        },
        controller.signal
      );
      if (epoch === epochRef.current && requestId === requestRef.current && !started) {
        setMessages((current) => [
          ...current,
          {
            id: assistantId,
            role: "assistant",
            content: t.error,
            language,
          },
        ]);
      }
    } catch (error) {
      if (epoch !== epochRef.current || requestId !== requestRef.current) return;
      if (error instanceof DOMException && error.name === "AbortError") {
        if (!started) {
          setMessages((current) => [
            ...current,
            {
              id: assistantId,
              role: "assistant",
              content: t.error,
              language,
            },
          ]);
        }
        return;
      }
      if (!started) {
        setMessages((current) => [
          ...current,
          {
            id: assistantId,
            role: "assistant",
            content: t.error,
            language,
          },
        ]);
      }
    } finally {
      window.clearTimeout(timeout);
      if (epoch === epochRef.current && requestId === requestRef.current) setPending(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void ask(input);
  }

  function clearChat() {
    resetActiveSession();
  }

  async function playLastReply() {
    const last = [...messages].reverse().find((item) => item.role === "assistant");
    if (!last) return;
    try {
      setPlayingLast(true);
      const result = await requestVoice({
        text: last.content,
        language: last.language || language,
        session_id: sessionId,
        session_token: sessionToken,
      });
      const audio = new Audio(result.audio_url);
      audio.onended = () => setPlayingLast(false);
      audio.onerror = () => setPlayingLast(false);
      await audio.play();
    } catch (error) {
      console.error("voice_playback_failed", error);
      setPlayingLast(false);
    }
  }

  const panel = (
    <div
      dir="ltr"
      className={cn(
        "flex h-full w-full flex-col overflow-hidden rounded-[28px] border shadow-widget",
        dark
          ? "border-adroit-gold/25 bg-adroit-black text-white"
          : "border-adroit-gold/30 bg-adroit-cream text-[#0B0B0B]"
      )}
    >
      <header
        dir="ltr"
        className="flex min-h-20 shrink-0 items-center justify-between gap-2 border-b border-white/10 bg-white/5 px-4 py-3 shadow-header backdrop-blur-xl"
      >
        <div className="flex min-w-0 flex-1 items-center gap-2.5">
          <ScenicWorksMark className="h-10 w-10 shrink-0" />
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h1
                dir={arabic ? "rtl" : "ltr"}
                className={cn(
                  "whitespace-nowrap text-[18px] font-bold leading-none tracking-tight",
                  arabic && "font-arabic"
                )}
              >
                {t.title}
              </h1>
              <span className="shrink-0 rounded-full bg-adroit-gold px-2 py-0.5 text-[10px] font-bold tracking-wide text-[#0B0B0B]">
                {t.badge}
              </span>
            </div>
            <p
              dir={arabic ? "rtl" : "ltr"}
              className={cn(
                "mt-1.5 text-[12px] font-medium leading-snug text-adroit-muted",
                arabic && "font-arabic"
              )}
            >
              {t.subtitle}
            </p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <span className="flex items-center gap-1.5 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-2 py-1 text-[10px] text-emerald-300">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            {t.online}
          </span>
          <div className="flex rounded-full border border-adroit-border bg-black/30 p-0.5 text-[11px] font-semibold">
            <button
              type="button"
              onClick={() => setLanguage("en")}
              className={cn(
                "rounded-full px-2 py-1",
                language === "en" ? "bg-adroit-gold text-[#0B0B0B]" : "text-adroit-muted"
              )}
            >
              {t.langEn}
            </button>
            <button
              type="button"
              onClick={() => setLanguage("ar")}
              className={cn(
                "rounded-full px-2 py-1",
                language === "ar" ? "bg-adroit-gold text-[#0B0B0B]" : "text-adroit-muted"
              )}
            >
              {t.langAr}
            </button>
          </div>
          <button
            type="button"
            onClick={() => setDark((value) => !value)}
            className="rounded-full p-2 hover:bg-white/10"
            aria-label="Toggle theme"
          >
            {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          <button
            type="button"
            onClick={closeChat}
            className="rounded-full p-2 hover:bg-white/10"
            aria-label="Close chat"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </header>

      <div
        ref={scroller}
        className="adroit-scroll flex-1 space-y-4 overflow-y-auto px-5 py-5"
      >
        {messages.length === 0 ? (
          <WelcomeHero
            language={language}
            onSelect={(prompt, options) => {
              if (options?.openLead) {
                setShowLead(true);
                setLeadHint(t.leadHint);
              }
              void ask(prompt);
            }}
          />
        ) : (
          messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              language={language}
              sessionId={sessionId}
              sessionToken={sessionToken}
            />
          ))
        )}
        {pending ? <ThinkingIndicator language={language} /> : null}
        {showLead ? (
          <LeadForm
            language={language}
            sessionId={sessionId}
            sessionToken={sessionToken}
            hint={leadHint}
            onDone={() => setShowLead(false)}
          />
        ) : null}
      </div>

      <form
        dir="ltr"
        onSubmit={onSubmit}
        className="shrink-0 border-t border-adroit-border bg-[#0E0E0E] px-4 py-4"
      >
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={clearChat}
            className="flex h-[60px] w-[48px] shrink-0 items-center justify-center rounded-full border border-adroit-border text-adroit-muted hover:text-white"
            aria-label={t.clear}
            title={t.clear}
          >
            <Eraser className="h-4 w-4" />
          </button>
          <input
            dir={arabic ? "rtl" : "ltr"}
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder={t.placeholder}
            className={cn(
              "h-[60px] min-w-0 flex-1 rounded-full border border-adroit-border bg-adroit-card px-5 text-[16px] text-white placeholder:text-adroit-muted focus:border-adroit-gold/50 focus:outline-none focus:ring-2 focus:ring-adroit-gold/40",
              arabic ? "text-right font-arabic" : "text-left"
            )}
          />
          <motion.button
            type="button"
            whileTap={{ scale: 0.96 }}
            onClick={() => void playLastReply()}
            disabled={playingLast}
            className="flex h-[60px] w-[48px] shrink-0 items-center justify-center rounded-full border border-adroit-gold/30 text-adroit-gold hover:bg-adroit-gold/10"
            aria-label={t.voiceLast}
            title={t.voiceLast}
          >
            {playingLast ? <Volume2 className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
          </motion.button>
          <Button
            type="submit"
            size="icon"
            className="h-[60px] w-[60px] rounded-full shadow-gold"
            disabled={pending}
            aria-label={t.send}
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
      </form>
    </div>
  );

  if (!mounted) return null;

  return (
    <div
      dir="ltr"
      className="pointer-events-none fixed inset-x-0 bottom-0 z-[9999] flex justify-end p-3 sm:p-5"
    >
      <div className="pointer-events-auto flex max-w-full flex-col items-end gap-3">
        <AnimatePresence>
          {open ? (
            <motion.div
              key="scenic-works-panel"
              initial={{ opacity: 0, y: 18, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 12, scale: 0.98 }}
              className="h-[min(700px,calc(100dvh-6.5rem))] w-[min(500px,calc(100vw-1.5rem))] max-md:w-[min(420px,calc(100vw-1.5rem))] max-sm:h-[min(700px,calc(100dvh-6rem))] max-sm:w-[calc(100vw-1rem)]"
            >
              {panel}
            </motion.div>
          ) : null}
        </AnimatePresence>
        <motion.div whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.96 }}>
          <Button
            size="launcher"
            onClick={toggleChat}
            className="relative bg-gradient-to-br from-adroit-gold to-[#9a7a32] text-[#0B0B0B] shadow-gold"
            aria-label="Open Scenic Works chat"
          >
            {!open ? (
              <span className="absolute inset-0 animate-ping rounded-full bg-adroit-gold/30" />
            ) : null}
            {open ? (
              <X className="relative h-7 w-7" />
            ) : (
              <MessageCircle className="relative h-8 w-8" />
            )}
          </Button>
        </motion.div>
      </div>
    </div>
  );
}
