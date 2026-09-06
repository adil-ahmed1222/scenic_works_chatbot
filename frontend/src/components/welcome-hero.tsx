"use client";

import { motion } from "framer-motion";
import {
  Building2,
  CalendarDays,
  ChevronRight,
  FileText,
  Lightbulb,
  MessagesSquare,
  Palette,
  PanelsTopLeft,
  Phone,
  Sparkles,
} from "lucide-react";

import { copy, type Lang } from "@/lib/i18n";
import { cn } from "@/lib/utils";

const capabilityIcons = [
  Building2,
  CalendarDays,
  PanelsTopLeft,
  Palette,
  Lightbulb,
  MessagesSquare,
];

const actionIcons = [Building2, FileText, Sparkles, Phone];

export function WelcomeHero({
  language,
  onSelect,
}: {
  language: Lang;
  onSelect: (prompt: string, options?: { openLead?: boolean }) => void;
}) {
  const t = copy[language];
  const arabic = language === "ar";

  return (
    <div
      dir={arabic ? "rtl" : "ltr"}
      className={cn("space-y-6 px-0.5 pb-1", arabic ? "text-right" : "text-left")}
    >
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: "easeOut" }}
      >
        <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-scenic-orange">
          Engineering Emotion
        </p>
        <h2
          className={cn(
            "mt-2 text-[22px] font-semibold tracking-tight text-[var(--sw-fg)]",
            arabic ? "font-arabic leading-snug" : "leading-tight"
          )}
        >
          {t.welcomeTitle}
        </h2>
        <p className="mt-2 text-[14px] leading-relaxed text-[var(--sw-muted)]">
          {t.welcomeBody}
        </p>
      </motion.div>

      <div className="grid grid-cols-2 gap-2">
        {t.capabilities.map((item, index) => {
          const Icon = capabilityIcons[index] ?? Sparkles;
          return (
            <motion.div
              key={item}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.04 * index, duration: 0.3 }}
              className="flex items-center gap-2.5 rounded-card border border-[var(--sw-border)] bg-[var(--sw-card)] px-3 py-2.5"
            >
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-scenic-orange/10 text-scenic-orange">
                <Icon className="h-4 w-4" strokeWidth={1.75} />
              </span>
              <span
                className={cn(
                  "text-[12.5px] font-medium leading-snug text-[var(--sw-fg)]",
                  arabic && "font-arabic"
                )}
              >
                {item}
              </span>
            </motion.div>
          );
        })}
      </div>

      <div>
        <p className="mb-2.5 text-[10px] font-semibold uppercase tracking-[0.22em] text-[var(--sw-muted)]">
          {t.suggested}
        </p>
        <div className="grid grid-cols-2 gap-2.5">
          {t.actions.map((action, index) => {
            const Icon = actionIcons[index] ?? Sparkles;
            return (
              <motion.button
                key={action.label}
                type="button"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.08 + 0.05 * index, duration: 0.3 }}
                whileHover={{ y: -2 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => onSelect(action.prompt, { openLead: action.openLead })}
                className="group rounded-card border border-[var(--sw-border)] bg-[var(--sw-card)] p-3.5 text-start transition-colors duration-200 hover:border-scenic-orange/50 hover:bg-[var(--sw-elevated)]"
              >
                <span className="mb-3 flex items-center justify-between">
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-scenic-orange/10 text-scenic-orange transition-colors duration-200 group-hover:bg-scenic-orange/16">
                    <Icon className="h-[18px] w-[18px]" strokeWidth={1.75} />
                  </span>
                  <ChevronRight
                    className={cn(
                      "h-4 w-4 text-[var(--sw-muted)] transition-all duration-200 group-hover:text-scenic-orange",
                      arabic && "rotate-180"
                    )}
                    strokeWidth={1.75}
                  />
                </span>
                <span
                  className={cn(
                    "block font-semibold leading-snug text-[var(--sw-fg)]",
                    arabic ? "font-arabic text-[14px]" : "text-[13px]"
                  )}
                >
                  {action.label}
                </span>
              </motion.button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
