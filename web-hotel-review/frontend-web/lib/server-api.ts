const DEFAULT_API_BASE_URL = "http://localhost:3001/api";

export function getServerApiBaseUrl() {
  return (
    process.env.INTERNAL_API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    DEFAULT_API_BASE_URL
  );
}
