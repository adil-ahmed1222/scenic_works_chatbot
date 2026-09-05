import * as React from "react";

import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-11 w-full rounded-xl border border-adroit-border bg-[#0B0B0B] px-4 text-[15px] text-white placeholder:text-adroit-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-adroit-gold",
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
