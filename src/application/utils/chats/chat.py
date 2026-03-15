import base64
import datetime
import uuid


def encode_chat_cursor(activity_at: datetime.datetime, chat_id: uuid.UUID) -> str:
    payload = f"{activity_at.isoformat()}|{chat_id}"
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8")


def decode_chat_cursor(cursor: str) -> tuple[datetime.datetime, uuid.UUID]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        activity_at_raw, chat_id_raw = raw.split("|", 1)
        return datetime.datetime.fromisoformat(activity_at_raw), uuid.UUID(chat_id_raw)
    except Exception as exc:  # pragma: no cover - invalid external input
        raise ValueError("Invalid cursor") from exc
