import { DashboardFilters, LocalizedReviewText, Review } from "@/lib/types";

const STOP_WORDS = new Set([
  "the",
  "and",
  "for",
  "with",
  "that",
  "this",
  "from",
  "were",
  "have",
  "very",
  "just",
  "room",
  "hotel",
  "staff",
  "good",
  "great",
  "nice",
  "clean",
  "helpful",
  "will",
  "into",
  "stay",
  "there",
  "them",
  "they",
  "your",
  "about",
  "near",
  "next",
]);

export function parsePlatformFilterValue(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function buildReviewQuery(filters: DashboardFilters) {
  const params = new URLSearchParams();
  const selectedPlatforms = parsePlatformFilterValue(filters.platformCode);

  if (filters.hotelId) params.set("hotel_id", filters.hotelId);
  if (selectedPlatforms.length === 1) params.set("platform_code", selectedPlatforms[0]);
  if (filters.badOnly) params.set("is_bad_review", "true");
  if (filters.reviewerCountryCode) {
    params.set("reviewer_country_code", filters.reviewerCountryCode);
  }
  if (filters.ratingMin) params.set("rating_min", filters.ratingMin.trim());
  if (filters.ratingMax) params.set("rating_max", filters.ratingMax.trim());
  if (filters.dateFrom) {
    const startDate = new Date(`${filters.dateFrom}T00:00:00`);
    params.set("date_from", startDate.toISOString());
  }
  if (filters.dateTo) {
    const endDate = new Date(`${filters.dateTo}T23:59:59.999`);
    params.set("date_to", endDate.toISOString());
  }
  if (filters.q.trim()) params.set("q", filters.q.trim());
  params.set("sort_by", filters.sortBy);
  params.set("sort_order", filters.sortOrder);

  return params;
}

export function normalizeScore(review: Review) {
  if (!review.rating || !review.rating_scale) {
    return null;
  }

  return Number(((review.rating / review.rating_scale) * 10).toFixed(1));
}

export function summarizeReviews(reviews: Review[]) {
  const normalizedScores = reviews
    .map((review) => normalizeScore(review))
    .filter((value): value is number => value !== null);
  const badReviewCount = reviews.filter((review) => review.is_bad_review).length;
  const hotelCount = new Set(reviews.map((review) => review.hotel_id)).size;
  const reviewerCountryCounts = countBy(reviews, (review) => review.reviewer_country_code || "Unknown");
  const platformCounts = countBy(reviews, (review) => review.platform_code || "unknown");
  const averageScore =
    normalizedScores.length > 0
      ? normalizedScores.reduce((sum, value) => sum + value, 0) / normalizedScores.length
      : 0;

  return {
    totalReviews: reviews.length,
    averageScore: Number(averageScore.toFixed(1)),
    hotelCount,
    badReviewCount,
    badReviewRate: reviews.length ? Math.round((badReviewCount / reviews.length) * 100) : 0,
    topReviewerCountry: reviewerCountryCounts[0] || null,
    platformCounts,
  };
}

export function buildScoreBuckets(reviews: Review[]) {
  const buckets = [
    { label: "0-2", min: 0, max: 2, count: 0 },
    { label: "2-4", min: 2, max: 4, count: 0 },
    { label: "4-6", min: 4, max: 6, count: 0 },
    { label: "6-8", min: 6, max: 8, count: 0 },
    { label: "8-10", min: 8, max: 10.01, count: 0 },
  ];

  reviews.forEach((review) => {
    const score = normalizeScore(review);
    if (score === null) return;

    const bucket = buckets.find((item) => score >= item.min && score < item.max);
    if (bucket) bucket.count += 1;
  });

  return buckets;
}

export function buildReviewMix(reviews: Review[]) {
  const segments = [
    { label: "Strong", count: 0, color: "#2563eb" },
    { label: "Mixed", count: 0, color: "#14b8a6" },
    { label: "Critical", count: 0, color: "#f97316" },
  ];

  reviews.forEach((review) => {
    const score = normalizeScore(review);
    if (score === null) return;

    if (score >= 8) {
      segments[0].count += 1;
      return;
    }

    if (score >= 6) {
      segments[1].count += 1;
      return;
    }

    segments[2].count += 1;
  });

  return segments;
}

export function countBy<T>(items: T[], getter: (item: T) => string) {
  const map = new Map<string, number>();

  items.forEach((item) => {
    const key = getter(item);
    map.set(key, (map.get(key) || 0) + 1);
  });

  return [...map.entries()]
    .map(([label, value]) => ({ label, value }))
    .sort((left, right) => right.value - left.value);
}

export function topKeywords(reviews: Review[], limit = 8) {
  const words = new Map<string, number>();

  reviews.forEach((review) => {
    const content = [
      review.translated_title_vi,
      review.translated_text_vi,
      review.review_title,
      review.review_text,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();

    content
      .replace(/[^a-z0-9\s]/g, " ")
      .split(/\s+/)
      .filter((word) => word.length >= 4 && !STOP_WORDS.has(word))
      .forEach((word) => {
        words.set(word, (words.get(word) || 0) + 1);
      });
  });

  return [...words.entries()]
    .map(([label, value]) => ({ label, value }))
    .sort((left, right) => right.value - left.value)
    .slice(0, limit);
}

export function buildInsightNotes(reviews: Review[]) {
  const summary = summarizeReviews(reviews);
  const keywords = topKeywords(reviews, 5);
  const notes: string[] = [];

  if (summary.averageScore >= 8) {
    notes.push("Guest sentiment is broadly strong across the current result set.");
  } else if (summary.averageScore >= 6) {
    notes.push("Guest feedback is mixed, with clear room for service improvements.");
  } else {
    notes.push("The visible reviews indicate operational issues that need urgent attention.");
  }

  if (summary.badReviewRate >= 35) {
    notes.push("Bad review share is high enough to justify a response workflow and escalation queue.");
  } else if (summary.badReviewRate >= 15) {
    notes.push("Bad review volume is noticeable and worth monitoring daily.");
  } else {
    notes.push("Bad review volume is currently contained relative to total visible reviews.");
  }

  if (keywords.length > 0) {
    notes.push(
      `Recurring discussion points: ${keywords
        .slice(0, 3)
        .map((keyword) => keyword.label)
        .join(", ")}.`,
    );
  }

  return notes;
}

const MOJIBAKE_PATTERN = /Ã|Â|Ä|á»|áº|Æ|â€™|â€œ|â€|ðŸ|¢/;
const VIETNAMESE_PATTERN =
  /[ăâđêôơưĂÂĐÊÔƠƯáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]/i;

function repairLatin1Mojibake(value: string | null | undefined) {
  if (!value) return "";
  if (!MOJIBAKE_PATTERN.test(value)) return value;

  try {
    const bytes = Uint8Array.from([...value].map((character) => character.charCodeAt(0) & 0xff));
    const decoded = new TextDecoder("utf-8", { fatal: false }).decode(bytes);
    return decoded;
  } catch {
    return value;
  }
}

export function normalizeReadableText(value: string | null | undefined) {
  const repaired = repairLatin1Mojibake(value);
  return repaired.trim();
}

export function hasUsableVietnamese(value: string | null | undefined) {
  const normalized = normalizeReadableText(value);
  return normalized.length > 0 && VIETNAMESE_PATTERN.test(normalized);
}

export function buildLocalizedReviewText(
  review: Review,
  autoTranslation?: { title?: string; body?: string },
): LocalizedReviewText {
  const repairedTranslatedTitle = normalizeReadableText(review.translated_title_vi);
  const repairedTranslatedBody = normalizeReadableText(review.translated_text_vi);
  const repairedOriginalTitle = normalizeReadableText(review.review_title);
  const repairedOriginalBody = normalizeReadableText(review.review_text);

  if (hasUsableVietnamese(repairedTranslatedTitle) || hasUsableVietnamese(repairedTranslatedBody)) {
    return {
      title: repairedTranslatedTitle || repairedOriginalTitle || "Chua co tieu de",
      body: repairedTranslatedBody || repairedOriginalBody || "Chua co noi dung review.",
      originalTitle: repairedOriginalTitle || "No original title",
      originalBody: repairedOriginalBody || "No original body",
      translationSource:
        MOJIBAKE_PATTERN.test(review.translated_title_vi || "") ||
        MOJIBAKE_PATTERN.test(review.translated_text_vi || "")
          ? "repaired_vi"
          : "api_vi",
    };
  }

  if (autoTranslation?.title || autoTranslation?.body) {
    return {
      title: autoTranslation.title || repairedOriginalTitle || "Chua co tieu de",
      body: autoTranslation.body || repairedOriginalBody || "Chua co noi dung review.",
      originalTitle: repairedOriginalTitle || "No original title",
      originalBody: repairedOriginalBody || "No original body",
      translationSource: "auto_vi",
    };
  }

  return {
    title: repairedOriginalTitle || "Chua co tieu de",
    body: repairedOriginalBody || "Chua co noi dung review.",
    originalTitle: repairedOriginalTitle || "No original title",
    originalBody: repairedOriginalBody || "No original body",
    translationSource: "original",
  };
}

export function formatDisplayText(
  review: Review,
  autoTranslation?: { title?: string; body?: string },
) {
  return buildLocalizedReviewText(review, autoTranslation);
}

export function formatDate(dateString: string | null) {
  if (!dateString) return "-";
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(dateString));
}

export function formatDateTime(dateString: string | null) {
  if (!dateString) return "-";
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(dateString));
}

export function formatRating(review: Review) {
  if (review.rating === null || review.rating_scale === null) {
    return "-";
  }

  return `${review.rating} / ${review.rating_scale}`;
}
