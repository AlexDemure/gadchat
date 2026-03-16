import base64
import json
import typing


class Cursor:
    @classmethod
    def encode(cls, payload: dict[str, typing.Any]) -> str:
        raw = json.dumps(payload, separators=(",", ":"))
        return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")

    @classmethod
    def decode(cls, cursor: str) -> dict[str, typing.Any]:
        try:
            raw = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
            return typing.cast(dict[str, typing.Any], json.loads(raw))
        except Exception as exc:
            raise ValueError("Invalid cursor") from exc
