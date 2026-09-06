"use client";

import { motion } from "framer-motion";
import { Pause, Play } from "lucide-react";
import { useRef, useState } from "react";

import { MarkdownContent } from "@/components/markdown-content";
import { requestVoice, type ChatSource } from "@/lib/api";
import { copy, type Lang } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  language?: Lang;
  sources?: ChatSource[];
  streaming?: boolean;
};

export function MessageBubble({
  message,
  language,
  sessionId,
  sessionToken,
}: {
  message: ChatMessage;
  language: Lang;
  sessionId?: string;
  sessionToken?: string;
}) {
  const t = copy[language];
  const isUser = message.role === "user";
  const arabic = (message.language || language) === "ar";
  const [playing, setPlaying] = useState(false);
  const [voiceError, setVoiceError] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const requestLock = useRef(false);

  async function listen() {
    if (playing) {
      audioRef.current?.pause();
      audioRef.current = null;
      setPlaying(false);
      return;
    }
    if (requestLock.current) return;
    requestLock.current = true;
    try {
      setVoiceError(false);
      setPlaying(true);
      const result = await requestVoice({
        text: message.content,
        language: message.language || language,
        session_id: sessionId,
        session_token: sessionToken,
      });
      const audio = new Audio(result.audio_url);
      audioRef.current = audio;
      audio.onended = () => {
        setPlaying(false);
        audioRef.current = null;
      };
      audio.onerror = () => {
        setPlaying(false);
        setVoiceError(true);
        audioRef.current = null;
      };
      await audio.play();
    } catch {
      setPlaying(false);
      setVoiceError(true);
    } finally {
      requestLock.current = false;
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28, ease: "easeOut" }}
      className={cn("flex", isUser ? "justify-end" : "justify-start")}
    >
      <div
        className={cn(
          "max-w-[85%] px-4 py-3.5",
          isUser
            ? "rounded-bubble rounded-br-md bg-scenic-orange text-white shadow-gold"
            : "rounded-bubble rounded-bl-md border border-[var(--sw-border)] bg-[var(--sw-card)] text-[var(--sw-fg)]"
        )}
        style={{
          fontSize: arabic ? 17 : 15,
          lineHeight: 1.7,
          fontFamily: arabic
            ? "var(--font-cairo), Tahoma, sans-serif"
            : "var(--font-inter), system-ui, sans-serif",
        }}
      >
        <div dir={arabic ? "rtl" : "ltr"} className={arabic ? "text-right" : "text-left"}>
          <MarkdownContent
            content={message.content}
            className={isUser ? "sw-md-user" : undefined}
          />
        </div>
        {!isUser && !message.streaming && message.content ? (
          <motion.button
            type="button"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={listen}
            className="mt-3 inline-flex items-center gap-2 rounded-full border border-scenic-orange/30 bg-scenic-orange/10 px-3.5 py-1.5 text-[12px] font-semibold tracking-wide text-scenic-orange transition-colors duration-200 hover:border-scenic-orange/50 hover:bg-scenic-orange/15"
          >
            {playing ? (
              <Pause className="h-3.5 w-3.5" strokeWidth={1.75} />
            ) : (
              <Play className="h-3.5 w-3.5 fill-current" strokeWidth={1.75} />
            )}
            {playing ? t.listening : t.listen}
          </motion.button>
        ) : null}
        {voiceError && !isUser ? (
          <p className="mt-2 text-[12px] leading-relaxed text-red-400">{t.voiceError}</p>
        ) : null}
      </div>
    </motion.div>
  );
}

export function ThinkingIndicator({ language }: { language: Lang }) {
  const t = copy[language];
  const arabic = language === "ar";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex justify-start"
    >
      <div
        dir={arabic ? "rtl" : "ltr"}
        className="flex items-center gap-3 rounded-bubble rounded-bl-md border border-[var(--sw-border)] bg-[var(--sw-card)] px-4 py-3.5"
      >
        <span className="sw-buffer shrink-0" aria-hidden="true" />
        <p
          className={cn(
            "text-[13px] font-medium tracking-wide text-scenic-orange",
            arabic ? "font-arabic text-right" : "text-left"
          )}
        >
          {t.thinking}
        </p>
      </div>
    </motion.div>
  );
}
