import { NextRequest, NextResponse } from "next/server";
import { getServerApiBaseUrl } from "@/lib/server-api";

const API_BASE_URL = getServerApiBaseUrl();
const REVIEWS_CACHE_TTL_MS = 30_000;
const REVIEWS_FETCH_TIMEOUT_MS = 15_000;

type CachedResponse = {
  body: string;
  status: number;
  contentType: string;
  expiresAt: number;
};

const responseCache = new Map<string, CachedResponse>();
const pendingRequests = new Map<string, Promise<CachedResponse>>();

function buildCacheKey(searchParams: URLSearchParams) {
  return searchParams.toString();
}

async function fetchReviews(url: string) {
  const response = await fetch(url, {
    cache: "no-store",
    signal: AbortSignal.timeout(REVIEWS_FETCH_TIMEOUT_MS),
    headers: {
      Accept: "application/json",
    },
  });

  const body = await response.text();

  return {
    body,
    status: response.status,
    contentType: response.headers.get("content-type") || "application/json",
    expiresAt: Date.now() + REVIEWS_CACHE_TTL_MS,
  } satisfies CachedResponse;
}

export async function GET(request: NextRequest) {
  const cacheKey = buildCacheKey(request.nextUrl.searchParams);
  const cached = responseCache.get(cacheKey);

  if (cached && cached.expiresAt > Date.now()) {
    return new NextResponse(cached.body, {
      status: cached.status,
      headers: {
        "content-type": cached.contentType,
        "x-cache": "HIT",
      },
    });
  }

  const url = new URL("/api/v1/reviews", API_BASE_URL);
  request.nextUrl.searchParams.forEach((value, key) => {
    url.searchParams.set(key, value);
  });

  const pending = pendingRequests.get(cacheKey);
  const dataPromise = pending || fetchReviews(url.toString());
  if (!pending) {
    pendingRequests.set(cacheKey, dataPromise);
  }

  let result: CachedResponse;
  try {
    result = await dataPromise.finally(() => {
      pendingRequests.delete(cacheKey);
    });
  } catch (error) {
    const message =
      error instanceof Error && error.message.length > 0
        ? error.message
        : "Review query timed out.";

    return NextResponse.json(
      {
        message,
        hint: "The review dataset query took too long. Try narrowing filters or reducing the result scope.",
      },
      {
        status: 504,
        headers: {
          "x-cache": "MISS",
        },
      },
    );
  }

  responseCache.set(cacheKey, result);

  return new NextResponse(result.body, {
    status: result.status,
    headers: {
      "content-type": result.contentType,
      "x-cache": "MISS",
    },
  });
}
