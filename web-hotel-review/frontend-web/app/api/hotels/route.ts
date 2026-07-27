import { NextRequest, NextResponse } from "next/server";
import { getServerApiBaseUrl } from "@/lib/server-api";

const API_BASE_URL = getServerApiBaseUrl();

export async function GET(request: NextRequest) {
  const url = new URL("/api/v1/hotels", API_BASE_URL);
  request.nextUrl.searchParams.forEach((value, key) => {
    url.searchParams.set(key, value);
  });

  const response = await fetch(url.toString(), {
    cache: "no-store",
    headers: {
      Accept: "application/json",
    },
  });

  const body = await response.text();

  return new NextResponse(body, {
    status: response.status,
    headers: {
      "content-type": response.headers.get("content-type") || "application/json",
    },
  });
}
