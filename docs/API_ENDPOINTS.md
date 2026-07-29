# API Endpoints

Tai lieu nay duoc sinh tu code route FastAPI trong repo nay.
Nguon su that la code; khi route doi, hay sinh lai file nay.

| Method | Path | Handler | Response | Tags |
| --- | --- | --- | --- | --- |
| GET | `/` | `app.main.root` | `-` | - |
| POST | `/api/v1/exports/google-sheets/reviews` | `app.api.routes.google_sheets.export_reviews_to_google_sheets` | `GoogleSheetsExportResponse` | google-sheets |
| POST | `/api/v1/exports/google-sheets/reviews/async` | `app.api.routes.google_sheets.export_reviews_to_google_sheets_async` | `GoogleSheetsExportAcceptedResponse` | google-sheets |
| GET | `/api/v1/hotels` | `app.api.routes.hotels.list_hotels` | `HotelListResponse` | hotels |
| POST | `/api/v1/hotels` | `app.api.routes.hotels.create_hotel` | `HotelResponse` | hotels |
| GET | `/api/v1/incidents` | `app.api.routes.incidents.list_incidents` | `IncidentListResponse` | incidents |
| POST | `/api/v1/notifications/deliveries` | `app.api.routes.notifications.upsert_notification_delivery` | `NotificationDeliveryUpsertResponse` | notifications |
| GET | `/api/v1/review-categories/current` | `app.api.routes.review_categories.list_current_review_categories` | `ReviewCategoryCurrentListResponse` | review-categories |
| GET | `/api/v1/review-metrics/current` | `app.api.routes.review_metrics.list_current_review_metrics` | `ReviewMetricListResponse` | review-metrics |
| GET | `/api/v1/reviews` | `app.api.routes.reviews.list_reviews` | `ReviewListResponse` | reviews |
| GET | `/api/v1/reviews/bad` | `app.api.routes.reviews.list_bad_reviews` | `ReviewListResponse` | reviews |
| GET | `/api/v1/reviews/bad/unnotified` | `app.api.routes.notifications.list_unnotified_bad_reviews` | `UnnotifiedBadReviewListResponse` | notifications |
| GET | `/api/v1/reviews/country-breakdown` | `app.api.routes.review_analytics.get_country_breakdown` | `ReviewCountryBreakdownResponse` | review-analytics |
| GET | `/api/v1/reviews/daily-trend` | `app.api.routes.review_analytics.get_daily_trend` | `ReviewDailyTrendResponse` | review-analytics |
| GET | `/api/v1/reviews/hotel-breakdown` | `app.api.routes.review_analytics.get_hotel_breakdown` | `ReviewHotelBreakdownResponse` | review-analytics |
| GET | `/api/v1/reviews/score-buckets` | `app.api.routes.review_analytics.get_score_buckets` | `ReviewScoreBucketsResponse` | review-analytics |
| GET | `/api/v1/reviews/stats` | `app.api.routes.reviews.list_review_stats` | `ReviewStatsListResponse` | reviews |
| GET | `/api/v1/reviews/summary` | `app.api.routes.review_analytics.get_review_summary` | `ReviewSummaryAggregateResponse` | review-analytics |
| POST | `/api/v1/sync/reviews/{platform_code}` | `app.api.routes.sync.sync_reviews` | `SyncReviewsResponse` | sync |
| GET | `/api/v1/system/backup/config` | `app.api.routes.system.get_backup_config` | `BackupConfigResponse` | system |
| POST | `/api/v1/system/backup/run` | `app.api.routes.system.run_backup` | `BackupRunResponse` | system |
| POST | `/api/v1/system/hotels` | `app.api.routes.system.create_admin_hotel` | `HotelResponse` | system |
| POST | `/api/v1/system/hotels/purge` | `app.api.routes.system.purge_hotels` | `HotelPurgeResponse` | system |
| POST | `/api/v1/system/hotels/reset-import` | `app.api.routes.system.reset_and_import_hotels` | `HotelResetImportResponse` | system |
| POST | `/api/v1/system/hotels/reset-import/default-manifest` | `app.api.routes.system.reset_and_import_default_manifest` | `HotelResetImportResponse` | system |
| DELETE | `/api/v1/system/hotels/{hotel_id}` | `app.api.routes.system.delete_admin_hotel` | `HotelDeleteResponse` | system |
| PUT | `/api/v1/system/hotels/{hotel_id}` | `app.api.routes.system.update_admin_hotel` | `HotelResponse` | system |
| GET | `/health` | `app.api.routes.health.healthcheck` | `-` | health |
| GET | `/version` | `app.api.routes.health.version` | `-` | health |

## Endpoint Details

### `GET /`

- Handler: `app.main.root`
- Response: `-`
- Tags: -
- Query params: -
- Path params: -
- Body params: -

### `POST /api/v1/exports/google-sheets/reviews`

- Handler: `app.api.routes.google_sheets.export_reviews_to_google_sheets`
- Response: `GoogleSheetsExportResponse`
- Tags: google-sheets
- Query params: -
- Path params: -
- Body params: -

### `POST /api/v1/exports/google-sheets/reviews/async`

- Handler: `app.api.routes.google_sheets.export_reviews_to_google_sheets_async`
- Response: `GoogleSheetsExportAcceptedResponse`
- Tags: google-sheets
- Query params: -
- Path params: -
- Body params: -

### `GET /api/v1/hotels`

- Handler: `app.api.routes.hotels.list_hotels`
- Response: `HotelListResponse`
- Tags: hotels
- Query params: q, status, limit, offset
- Path params: -
- Body params: -

### `POST /api/v1/hotels`

Trang thai hien tai:

- public create hotel da bi khoa
- endpoint nay tra `403 Forbidden`
- hotel moi chi duoc tao qua admin/system flow

- Handler: `app.api.routes.hotels.create_hotel`
- Response: `HotelResponse`
- Tags: hotels
- Query params: -
- Path params: -
- Body params: -

### `GET /api/v1/incidents`

- Handler: `app.api.routes.incidents.list_incidents`
- Response: `IncidentListResponse`
- Tags: incidents
- Query params: hotel_id, status, severity, limit, offset
- Path params: -
- Body params: -

### `POST /api/v1/notifications/deliveries`

- Handler: `app.api.routes.notifications.upsert_notification_delivery`
- Response: `NotificationDeliveryUpsertResponse`
- Tags: notifications
- Query params: -
- Path params: -
- Body params: -

### `GET /api/v1/review-categories/current`

- Handler: `app.api.routes.review_categories.list_current_review_categories`
- Response: `ReviewCategoryCurrentListResponse`
- Tags: review-categories
- Query params: hotel_id, platform_code
- Path params: -
- Body params: -

### `GET /api/v1/review-metrics/current`

- Handler: `app.api.routes.review_metrics.list_current_review_metrics`
- Response: `ReviewMetricListResponse`
- Tags: review-metrics
- Query params: hotel_id, platform_code
- Path params: -
- Body params: -

### `GET /api/v1/reviews`

- Handler: `app.api.routes.reviews.list_reviews`
- Response: `ReviewListResponse`
- Tags: reviews
- Query params: hotel_id, platform_code, is_bad_review, reviewer_country_code, rating_min, rating_max, date_from, date_to, q, sort_by, sort_order, limit, offset, hydrate_missing_translations
- Path params: -
- Body params: -

### `GET /api/v1/reviews/bad`

- Handler: `app.api.routes.reviews.list_bad_reviews`
- Response: `ReviewListResponse`
- Tags: reviews
- Query params: hotel_id, platform_code, reviewer_country_code, rating_min, rating_max, date_from, date_to, q, sort_by, sort_order, limit, offset, hydrate_missing_translations
- Path params: -
- Body params: -

### `GET /api/v1/reviews/bad/unnotified`

- Handler: `app.api.routes.notifications.list_unnotified_bad_reviews`
- Response: `UnnotifiedBadReviewListResponse`
- Tags: notifications
- Query params: channel_code, event_type, hotel_id, platform_code, limit, offset
- Path params: -
- Body params: -

### `GET /api/v1/reviews/country-breakdown`

- Handler: `app.api.routes.review_analytics.get_country_breakdown`
- Response: `ReviewCountryBreakdownResponse`
- Tags: review-analytics
- Query params: hotel_id, platform_code, date_from, date_to, limit
- Path params: -
- Body params: -

### `GET /api/v1/reviews/daily-trend`

- Handler: `app.api.routes.review_analytics.get_daily_trend`
- Response: `ReviewDailyTrendResponse`
- Tags: review-analytics
- Query params: hotel_id, platform_code, date_from, date_to
- Path params: -
- Body params: -

### `GET /api/v1/reviews/hotel-breakdown`

- Handler: `app.api.routes.review_analytics.get_hotel_breakdown`
- Response: `ReviewHotelBreakdownResponse`
- Tags: review-analytics
- Query params: platform_code, date_from, date_to, sort_by, sort_order, limit
- Path params: -
- Body params: -

### `GET /api/v1/reviews/score-buckets`

- Handler: `app.api.routes.review_analytics.get_score_buckets`
- Response: `ReviewScoreBucketsResponse`
- Tags: review-analytics
- Query params: hotel_id, platform_code, reviewer_country_code, date_from, date_to
- Path params: -
- Body params: -

### `GET /api/v1/reviews/stats`

- Handler: `app.api.routes.reviews.list_review_stats`
- Response: `ReviewStatsListResponse`
- Tags: reviews
- Query params: hotel_id, platform_code
- Path params: -
- Body params: -

### `GET /api/v1/reviews/summary`

- Handler: `app.api.routes.review_analytics.get_review_summary`
- Response: `ReviewSummaryAggregateResponse`
- Tags: review-analytics
- Query params: hotel_id, platform_code, reviewer_country_code, date_from, date_to
- Path params: -
- Body params: -

### `POST /api/v1/sync/reviews/{platform_code}`

- Handler: `app.api.routes.sync.sync_reviews`
- Response: `SyncReviewsResponse`
- Tags: sync
- Query params: -
- Path params: platform_code
- Body params: -

### `GET /api/v1/system/backup/config`

- Handler: `app.api.routes.system.get_backup_config`
- Response: `BackupConfigResponse`
- Tags: system
- Query params: -
- Path params: -
- Body params: -

### `POST /api/v1/system/backup/run`

- Handler: `app.api.routes.system.run_backup`
- Response: `BackupRunResponse`
- Tags: system
- Query params: -
- Path params: -
- Body params: payload

### `POST /api/v1/system/hotels`

- Handler: `app.api.routes.system.create_admin_hotel`
- Response: `HotelResponse`
- Tags: system
- Query params: -
- Path params: -
- Body params: -

### `POST /api/v1/system/hotels/purge`

- Handler: `app.api.routes.system.purge_hotels`
- Response: `HotelPurgeResponse`
- Tags: system
- Query params: -
- Path params: -
- Body params: -

### `POST /api/v1/system/hotels/reset-import`

- Handler: `app.api.routes.system.reset_and_import_hotels`
- Response: `HotelResetImportResponse`
- Tags: system
- Query params: -
- Path params: -
- Body params: -

### `POST /api/v1/system/hotels/reset-import/default-manifest`

- Handler: `app.api.routes.system.reset_and_import_default_manifest`
- Response: `HotelResetImportResponse`
- Tags: system
- Query params: -
- Path params: -
- Body params: -

### `DELETE /api/v1/system/hotels/{hotel_id}`

- Handler: `app.api.routes.system.delete_admin_hotel`
- Response: `HotelDeleteResponse`
- Tags: system
- Query params: -
- Path params: hotel_id
- Body params: -

### `PUT /api/v1/system/hotels/{hotel_id}`

- Handler: `app.api.routes.system.update_admin_hotel`
- Response: `HotelResponse`
- Tags: system
- Query params: -
- Path params: hotel_id
- Body params: -

### `GET /health`

- Handler: `app.api.routes.health.healthcheck`
- Response: `-`
- Tags: health
- Query params: -
- Path params: -
- Body params: -

### `GET /version`

- Handler: `app.api.routes.health.version`
- Response: `-`
- Tags: health
- Query params: -
- Path params: -
- Body params: -
