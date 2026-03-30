from apify_client import ApifyClient
from backend.config import get_settings

_client: ApifyClient | None = None


def get_apify_client() -> ApifyClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = ApifyClient(settings.apify_token)
    return _client
