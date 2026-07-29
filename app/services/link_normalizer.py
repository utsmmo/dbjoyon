from urllib.parse import urlsplit, urlunsplit


def normalize_source_link(platform_code: str, url: str) -> str:
    cleaned = url.strip()
    if not cleaned:
        return cleaned

    parts = urlsplit(cleaned)
    base = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))

    if platform_code == "agoda":
        return base

    return cleaned


def normalize_source_links(links: dict[str, list[str]]) -> dict[str, list[str]]:
    normalized: dict[str, list[str]] = {}

    for platform_code, raw_links in links.items():
        cleaned_links: list[str] = []
        seen: set[str] = set()

        for raw_link in raw_links:
            normalized_link = normalize_source_link(platform_code, raw_link)
            if not normalized_link or normalized_link in seen:
                continue
            seen.add(normalized_link)
            cleaned_links.append(normalized_link)

        if cleaned_links:
            normalized[platform_code] = cleaned_links

    return normalized
