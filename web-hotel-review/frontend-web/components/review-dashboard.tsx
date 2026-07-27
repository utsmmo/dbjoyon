"use client";

import { useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import { WorkspaceShell } from "@/components/workspace-shell";
import {
  buildInsightNotes,
  buildLocalizedReviewText,
  parsePlatformFilterValue,
  buildReviewQuery,
  formatDate,
  formatDateTime,
  formatRating,
  normalizeReadableText,
  topKeywords,
} from "@/lib/dashboard";
import {
  DashboardAnalyticsResponse,
  DashboardFilters,
  Hotel,
  PaginatedResponse,
  ReviewCategoryCurrentListResponse,
  ReviewCategoryCurrentSummary,
  Review,
} from "@/lib/types";

const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH || "";
const CLIENT_PAGE_SIZE = 12;
const CLIENT_CACHE_TTL_MS = 60_000;

type CacheEntry<T> = {
  data: T;
  expiresAt: number;
};

type BarDatum = {
  label: string;
  value: number;
};

type CategoryDatum = {
  code: string;
  label: string;
  value: number;
  scale: number;
};

function normalizeCategorySummary(
  summary: ReviewCategoryCurrentSummary,
): ReviewCategoryCurrentSummary {
  const normalizedCategories = Array.isArray(summary.categories) ? summary.categories : [];
  const fallbackItems = Array.isArray(summary.raw_payload?.items)
    ? summary.raw_payload.items
    : [];

  if (normalizedCategories.length > 0 || fallbackItems.length === 0) {
    return {
      ...summary,
      categories: normalizedCategories,
    };
  }

  return {
    ...summary,
    categories: fallbackItems
      .filter((item) => typeof item.score === "number" && item.name)
      .map((item, index) => ({
        category_code: item.id || `raw_category_${index + 1}`,
        category_name: item.name || `Category ${index + 1}`,
        score: item.score ?? null,
        score_scale: item.score_scale ?? 10,
      })),
  };
}

type TableScoreFilter = "good" | "average" | "bad" | "unrated";
type ReviewFlagFilter = TableScoreFilter;

type DashboardIconName =
  | "spark"
  | "chart"
  | "hotel"
  | "globe"
  | "filter"
  | "insight"
  | "table"
  | "review"
  | "warning";

const DEFAULT_FILTERS: DashboardFilters = {
  hotelId: "",
  platformCode: "",
  reviewerCountryCode: "",
  ratingMin: "",
  ratingMax: "",
  dateFrom: "",
  dateTo: "",
  q: "",
  sortBy: "reviewed_at",
  sortOrder: "desc",
  badOnly: false,
};

const REVIEW_FLAG_OPTIONS: { label: string; value: ReviewFlagFilter }[] = [
  { label: "Good", value: "good" },
  { label: "Average", value: "average" },
  { label: "Bad", value: "bad" },
  { label: "Unknown", value: "unrated" },
] as const;

function buildLocalUrl(path: string) {
  return `${BASE_PATH}${path}`;
}

function clampRatingValue(value: string) {
  const trimmed = value.trim();
  if (!trimmed) {
    return "";
  }

  const parsed = Number(trimmed);
  if (Number.isNaN(parsed)) {
    return "";
  }

  return String(Math.min(10, Math.max(0, parsed)));
}

function getReviewScoreBucket(review: Review): TableScoreFilter {
  if (review.rating === null) {
    return "unrated";
  }

  if (review.rating >= 9) {
    return "good";
  }

  if (review.rating >= 7) {
    return "average";
  }

  return "bad";
}

function areReviewFlagFiltersEqual(left: ReviewFlagFilter[], right: ReviewFlagFilter[]) {
  if (left.length !== right.length) {
    return false;
  }

  const leftSorted = [...left].sort();
  const rightSorted = [...right].sort();
  return leftSorted.every((value, index) => value === rightSorted[index]);
}

function buildReviewFlagSummary(flags: ReviewFlagFilter[]) {
  if (flags.length === 0) {
    return "filtered";
  }

  return flags
    .map((flag) => REVIEW_FLAG_OPTIONS.find((option) => option.value === flag)?.label || flag)
    .join(" + ");
}

function enforceBadReviewMode(filters: DashboardFilters, mode: "dashboard" | "reviews"): DashboardFilters {
  if (mode !== "reviews") {
    return filters;
  }

  return {
    ...filters,
    badOnly: true,
  };
}

function buildDashboardCacheKey(filters: DashboardFilters) {
  return buildReviewQuery(filters).toString();
}

function isDefaultDashboardFilters(filters: DashboardFilters) {
  return (
    filters.hotelId === "" &&
    filters.platformCode === "" &&
    filters.reviewerCountryCode === "" &&
    filters.ratingMin === "" &&
    filters.ratingMax === "" &&
    filters.dateFrom === "" &&
    filters.dateTo === "" &&
    filters.q === "" &&
    filters.sortBy === "reviewed_at" &&
    filters.sortOrder === "desc" &&
    filters.badOnly === false
  );
}

function areFiltersEqual(left: DashboardFilters, right: DashboardFilters) {
  return (
    left.hotelId === right.hotelId &&
    left.platformCode === right.platformCode &&
    left.reviewerCountryCode === right.reviewerCountryCode &&
    left.ratingMin === right.ratingMin &&
    left.ratingMax === right.ratingMax &&
    left.dateFrom === right.dateFrom &&
    left.dateTo === right.dateTo &&
    left.q === right.q &&
    left.sortBy === right.sortBy &&
    left.sortOrder === right.sortOrder &&
    left.badOnly === right.badOnly
  );
}

async function fetchHotels() {
  const response = await fetch(buildLocalUrl("/api/hotels?limit=200&offset=0"), {
    cache: "no-store",
  });

  if (!response.ok) throw new Error("Failed to load hotels.");
  return (await response.json()) as PaginatedResponse<Hotel>;
}

async function fetchReviewPage(filters: DashboardFilters, page = 1, limit = CLIENT_PAGE_SIZE) {
  const params = buildReviewQuery(filters);
  params.set("limit", String(limit));
  params.set("offset", String(Math.max(page - 1, 0) * limit));

  const response = await fetch(buildLocalUrl(`/api/reviews?${params.toString()}`), {
    cache: "no-store",
    signal: AbortSignal.timeout(25_000),
  });
  if (!response.ok) throw new Error((await response.text()) || "Failed to load reviews.");
  return (await response.json()) as PaginatedResponse<Review>;
}

async function fetchReviewAnalytics(filters: DashboardFilters) {
  const params = buildReviewQuery(filters);
  const response = await fetch(buildLocalUrl(`/api/reviews-analytics?${params.toString()}`), {
    cache: "no-store",
    signal: AbortSignal.timeout(35_000),
  });

  if (!response.ok) {
    throw new Error((await response.text()) || "Failed to load analytics.");
  }

  return (await response.json()) as DashboardAnalyticsResponse;
}

async function fetchReviewCategoriesCurrent(filters: {
  hotelId?: string;
  platformCode?: string;
}) {
  async function requestCategorySummary(query: { hotelId?: string; platformCode?: string }) {
    const params = new URLSearchParams();
    if (query.hotelId) {
      params.set("hotel_id", query.hotelId);
    }
    if (query.platformCode) {
      params.set("platform_code", query.platformCode);
    }

    const suffix = params.toString();
    const response = await fetch(
      buildLocalUrl(`/api/review-categories/current${suffix ? `?${suffix}` : ""}`),
      {
        cache: "no-store",
        signal: AbortSignal.timeout(20_000),
      },
    );

    if (!response.ok) {
      throw new Error((await response.text()) || "Failed to load review categories.");
    }

    const payload = (await response.json()) as ReviewCategoryCurrentListResponse;
    return {
      ...payload,
      items: payload.items.map(normalizeCategorySummary),
    } satisfies ReviewCategoryCurrentListResponse;
  }

  const exact = await requestCategorySummary(filters);
  if (exact.items.length > 0) {
    return exact;
  }

  if (!filters.hotelId && filters.platformCode) {
    return requestCategorySummary({ platformCode: filters.platformCode });
  }

  return exact;
}

async function fetchReviewInsights(payload: {
  totalMatches: number;
  visibleReviewCount: number;
  filters: Record<string, string | string[] | boolean | null | undefined>;
  analyticsSummary?: Record<string, unknown> | null;
  countryBreakdown?: Array<{ label: string; value: number }>;
  hotelBreakdown?: Array<{ label: string; value: number }>;
  keywordSummary?: Array<{ label: string; value: number }>;
  categories?: CategoryDatum[];
  reviews: Array<{
    hotel_name: string;
    platform_code: string | null;
    reviewer_country_code: string | null;
    rating: number | null;
    rating_scale: number | null;
    reviewed_at: string;
    is_bad_review: boolean;
    title: string;
    body: string;
  }>;
}) {
  const response = await fetch(buildLocalUrl("/api/review-insights"), {
    method: "POST",
    cache: "no-store",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(50_000),
  });

  if (!response.ok) {
    throw new Error((await response.text()) || "Failed to generate AI insights.");
  }

  return (await response.json()) as { content: string };
}

function FilterField({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="flex min-w-0 flex-col gap-2">
      <span className="text-[14px] font-semibold text-[#46556D]">
        {label}
      </span>
      {children}
    </label>
  );
}

function InputControl({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={`h-12 w-full min-w-0 rounded-[14px] border border-slate-200 bg-white px-4 text-[14px] font-medium text-[#1F2937] shadow-sm outline-none transition placeholder:text-slate-400 focus:border-[var(--accent)] focus:ring-4 focus:ring-[rgba(91,91,214,0.09)] xl:text-[15px] ${className || ""}`}
    />
  );
}

function formatIsoDateForDisplay(value: string) {
  if (!value) {
    return "";
  }

  const [year, month, day] = value.split("-");
  if (!year || !month || !day) {
    return value;
  }

  return `${day}/${month}/${year}`;
}

function DateTextControl({
  value,
  onChange,
  placeholder,
  compact = false,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  compact?: boolean;
}) {
  const pickerRef = useRef<HTMLInputElement | null>(null);

  const displayValue = formatIsoDateForDisplay(value);

  return (
    <div className="relative w-full min-w-0">
      <InputControl
        type="text"
        readOnly
        value={displayValue}
        placeholder={placeholder}
        onClick={() => pickerRef.current?.showPicker?.()}
        className={compact ? "pr-10" : undefined}
      />
      <input
        ref={pickerRef}
        type="date"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="absolute inset-0 cursor-pointer opacity-0"
        aria-label={placeholder}
      />
      <span className="pointer-events-none absolute inset-y-0 right-4 flex items-center text-slate-400">
        <svg viewBox="0 0 20 20" fill="none" className="h-4 w-4" aria-hidden="true">
          <rect x="4" y="5.5" width="12" height="10.5" rx="2" stroke="currentColor" strokeWidth="1.6" />
          <path d="M6.5 3.75v3M13.5 3.75v3M4 8.25h12" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
      </span>
    </div>
  );
}

function DashboardGlyph({
  name,
  className = "h-4 w-4",
}: {
  name: DashboardIconName;
  className?: string;
}) {
  switch (name) {
    case "spark":
      return (
        <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
          <path d="M10 2.75 11.9 7.1l4.6 1.4-3.1 3.05.75 4.7L10 13.95 5.85 16.25l.75-4.7L3.5 8.5l4.6-1.4L10 2.75Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
        </svg>
      );
    case "chart":
      return (
        <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
          <path d="M4 14.5 8 10.5l2.5 2.5L16 7.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M14 7.5h2v2" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "hotel":
      return (
        <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
          <path d="M4.5 16V5.5A1.5 1.5 0 0 1 6 4h4.75v12M10.75 8h4.75V16M7 7.5h1M7 10.5h1M7 13.5h1" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "globe":
      return (
        <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
          <circle cx="10" cy="10" r="6.5" stroke="currentColor" strokeWidth="1.6" />
          <path d="M3.75 10h12.5M10 3.75c1.55 1.7 2.4 3.9 2.4 6.25S11.55 14.55 10 16.25M10 3.75C8.45 5.45 7.6 7.65 7.6 10s.85 4.55 2.4 6.25" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
      );
    case "filter":
      return (
        <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
          <path d="M4 5.5h12M6.5 10h7M8.5 14.5h3" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
        </svg>
      );
    case "insight":
      return (
        <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
          <path d="M10 3.5a5.25 5.25 0 0 1 3.9 8.75c-.62.68-1.1 1.26-1.37 2H7.47c-.27-.74-.75-1.32-1.37-2A5.25 5.25 0 0 1 10 3.5Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
          <path d="M7.75 16h4.5M8.5 13.75h3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
      );
    case "table":
      return (
        <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
          <rect x="3.5" y="4" width="13" height="12" rx="2" stroke="currentColor" strokeWidth="1.6" />
          <path d="M3.5 8.5h13M8 4v12M12.5 4v12" stroke="currentColor" strokeWidth="1.6" />
        </svg>
      );
    case "review":
      return (
        <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
          <path d="M5 5.5h10M5 9.5h10M5 13.5h6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
          <path d="M14 13.25 15.25 14.5 17 12.75" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "warning":
      return (
        <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
          <path d="m10 4 6 10.5H4L10 4Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
          <path d="M10 8v2.8M10 13.1h.01" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
      );
  }
}

function WorkspaceHero({
  eyebrow,
  title,
  description,
  summary,
  support,
  meta,
}: {
  eyebrow: string;
  title: string;
  description: string;
  summary: string;
  support: string;
  meta: { label: string; value: string }[];
}) {
  return (
    <section className="overflow-hidden rounded-[16px] border border-slate-200 bg-white shadow-sm">
      <div className="grid gap-5 p-5 xl:grid-cols-[1.4fr_0.6fr] xl:p-6">
        <div>
          <div className="inline-flex rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[12px] font-semibold text-[#667085]">
            {eyebrow}
          </div>
          <h2 className="mt-4 max-w-3xl font-display text-[30px] font-semibold leading-tight text-[#111827]">
            {title}
          </h2>
          <p className="mt-2 max-w-2xl text-[14px] leading-7 text-[#667085]">
            {description}
          </p>

          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            {meta.map((item) => (
              <div key={item.label} className="rounded-[12px] border border-slate-200 bg-slate-50 px-4 py-4">
                <p className="text-[12px] font-semibold uppercase tracking-[0.06em] text-[#667085]">
                  {item.label}
                </p>
                <p className="mt-2 text-[20px] font-semibold text-[#111827]">{item.value}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="grid gap-4">
          <div className="rounded-[12px] border border-slate-200 bg-slate-50 p-5">
            <p className="text-[12px] font-semibold uppercase tracking-[0.06em] text-[#667085]">
              Current focus
            </p>
            <p className="mt-3 text-[22px] font-semibold leading-snug text-[#111827]">
              {summary}
            </p>
            <p className="mt-2 text-[13px] leading-6 text-[#667085]">
              {support}
            </p>
          </div>

          <div className="rounded-[12px] border border-slate-200 bg-white px-5 py-4">
            <p className="text-[13px] font-semibold text-[#111827]">Layout note</p>
            <p className="mt-1 text-[13px] leading-6 text-[#667085]">
              This view prioritizes summary, filters, and actionable review data in that order.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

function SourceCheckboxGroup({
  value,
  options,
  onChange,
}: {
  value: string;
  options: { label: string; value: string }[];
  onChange: (value: string) => void;
}) {
  const selected = parsePlatformFilterValue(value);
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const summaryLabel =
    selected.length === 0
      ? "All OTAs"
      : selected.length === 1
        ? options.find((option) => option.value === selected[0])?.label || selected[0]
        : `${selected.length} OTAs selected`;

  useEffect(() => {
    if (!open) {
      return;
    }

    function handlePointerDown(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
    };
  }, [open]);

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="flex h-12 w-full items-center justify-between rounded-[14px] border border-slate-200 bg-white px-4 text-[14px] font-medium text-[#1F2937] shadow-sm outline-none transition hover:bg-slate-50 focus:border-[var(--accent)] focus:ring-4 focus:ring-[rgba(91,91,214,0.09)] xl:text-[15px]"
      >
        <span className="truncate">{summaryLabel}</span>
        <span className={`text-[14px] text-slate-400 transition ${open ? "rotate-180" : ""}`}>▼</span>
      </button>

      {open ? (
        <div className="absolute left-0 top-[calc(100%+8px)] z-20 w-full min-w-[220px] rounded-[14px] border border-slate-200 bg-white p-2 shadow-lg shadow-slate-200/80">
          <button
            type="button"
            onClick={() => onChange("")}
            className="mb-1 w-full rounded-[12px] px-3 py-2.5 text-left text-[14px] font-medium text-[#52627A] transition hover:bg-slate-50"
          >
            Clear all
          </button>
          <div className="space-y-1">
            {options.map((option) => {
              const active = selected.includes(option.value);
              return (
                <label
                  key={option.value}
                  className={`flex cursor-pointer items-center gap-3 rounded-[12px] px-3 py-3 text-[14px] transition xl:text-[15px] ${
                    active ? "bg-blue-50 text-blue-700" : "text-slate-700 hover:bg-slate-50"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={active}
                    onChange={() => {
                      const nextSelected = active
                        ? selected.filter((item) => item !== option.value)
                        : [...selected, option.value];
                      onChange(nextSelected.join(","));
                    }}
                    className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span>{option.label}</span>
                </label>
              );
            })}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function SelectControl({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (value: string) => void;
  options: { label: string; value: string }[];
}) {
  return (
    <select
      className="h-12 w-full min-w-0 rounded-[14px] border border-slate-200 bg-white px-4 text-[14px] font-medium text-[#1F2937] shadow-sm outline-none transition focus:border-[var(--accent)] focus:ring-4 focus:ring-[rgba(91,91,214,0.09)] xl:text-[15px]"
      value={value}
      onChange={(event) => onChange(event.target.value)}
    >
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

function MultiCheckboxSelect({
  value,
  onChange,
  options,
  placeholder,
}: {
  value: string[];
  onChange: (value: string[]) => void;
  options: { label: string; value: string; count?: number }[];
  placeholder: string;
}) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }

    function handlePointerDown(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
    };
  }, [open]);

  const selectedOptions = options.filter((option) => value.includes(option.value));
  const summaryLabel =
    selectedOptions.length === 0
      ? placeholder
      : selectedOptions.length === 1
        ? selectedOptions[0].label
        : `${selectedOptions.length} selected`;

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="flex h-12 w-full items-center justify-between rounded-[14px] border border-slate-200 bg-white px-4 text-[14px] font-medium text-[#1F2937] shadow-sm outline-none transition hover:bg-slate-50 focus:border-[var(--accent)] focus:ring-4 focus:ring-[rgba(91,91,214,0.09)] xl:text-[15px]"
      >
        <span className="truncate">{summaryLabel}</span>
        <span className={`text-[14px] text-slate-400 transition ${open ? "rotate-180" : ""}`}>▼</span>
      </button>

      {open ? (
        <div className="absolute left-0 top-[calc(100%+8px)] z-20 w-full min-w-[240px] rounded-[14px] border border-slate-200 bg-white p-2 shadow-lg shadow-slate-200/80">
          <button
            type="button"
            onClick={() => onChange([])}
            className="mb-1 w-full rounded-[12px] px-3 py-2.5 text-left text-[14px] font-medium text-[#52627A] transition hover:bg-slate-50"
          >
            Clear all
          </button>
          <div className="max-h-72 space-y-1 overflow-auto">
            {options.map((option) => {
              const active = value.includes(option.value);
              return (
                <label
                  key={option.value}
                  className={`flex cursor-pointer items-center gap-3 rounded-[12px] px-3 py-3 text-[14px] transition xl:text-[15px] ${
                    active ? "bg-blue-50 text-blue-700" : "text-slate-700 hover:bg-slate-50"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={active}
                    onChange={() =>
                      onChange(
                        active
                          ? value.filter((item) => item !== option.value)
                          : [...value, option.value],
                      )
                    }
                    className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="min-w-0 flex-1 truncate">{option.label}</span>
                  {typeof option.count === "number" ? (
                    <span className="shrink-0 text-[13px] font-medium text-slate-400">
                      {option.count}
                    </span>
                  ) : null}
                </label>
              );
            })}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function MetricCard({
  title,
  value,
  helper,
  tone = "text-slate-900",
  accent,
  valueClassName,
  icon,
  iconTint = "bg-white text-slate-500",
}: {
  title: string;
  value: string;
  helper: string;
  tone?: string;
  accent: string;
  valueClassName?: string;
  icon?: DashboardIconName;
  iconTint?: string;
}) {
  return (
    <section className={`rounded-[16px] border bg-white p-5 shadow-sm ${accent}`}>
      <div className="min-w-0">
        <div className="flex items-center gap-3">
          {icon ? (
            <span className={`flex h-10 w-10 items-center justify-center rounded-[12px] ${iconTint}`}>
              <DashboardGlyph name={icon} className="h-5 w-5" />
            </span>
          ) : null}
          <p className="text-[17px] font-semibold text-[#111827] xl:text-[18px]">{title}</p>
        </div>
        <div
          className={`mt-2 min-w-0 font-display leading-none ${valueClassName || "text-[36px] xl:text-[40px]"} ${tone}`}
        >
          {value}
        </div>
      </div>
      <p className="mt-3 text-[14px] leading-6 xl:leading-7 text-[#667085]">{helper}</p>
    </section>
  );
}

function Panel({
  title,
  subtitle,
  action,
  children,
  showBadge = false,
  icon,
}: {
  title: string;
  subtitle: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  showBadge?: boolean;
  icon?: DashboardIconName;
}) {
  return (
    <section className="rounded-[16px] border border-[var(--border)] bg-white shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 px-6 py-5">
        <div>
          {showBadge ? (
            <div className="inline-flex rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[12px] font-semibold text-[#667085]">
              Dashboard block
            </div>
          ) : null}
          <div className={`flex items-center gap-3 ${showBadge ? "mt-3" : ""}`}>
            {icon ? (
              <span className="flex h-11 w-11 items-center justify-center rounded-[10px] bg-slate-100 text-slate-700">
                <DashboardGlyph name={icon} className="h-5 w-5" />
              </span>
            ) : null}
            <h2 className="font-display text-[20px] font-semibold text-[#111827] xl:text-[22px]">{title}</h2>
          </div>
          {subtitle ? <p className="mt-1 text-[14px] leading-6 text-[#667085]">{subtitle}</p> : null}
        </div>
        {action}
      </div>
      <div className="p-6">{children}</div>
    </section>
  );
}

function HorizontalBars({
  data,
  colorClass,
}: {
  data: { label: string; value: number; meta?: string }[];
  colorClass: string;
}) {
  const maxValue = Math.max(...data.map((item) => item.value), 1);

  return (
    <div className="space-y-4">
      {data.map((item) => (
        <div key={item.label} className="space-y-2">
          <div className="flex items-center justify-between gap-4 text-[14px] xl:text-[15px]">
            <span className="truncate font-medium text-[#1F2937]">{item.label}</span>
            <span className="shrink-0 font-semibold text-slate-900">
              {item.value}
              {item.meta ? <span className="ml-1 text-[13px] font-medium text-[#52627A]">{item.meta}</span> : null}
            </span>
          </div>
          <div className="h-2 rounded-full bg-slate-100">
            <div
              className={`h-2 rounded-full ${colorClass}`}
              style={{ width: `${Math.max((item.value / maxValue) * 100, 8)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function ExpandableBars({
  data,
  colorClass,
  initialCount = 6,
}: {
  data: { label: string; value: number }[];
  colorClass: string;
  initialCount?: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const visibleItems = expanded ? data : data.slice(0, initialCount);

  return (
    <div>
      <HorizontalBars data={visibleItems} colorClass={colorClass} />
      {data.length > initialCount ? (
        <button
          type="button"
          onClick={() => setExpanded((current) => !current)}
          className="mt-4 rounded-[12px] border border-slate-200 bg-white px-3 py-2.5 text-[14px] font-semibold text-slate-700 transition hover:bg-slate-50"
        >
          {expanded ? "Show less" : `Show more (${data.length - initialCount})`}
        </button>
      ) : null}
    </div>
  );
}

function CategoryBars({ items }: { items: CategoryDatum[] }) {
  const maxRatio = Math.max(...items.map((item) => item.value / Math.max(item.scale, 1)), 0.1);

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {items.map((item) => (
        <div key={item.code} className="rounded-[18px] border border-slate-100 bg-white px-4 py-4 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <p className="text-[14px] font-semibold text-[#1F2937]">{item.label}</p>
            <p className="text-[15px] font-semibold text-slate-900">
              {item.value.toFixed(1)}
            </p>
          </div>
          <div className="mt-3 h-2.5 rounded-full bg-slate-100">
            <div
              className="h-2.5 rounded-full bg-blue-700"
              style={{ width: `${Math.max(((item.value / Math.max(item.scale, 1)) / maxRatio) * 100, 10)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyState({ label }: { label: string }) {
  return (
    <div className="rounded-[14px] border border-dashed border-slate-200 bg-slate-50 px-4 py-10 text-center text-[14px] leading-7 text-[#52627A]">
      {label}
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-[14px] border border-slate-100 bg-slate-50 p-4">
      <div className="h-4 w-28 rounded-full bg-slate-200" />
      <div className="mt-4 h-8 w-16 rounded-full bg-slate-200" />
      <div className="mt-4 h-3 w-full rounded-full bg-slate-200" />
      <div className="mt-2 h-3 w-2/3 rounded-full bg-slate-200" />
    </div>
  );
}

function buildAnalyticsSupportMessage(unsupportedFilters: string[]) {
  const unsupportedSet = new Set(unsupportedFilters);

  if (unsupportedSet.has("rating_min") || unsupportedSet.has("rating_max")) {
    return "Aggregate analytics currently does not support Flag or score-range filtering. The review list below is still filtering correctly.";
  }

  if (unsupportedFilters.length === 0) {
    return "The aggregate dashboard is using the default all-time snapshot or the current supported filters.";
  }

  return `Aggregate cards and charts do not yet support: ${unsupportedFilters.join(", ")}. Remove those filters if you want the dashboard totals to align completely.`;
}

function buildReviewMixFromBuckets(buckets: DashboardAnalyticsResponse["score_buckets"]) {
  const segments = [
    { label: "Good", count: 0, color: "#2563eb" },
    { label: "Average", count: 0, color: "#14b8a6" },
    { label: "Bad", count: 0, color: "#f97316" },
    { label: "Unknown", count: 0, color: "#94a3b8" },
  ];

  buckets.forEach((bucket) => {
    if (bucket.bucket_code === "unrated") {
      segments[3].count += bucket.review_count;
      return;
    }

    if (bucket.rating_from >= 8) {
      segments[0].count += bucket.review_count;
      return;
    }

    if (bucket.rating_from >= 6) {
      segments[1].count += bucket.review_count;
      return;
    }

    segments[2].count += bucket.review_count;
  });

  return segments;
}

function DonutChart({
  segments,
  onSegmentClick,
  activeLabels = [],
}: {
  segments: { label: string; count: number; color: string }[];
  onSegmentClick?: (label: string) => void;
  activeLabels?: string[];
}) {
  const total = segments.reduce((sum, segment) => sum + segment.count, 0);

  if (total === 0) {
    return <EmptyState label="No ratio data available." />;
  }

  const gradient = segments
    .reduce(
      (state, segment) => {
        const start = total === 0 ? 0 : (state.offset / total) * 360;
        const nextOffset = state.offset + segment.count;
        const end = total === 0 ? start : (nextOffset / total) * 360;

        state.parts.push(`${segment.color} ${start}deg ${end}deg`);
        return {
          offset: nextOffset,
          parts: state.parts,
        };
      },
      { offset: 0, parts: [] as string[] },
    )
    .parts.join(", ");

  return (
    <div className="flex flex-col gap-5 lg:flex-row lg:items-center">
      <div className="relative mx-auto h-40 w-40 shrink-0">
        <div
          className="h-40 w-40 rounded-full"
          style={{ background: `conic-gradient(${gradient})` }}
        />
        <div className="absolute inset-5 flex flex-col items-center justify-center rounded-full bg-white shadow-inner">
          <span className="text-3xl font-semibold text-slate-900">{total}</span>
          <span className="text-[13px] font-semibold text-[#52627A]">Reviews</span>
        </div>
      </div>
      <div className="grid flex-1 gap-3">
        {segments.map((segment) => {
          const percentage = total === 0 ? 0 : Math.round((segment.count / total) * 100);
          const isActive = activeLabels.includes(segment.label.toLowerCase());
          return (
            <button
              key={segment.label}
              type="button"
              onClick={() => onSegmentClick?.(segment.label)}
              className={`flex w-full items-center justify-between rounded-[14px] border px-4 py-3 text-left transition ${
                isActive
                  ? "border-blue-200 bg-blue-50/80"
                  : "border-slate-100 bg-white hover:bg-slate-50"
              } ${onSegmentClick ? "cursor-pointer" : "cursor-default"}`}
            >
              <div className="flex items-center gap-3">
                <span
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: segment.color }}
                />
                <span className="text-[14px] font-medium text-[#1F2937]">{segment.label}</span>
              </div>
              <div className="text-right">
                <div className="text-[14px] font-semibold text-slate-900 xl:text-[15px]">{segment.count}</div>
                <div className="text-[13px] text-[#52627A]">{percentage}%</div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function ReviewDashboard({
  mode = "dashboard",
}: {
  mode?: "dashboard" | "reviews";
}) {
  const hotelsCacheRef = useRef<CacheEntry<PaginatedResponse<Hotel>> | null>(null);
  const reviewPageCacheRef = useRef<Map<string, CacheEntry<PaginatedResponse<Review>>>>(new Map());
  const analyticsCacheRef = useRef<Map<string, CacheEntry<DashboardAnalyticsResponse>>>(new Map());
  const [hotels, setHotels] = useState<Hotel[]>([]);
  const [filterSeedReviews, setFilterSeedReviews] = useState<Review[]>([]);
  const [platformFilterOptions, setPlatformFilterOptions] = useState<{ label: string; value: string }[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [analytics, setAnalytics] = useState<DashboardAnalyticsResponse | null>(null);
  const [reviewCategories, setReviewCategories] = useState<ReviewCategoryCurrentSummary[]>([]);
  const [totalMatches, setTotalMatches] = useState(0);
  const [draftFilters, setDraftFilters] = useState<DashboardFilters>(DEFAULT_FILTERS);
  const [filters, setFilters] = useState<DashboardFilters>(DEFAULT_FILTERS);
  const [draftReviewFlags, setDraftReviewFlags] = useState<ReviewFlagFilter[]>([]);
  const [appliedReviewFlags, setAppliedReviewFlags] = useState<ReviewFlagFilter[]>([]);
  const [translationMap, setTranslationMap] = useState<Record<string, { title?: string; body?: string }>>({});
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedReviewId, setSelectedReviewId] = useState<string | null>(null);
  const [tableScoreFilters, setTableScoreFilters] = useState<TableScoreFilter[]>([]);
  const [tableLanguageFilters, setTableLanguageFilters] = useState<string[]>([]);
  const [dashboardInsightsRequested, setDashboardInsightsRequested] = useState(false);
  const [aiInsightContent, setAiInsightContent] = useState("");
  const [aiInsightError, setAiInsightError] = useState<string | null>(null);
  const [isAiInsightLoading, setIsAiInsightLoading] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyticsLoading, setIsAnalyticsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingFilterKey, setPendingFilterKey] = useState<string | null>(null);

  function beginDatasetRefresh(nextFilterKey: string | null) {
    setPendingFilterKey(nextFilterKey);
    setReviews([]);
    setAnalytics(null);
    setTotalMatches(0);
    setTranslationMap({});
    setDashboardInsightsRequested(false);
    setSelectedReviewId(null);
    setCurrentPage(1);
    setIsLoading(true);
    setIsAnalyticsLoading(true);
  }

  const deferredSearch = useDeferredValue(filters.q);
  const effectiveFilters = useMemo(
    () => enforceBadReviewMode(filters, mode),
    [filters, mode],
  );
  const effectiveDraftFilters = useMemo(
    () => enforceBadReviewMode(draftFilters, mode),
    [draftFilters, mode],
  );
  const apiFilters = useMemo(
    () => ({
      hotelId: effectiveFilters.hotelId,
      platformCode: effectiveFilters.platformCode,
      reviewerCountryCode: effectiveFilters.reviewerCountryCode,
      ratingMin: effectiveFilters.ratingMin,
      ratingMax: effectiveFilters.ratingMax,
      dateFrom: effectiveFilters.dateFrom,
      dateTo: effectiveFilters.dateTo,
      q: deferredSearch,
      sortBy: effectiveFilters.sortBy,
      sortOrder: effectiveFilters.sortOrder,
      badOnly: effectiveFilters.badOnly,
    }),
    [
      deferredSearch,
      effectiveFilters.badOnly,
      effectiveFilters.dateFrom,
      effectiveFilters.dateTo,
      effectiveFilters.hotelId,
      effectiveFilters.platformCode,
      effectiveFilters.ratingMax,
      effectiveFilters.ratingMin,
      effectiveFilters.reviewerCountryCode,
      effectiveFilters.sortBy,
      effectiveFilters.sortOrder,
    ],
  );

  useEffect(() => {
    let isActive = true;

    const cachedHotels = hotelsCacheRef.current;
    if (cachedHotels && cachedHotels.expiresAt > Date.now()) {
      setHotels(cachedHotels.data.items);
      return () => {
        isActive = false;
      };
    }

    fetchHotels()
      .then((hotelData) => {
        if (!isActive) return;
        hotelsCacheRef.current = {
          data: hotelData,
          expiresAt: Date.now() + CLIENT_CACHE_TTL_MS,
        };
        setHotels(hotelData.items);
      })
      .catch((loadError) => {
        if (!isActive) return;
        setError(loadError instanceof Error ? loadError.message : "Failed to load hotels.");
      });

    return () => {
      isActive = false;
    };
  }, []);

  useEffect(() => {
    let isActive = true;

    const cacheKey = `${buildDashboardCacheKey(apiFilters)}::page=${currentPage}`;
    const reviewCache = reviewPageCacheRef.current.get(cacheKey);
    const defaultFilters = isDefaultDashboardFilters(apiFilters);

    setError(null);
    setTranslationMap({});

    async function loadReviewPageData() {
      if (reviewCache && reviewCache.expiresAt > Date.now()) {
        setReviews(reviewCache.data.items);
        setTotalMatches(reviewCache.data.total);
        if (filterSeedReviews.length === 0 && defaultFilters) {
          setFilterSeedReviews(reviewCache.data.items);
        }
        if (pendingFilterKey === cacheKey) {
          setPendingFilterKey(null);
        }
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      try {
        const dataset = await fetchReviewPage(apiFilters, currentPage, CLIENT_PAGE_SIZE);
        if (!isActive) return;
        reviewPageCacheRef.current.set(cacheKey, {
          data: dataset,
          expiresAt: Date.now() + CLIENT_CACHE_TTL_MS,
        });
        setReviews(dataset.items);
        setTotalMatches(dataset.total);
        if (filterSeedReviews.length === 0 && defaultFilters) {
          setFilterSeedReviews(dataset.items);
        }
        if (pendingFilterKey === cacheKey) {
          setPendingFilterKey(null);
        }
      } catch (loadError) {
        if (!isActive) return;
        if (pendingFilterKey === cacheKey) {
          setPendingFilterKey(null);
        }
        setError(loadError instanceof Error ? loadError.message : "Failed to load reviews.");
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    loadReviewPageData();

    return () => {
      isActive = false;
    };
  }, [apiFilters, currentPage, filterSeedReviews.length, pendingFilterKey]);

  useEffect(() => {
    let isActive = true;

    const cacheKey = buildDashboardCacheKey(apiFilters);
    const analyticsCache = analyticsCacheRef.current.get(cacheKey);

    if (analyticsCache && analyticsCache.expiresAt > Date.now()) {
      setAnalytics(analyticsCache.data);
      if (pendingFilterKey === cacheKey) {
        setPendingFilterKey(null);
      }
      setIsAnalyticsLoading(false);
      return () => {
        isActive = false;
      };
    }

    async function loadAnalyticsData() {
      setIsAnalyticsLoading(true);
      try {
        const dataset = await fetchReviewAnalytics(apiFilters);
        if (!isActive) return;
        analyticsCacheRef.current.set(cacheKey, {
          data: dataset,
          expiresAt: Date.now() + CLIENT_CACHE_TTL_MS,
        });
        setAnalytics(dataset);
        if (pendingFilterKey === cacheKey) {
          setPendingFilterKey(null);
        }
      } catch (loadError) {
        if (!isActive) return;
        if (pendingFilterKey === cacheKey) {
          setPendingFilterKey(null);
        }
        setError((current) =>
          current || (loadError instanceof Error ? loadError.message : "Failed to load analytics."),
        );
      } finally {
        if (isActive) {
          setIsAnalyticsLoading(false);
        }
      }
    }

    loadAnalyticsData();
    return () => {
      isActive = false;
    };
  }, [apiFilters, pendingFilterKey]);

  useEffect(() => {
    let isActive = true;

    async function loadPlatformFilterOptions() {
      const optionFilters = enforceBadReviewMode(
        {
          ...DEFAULT_FILTERS,
          hotelId: effectiveDraftFilters.hotelId,
        },
        mode,
      );
      const cacheKey = buildDashboardCacheKey(optionFilters);
      const cached = reviewPageCacheRef.current.get(cacheKey);

      const dataset =
        cached && cached.expiresAt > Date.now()
          ? cached.data
          : await fetchReviewPage(optionFilters);

      if (!cached || cached.expiresAt <= Date.now()) {
        reviewPageCacheRef.current.set(cacheKey, {
          data: dataset,
          expiresAt: Date.now() + CLIENT_CACHE_TTL_MS,
        });
      }

      if (!isActive) {
        return;
      }

      const nextOptions = [...new Set(dataset.items.map((review) => review.platform_code).filter(Boolean))].map(
        (platform) => ({
          label: String(platform).charAt(0).toUpperCase() + String(platform).slice(1).toLowerCase(),
          value: platform as string,
        }),
      );

      setPlatformFilterOptions(nextOptions);
    }

    loadPlatformFilterOptions().catch(() => {
      if (!isActive) {
        return;
      }

      setPlatformFilterOptions([]);
    });

    return () => {
      isActive = false;
    };
  }, [effectiveDraftFilters.hotelId, mode]);

  useEffect(() => {
    let isActive = true;
    const selectedPlatforms = parsePlatformFilterValue(effectiveFilters.platformCode);
    const selectedPlatform = selectedPlatforms.length === 1 ? selectedPlatforms[0] : "";

    if (!effectiveFilters.hotelId && !selectedPlatform) {
      setReviewCategories([]);
      return () => {
        isActive = false;
      };
    }

    fetchReviewCategoriesCurrent({
      hotelId: effectiveFilters.hotelId || undefined,
      platformCode: selectedPlatform || undefined,
    })
      .then((response) => {
        if (!isActive) {
          return;
        }
        setReviewCategories(response.items);
      })
      .catch(() => {
        if (!isActive) {
          return;
        }
        setReviewCategories([]);
      });

    return () => {
      isActive = false;
    };
  }, [effectiveFilters.hotelId, effectiveFilters.platformCode]);

  useEffect(() => {
    setCurrentPage(1);
  }, [tableLanguageFilters, tableScoreFilters]);

  const filteredReviews = useMemo(
    () =>
      reviews.filter((review) => {
        if (appliedReviewFlags.length === 0) {
          return true;
        }

        return appliedReviewFlags.includes(getReviewScoreBucket(review));
      }),
    [appliedReviewFlags, reviews],
  );
  const tableLanguageOptions = useMemo(
    () =>
      Array.from(
        filteredReviews.reduce((map, review) => {
          const key = (review.review_language || "Unknown").toUpperCase();
          map.set(key, (map.get(key) || 0) + 1);
          return map;
        }, new Map<string, number>()),
      )
        .map(([value, count]) => ({ value, label: value, count }))
        .sort((left, right) => right.count - left.count),
    [filteredReviews],
  );
  const tableScoreOptions = useMemo(
    () => {
      const counts = filteredReviews.reduce(
        (accumulator, review) => {
          accumulator[getReviewScoreBucket(review)] += 1;
          return accumulator;
        },
        { good: 0, average: 0, bad: 0, unrated: 0 } as Record<TableScoreFilter, number>,
      );

      return [
        { value: "good", label: "Good: 9-10", count: counts.good },
        { value: "average", label: "Average: 7-8", count: counts.average },
        { value: "bad", label: "Bad: 1-6", count: counts.bad },
        { value: "unrated", label: "Unrated", count: counts.unrated },
      ] satisfies { value: TableScoreFilter; label: string; count: number }[];
    },
    [filteredReviews],
  );
  const tableFilteredReviews = useMemo(
    () =>
      filteredReviews.filter((review) => {
        const scoreBucket = getReviewScoreBucket(review);
        const language = (review.review_language || "Unknown").toUpperCase();

        if (tableScoreFilters.length > 0 && !tableScoreFilters.includes(scoreBucket)) {
          return false;
        }

        if (tableLanguageFilters.length > 0 && !tableLanguageFilters.includes(language)) {
          return false;
        }

        return true;
      }),
    [filteredReviews, tableLanguageFilters, tableScoreFilters],
  );
  const summary = analytics?.summary ?? null;
  const hasReviewData = filteredReviews.length > 0 || totalMatches > 0;
  const hasAnalyticsData = Boolean(analytics);
  const scoreBuckets = useMemo<BarDatum[]>(
    () =>
      (analytics?.score_buckets ?? []).map((item) => ({
        label: item.bucket_code === "unrated" ? "Unrated" : item.bucket_label.replace(".0", ""),
        value: item.review_count,
      })),
    [analytics],
  );
  const reviewMix = useMemo(
    () => buildReviewMixFromBuckets(analytics?.score_buckets ?? []),
    [analytics],
  );
  const activeReviewMixLabels = useMemo(
    () => tableScoreFilters.map((item) => (item === "unrated" ? "unknown" : item)),
    [tableScoreFilters],
  );
  const hotelCounts = useMemo<BarDatum[]>(
    () =>
      (analytics?.hotel_breakdown ?? [])
        .slice(0, 8)
        .map((item) => ({ label: item.hotel_name, value: item.total_reviews })),
    [analytics],
  );
  const reviewerCountryCounts = useMemo<BarDatum[]>(
    () =>
      (analytics?.country_breakdown ?? [])
        .slice(0, 10)
        .map((item) => ({ label: item.reviewer_country_code || "Unknown", value: item.total_reviews })),
    [analytics],
  );
  const keywordSummary = useMemo(() => topKeywords(filteredReviews, 6), [filteredReviews]);
  const insightNotes = useMemo(() => buildInsightNotes(filteredReviews), [filteredReviews]);

  const totalPages = Math.max(Math.ceil(totalMatches / CLIENT_PAGE_SIZE), 1);
  const pagedReviews = tableFilteredReviews;
  const selectedReview =
    tableFilteredReviews.find((review) => review.id === selectedReviewId) || tableFilteredReviews[0] || null;

  useEffect(() => {
    let isActive = true;

    async function translateVisibleReviews() {
      const targetReviews = selectedReview
        ? [selectedReview, ...pagedReviews.filter((review) => review.id !== selectedReview.id)]
        : pagedReviews;

      const tasks = targetReviews
        .map((review) => {
          if (translationMap[review.id]) return null;
          const localized = buildLocalizedReviewText(review);
          if (localized.translationSource !== "original") return null;

          const title = normalizeReadableText(review.review_title);
          const body = normalizeReadableText(review.review_text);
          return { reviewId: review.id, title, body };
        })
        .filter((task): task is { reviewId: string; title: string; body: string } => Boolean(task));

      if (tasks.length === 0) return;

      try {
        const responses = await Promise.all(
          tasks.map(async (task) => {
            const [translatedTitle, translatedBody] = await Promise.all([
              task.title
                ? fetch(buildLocalUrl("/api/translate"), {
                    method: "POST",
                    headers: { "content-type": "application/json" },
                    body: JSON.stringify({ texts: [task.title], target: "vi" }),
                  })
                    .then(async (response) =>
                      response.ok ? ((await response.json()) as { items: { translated: string }[] }).items[0]?.translated || "" : "",
                    )
                : Promise.resolve(""),
              task.body
                ? fetch(buildLocalUrl("/api/translate"), {
                    method: "POST",
                    headers: { "content-type": "application/json" },
                    body: JSON.stringify({ texts: [task.body], target: "vi" }),
                  })
                    .then(async (response) =>
                      response.ok ? ((await response.json()) as { items: { translated: string }[] }).items[0]?.translated || "" : "",
                    )
                : Promise.resolve(""),
            ]);

            return { reviewId: task.reviewId, translatedTitle, translatedBody };
          }),
        );

        if (!isActive) return;
        setTranslationMap((current) => {
          const next = { ...current };
          responses.forEach((item) => {
            next[item.reviewId] = {
              title: item.translatedTitle || undefined,
              body: item.translatedBody || undefined,
            };
          });
          return next;
        });
      } catch {
        if (!isActive) return;
      }
    }

    translateVisibleReviews();
    return () => {
      isActive = false;
    };
  }, [pagedReviews, selectedReview, translationMap]);

  const hotelOptions = useMemo(
    () => [{ label: "All hotels", value: "" }, ...hotels.map((hotel) => ({ label: hotel.hotel_name, value: hotel.id }))],
    [hotels],
  );
  const analyticsPlatformOptions = useMemo(
    () =>
      [...new Set((analytics?.hotel_breakdown ?? []).map((item) => item.platform_code).filter(Boolean))].map(
        (platform) => ({
          label: String(platform).charAt(0).toUpperCase() + String(platform).slice(1).toLowerCase(),
          value: platform as string,
        }),
      ),
    [analytics],
  );
  const platformOptions = useMemo(() => {
    if (platformFilterOptions.length > 0) {
      return platformFilterOptions;
    }

    return analyticsPlatformOptions;
  }, [analyticsPlatformOptions, platformFilterOptions]);
  const selectedPlatformCodes = useMemo(
    () => parsePlatformFilterValue(effectiveDraftFilters.platformCode),
    [effectiveDraftFilters.platformCode],
  );
  useEffect(() => {
    const availablePlatforms = new Set(platformOptions.map((option) => option.value));
    const nextSelectedPlatforms = selectedPlatformCodes.filter((code) => availablePlatforms.has(code));

    if (nextSelectedPlatforms.length === selectedPlatformCodes.length) {
      return;
    }

    setDraftFilters((current) => ({
      ...current,
      platformCode: nextSelectedPlatforms.join(","),
    }));
  }, [platformOptions, selectedPlatformCodes]);
  const appliedReviewFlagSummary = useMemo(
    () => buildReviewFlagSummary(appliedReviewFlags),
    [appliedReviewFlags],
  );
  const effectiveFilterKey = buildDashboardCacheKey(effectiveFilters);
  const hasPendingReviewFlagChanges = !areReviewFlagFiltersEqual(draftReviewFlags, appliedReviewFlags);
  const isApplyingFilters = pendingFilterKey === effectiveFilterKey;
  const showHotelBreakdown = effectiveFilters.hotelId === "";

  useEffect(() => {
    setDashboardInsightsRequested(false);
    setAiInsightContent("");
    setAiInsightError(null);
    setIsAiInsightLoading(false);
  }, [effectiveFilterKey]);
  const guestCountryBaseReviews = useMemo(() => {
    const sourceBase = filterSeedReviews.length > 0 ? filterSeedReviews : reviews;

    return sourceBase.filter((review) => {
      if (effectiveDraftFilters.hotelId && review.hotel_id !== effectiveDraftFilters.hotelId) {
        return false;
      }

      if (
        selectedPlatformCodes.length === 1 &&
        review.platform_code !== selectedPlatformCodes[0]
      ) {
        return false;
      }

      if (effectiveDraftFilters.badOnly && !review.is_bad_review) {
        return false;
      }

      return true;
    });
  }, [
    effectiveDraftFilters.badOnly,
    effectiveDraftFilters.hotelId,
    filterSeedReviews,
    reviews,
    selectedPlatformCodes,
  ]);
  const reviewerCountryOptions = useMemo(() => {
    const countries = [
      ...new Set(guestCountryBaseReviews.map((review) => review.reviewer_country_code).filter(Boolean)),
    ];
    return [
      { label: "All guest countries", value: "" },
      ...countries.map((country) => ({ label: country as string, value: country as string })),
    ];
  }, [guestCountryBaseReviews]);
  const analyticsReady = analytics !== null;
  const analyticsSupportsFullDashboard = analytics?.supports_full_analytics ?? false;
  const unsupportedAnalyticsFilters = analytics?.unsupported_filters ?? [];
  const analyticsBlockedByRatingFilter =
    unsupportedAnalyticsFilters.includes("rating_min") ||
    unsupportedAnalyticsFilters.includes("rating_max");
  const useFilteredAnalytics =
    appliedReviewFlags.length > 0 || analyticsBlockedByRatingFilter;
  const filteredAverageRating = useMemo(() => {
    const ratedReviews = filteredReviews.filter(
      (review) => typeof review.rating === "number" && !Number.isNaN(review.rating),
    );

    if (ratedReviews.length === 0) {
      return null;
    }

    const totalRating = ratedReviews.reduce((sum, review) => sum + (review.rating ?? 0), 0);
    return totalRating / ratedReviews.length;
  }, [filteredReviews]);
  const displayTotalMatches = useFilteredAnalytics ? filteredReviews.length : summary?.total_reviews ?? totalMatches;
  const displayAverageRating = useFilteredAnalytics ? filteredAverageRating : summary?.avg_rating ?? null;
  const analyticsSupportMessage = analytics
    ? buildAnalyticsSupportMessage(unsupportedAnalyticsFilters)
    : "Loading analytics...";
  const hasPendingFilterChanges =
    !areFiltersEqual(effectiveFilters, effectiveDraftFilters) || hasPendingReviewFlagChanges;
  const badReviewRows = useMemo(
    () => filteredReviews.filter((review) => review.is_bad_review),
    [filteredReviews],
  );
  const badReviewCountryCounts = useMemo(
    () =>
      Array.from(
        badReviewRows.reduce((map, review) => {
          const key = review.reviewer_country_code || "Unknown";
          map.set(key, (map.get(key) || 0) + 1);
          return map;
        }, new Map<string, number>()),
      )
        .map(([label, value]) => ({ label, value }))
        .sort((left, right) => right.value - left.value)
        .slice(0, 8),
    [badReviewRows],
  );
  const badReviewHotelCounts = useMemo(
    () =>
      Array.from(
        badReviewRows.reduce((map, review) => {
          const key = review.hotel_name;
          map.set(key, (map.get(key) || 0) + 1);
          return map;
        }, new Map<string, number>()),
      )
        .map(([label, value]) => ({ label, value }))
        .sort((left, right) => right.value - left.value)
        .slice(0, 8),
    [badReviewRows],
  );
  const badReviewPlatformCounts = useMemo(
    () =>
      Array.from(
        badReviewRows.reduce((map, review) => {
          const key = review.platform_code || "unknown";
          map.set(key, (map.get(key) || 0) + 1);
          return map;
        }, new Map<string, number>()),
      )
        .map(([label, value]) => ({ label, value }))
        .sort((left, right) => right.value - left.value)
        .slice(0, 6),
    [badReviewRows],
  );
  const badReviewCountryDisplay = useMemo(
    () =>
      badReviewCountryCounts.map((item) => ({
        ...item,
        meta: `(${Math.round((item.value / Math.max(badReviewRows.length, 1)) * 100)}%)`,
      })),
    [badReviewCountryCounts, badReviewRows.length],
  );
  const badReviewKeywords = useMemo(
    () => topKeywords(badReviewRows, 8),
    [badReviewRows],
  );
  const badReviewInsightNotes = useMemo(() => {
    const notes: string[] = [];
    const topCountry = badReviewCountryCounts[0];
    const topHotel = badReviewHotelCounts[0];
    const topPlatform = badReviewPlatformCounts[0];
    const primaryKeyword = badReviewKeywords[0];

    if (badReviewRows.length === 0) {
      notes.push("Chưa có bad review trong tập dữ liệu đang xem, nên chưa thể rút ra nguyên nhân ưu tiên.");
      return notes;
    }

    if (topCountry) {
      const share = Math.round((topCountry.value / Math.max(badReviewRows.length, 1)) * 100);
      notes.push(`${topCountry.label} đang chiếm khoảng ${share}% bad review trong tập hiện tại, nên đây là nhóm khách cần đọc kỹ đầu tiên.`);
    }

    if (topHotel) {
      notes.push(`${topHotel.label} đang có nhiều bad review nhất trong tập đang lọc, nên nên kiểm tra lại vận hành tại khách sạn này trước.`);
    }

    if (topPlatform) {
      notes.push(`Nguồn ${String(topPlatform.label).toUpperCase()} đang đóng góp nhiều review xấu nhất trong tập hiện tại, cần so lại trải nghiệm khách trên nền tảng này.`);
    }

    if (primaryKeyword) {
      notes.push(`Từ khóa phàn nàn nổi bật hiện là "${primaryKeyword.label}", đây có thể là chủ đề cần ưu tiên cải thiện.`);
    }

    if (badReviewRows.length >= 8) {
      notes.push("Số lượng bad review hiện đủ lớn để bắt đầu gom nhóm nguyên nhân theo quốc gia, khách sạn và chủ đề phàn nàn.");
    } else {
      notes.push("Tập bad review hiện còn khá nhỏ, nên cần đọc từng review chi tiết để tránh kết luận vội.");
    }

    return notes;
  }, [badReviewCountryCounts, badReviewHotelCounts, badReviewKeywords, badReviewPlatformCounts, badReviewRows.length]);
  const filteredAnalyticsCountryCounts = useMemo<BarDatum[]>(
    () =>
      Array.from(
        filteredReviews.reduce((map, review) => {
          const key = review.reviewer_country_code || "Unknown";
          map.set(key, (map.get(key) || 0) + 1);
          return map;
        }, new Map<string, number>()),
      )
        .map(([label, value]) => ({ label, value }))
        .sort((left, right) => right.value - left.value)
        .slice(0, 10),
    [filteredReviews],
  );
  const filteredAnalyticsHotelCounts = useMemo<BarDatum[]>(
    () =>
      Array.from(
        filteredReviews.reduce((map, review) => {
          const key = review.hotel_name;
          map.set(key, (map.get(key) || 0) + 1);
          return map;
        }, new Map<string, number>()),
      )
        .map(([label, value]) => ({ label, value }))
        .sort((left, right) => right.value - left.value)
        .slice(0, 8),
    [filteredReviews],
  );
  const filteredAnalyticsScoreBuckets = useMemo<BarDatum[]>(
    () => {
      const counts = filteredReviews.reduce(
        (accumulator, review) => {
          accumulator[getReviewScoreBucket(review)] += 1;
          return accumulator;
        },
        { good: 0, average: 0, bad: 0, unrated: 0 } as Record<TableScoreFilter, number>,
      );

      return [
        { label: "Good", value: counts.good },
        { label: "Average", value: counts.average },
        { label: "Bad", value: counts.bad },
        { label: "Unrated", value: counts.unrated },
      ];
    },
    [filteredReviews],
  );
  const filteredAnalyticsReviewMix = useMemo(
    () => [
      { label: "Good", count: filteredAnalyticsScoreBuckets[0]?.value || 0, color: "#2563eb" },
      { label: "Average", count: filteredAnalyticsScoreBuckets[1]?.value || 0, color: "#14b8a6" },
      { label: "Bad", count: filteredAnalyticsScoreBuckets[2]?.value || 0, color: "#f97316" },
      { label: "Unknown", count: filteredAnalyticsScoreBuckets[3]?.value || 0, color: "#94a3b8" },
    ],
    [filteredAnalyticsScoreBuckets],
  );
  const reviewSortOptions = [
    { label: "Newest review", value: "reviewed_at" },
    { label: "Lowest rating", value: "rating" },
    { label: "Recently created", value: "created_at" },
    { label: "Hotel name", value: "hotel_name" },
    { label: "Guest name", value: "reviewer_name" },
  ];
  const reviewOrderOptions = [
    { label: "Descending", value: "desc" },
    { label: "Ascending", value: "asc" },
  ];
  const pageTitle = mode === "reviews" ? "Review Workspace" : "Review Overview";
  const pageSubtitle =
    mode === "reviews"
      ? "Inspect bad reviews, narrow the root cause, and review translated complaints in one workspace."
      : "Track review quality and guest feedback.";
  const statusLabel =
    isLoading || isAnalyticsLoading
      ? mode === "reviews"
        ? "Updating reviews..."
        : "Updating dashboard..."
      : `${displayTotalMatches} reviews matched`;
  const showMetricSkeleton = mode === "dashboard" && isLoading && !hasReviewData;
  const activeCategorySummary = useMemo(() => {
    if (reviewCategories.length === 0) {
      return null;
    }

    const selectedPlatforms = parsePlatformFilterValue(effectiveFilters.platformCode);
    const selectedPlatform = selectedPlatforms.length === 1 ? selectedPlatforms[0] : "";

    if (effectiveFilters.hotelId) {
      return (
        reviewCategories.find(
          (item) =>
            item.hotel_id === effectiveFilters.hotelId &&
            (!selectedPlatform || item.platform_code === selectedPlatform),
        ) || null
      );
    }

    if (selectedPlatform) {
      return (
        reviewCategories.find((item) => item.platform_code === selectedPlatform) || null
      );
    }

    return reviewCategories[0] || null;
  }, [effectiveFilters.hotelId, effectiveFilters.platformCode, reviewCategories]);
  const categoryData = useMemo<CategoryDatum[]>(() => {
    if (!activeCategorySummary) {
      return [];
    }

    const normalized = (activeCategorySummary.categories || [])
      .filter((item) => typeof item.score === "number")
      .map((item) => ({
        code: item.category_code || item.category_name.toLowerCase().replace(/\s+/g, "_"),
        label: item.category_name,
        value: item.score || 0,
        scale: item.score_scale || 10,
      }));

    if (normalized.length > 0) {
      return normalized.sort((left, right) => (left.code > right.code ? 1 : -1));
    }

    const fallbackItems = Array.isArray(activeCategorySummary.raw_payload?.items)
      ? activeCategorySummary.raw_payload.items
      : [];

    return fallbackItems
      .filter((item) => typeof item.score === "number" && item.name)
      .map((item, index) => ({
        code: item.id || `category_${index + 1}`,
        label: item.name || `Category ${index + 1}`,
        value: item.score || 0,
        scale: item.score_scale || 10,
      }));
  }, [activeCategorySummary]);
  const insightReviewPayload = useMemo(
    () =>
      filteredReviews.slice(0, 12).map((review) => {
        const localized = buildLocalizedReviewText(review, translationMap[review.id]);

        return {
          hotel_name: review.hotel_name,
          platform_code: review.platform_code,
          reviewer_country_code: review.reviewer_country_code,
          rating: review.rating,
          rating_scale: review.rating_scale,
          reviewed_at: review.reviewed_at,
          is_bad_review: review.is_bad_review,
          title: localized.title,
          body: localized.body,
        };
      }),
    [filteredReviews, translationMap],
  );

  return (
    <WorkspaceShell
      mode={mode}
      title={pageTitle}
      subtitle={pageSubtitle}
      statusLabel={statusLabel}
      showHeaderActions={mode !== "dashboard"}
    >
      {mode === "reviews" ? (
              <>
                <WorkspaceHero
                  eyebrow="Review operations"
                  title="Review issues, translation output, and flagged guest feedback."
                  description="Use this workspace to narrow the dataset, inspect flagged reviews, and compare translated content with OTA metadata."
                  summary={
                    selectedReview
                      ? `Inspecting ${selectedReview.hotel_name}`
                      : badReviewRows.length > 0
                        ? `${badReviewRows.length} flagged reviews currently need attention`
                        : "No flagged reviews in the current visible set"
                  }
                  support={
                    selectedReview
                      ? "Use the review detail pane below to compare translation, metadata, and original wording."
                      : "Start with filters only when you need to narrow the queue further."
                  }
                  meta={[
                    { label: "Matched reviews", value: String(displayTotalMatches) },
                    { label: "Flagged rows", value: String(badReviewRows.length) },
                    { label: "Top country", value: badReviewCountryCounts[0]?.label || "-" },
                  ]}
                />
                <Panel
                  title="Filters"
                  subtitle="Focus bad-review investigation by hotel, OTA, guest country, score range, and time."
                  action={
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          if (!hasPendingFilterChanges) {
                            setPendingFilterKey(null);
                            return;
                          }
                          if (!areFiltersEqual(effectiveFilters, effectiveDraftFilters)) {
                            beginDatasetRefresh(buildDashboardCacheKey(effectiveDraftFilters));
                          } else {
                            setPendingFilterKey(null);
                          }
                          setFilters(draftFilters);
                          setAppliedReviewFlags(draftReviewFlags);
                          setTableScoreFilters(draftReviewFlags);
                        }}
                        className="rounded-xl bg-slate-900 px-4 py-2.5 text-[15px] font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70"
                        disabled={isApplyingFilters || !hasPendingFilterChanges}
                      >
                        {isApplyingFilters ? "Filtering..." : hasPendingFilterChanges ? "Filter" : "Applied"}
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          beginDatasetRefresh(buildDashboardCacheKey(enforceBadReviewMode(DEFAULT_FILTERS, mode)));
                          setDraftFilters(DEFAULT_FILTERS);
                          setFilters(DEFAULT_FILTERS);
                          setDraftReviewFlags([]);
                          setAppliedReviewFlags([]);
                          setTableScoreFilters([]);
                          setTableLanguageFilters([]);
                        }}
                        className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-[15px] font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
                      >
                        Reset
                      </button>
                    </div>
                  }
                >
                  <div className="mb-4 flex flex-wrap gap-2">
                    <span className="rounded-full border border-red-200 bg-red-50 px-3 py-1.5 text-[12px] font-semibold text-red-700">
                      Bad reviews only
                    </span>
                    {badReviewCountryCounts.slice(0, 2).map((item) => (
                      <button
                        key={`country-focus-${item.label}`}
                        type="button"
                        onClick={() =>
                          setDraftFilters((current) => ({
                            ...current,
                            reviewerCountryCode: item.label === "Unknown" ? "" : item.label,
                          }))
                        }
                        className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[12px] font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
                      >
                        Country: {item.label} ({item.value})
                      </button>
                    ))}
                    {badReviewHotelCounts.slice(0, 2).map((item) => {
                      const matchedHotel = hotels.find((hotel) => hotel.hotel_name === item.label);
                      if (!matchedHotel) return null;
                      return (
                        <button
                          key={`hotel-focus-${item.label}`}
                          type="button"
                          onClick={() =>
                            setDraftFilters((current) => ({
                              ...current,
                              hotelId: matchedHotel.id,
                            }))
                          }
                          className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[12px] font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
                        >
                          Hotel: {item.label} ({item.value})
                        </button>
                      );
                    })}
                    {badReviewPlatformCounts.slice(0, 1).map((item) => (
                      <button
                        key={`platform-focus-${item.label}`}
                        type="button"
                        onClick={() =>
                          setDraftFilters((current) => ({
                            ...current,
                            platformCode: item.label === "unknown" ? "" : item.label,
                          }))
                        }
                        className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[12px] font-medium capitalize text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
                      >
                        OTA: {item.label} ({item.value})
                      </button>
                    ))}
                  </div>

                  <div className="grid gap-4 xl:grid-cols-4 2xl:grid-cols-7">
                    <div className="xl:col-span-2">
                      <FilterField label="Search keyword">
                        <InputControl
                          type="search"
                          value={draftFilters.q}
                          placeholder="Search review text, title, or guest name..."
                          onChange={(event) =>
                            setDraftFilters((current) => ({
                              ...current,
                              q: event.target.value,
                            }))
                          }
                        />
                      </FilterField>
                    </div>
                    <FilterField label="Hotel">
                      <SelectControl value={draftFilters.hotelId} onChange={(value) => setDraftFilters((current) => ({ ...current, hotelId: value }))} options={hotelOptions} />
                    </FilterField>
                    <FilterField label="OTA">
                      <SourceCheckboxGroup
                        value={draftFilters.platformCode}
                        onChange={(value) => setDraftFilters((current) => ({ ...current, platformCode: value }))}
                        options={platformOptions}
                      />
                    </FilterField>
                    <FilterField label="Guest country">
                      <SelectControl value={draftFilters.reviewerCountryCode} onChange={(value) => setDraftFilters((current) => ({ ...current, reviewerCountryCode: value }))} options={reviewerCountryOptions} />
                    </FilterField>
                    <FilterField label="Min rating">
                      <InputControl
                        type="number"
                        min={0}
                        max={10}
                        step="1"
                        value={draftFilters.ratingMin}
                        placeholder="0"
                        onChange={(event) =>
                          setDraftFilters((current) => ({
                            ...current,
                            ratingMin: clampRatingValue(event.target.value),
                            badOnly: false,
                          }))
                        }
                        onBlur={(event) =>
                          setDraftFilters((current) => ({
                            ...current,
                            ratingMin: clampRatingValue(event.target.value),
                          }))
                        }
                      />
                    </FilterField>
                    <FilterField label="Max rating">
                      <InputControl
                        type="number"
                        min={0}
                        max={10}
                        step="1"
                        value={draftFilters.ratingMax}
                        placeholder="10"
                        onChange={(event) =>
                          setDraftFilters((current) => ({
                            ...current,
                            ratingMax: clampRatingValue(event.target.value),
                            badOnly: false,
                          }))
                        }
                        onBlur={(event) =>
                          setDraftFilters((current) => ({
                            ...current,
                            ratingMax: clampRatingValue(event.target.value),
                          }))
                        }
                      />
                    </FilterField>
                    <FilterField label="Flag">
                      <div className="flex h-12 items-center rounded-[14px] border border-red-200 bg-red-50 px-4 text-[15px] font-semibold text-red-700 shadow-sm">
                        Bad reviews only
                      </div>
                    </FilterField>
                    <FilterField label="Sort by">
                      <SelectControl
                        value={draftFilters.sortBy}
                        onChange={(value) =>
                          setDraftFilters((current) => ({
                            ...current,
                            sortBy: value as DashboardFilters["sortBy"],
                          }))
                        }
                        options={reviewSortOptions}
                      />
                    </FilterField>
                    <FilterField label="Order">
                      <SelectControl
                        value={draftFilters.sortOrder}
                        onChange={(value) =>
                          setDraftFilters((current) => ({
                            ...current,
                            sortOrder: value as DashboardFilters["sortOrder"],
                          }))
                        }
                        options={reviewOrderOptions}
                      />
                    </FilterField>
                  </div>

                  <div className="mt-4 grid gap-3 xl:grid-cols-2">
                    <FilterField label="Date from">
                      <DateTextControl
                        key={`reviews-date-from-${draftFilters.dateFrom}`}
                        value={draftFilters.dateFrom}
                        placeholder="DD/MM/YYYY"
                        onChange={(value) =>
                          setDraftFilters((current) => ({ ...current, dateFrom: value }))
                        }
                      />
                    </FilterField>
                    <FilterField label="Date to">
                    <DateTextControl
                      key={`reviews-date-to-${draftFilters.dateTo}`}
                      value={draftFilters.dateTo}
                      placeholder="DD/MM/YYYY"
                      onChange={(value) =>
                        setDraftFilters((current) => ({ ...current, dateTo: value }))
                      }
                      />
                    </FilterField>
                  </div>
                </Panel>

                <section className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
                  <MetricCard
                    title="Bad reviews in view"
                    value={String(badReviewRows.length)}
                    helper="Rows currently flagged as bad reviews in the visible dataset."
                    tone="text-red-600"
                    accent="border-slate-200"
                    icon="warning"
                    iconTint="bg-red-100 text-red-600"
                  />
                  <MetricCard
                    title="Top complaint country"
                    value={badReviewCountryCounts[0]?.label || "-"}
                    helper={
                      badReviewCountryCounts[0]
                        ? `${badReviewCountryCounts[0].value} flagged reviews in the current dataset.`
                        : "No standout country signal yet."
                    }
                    tone="text-violet-600"
                    accent="border-slate-200"
                    icon="globe"
                    iconTint="bg-violet-100 text-violet-600"
                  />
                  <MetricCard
                    title="Most affected hotel"
                    value={badReviewHotelCounts[0]?.label || "-"}
                    helper={
                      badReviewHotelCounts[0]
                        ? `${badReviewHotelCounts[0].value} flagged reviews need checking here.`
                        : "No standout hotel signal in bad reviews yet."
                    }
                    tone="text-amber-600"
                    accent="border-slate-200"
                    valueClassName="text-[24px] leading-[1.05] break-words"
                    icon="hotel"
                    iconTint="bg-amber-100 text-amber-600"
                  />
                  <MetricCard
                    title="Aggregate status"
                    value="Stable"
                    helper="Current workflows are working well; this slot is ready for future aggregate APIs."
                    tone="text-slate-700"
                    accent="border-slate-200"
                    icon="spark"
                  />
                </section>

                <Panel
                  title="Bad Review Investigation"
                  subtitle="Quickly surface where negative review signals are clustering in the current dataset."
                  icon="chart"
                >
                  <div className="grid gap-5 xl:grid-cols-2">
                    <div className="rounded-[24px] border border-slate-100 bg-slate-50/80 p-4">
                      <p className="text-[16px] font-semibold text-[#172033]">Bad reviews by guest country</p>
                      <p className="mt-1 text-[13px] text-[#52627A]">Shows both the number of flagged reviews and each country&apos;s share of the current bad-review set, so the team can see which guest market should be checked first.</p>
                      <div className="mt-5">
                        {badReviewCountryDisplay.length > 0 ? (
                          <HorizontalBars data={badReviewCountryDisplay} colorClass="bg-violet-600" />
                        ) : (
                          <EmptyState label="No guest-country data in the current bad-review set." />
                        )}
                      </div>
                    </div>

                    <div className="rounded-[24px] border border-slate-100 bg-slate-50/80 p-4">
                      <p className="text-[16px] font-semibold text-[#172033]">Bad reviews by hotel</p>
                      <p className="mt-1 text-[13px] text-[#52627A]">A quick lens on which properties may need attention first.</p>
                      <div className="mt-5">
                        {badReviewHotelCounts.length > 0 ? (
                          <HorizontalBars data={badReviewHotelCounts} colorClass="bg-rose-600" />
                        ) : (
                          <EmptyState label="No hotel breakdown available in the current bad-review set." />
                        )}
                      </div>
                    </div>
                  </div>
                </Panel>

                <Panel
                  title="Insights"
                  subtitle="AI-guided notes to help the team find the likely issues to improve first."
                  icon="insight"
                >
                  <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
                    <div className="rounded-[24px] border border-slate-100 bg-slate-50/80 p-4">
                      <p className="text-[16px] font-semibold text-[#172033]">What needs attention</p>
                      <div className="mt-4 space-y-3">
                        {badReviewInsightNotes.map((note) => (
                          <div key={note} className="rounded-xl border border-[var(--border)] bg-white px-3 py-3 text-[13px] leading-6 text-[#52627A]">
                            {note}
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="rounded-[24px] border border-slate-100 bg-slate-50/80 p-4">
                      <p className="text-[16px] font-semibold text-[#172033]">Complaint themes</p>
                      <p className="mt-1 text-[13px] text-[#52627A]">Frequent complaint words pulled from the currently filtered bad-review text.</p>
                      <div className="mt-4 flex flex-wrap gap-2">
                        {badReviewKeywords.length > 0 ? (
                          badReviewKeywords.map((item) => (
                            <span key={item.label} className="rounded-lg border border-[var(--border)] bg-white px-2.5 py-1.5 text-[13px] text-slate-700">
                              {item.label} <span className="text-slate-400">{item.value}</span>
                            </span>
                          ))
                        ) : (
                          <span className="text-[13px] text-[#52627A]">Chưa có đủ từ khóa nổi bật trong tập review xấu hiện tại.</span>
                        )}
                      </div>
                    </div>
                  </div>
                </Panel>

                <Panel
                  title="Priority Review Queue"
                  subtitle="Translated or normalized guest complaints the team should inspect first."
                  icon="review"
                  action={
                    <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-[13px] font-medium text-[#52627A]">
                      {`${badReviewRows.length} rows`}
                    </div>
                  }
                >
                  {badReviewRows.length === 0 ? (
                    <EmptyState label="No flagged reviews are visible in the current dataset. Adjust filters to inspect more results." />
                  ) : (
                    <div className="space-y-4">
                      {badReviewRows.slice(0, 8).map((review) => {
                        const localized = buildLocalizedReviewText(review, translationMap[review.id]);
                        return (
                          <div key={review.id} className="rounded-[24px] border border-slate-100 bg-white p-4 shadow-sm">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="rounded-md bg-red-50 px-2 py-1 text-[12px] font-semibold text-red-600">
                                Bad review
                              </span>
                              <span className="rounded-md bg-slate-100 px-2 py-1 text-[12px] font-semibold text-slate-600">
                                {review.platform_code || "unknown"}
                              </span>
                              <span className="rounded-md bg-slate-100 px-2 py-1 text-[12px] font-semibold text-slate-600">
                                {review.reviewer_country_code || "Unknown"}
                              </span>
                              <span className="rounded-md bg-slate-100 px-2 py-1 text-[12px] font-semibold text-slate-600">
                                {formatRating(review)}
                              </span>
                            </div>
                            <h3 className="mt-3 text-[15px] font-semibold text-slate-900">{localized.title}</h3>
                            <p className="mt-2 text-[13px] leading-6 text-[#52627A]">{localized.body}</p>
                            <div className="mt-3 flex flex-wrap gap-4 text-[13px] text-[#52627A]">
                              <span>{review.hotel_name}</span>
                              <span>{review.reviewer_name || "Anonymous"}</span>
                              <span>{formatDate(review.reviewed_at)}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </Panel>
              </>
      ) : null}

      <div className={mode === "dashboard" ? "space-y-6" : "hidden"}>
      <section className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
              {showMetricSkeleton ? (
                <>
                  <MetricCard
                    title="Visible reviews"
                    value="..."
                    helper="Loading current dataset..."
                    accent="border-slate-200"
                    icon="table"
                  />
                  <SkeletonCard />
                  <SkeletonCard />
                  <SkeletonCard />
                </>
              ) : (
                <>
                  <MetricCard
                    title="Visible reviews"
                    value={String(displayTotalMatches)}
                    helper={isLoading || isAnalyticsLoading ? "Refreshing matched rows for the current filters." : "Rows matching the current filters."}
                    accent="border-slate-200"
                    icon="table"
                  />
                  {analyticsReady ? (
                    <>
                      <MetricCard
                        title="Average score / 10"
                        value={displayAverageRating?.toFixed(1) || "-"}
                        helper={
                          isAnalyticsLoading
                            ? "Refreshing analytics..."
                            : useFilteredAnalytics
                              ? `Average score inside the current ${appliedReviewFlagSummary} review set.`
                              : "Average score in the current dataset."
                        }
                        tone="text-blue-600"
                        accent="border-slate-200"
                        icon="chart"
                        iconTint="bg-blue-100 text-blue-600"
                      />
                      <MetricCard
                        title="Hotels in view"
                        value={useFilteredAnalytics ? String(filteredAnalyticsHotelCounts.length) : String(hotelCounts.length)}
                        helper={
                          isAnalyticsLoading
                            ? "Refreshing analytics..."
                            : useFilteredAnalytics
                              ? `Based on the current ${appliedReviewFlagSummary} review set.`
                              : analyticsSupportsFullDashboard
                                ? "Distinct hotels in the aggregate dataset."
                                : "Requires supported aggregate filters to compare hotels."
                        }
                        tone="text-emerald-600"
                        accent="border-slate-200"
                        icon="hotel"
                        iconTint="bg-emerald-100 text-emerald-600"
                      />
                      <MetricCard
                        title="Top guest country"
                        value={useFilteredAnalytics ? filteredAnalyticsCountryCounts[0]?.label || "-" : reviewerCountryCounts[0]?.label || "-"}
                        helper={
                          isAnalyticsLoading
                            ? "Refreshing analytics..."
                            : useFilteredAnalytics
                              ? filteredAnalyticsCountryCounts[0]
                                ? `${filteredAnalyticsCountryCounts[0].value} reviews in the current ${appliedReviewFlagSummary} set.`
                                : "No country data in the current filtered set."
                              : reviewerCountryCounts[0]
                              ? `${reviewerCountryCounts[0].value} reviews`
                              : "No country data"
                        }
                        tone="text-violet-600"
                        accent="border-slate-200"
                        icon="globe"
                        iconTint="bg-violet-100 text-violet-600"
                      />
                    </>
                  ) : (
                    <>
                      <SkeletonCard />
                      <SkeletonCard />
                      <SkeletonCard />
                    </>
                  )}
                </>
              )}
            </section>

            <Panel
              title="Filters"
              subtitle=""
              icon="filter"
              action={
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      if (!hasPendingFilterChanges) {
                        setPendingFilterKey(null);
                        return;
                      }
                      if (!areFiltersEqual(effectiveFilters, effectiveDraftFilters)) {
                        beginDatasetRefresh(buildDashboardCacheKey(effectiveDraftFilters));
                      } else {
                        setPendingFilterKey(null);
                      }
                      setFilters(draftFilters);
                      setAppliedReviewFlags(draftReviewFlags);
                      setTableScoreFilters(draftReviewFlags);
                    }}
                    className="rounded-xl bg-slate-900 px-4 py-2.5 text-[15px] font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70"
                    disabled={isApplyingFilters || !hasPendingFilterChanges}
                  >
                    {isApplyingFilters ? "Filtering..." : hasPendingFilterChanges ? "Filter" : "Applied"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      beginDatasetRefresh(buildDashboardCacheKey(DEFAULT_FILTERS));
                      setDraftFilters(DEFAULT_FILTERS);
                      setFilters(DEFAULT_FILTERS);
                      setDraftReviewFlags([]);
                      setAppliedReviewFlags([]);
                      setTableScoreFilters([]);
                      setTableLanguageFilters([]);
                    }}
                    className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-[15px] font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
                  >
                    Reset
                  </button>
                </div>
              }
            >
              <div className="grid gap-4 xl:grid-cols-[minmax(0,1.7fr)_minmax(0,1.35fr)_minmax(0,0.82fr)_minmax(0,0.82fr)_minmax(0,1fr)_minmax(0,0.95fr)_minmax(0,0.95fr)] xl:items-end">
                <FilterField label="Hotel">
                  <SelectControl value={draftFilters.hotelId} onChange={(value) => setDraftFilters((current) => ({ ...current, hotelId: value }))} options={hotelOptions} />
                </FilterField>
                <FilterField label="OTA">
                  <SourceCheckboxGroup
                    value={draftFilters.platformCode}
                    onChange={(value) => setDraftFilters((current) => ({ ...current, platformCode: value }))}
                    options={platformOptions}
                  />
                </FilterField>
                <FilterField label="Min rating">
                  <InputControl
                    type="number"
                    min={0}
                    max={10}
                    step="1"
                    value={draftFilters.ratingMin}
                    placeholder="0"
                    onChange={(event) =>
                      setDraftFilters((current) => ({
                        ...current,
                        ratingMin: clampRatingValue(event.target.value),
                        badOnly: false,
                      }))
                    }
                    onBlur={(event) =>
                      setDraftFilters((current) => ({
                        ...current,
                        ratingMin: clampRatingValue(event.target.value),
                      }))
                    }
                  />
                </FilterField>
                <FilterField label="Max rating">
                  <InputControl
                    type="number"
                    min={0}
                    max={10}
                    step="1"
                    value={draftFilters.ratingMax}
                    placeholder="10"
                    onChange={(event) =>
                      setDraftFilters((current) => ({
                        ...current,
                        ratingMax: clampRatingValue(event.target.value),
                        badOnly: false,
                      }))
                    }
                    onBlur={(event) =>
                      setDraftFilters((current) => ({
                        ...current,
                        ratingMax: clampRatingValue(event.target.value),
                      }))
                    }
                  />
                </FilterField>
                <FilterField label="Flag">
                  <MultiCheckboxSelect
                    value={draftReviewFlags}
                    onChange={(value) => setDraftReviewFlags(value as ReviewFlagFilter[])}
                    options={REVIEW_FLAG_OPTIONS}
                    placeholder="All statuses"
                  />
                </FilterField>
                <FilterField label="From">
                  <DateTextControl
                    key={`dashboard-date-from-${draftFilters.dateFrom}`}
                    value={draftFilters.dateFrom}
                    placeholder="DD/MM/YYYY"
                    compact
                    onChange={(value) =>
                      setDraftFilters((current) => ({ ...current, dateFrom: value }))
                    }
                  />
                </FilterField>
                <FilterField label="To">
                  <DateTextControl
                    key={`dashboard-date-to-${draftFilters.dateTo}`}
                    value={draftFilters.dateTo}
                    placeholder="DD/MM/YYYY"
                    compact
                    onChange={(value) =>
                      setDraftFilters((current) => ({ ...current, dateTo: value }))
                    }
                  />
                </FilterField>
              </div>
            </Panel>

            <div className="grid gap-6 2xl:grid-cols-[1.25fr_0.75fr]">
              <Panel title="Analytics" subtitle="" icon="chart">
                {isAnalyticsLoading && !hasAnalyticsData ? (
                  <div className="grid gap-5 xl:grid-cols-2">
                    <SkeletonCard />
                    <SkeletonCard />
                    <SkeletonCard />
                    <SkeletonCard />
                  </div>
                ) : isAnalyticsLoading ? (
                  <div className="mb-4 rounded-2xl border border-blue-100 bg-blue-50/80 px-4 py-3 text-[13px] text-blue-700">
                    Analytics is updating. The cards below are showing the last stable snapshot.
                  </div>
                ) : null}
                {!isAnalyticsLoading && !analyticsReady ? (
                  <div className="grid gap-5 xl:grid-cols-2">
                    <SkeletonCard />
                    <SkeletonCard />
                    <SkeletonCard />
                    <SkeletonCard />
                  </div>
                ) : !analyticsSupportsFullDashboard && !useFilteredAnalytics ? (
                  <div className="rounded-[24px] border border-dashed border-amber-200 bg-amber-50/80 px-5 py-6 text-[13px] leading-6 text-amber-900">
                    {analyticsSupportMessage}
                  </div>
                ) : (
                  <div className="grid gap-5 xl:grid-cols-2">
                    <div className="rounded-[24px] border border-slate-100 bg-slate-50/80 p-4 xl:col-span-2">
                      <p className="text-[16px] font-semibold text-[#172033]">Review ratio</p>
                      <p className="mt-1 text-[13px] text-[#52627A]">
                        {useFilteredAnalytics
                          ? `Showing the ratio inside the current ${appliedReviewFlagSummary} filter result.`
                          : "Good = 9-10, Average = 7-8, Bad = 1-6, Unknown = no rating."}
                      </p>
                      <div className="mt-5">
                        <DonutChart
                          segments={useFilteredAnalytics ? filteredAnalyticsReviewMix : reviewMix}
                          activeLabels={activeReviewMixLabels}
                          onSegmentClick={(label) => {
                            const mapped =
                              label.toLowerCase() === "unknown"
                                ? "unrated"
                                : (label.toLowerCase() as TableScoreFilter);
                            setTableScoreFilters((current) =>
                              current.length === 1 && current[0] === mapped ? [] : [mapped],
                            );
                            setSelectedReviewId(null);
                          }}
                        />
                      </div>
                    </div>

                    <div className="rounded-[24px] border border-slate-100 bg-slate-50/80 p-4">
                      <p className="text-[16px] font-semibold text-[#172033]">Score distribution</p>
                      <p className="mt-1 text-[13px] text-[#52627A]">
                        {useFilteredAnalytics
                          ? `Distribution for the currently filtered ${appliedReviewFlagSummary} result set.`
                          : "Quick score spread by normalized bucket."}
                      </p>
                      <div className="mt-5">
                        {(useFilteredAnalytics ? filteredAnalyticsScoreBuckets : scoreBuckets).some((item) => item.value > 0) ? (
                          <HorizontalBars data={useFilteredAnalytics ? filteredAnalyticsScoreBuckets : scoreBuckets} colorClass="bg-blue-600" />
                        ) : (
                          <EmptyState label="No score distribution available." />
                        )}
                      </div>
                    </div>

                    <div className="rounded-[24px] border border-slate-100 bg-slate-50/80 p-4">
                      <p className="text-[16px] font-semibold text-[#172033]">Reviews by guest country</p>
                      <p className="mt-1 text-[13px] text-[#52627A]">
                        {useFilteredAnalytics
                          ? `Country breakdown for the current ${appliedReviewFlagSummary} filter result.`
                          : "Country of the reviewer, not the hotel."}
                      </p>
                      <div className="mt-5">
                        {(useFilteredAnalytics ? filteredAnalyticsCountryCounts : reviewerCountryCounts).length > 0 ? (
                          <ExpandableBars data={useFilteredAnalytics ? filteredAnalyticsCountryCounts : reviewerCountryCounts} colorClass="bg-violet-600" />
                        ) : (
                          <EmptyState label="No guest-country data available." />
                        )}
                      </div>
                    </div>

                    {showHotelBreakdown ? (
                      <div className="rounded-[24px] border border-slate-100 bg-slate-50/80 p-4 xl:col-span-2">
                        <p className="text-[16px] font-semibold text-[#172033]">Reviews by hotel</p>
                        <p className="mt-1 text-[13px] text-[#52627A]">
                          {useFilteredAnalytics
                            ? `Hotel breakdown for the current ${appliedReviewFlagSummary} filter result.`
                            : "Top hotel concentration in the current dataset."}
                        </p>
                        <div className="mt-5">
                          {(useFilteredAnalytics ? filteredAnalyticsHotelCounts : hotelCounts).length > 0 ? (
                            <HorizontalBars data={useFilteredAnalytics ? filteredAnalyticsHotelCounts : hotelCounts} colorClass="bg-emerald-600" />
                          ) : (
                            <EmptyState label="No hotel comparison available." />
                          )}
                        </div>
                      </div>
                    ) : null}

                    <div className="rounded-[24px] border border-slate-100 bg-slate-50/80 p-4 xl:col-span-2">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <p className="text-[16px] font-semibold text-[#172033]">Categories</p>
                          <p className="mt-1 text-[13px] text-[#52627A]">
                            {activeCategorySummary
                              ? `${activeCategorySummary.hotel_name} · ${activeCategorySummary.platform_code}`
                              : "Current source category scores for the active hotel / OTA selection."}
                          </p>
                        </div>
                        {activeCategorySummary ? (
                          <span className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[12px] font-semibold uppercase tracking-[0.04em] text-slate-600">
                            {formatDateTime(activeCategorySummary.source_captured_at)}
                          </span>
                        ) : null}
                      </div>
                      <div className="mt-5">
                        {categoryData.length > 0 ? (
                          <CategoryBars items={categoryData} />
                        ) : (
                          <EmptyState label="No category breakdown available for the current hotel / OTA filter." />
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </Panel>

              <Panel
                title="Insights"
                subtitle=""
                icon="insight"
                action={
                  <button
                    type="button"
                    onClick={async () => {
                      setDashboardInsightsRequested(true);
                      setIsAiInsightLoading(true);
                      setAiInsightError(null);

                      try {
                        const response = await fetchReviewInsights({
                          totalMatches: displayTotalMatches,
                          visibleReviewCount: filteredReviews.length,
                          filters: {
                            hotelId: effectiveFilters.hotelId,
                            platformCode: parsePlatformFilterValue(effectiveFilters.platformCode),
                            reviewerCountryCode: effectiveFilters.reviewerCountryCode,
                            ratingMin: effectiveFilters.ratingMin,
                            ratingMax: effectiveFilters.ratingMax,
                            dateFrom: effectiveFilters.dateFrom,
                            dateTo: effectiveFilters.dateTo,
                            badOnly: effectiveFilters.badOnly,
                            reviewFlags: appliedReviewFlags,
                          },
                          analyticsSummary: summary,
                          countryBreakdown: (useFilteredAnalytics ? filteredAnalyticsCountryCounts : reviewerCountryCounts).slice(0, 6),
                          hotelBreakdown: (useFilteredAnalytics ? filteredAnalyticsHotelCounts : hotelCounts).slice(0, 6),
                          keywordSummary,
                          categories: categoryData,
                          reviews: insightReviewPayload,
                        });

                        setAiInsightContent(response.content);
                      } catch (insightError) {
                        setAiInsightError(
                          insightError instanceof Error
                            ? insightError.message
                            : "Failed to analyze the current filtered data.",
                        );
                      } finally {
                        setIsAiInsightLoading(false);
                      }
                    }}
                    className="rounded-xl bg-slate-900 px-4 py-2.5 text-[14px] font-semibold text-white shadow-sm transition hover:bg-slate-800"
                  >
                    {isAiInsightLoading ? "Analyzing..." : "AI analyze current filtered data"}
                  </button>
                }
              >
                {isLoading && !hasReviewData ? (
                  <div className="space-y-4">
                    <SkeletonCard />
                    <SkeletonCard />
                  </div>
                ) : !dashboardInsightsRequested ? (
                  <EmptyState label={`Click "AI analyze current filtered data" to analyze the current filtered result set (${filteredReviews.length} visible reviews).`} />
                ) : isAiInsightLoading ? (
                  <div className="space-y-4">
                    <SkeletonCard />
                    <SkeletonCard />
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="rounded-[24px] border border-slate-100 bg-slate-50/80 p-4">
                      <p className="text-[16px] font-semibold text-[#172033]">AI analysis</p>
                      {aiInsightError ? (
                        <div className="mt-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[13px] leading-6 text-red-700">
                          {aiInsightError}
                        </div>
                      ) : (
                        <div className="mt-3 rounded-xl border border-[var(--border)] bg-white px-4 py-4 text-[14px] leading-7 text-[#334155] whitespace-pre-wrap">
                          {aiInsightContent || "AI chua tra ve noi dung phan tich."}
                        </div>
                      )}
                    </div>

                    <div className="rounded-[24px] border border-slate-100 bg-slate-50/80 p-4">
                      <p className="text-[16px] font-semibold text-[#172033]">Supporting signals</p>
                      <div className="mt-3 space-y-3">
                        {insightNotes.map((note) => (
                          <div key={note} className="rounded-xl border border-[var(--border)] bg-white px-3 py-3 text-[13px] leading-6 text-[#52627A]">
                            {note}
                          </div>
                        ))}
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {keywordSummary.length > 0 ? (
                          keywordSummary.map((item) => (
                            <span key={item.label} className="rounded-lg border border-[var(--border)] bg-white px-2.5 py-1.5 text-[13px] text-slate-700">
                              {item.label} <span className="text-slate-400">{item.value}</span>
                            </span>
                          ))
                        ) : (
                          <span className="text-[13px] text-[#52627A]">No keyword signal available.</span>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </Panel>
            </div>

            <div className="grid gap-6 2xl:grid-cols-[1.42fr_0.78fr]">
              <Panel
                title="Review Table"
                subtitle=""
                icon="table"
                action={<div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-[13px] font-medium text-[#52627A]">{isLoading ? "Updating rows" : `${tableFilteredReviews.length}/${filteredReviews.length} rows`}</div>}
              >
                <div className="mb-4 grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] xl:items-end">
                  <FilterField label="Review scores">
                    <MultiCheckboxSelect
                      value={tableScoreFilters}
                      onChange={(value) => {
                        setTableScoreFilters(value as TableScoreFilter[]);
                        setSelectedReviewId(null);
                      }}
                      options={tableScoreOptions}
                      placeholder="All score groups"
                    />
                  </FilterField>
                  <FilterField label="Languages">
                    <MultiCheckboxSelect
                      value={tableLanguageFilters}
                      onChange={(value) => {
                        setTableLanguageFilters(value);
                        setSelectedReviewId(null);
                      }}
                      options={tableLanguageOptions}
                      placeholder="All languages"
                    />
                  </FilterField>
                  <div className="flex items-center gap-2 xl:justify-end">
                    <button
                      type="button"
                      onClick={() => {
                        setTableScoreFilters([]);
                        setTableLanguageFilters([]);
                        setSelectedReviewId(null);
                      }}
                      className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-[14px] font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
                    >
                      Clear table filters
                    </button>
                  </div>
                </div>

                {error ? (
                  <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-[13px] text-red-600">{error}</div>
                ) : null}

                {pagedReviews.length === 0 && !isLoading ? (
                  <EmptyState label="No reviews match the current table filters." />
                ) : (
                  <>
                    {isLoading && hasReviewData ? (
                      <div className="mb-3 rounded-2xl border border-blue-100 bg-blue-50/80 px-4 py-3 text-[13px] text-blue-700">
                        Review rows are updating for the current filters.
                      </div>
                    ) : null}
                    <div className="overflow-hidden rounded-[24px] border border-slate-100 bg-white shadow-sm">
                      <div className="hidden grid-cols-[2.35fr_1.35fr_0.95fr_1fr_0.8fr_1fr] gap-4 border-b border-slate-100 bg-slate-50/80 px-4 py-3.5 text-[13px] font-semibold text-[#46556D] lg:grid">
                        <div>Review</div>
                        <div>Hotel</div>
                        <div>OTA</div>
                        <div>Guest</div>
                        <div>Score</div>
                        <div>Date</div>
                      </div>

                      <div className="divide-y divide-slate-100 bg-white">
                        {isLoading && !hasReviewData
                          ? Array.from({ length: 6 }).map((_, index) => (
                              <div key={`review-skeleton-${index}`}>
                                <div className="space-y-2 px-4 py-4 lg:hidden">
                                  <div className="rounded-[14px] border border-slate-100 bg-slate-50 p-4">
                                    <div className="h-4 w-3/4 animate-pulse rounded bg-slate-200" />
                                    <div className="mt-3 h-3 w-full animate-pulse rounded bg-slate-100" />
                                    <div className="mt-4 grid grid-cols-2 gap-3">
                                      <div className="h-10 animate-pulse rounded bg-slate-100" />
                                      <div className="h-10 animate-pulse rounded bg-slate-100" />
                                    </div>
                                  </div>
                                </div>
                                <div
                                  className="hidden grid-cols-[2.35fr_1.35fr_0.95fr_1fr_0.8fr_1fr] gap-4 px-4 py-4 lg:grid"
                                >
                                  <div className="space-y-2">
                                    <div className="h-4 w-3/4 animate-pulse rounded bg-slate-200" />
                                    <div className="h-3 w-full animate-pulse rounded bg-slate-100" />
                                  </div>
                                  <div className="h-4 w-5/6 animate-pulse rounded bg-slate-100" />
                                  <div className="h-4 w-16 animate-pulse rounded bg-slate-100" />
                                  <div className="space-y-2">
                                    <div className="h-4 w-20 animate-pulse rounded bg-slate-100" />
                                    <div className="h-3 w-10 animate-pulse rounded bg-slate-100" />
                                  </div>
                                  <div className="h-4 w-16 animate-pulse rounded bg-slate-100" />
                                  <div className="h-4 w-20 animate-pulse rounded bg-slate-100" />
                                </div>
                              </div>
                            ))
                          : pagedReviews.map((review) => {
                              const localized = buildLocalizedReviewText(review, translationMap[review.id]);
                              const active = selectedReview?.id === review.id;

                              return (
                                <div key={review.id}>
                                  <button
                                    type="button"
                                    onClick={() => setSelectedReviewId(review.id)}
                                    className={`w-full rounded-[14px] p-4 text-left transition lg:hidden ${
                                      active ? "bg-blue-50/80" : "hover:bg-slate-50"
                                    }`}
                                  >
                                    <div className="flex flex-wrap items-center gap-2">
                                      <span className="text-[14px] font-semibold text-slate-900">{localized.title}</span>
                                      {review.is_bad_review ? (
                                        <span className="rounded-md bg-red-50 px-2 py-1 text-[12px] font-semibold text-red-600">
                                          Alert
                                        </span>
                                      ) : null}
                                      {localized.translationSource === "auto_vi" ? (
                                        <span className="rounded-md bg-blue-50 px-2 py-1 text-[12px] font-semibold text-blue-600">
                                          Auto VI
                                        </span>
                                      ) : null}
                                    </div>
                                    <p className="mt-2 line-clamp-3 text-[13px] leading-6 text-[#52627A]">{localized.body}</p>
                                    <div className="mt-4 grid grid-cols-2 gap-3 text-[12px]">
                                      <div className="rounded-[12px] bg-slate-50 px-3 py-2">
                                        <p className="font-semibold text-slate-500">Hotel</p>
                                        <p className="mt-1 text-[#1F2937]">{review.hotel_name}</p>
                                      </div>
                                      <div className="rounded-[12px] bg-slate-50 px-3 py-2">
                                        <p className="font-semibold text-slate-500">OTA</p>
                                        <p className="mt-1 capitalize text-[#1F2937]">{review.platform_code || "-"}</p>
                                      </div>
                                      <div className="rounded-[12px] bg-slate-50 px-3 py-2">
                                        <p className="font-semibold text-slate-500">Guest</p>
                                        <p className="mt-1 text-[#1F2937]">{review.reviewer_name || "Anonymous"}</p>
                                        <p className="text-slate-400">{review.reviewer_country_code || "Unknown"}</p>
                                      </div>
                                      <div className="rounded-[12px] bg-slate-50 px-3 py-2">
                                        <p className="font-semibold text-slate-500">Score / Date</p>
                                        <p className="mt-1 text-[#1F2937]">{formatRating(review)}</p>
                                        <p className="text-slate-400">{formatDate(review.reviewed_at)}</p>
                                      </div>
                                    </div>
                                  </button>

                                  <button
                                    type="button"
                                    onClick={() => setSelectedReviewId(review.id)}
                                    className={`hidden w-full grid-cols-[2.35fr_1.35fr_0.95fr_1fr_0.8fr_1fr] gap-4 px-4 py-4 text-left transition lg:grid ${
                                      active ? "bg-blue-50/80" : "hover:bg-slate-50"
                                    }`}
                                  >
                                    <div className="min-w-0">
                                      <div className="flex flex-wrap items-center gap-2">
                                        <span className="truncate text-[14px] font-semibold text-slate-900">{localized.title}</span>
                                        {review.is_bad_review ? (
                                          <span className="rounded-md bg-red-50 px-2 py-1 text-[12px] font-semibold text-red-600">
                                            Alert
                                          </span>
                                        ) : null}
                                        {localized.translationSource === "auto_vi" ? (
                                          <span className="rounded-md bg-blue-50 px-2 py-1 text-[12px] font-semibold text-blue-600">
                                            Auto VI
                                          </span>
                                        ) : null}
                                      </div>
                                      <p className="mt-1 line-clamp-2 text-[13px] leading-6 text-[#52627A]">{localized.body}</p>
                                    </div>
                                    <div className="text-[13px] leading-6 text-[#52627A]">{review.hotel_name}</div>
                                    <div className="text-[13px] capitalize text-[#52627A]">{review.platform_code || "-"}</div>
                                    <div className="text-[13px] text-[#52627A]">
                                      <div>{review.reviewer_name || "Anonymous"}</div>
                                      <div className="mt-1 text-[12px] text-slate-400">
                                        {review.reviewer_country_code || "Unknown"}
                                      </div>
                                    </div>
                                    <div className="text-[13px] font-semibold text-slate-900">{formatRating(review)}</div>
                                    <div className="text-[13px] text-[#52627A]">{formatDate(review.reviewed_at)}</div>
                                  </button>
                                </div>
                              );
                            })}
                      </div>
                    </div>

                    <div className="mt-4 flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
                      <p className="text-[14px] text-[#52627A]">
                        Page {currentPage} of {totalPages}
                      </p>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          disabled={currentPage === 1}
                          onClick={() => setCurrentPage((page) => Math.max(page - 1, 1))}
                          className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-[13px] font-medium text-slate-700 shadow-sm disabled:cursor-not-allowed disabled:opacity-40"
                        >
                          Previous
                        </button>
                        <button
                          type="button"
                          disabled={currentPage === totalPages}
                          onClick={() => setCurrentPage((page) => Math.min(page + 1, totalPages))}
                          className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-[13px] font-medium text-slate-700 shadow-sm disabled:cursor-not-allowed disabled:opacity-40"
                        >
                          Next
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </Panel>

              <Panel title="Selected Review" subtitle="" icon="review">
                {selectedReview ? (
                  <div className="space-y-4">
                    <div className="rounded-[24px] border border-slate-100 bg-slate-50/80 p-4">
                      <div className="flex flex-wrap gap-2">
                        <span className="rounded-md bg-white px-2.5 py-1 text-[12px] font-semibold text-[#52627A]">
                          {selectedReview.platform_code || "unknown"}
                        </span>
                        <span className="rounded-md bg-white px-2.5 py-1 text-[12px] font-semibold text-[#52627A]">
                          {formatRating(selectedReview)}
                        </span>
                        <span className="rounded-md bg-white px-2.5 py-1 text-[12px] font-semibold text-[#52627A]">
                          {selectedReview.reviewer_country_code || "Unknown"}
                        </span>
                      </div>

                      <div className="mt-4">
                        <h3 className="font-display text-2xl text-slate-900">
                          {buildLocalizedReviewText(selectedReview, translationMap[selectedReview.id]).title}
                        </h3>
                        <p className="mt-3 text-[13px] leading-7 text-[#52627A]">
                          {buildLocalizedReviewText(selectedReview, translationMap[selectedReview.id]).body}
                        </p>
                      </div>
                    </div>

                    <div className="rounded-[24px] border border-slate-100 bg-white p-4 shadow-sm">
                      <p className="text-[12px] font-semibold text-[#46556D]">Original review</p>
                      <p className="mt-3 text-[13px] leading-7 text-[#52627A]">
                        {buildLocalizedReviewText(selectedReview, translationMap[selectedReview.id]).originalBody}
                      </p>
                    </div>

                    <div className="rounded-[24px] border border-slate-100 bg-white p-4 shadow-sm">
                      <dl className="space-y-3 text-[13px]">
                        <div className="flex items-center justify-between gap-4">
                          <dt className="text-slate-500">Hotel</dt>
                          <dd className="text-right font-medium text-slate-900">{selectedReview.hotel_name}</dd>
                        </div>
                        <div className="flex items-center justify-between gap-4">
                          <dt className="text-slate-500">Reviewer</dt>
                          <dd className="text-right font-medium text-slate-900">{selectedReview.reviewer_name || "-"}</dd>
                        </div>
                        <div className="flex items-center justify-between gap-4">
                          <dt className="text-slate-500">Reviewed at</dt>
                          <dd className="text-right font-medium text-slate-900">{formatDateTime(selectedReview.reviewed_at)}</dd>
                        </div>
                        <div className="flex items-center justify-between gap-4">
                          <dt className="text-slate-500">Updated at OTA</dt>
                          <dd className="text-right font-medium text-slate-900">{formatDateTime(selectedReview.source_updated_at)}</dd>
                        </div>
                        <div className="flex items-center justify-between gap-4">
                          <dt className="text-slate-500">Bad review</dt>
                          <dd className={`text-right font-medium ${selectedReview.is_bad_review ? "text-red-600" : "text-emerald-600"}`}>
                            {selectedReview.is_bad_review ? "Yes" : "No"}
                          </dd>
                        </div>
                      </dl>
                    </div>
                  </div>
                ) : (
                  <EmptyState label="Select a review row to inspect the translated content and metadata." />
                )}
              </Panel>
            </div>
      </div>
    </WorkspaceShell>
  );
}
