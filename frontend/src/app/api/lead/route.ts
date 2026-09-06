import { proxyBackend } from "@/lib/backend-proxy";

export const maxDuration = 60;
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  return proxyBackend("/lead", request);
}
