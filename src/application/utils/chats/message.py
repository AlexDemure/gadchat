import base64
import datetime
import hashlib
import uuid


def compute_shard_key(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:15], 16)


def encode_message_cursor(created: datetime.datetime, message_id: uuid.UUID) -> str:
    payload = f"{created.isoformat()}|{message_id}"
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8")


def decode_message_cursor(cursor: str) -> tuple[datetime.datetime, uuid.UUID]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        created_raw, message_id_raw = raw.split("|", 1)
        return datetime.datetime.fromisoformat(created_raw), uuid.UUID(message_id_raw)
    except Exception as exc:  # pragma: no cover - invalid external input
        raise ValueError("Invalid cursor") from exc


def parse_ingest_event(event: dict[str, object]) -> dict[str, object]:
    sender_id = event.get("sender_id")
    if not isinstance(sender_id, str):
        raise ValueError("sender_id is required")

    attachments_raw = event.get("attachments")
    attachments = (
        [item for item in attachments_raw if isinstance(item, dict)] if isinstance(attachments_raw, list) else []
    )

    return {
        "sender_id": sender_id,
        "body": event.get("body", "") if isinstance(event.get("body", ""), str) else "",
        "attachments": attachments,
        "chat_id": uuid.UUID(chat_id) if isinstance((chat_id := event.get("chat_id")), str) else None,
        "peer_user_id": event.get("peer_user_id") if isinstance(event.get("peer_user_id"), str) else None,
    }
