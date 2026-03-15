import base64
import hashlib
import hmac
import time

from fastapi import HTTPException


CHAT_SERVICE_SECRET = "dev-secret"


def sign_ws_ticket(user_id: str, ttl_seconds: int = 60) -> str:
    expires_at = int(time.time()) + ttl_seconds
    payload = f"{user_id}:{expires_at}"
    signature = hmac.new(
        CHAT_SERVICE_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}:{signature}".encode("utf-8")).decode("utf-8")


def verify_ws_ticket(ticket: str) -> str:
    try:
        decoded = base64.urlsafe_b64decode(ticket.encode("utf-8")).decode("utf-8")
        user_id, expires_at_raw, signature = decoded.split(":", 2)
    except Exception as exc:  # pragma: no cover - invalid external input
        raise HTTPException(status_code=401, detail="Invalid websocket ticket") from exc

    payload = f"{user_id}:{expires_at_raw}"
    expected = hmac.new(
        CHAT_SERVICE_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Invalid websocket ticket")
    if int(expires_at_raw) < int(time.time()):
        raise HTTPException(status_code=401, detail="Expired websocket ticket")

    return user_id
