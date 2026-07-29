import { NextRequest, NextResponse } from "next/server";
import { getServerApiBaseUrl } from "@/lib/server-api";

const API_BASE_URL = getServerApiBaseUrl();
const ANALYTICS_CACHE_TTL_MS = 5 * 60_000;
const ANALYTICS_FETCH_TIMEOUT_MS = 30_000;

type ReviewSummaryAggregate = {
  hotel_id: string | null;
  platform_code: string | null;
  reviewer_country_code: string | null;
  date_from: string | null;
  date_to: string | null;
  total_reviews: number;
  bad_reviews: number;
  bad_review_ratio: number;
  avg_rating: number | null;
  positive_reviews: number | null;
  neutral_reviews: number | null;
  negative_reviews: number | null;
  mixed_reviews: number | null;
  latest_reviewed_at: string | null;
  latest_source_updated_at: string | null;
  source_total_reviews: number | null;
  source_average_rating: number | null;
  source_rating_scale: number | null;
  last_aggregated_at: string | null;
};

type ReviewCountryBreakdownItem = {
  reviewer_country_code: string;
  total_reviews: number;
  bad_reviews: number;
  avg_rating: number | null;
};

type ReviewHotelBreakdownItem = {
  hotel_id: string;
  hotel_name: string;
  platform_code: string | null;
  total_reviews: number;
  bad_reviews: number;
  avg_rating: number | null;
  latest_reviewed_at: string | null;
};

type ReviewScoreBucketItem = {
  bucket_code: string;
  bucket_label: string;
  rating_from: number;
  rating_to: number;
  review_count: number;
  bad_review_count: number;
};

type ReviewDailyTrendItem = {
  metric_date: string;
  total_reviews: number;
  bad_reviews: number;
  avg_rating: number | null;
  positive_reviews: number | null;
  neutral_reviews: number | null;
  negative_reviews: number | null;
  mixed_reviews: number | null;
};

type BreakdownResponse<T> = {
  items: T[];
  total: number;
};

type AnalyticsPayload = {
  summary: ReviewSummaryAggregate;
  country_breakdown: ReviewCountryBreakdownItem[];
  hotel_breakdown: ReviewHotelBreakdownItem[];
  score_buckets: ReviewScoreBucketItem[];
  daily_trend: ReviewDailyTrendItem[];
  supports_full_analytics: boolean;
  unsupported_filters: string[];
};

type CachedAnalytics = {
  payload: AnalyticsPayload;
  expiresAt: number;
};

const analyticsCache = new Map<string, CachedAnalytics>();
const pendingAnalyticsRequests = new Map<string, Promise<AnalyticsPayload>>();

function buildAnalyticsCacheKey(searchParams: URLSearchParams) {
  const normalized = new URLSearchParams();
  searchParams.forEach((value, key) => {
    normalized.set(key, value);
  });
  return normalized.toString();
}

function buildBaseAnalyticsParams(searchParams: URLSearchParams) {
  const params = new URLSearchParams();

  const hotelId = searchParams.get("hotel_id");
  const platformCode = searchParams.get("platform_code");
  const reviewerCountryCode = searchParams.get("reviewer_country_code");
  const dateFrom = searchParams.get("date_from");
  const dateTo = searchParams.get("date_to");

  if (hotelId) params.set("hotel_id", hotelId);
  if (platformCode) params.set("platform_code", platformCode);
  if (reviewerCountryCode) params.set("reviewer_country_code", reviewerCountryCode);
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);

  return params;
}

function applyAggregateDateRange(searchParams: URLSearchParams, params: URLSearchParams) {
  const dateFrom = searchParams.get("date_from");
  const dateTo = searchParams.get("date_to");

  if (dateFrom && dateTo) {
    params.set("date_from", dateFrom);
    params.set("date_to", dateTo);
    return true;
  }

  if (!dateFrom && !dateTo) {
    params.set("date_from", "2000-01-01T00:00:00.000Z");
    params.set("date_to", "2100-12-31T23:59:59.999Z");
    return true;
  }

  return false;
}

function getUnsupportedFilters(searchParams: URLSearchParams) {
  const unsupported: string[] = [];
  const dateFrom = searchParams.get("date_from");
  const dateTo = searchParams.get("date_to");

  if (searchParams.get("reviewer_country_code")) unsupported.push("reviewer_country_code");
  if (searchParams.get("rating_min")) unsupported.push("rating_min");
  if (searchParams.get("rating_max")) unsupported.push("rating_max");
  if (searchParams.get("q")) unsupported.push("q");
  if (searchParams.get("is_bad_review")) unsupported.push("is_bad_review");
  if ((dateFrom && !dateTo) || (!dateFrom && dateTo)) unsupported.push("partial_date_range");

  return unsupported;
}

async function fetchJson<T>(path: string, searchParams: URLSearchParams) {
  const url = new URL(path, API_BASE_URL);
  searchParams.forEach((value, key) => {
    url.searchParams.set(key, value);
  });

  const response = await fetch(url.toString(), {
    cache: "no-store",
    signal: AbortSignal.timeout(ANALYTICS_FETCH_TIMEOUT_MS),
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return (await response.json()) as T;
}

async function fetchAnalytics(request: NextRequest) {
  const baseParams = buildBaseAnalyticsParams(request.nextUrl.searchParams);
  const unsupportedFilters = getUnsupportedFilters(request.nextUrl.searchParams);
  const aggregateParams = new URLSearchParams(baseParams);
  const hasAggregateRange = applyAggregateDateRange(request.nextUrl.searchParams, aggregateParams);
  const supportsFullAnalytics = unsupportedFilters.length === 0 && hasAggregateRange;

  const summaryParams = new URLSearchParams(baseParams);
  const summary = await fetchJson<ReviewSummaryAggregate>("/api/v1/reviews/summary", summaryParams);

  if (!supportsFullAnalytics) {
    return {
      summary,
      country_breakdown: [],
      hotel_breakdown: [],
      score_buckets: [],
      daily_trend: [],
      supports_full_analytics: false,
      unsupported_filters: unsupportedFilters,
    } satisfies AnalyticsPayload;
  }

  const countryParams = new URLSearchParams(aggregateParams);
  countryParams.set("limit", "10");

  const hotelParams = new URLSearchParams(aggregateParams);
  hotelParams.delete("hotel_id");
  hotelParams.set("sort_by", "total_reviews");
  hotelParams.set("sort_order", "desc");
  hotelParams.set("limit", "100");

  const [countryBreakdown, hotelBreakdown, scoreBuckets, dailyTrend] = await Promise.all([
    fetchJson<BreakdownResponse<ReviewCountryBreakdownItem>>(
      "/api/v1/reviews/country-breakdown",
      countryParams,
    ),
    fetchJson<BreakdownResponse<ReviewHotelBreakdownItem>>(
      "/api/v1/reviews/hotel-breakdown",
      hotelParams,
    ),
    fetchJson<BreakdownResponse<ReviewScoreBucketItem>>(
      "/api/v1/reviews/score-buckets",
      aggregateParams,
    ),
    fetchJson<BreakdownResponse<ReviewDailyTrendItem>>(
      "/api/v1/reviews/daily-trend",
      aggregateParams,
    ),
  ]);

  return {
    summary,
    country_breakdown: countryBreakdown.items,
    hotel_breakdown: hotelBreakdown.items,
    score_buckets: scoreBuckets.items,
    daily_trend: dailyTrend.items,
    supports_full_analytics: true,
    unsupported_filters: [],
  } satisfies AnalyticsPayload;
}

export async function GET(request: NextRequest) {
  const cacheKey = buildAnalyticsCacheKey(request.nextUrl.searchParams);
  const cached = analyticsCache.get(cacheKey);

  if (cached && cached.expiresAt > Date.now()) {
    return NextResponse.json(cached.payload, {
      headers: {
        "x-cache": "HIT",
      },
    });
  }

  const pending = pendingAnalyticsRequests.get(cacheKey);
  const payloadPromise = pending || fetchAnalytics(request);
  if (!pending) {
    pendingAnalyticsRequests.set(cacheKey, payloadPromise);
  }

  try {
    const payload = await payloadPromise;
    analyticsCache.set(cacheKey, {
      payload,
      expiresAt: Date.now() + ANALYTICS_CACHE_TTL_MS,
    });

    return NextResponse.json(payload, {
      headers: {
        "x-cache": "MISS",
      },
    });
  } catch (error) {
    const message =
      error instanceof Error && error.message.length > 0
        ? error.message
        : "Failed to load analytics.";
    return new NextResponse(message, {
      status: 500,
      headers: {
        "content-type": "text/plain; charset=utf-8",
      },
    });
  } finally {
    pendingAnalyticsRequests.delete(cacheKey);
  }
}
