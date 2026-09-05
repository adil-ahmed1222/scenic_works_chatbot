import * as React from "react";

import { cn } from "@/lib/utils";

const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.ComponentProps<"textarea">
>(({ className, ...props }, ref) => {
  return (
    <textarea
      className={cn(
        "flex min-h-[96px] w-full rounded-xl border border-adroit-border bg-[#0B0B0B] px-4 py-3 text-[15px] text-white placeholder:text-adroit-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-adroit-gold",
        className
      )}
      ref={ref}
      {...props}
    />
  );
});
Textarea.displayName = "Textarea";

export { Textarea };
