from app.services.platforms.agoda import AgodaReviewMapper
from app.services.platforms.base import BaseReviewMapper
from app.services.platforms.booking import BookingReviewMapper
from app.services.platforms.google import GoogleReviewMapper
from app.services.platforms.tripadvisor import TripadvisorReviewMapper

PLATFORM_MAPPERS: dict[str, type[BaseReviewMapper]] = {
    "booking": BookingReviewMapper,
    "agoda": AgodaReviewMapper,
    "tripadvisor": TripadvisorReviewMapper,
    "google": GoogleReviewMapper,
}


def get_review_mapper(platform_code: str) -> BaseReviewMapper:
    mapper_cls = PLATFORM_MAPPERS.get(platform_code)
    if mapper_cls is None:
        raise ValueError(f"Unsupported platform: {platform_code}")
    return mapper_cls()
