import * as React from "react";

import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-11 w-full rounded-card border border-[var(--sw-border,#2A2A2A)] bg-[var(--sw-composer,#0B0B0B)] px-4 text-[15px] leading-none text-[var(--sw-fg,#fff)] placeholder:text-[var(--sw-muted,#9A9A9A)] transition-colors duration-200 focus-visible:border-scenic-orange/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-scenic-orange/35",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input };
