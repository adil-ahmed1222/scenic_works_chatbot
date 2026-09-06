"use client";

import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { submitLead } from "@/lib/api";
import { copy, type Lang } from "@/lib/i18n";

type LeadFormProps = {
  language: Lang;
  sessionId?: string;
  sessionToken?: string;
  hint?: string | null;
  onDone?: () => void;
};

export function LeadForm({
  language,
  sessionId,
  sessionToken,
  hint,
  onDone,
}: LeadFormProps) {
  const t = copy[language];
  const [pending, setPending] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setPending(true);
    setError("");
    try {
      await submitLead({
        name: String(form.get("name") || ""),
        email: String(form.get("email") || ""),
        phone: String(form.get("phone") || ""),
        company: String(form.get("company") || ""),
        requirements: String(form.get("requirements") || ""),
        session_id: sessionId,
        session_token: sessionToken,
        language,
        website: String(form.get("website") || ""),
      });
      setDone(true);
    } catch (error) {
      const detail = error instanceof Error ? error.message : "";
      setError(detail && !detail.startsWith("{") ? detail : t.error);
    } finally {
      setPending(false);
    }
  }

  const arabic = language === "ar";
  const textDir = arabic ? "rtl" : "ltr";

  if (done) {
    return (
      <div
        dir={textDir}
        className={`rounded-2xl border border-adroit-gold/30 bg-adroit-gold/10 p-5 text-[15px] leading-relaxed text-white ${arabic ? "text-right" : "text-left"}`}
      >
        {t.thanks}
      </div>
    );
  }

  return (
    <form
      dir="ltr"
      onSubmit={onSubmit}
      className="relative space-y-3 rounded-2xl border border-adroit-border bg-adroit-card p-5"
    >
      <p
        dir={textDir}
        className={`text-[16px] font-semibold text-adroit-gold ${arabic ? "text-right" : "text-left"}`}
      >
        {t.leadTitle}
      </p>
      <p
        dir={textDir}
        className={`text-[13px] text-adroit-muted ${arabic ? "text-right" : "text-left"}`}
      >
        {hint || t.leadHint}
      </p>
      <input
        type="text"
        name="website"
        tabIndex={-1}
        autoComplete="off"
        aria-hidden="true"
        className="absolute -left-[9999px] h-0 w-0 opacity-0"
      />
      <Input
        dir={textDir}
        name="name"
        required
        placeholder={t.name}
        className={arabic ? "text-right" : "text-left"}
      />
      <Input
        dir={textDir}
        name="email"
        type="email"
        required
        placeholder={t.email}
        className={arabic ? "text-right" : "text-left"}
      />
      <Input
        dir={textDir}
        name="phone"
        placeholder={t.phone}
        className={arabic ? "text-right" : "text-left"}
      />
      <Input
        dir={textDir}
        name="company"
        placeholder={t.company}
        className={arabic ? "text-right" : "text-left"}
      />
      <Textarea
        dir={textDir}
        name="requirements"
        placeholder={t.requirements}
        className={arabic ? "text-right" : "text-left"}
      />
      {error ? <p className="text-xs text-red-400">{error}</p> : null}
      <Button type="submit" className="h-11 w-full rounded-full" disabled={pending}>
        {pending ? "…" : t.submit}
      </Button>
    </form>
  );
}
