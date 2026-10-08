import hashlib
import json
from typing import Any, Optional
from fastapi import Request, Response, status


def generate_etag(data: Any) -> str:
    """
    Generate an ETag hash from arbitrary serializable data or string.
    """
    if isinstance(data, (dict, list)):
        payload = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
    elif isinstance(data, str):
        payload = data.encode("utf-8")
    elif isinstance(data, bytes):
        payload = data
    else:
        payload = str(data).encode("utf-8")

    digest = hashlib.sha256(payload).hexdigest()[:16]
    return f'"{digest}"'


def verify_etag_and_respond(request: Request, etag: str, response: Response) -> Optional[Response]:
    """
    Check the If-None-Match header against the computed ETag.
    If they match, return an HTTP 304 Not Modified response.
    Otherwise, set the ETag header on the outgoing response.
    """
    response.headers["ETag"] = etag
    if_none_match = request.headers.get("if-none-match")
    if if_none_match:
        # Client may send comma-separated list of etags or quoted string
        client_etags = [tag.strip() for tag in if_none_match.split(",")]
        if etag in client_etags or "*" in client_etags:
            return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers={"ETag": etag})
    return None
