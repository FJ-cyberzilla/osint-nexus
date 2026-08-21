from typing import Any, Protocol, runtime_checkable

from osint_nexus.core.type_defs import JSONValue


@runtime_checkable
class ResponseProtocol(Protocol):
    status_code: int

    @property
    def content(self) -> bytes: ...
    @property
    def text(self) -> str: ...
    def json(self) -> JSONValue: ...


...


@runtime_checkable
class SessionProtocol(Protocol):
    """Protocol for HTTP sessions to support both curl_cffi and httpx."""

    async def aclose(self) -> None: ...
    async def close(self) -> None: ...
    async def get(self, url: str, **kwargs: Any) -> ResponseProtocol: ...
    async def post(self, url: str, **kwargs: Any) -> ResponseProtocol: ...


HAS_CURL_CFFI = False
NETWORK_EXCEPTION: type[Exception]

try:
    import curl_cffi.requests as curl_requests

    HAS_CURL_CFFI = True
    NETWORK_EXCEPTION = curl_requests.RequestsError
except ImportError:
    try:
        import httpx

        NETWORK_EXCEPTION = httpx.HTTPError
    except ImportError:
        # Optional dependency fallback: if neither backend is installed,
        # keep NETWORK_EXCEPTION as the default Exception.
        NETWORK_EXCEPTION = Exception
