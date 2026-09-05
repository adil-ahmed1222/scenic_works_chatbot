"use client";

import { motion } from "framer-motion";
import { Building2, FileText, Phone, Sparkles } from "lucide-react";

import { copy, type Lang } from "@/lib/i18n";

const icons = [Building2, FileText, Sparkles, Phone];

export function WelcomeHero({
  language,
  onSelect,
}: {
  language: Lang;
  onSelect: (prompt: string) => void;
}) {
  const t = copy[language];
  const arabic = language === "ar";

  return (
    <div
      dir={arabic ? "rtl" : "ltr"}
      className={`space-y-6 px-1 pb-2 ${arabic ? "text-right" : "text-left"}`}
    >
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45 }}
        className="rounded-3xl border border-adroit-border bg-gradient-to-br from-[#16120a] via-adroit-card to-[#0d0d0d] p-6 shadow-header"
      >
        <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-adroit-gold">
          Scenic Works · Enterprise AI
        </p>
        <h2
          className={`${arabic ? "font-arabic text-[26px] leading-snug" : "text-[26px] leading-tight"} mt-3 font-bold text-white`}
        >
          {t.welcomeTitle}
        </h2>
        <p className="mt-3 text-[15px] font-medium text-adroit-muted">
          {t.welcomeBody}
        </p>
        <ul className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {t.capabilities.map((item) => (
            <li
              key={item}
              className="flex items-center gap-2 text-[15px] text-white/90"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-adroit-gold" />
              {item}
            </li>
          ))}
        </ul>
      </motion.div>

      <div>
        <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-adroit-muted">
          {t.suggested}
        </p>
        <div className="grid grid-cols-2 gap-3">
          {t.actions.map((action, index) => {
            const Icon = icons[index] ?? Sparkles;
            return (
              <motion.button
                key={action.label}
                type="button"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.08 * index, duration: 0.35 }}
                whileHover={{ y: -2, scale: 1.01 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => onSelect(action.prompt)}
                className="rounded-2xl border border-adroit-border bg-adroit-card p-4 text-start shadow-sm transition-colors hover:border-adroit-gold/50 hover:bg-[#161616]"
              >
                <Icon className="mb-3 h-5 w-5 text-adroit-gold" />
                <span
                  className={`${arabic ? "font-arabic text-[15px]" : "text-[14px]"} block font-semibold text-white`}
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
