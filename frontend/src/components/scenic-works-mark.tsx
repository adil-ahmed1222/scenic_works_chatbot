export function ScenicWorksMark({ className = "h-10 w-10" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 40 40"
      className={className}
      aria-hidden="true"
      fill="none"
    >
      <rect width="40" height="40" rx="12" fill="#C8A24A" />
      <text
        x="20"
        y="26.5"
        textAnchor="middle"
        fill="#0B0B0B"
        fontFamily="Inter, system-ui, sans-serif"
        fontSize="13"
        fontWeight="800"
        letterSpacing="-0.4"
      >
        SW
      </text>
    </svg>
  );
}
