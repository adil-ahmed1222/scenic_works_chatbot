"use client";

import { motion } from "framer-motion";
import { Pause, Play } from "lucide-react";
import { useState } from "react";

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

  async function listen() {
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
      audio.onended = () => setPlaying(false);
      audio.onerror = () => {
        setPlaying(false);
        setVoiceError(true);
      };
      await audio.play();
    } catch {
      setPlaying(false);
      setVoiceError(true);
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28 }}
      className={cn("flex", isUser ? "justify-end" : "justify-start")}
    >
      <div
        className={cn(
          "max-w-[85%] whitespace-pre-wrap",
          isUser
            ? "rounded-[20px] bg-adroit-gold px-5 py-4 text-[#0B0B0B] shadow-gold"
            : "rounded-[20px] border border-adroit-border bg-adroit-card p-5 text-white"
        )}
        style={{
          fontSize: arabic ? 18 : 17,
          lineHeight: 1.8,
          fontFamily: arabic
            ? "var(--font-cairo), Tahoma, sans-serif"
            : "var(--font-inter), system-ui, sans-serif",
        }}
      >
        <p
          dir={arabic ? "rtl" : "ltr"}
          className={arabic ? "text-right" : "text-left"}
        >
          {message.content}
        </p>
        {!isUser && !message.streaming && message.content ? (
          <motion.button
            type="button"
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={listen}
            className="mt-4 inline-flex items-center gap-2 rounded-full border border-adroit-gold/40 bg-adroit-gold/10 px-4 py-2 text-[13px] font-semibold text-adroit-gold-bright"
          >
            {playing ? (
              <Pause className="h-3.5 w-3.5" />
            ) : (
              <Play className="h-3.5 w-3.5 fill-current" />
            )}
            {playing ? t.listening : t.listen}
          </motion.button>
        ) : null}
        {voiceError && !isUser ? (
          <p className="mt-2 text-[12px] text-red-400">{t.voiceError}</p>
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
      <div className="rounded-[20px] border border-adroit-border bg-adroit-card px-5 py-4">
        <p
          dir={arabic ? "rtl" : "ltr"}
          className={cn(
            "text-[14px] font-medium text-adroit-gold-bright",
            arabic ? "font-arabic text-right" : "text-left"
          )}
        >
          {t.thinking}
        </p>
        <div className="mt-3 flex gap-1.5">
          <span className="typing-dot h-2 w-2 rounded-full bg-adroit-gold animate-bounce-dot" />
          <span className="typing-dot h-2 w-2 rounded-full bg-adroit-gold animate-bounce-dot" />
          <span className="typing-dot h-2 w-2 rounded-full bg-adroit-gold animate-bounce-dot" />
        </div>
      </div>
    </motion.div>
  );
}
