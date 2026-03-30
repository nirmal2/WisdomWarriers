from typing import Any
from backend.services.apify.client import get_apify_client
from backend.config import get_settings


def _prepare_usernames(usernames: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in usernames:
        username = (item or "").strip().lstrip("@")
        if not username:
            continue
        key = username.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(username)
    return cleaned


def run_posts_actor(
    usernames: list[str],
    results_limit: int = 100,
    only_posts_newer_than: str | None = None,
    data_detail_level: str = "basicData",
) -> tuple[list[dict[str, Any]], list[str]]:
    settings = get_settings()
    client = get_apify_client()
    prepared_usernames = _prepare_usernames(usernames)
    effective_results_limit = max(results_limit, len(prepared_usernames))
    run_input: dict[str, Any] = {
        "username": prepared_usernames,
        "resultsLimit": effective_results_limit,
        "skipPinnedPosts": True,
        "dataDetailLevel": data_detail_level,
    }
    if only_posts_newer_than:
        value = only_posts_newer_than.strip()
        run_input["onlyPostsNewerThan"] = value if "day" in value.lower() else f"{value} days"

    run = client.actor(settings.apify_posts_actor_id).call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    
    # Capture logs from the run
    logs = []
    try:
        log_content = client.run(run["id"]).log().get()
        # Split log content into lines for better display
        logs = [line.strip() for line in log_content.split('\n') if line.strip()]
    except Exception:
        pass  # If log retrieval fails, just skip it
    
    return items, logs
