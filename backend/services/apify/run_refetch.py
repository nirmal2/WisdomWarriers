from datetime import datetime
from typing import Any, TypedDict

from backend.services.apify.client import get_apify_client


class ApifyRunMetadata(TypedDict, total=False):
    run_id: str
    dataset_id: str
    status: str
    started_at: datetime | None
    finished_at: datetime | None


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def refetch_apify_run_output(
    apify_run_id: str,
    dataset_id: str,
    apify_token: str | None = None,
) -> tuple[list[dict[str, Any]], list[str], ApifyRunMetadata]:
    client = get_apify_client(apify_token)
    run = client.run(apify_run_id).get() or {}
    items = list(client.dataset(dataset_id).iterate_items())

    logs: list[str] = []
    try:
        log_content = client.run(apify_run_id).log().get()
        logs = [line.strip() for line in log_content.split("\n") if line.strip()]
    except Exception:
        pass

    metadata: ApifyRunMetadata = {
        "run_id": str(run.get("id") or apify_run_id),
        "dataset_id": str(run.get("defaultDatasetId") or dataset_id),
        "status": str(run.get("status") or ""),
        "started_at": _parse_datetime(run.get("startedAt")),
        "finished_at": _parse_datetime(run.get("finishedAt")),
    }

    return items, logs, metadata
