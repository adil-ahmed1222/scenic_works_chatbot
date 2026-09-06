import { cn } from "@/lib/utils";

export function ScenicWorksMark({
  className = "h-10 w-auto",
  inverted = false,
}: {
  className?: string;
  inverted?: boolean;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center",
        inverted && "rounded-md bg-black px-2 py-1"
      )}
    >
      {/* Official lockup; black canvas was cropped to a transparent wide mark. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/scenic-works-logo.png"
        alt="Scenic Works"
        className={cn("object-contain object-left", className)}
      />
    </span>
  );
}
