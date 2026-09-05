export default function EmbedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <div className="h-screen w-screen bg-transparent">{children}</div>;
}
