"use client";

import dynamic from "next/dynamic";

export const ChatWidget = dynamic(
  () => import("@/components/chat-widget").then((mod) => mod.ChatWidget),
  { ssr: false }
);
