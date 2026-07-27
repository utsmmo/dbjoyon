export type Hotel = {
  id: string;
  hotel_code: string;
  hotel_name: string;
  country_code: string | null;
  city: string | null;
  status: string;
};

export type Review = {
  id: string;
  hotel_id: string;
  hotel_name: string;
  platform_code: string | null;
  external_review_id: string | null;
  reviewer_name: string | null;
  reviewer_country_code: string | null;
  rating: number | null;
  rating_scale: number | null;
  review_title: string | null;
  review_text: string | null;
  translated_title_vi: string | null;
  translated_text_vi: string | null;
  review_language: string | null;
  sentiment_label: string | null;
  is_bad_review: boolean;
  stay_date: string | null;
  reviewed_at: string;
  source_updated_at: string | null;
  created_at: string;
  updated_at: string;
};

export type LocalizedReviewText = {
  title: string;
  body: string;
  originalTitle: string;
  originalBody: string;
  translationSource: "api_vi" | "repaired_vi" | "auto_vi" | "original";
};

export type PaginatedResponse<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};

export type DashboardFilters = {
  hotelId: string;
  platformCode: string;
  reviewerCountryCode: string;
  ratingMin: string;
  ratingMax: string;
  dateFrom: string;
  dateTo: string;
  q: string;
  sortBy: "reviewed_at" | "rating" | "created_at" | "hotel_name" | "reviewer_name";
  sortOrder: "asc" | "desc";
  badOnly: boolean;
};

export type ReviewSummaryAggregate = {
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

export type ReviewCountryBreakdownItem = {
  reviewer_country_code: string;
  total_reviews: number;
  bad_reviews: number;
  avg_rating: number | null;
};

export type ReviewHotelBreakdownItem = {
  hotel_id: string;
  hotel_name: string;
  platform_code: string | null;
  total_reviews: number;
  bad_reviews: number;
  avg_rating: number | null;
  latest_reviewed_at: string | null;
};

export type ReviewScoreBucketItem = {
  bucket_code: string;
  bucket_label: string;
  rating_from: number;
  rating_to: number;
  review_count: number;
  bad_review_count: number;
};

export type ReviewDailyTrendItem = {
  metric_date: string;
  total_reviews: number;
  bad_reviews: number;
  avg_rating: number | null;
  positive_reviews: number | null;
  neutral_reviews: number | null;
  negative_reviews: number | null;
  mixed_reviews: number | null;
};

export type DashboardAnalyticsResponse = {
  summary: ReviewSummaryAggregate;
  country_breakdown: ReviewCountryBreakdownItem[];
  hotel_breakdown: ReviewHotelBreakdownItem[];
  score_buckets: ReviewScoreBucketItem[];
  daily_trend: ReviewDailyTrendItem[];
  supports_full_analytics: boolean;
  unsupported_filters: string[];
};

export type ReviewCategoryItem = {
  category_code: string | null;
  category_name: string;
  score: number | null;
  score_scale: number | null;
  display_order?: number | null;
  metadata?: Record<string, unknown>;
};

export type ReviewCategoryRawItem = {
  id?: string;
  name?: string;
  score?: number | null;
  raw_score?: number | null;
  score_scale?: number | null;
};

export type ReviewCategoryCurrentSummary = {
  hotel_id: string;
  hotel_name: string;
  platform_code: string;
  source_captured_at: string;
  categories: ReviewCategoryItem[];
  raw_payload?: {
    items?: ReviewCategoryRawItem[];
    categories_title?: string;
    provider?: string;
    [key: string]: unknown;
  };
  metadata?: Record<string, unknown>;
};

export type ReviewCategoryCurrentListResponse = {
  items: ReviewCategoryCurrentSummary[];
  total: number;
};
