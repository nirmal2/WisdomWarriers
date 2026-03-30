from typing import Any
from backend.services.apify.client import get_apify_client
from backend.config import get_settings


def run_profiles_actor(usernames: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    settings = get_settings()
    client = get_apify_client()
    run_input: dict[str, Any] = {
        "usernames": usernames,
        "includeAboutSection": False,
    }
    run = client.actor(settings.apify_profiles_actor_id).call(run_input=run_input)
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
