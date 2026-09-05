import { NextResponse } from "next/server";

function backendUrl() {
  return (
    process.env.BACKEND_URL?.replace(/\/$/, "") ||
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
    "http://localhost:8000"
  );
}

export async function proxyBackend(path: string, request: Request) {
  const secret = process.env.WIDGET_API_SECRET || "";
  const body = await request.text();
  if (body.length > 50_000) {
    return NextResponse.json({ detail: "Payload too large." }, { status: 413 });
  }
  const forwarded = request.headers.get("x-forwarded-for");
  const realIp = request.headers.get("x-real-ip");
  const response = await fetch(`${backendUrl()}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: request.headers.get("accept") || "application/json",
      ...(secret ? { "X-Widget-Key": secret } : {}),
      ...(forwarded ? { "X-Forwarded-For": forwarded } : {}),
      ...(realIp ? { "X-Real-IP": realIp } : {}),
    },
    body,
    cache: "no-store",
  });
  const contentType = response.headers.get("content-type") || "application/json";
  if (contentType.includes("text/event-stream") && response.body) {
    return new NextResponse(response.body, {
      status: response.status,
      headers: {
        "Content-Type": contentType,
        "Cache-Control": "no-store, no-transform",
        "X-Accel-Buffering": "no",
      },
    });
  }
  const text = await response.text();
  return new NextResponse(text, {
    status: response.status,
    headers: {
      "Content-Type": contentType,
    },
  });
}
