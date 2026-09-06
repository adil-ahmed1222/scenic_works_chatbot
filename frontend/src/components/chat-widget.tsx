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
      data-theme={dark ? "dark" : "light"}
      className={cn(
        "sw-widget flex h-full w-full flex-col overflow-hidden rounded-widget border shadow-widget",
        dark
          ? "border-scenic-orange/20 bg-[var(--sw-bg)] text-[var(--sw-fg)]"
          : "border-scenic-orange/25 bg-[var(--sw-bg)] text-[var(--sw-fg)]"
      )}
    >
      <header
        dir="ltr"
        className="flex min-h-[68px] shrink-0 items-center justify-between gap-3 border-b border-[var(--sw-border)] bg-[var(--sw-header)] px-4 py-3 shadow-header"
      >
        <div className="flex min-w-0 flex-1 items-center">
          <ScenicWorksMark
            inverted={!dark}
            className="h-9 w-auto max-w-[min(196px,46vw)] shrink-0 sm:h-10 sm:max-w-[220px]"
          />
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          <span className="hidden items-center gap-1.5 rounded-full border border-emerald-400/25 bg-emerald-400/10 px-2 py-1 text-[10px] font-medium tracking-wide text-emerald-300 sm:flex">
            <span className="sw-online-dot h-1.5 w-1.5 rounded-full bg-emerald-400" />
            {t.online}
          </span>
          <div className="flex rounded-full border border-[var(--sw-border)] bg-[var(--sw-card)] p-0.5 text-[10px] font-semibold tracking-wide">
            <button
              type="button"
              onClick={() => setLanguage("en")}
              className={cn(
                "rounded-full px-2 py-1 transition-colors duration-200",
                language === "en"
                  ? "bg-scenic-orange text-white"
                  : "text-[var(--sw-muted)] hover:text-[var(--sw-fg)]"
              )}
            >
              {t.langEn}
            </button>
            <button
              type="button"
              onClick={() => setLanguage("ar")}
              className={cn(
                "rounded-full px-2 py-1 transition-colors duration-200",
                language === "ar"
                  ? "bg-scenic-orange text-white"
                  : "text-[var(--sw-muted)] hover:text-[var(--sw-fg)]"
              )}
            >
              {t.langAr}
            </button>
          </div>
          <button
            type="button"
            onClick={() => setDark((value) => !value)}
            className="sw-icon-btn"
            aria-label="Toggle theme"
          >
            {dark ? <Sun className="h-4 w-4" strokeWidth={1.75} /> : <Moon className="h-4 w-4" strokeWidth={1.75} />}
          </button>
          <button
            type="button"
            onClick={closeChat}
            className="sw-icon-btn"
            aria-label="Close chat"
          >
            <X className="h-4 w-4" strokeWidth={1.75} />
          </button>
        </div>
      </header>

      <div
        ref={scroller}
        className="adroit-scroll flex-1 space-y-3.5 overflow-y-auto px-4 py-4"
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
        className="shrink-0 border-t border-[var(--sw-border)] bg-[var(--sw-surface)] px-3 py-3 sm:px-4"
      >
        <div className="sw-composer flex items-center gap-1 rounded-full border border-[var(--sw-border)] bg-[var(--sw-card)] p-1.5 shadow-card transition-[border-color,box-shadow] duration-200">
          <button
            type="button"
            onClick={clearChat}
            className="sw-icon-btn h-10 w-10"
            aria-label={t.clear}
            title={t.clear}
          >
            <Eraser className="h-4 w-4" strokeWidth={1.75} />
          </button>
          <input
            dir={arabic ? "rtl" : "ltr"}
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder={t.placeholder}
            className={cn(
              "h-10 min-w-0 flex-1 bg-transparent px-2 text-[15px] text-[var(--sw-fg)] placeholder:text-[var(--sw-muted)] focus:outline-none",
              arabic ? "text-right font-arabic" : "text-left"
            )}
          />
          <motion.button
            type="button"
            whileTap={{ scale: 0.96 }}
            onClick={() => void playLastReply()}
            disabled={playingLast}
            className="sw-icon-btn h-10 w-10 text-scenic-orange hover:text-scenic-orange-bright disabled:opacity-50"
            aria-label={t.voiceLast}
            title={t.voiceLast}
          >
            {playingLast ? (
              <Volume2 className="h-4 w-4" strokeWidth={1.75} />
            ) : (
              <Mic className="h-4 w-4" strokeWidth={1.75} />
            )}
          </motion.button>
          <Button
            type="submit"
            size="icon"
            className="h-10 w-10 rounded-full shadow-gold"
            disabled={pending}
            aria-label={t.send}
          >
            <Send className="h-4 w-4" strokeWidth={1.75} />
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
              initial={{ opacity: 0, y: 16, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.98 }}
              transition={{ duration: 0.28, ease: "easeOut" }}
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
            className="relative bg-gradient-to-br from-scenic-orange to-scenic-orange-deep text-white shadow-gold"
            aria-label="Open Scenic Works chat"
          >
            {!open ? (
              <span className="absolute inset-0 animate-ping rounded-full bg-scenic-orange/30" />
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
