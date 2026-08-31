from typing import Protocol, runtime_checkable, Literal

from osint_nexus.core.type_defs import JSONValue

type ImpersonateProfile = Literal[
    "edge99",
    "edge101",
    "chrome99",
    "chrome100",
    "chrome101",
    "chrome104",
    "chrome107",
    "chrome110",
    "chrome116",
    "chrome119",
    "chrome120",
    "chrome123",
    "chrome124",
    "chrome131",
    "chrome133a",
    "chrome136",
    "chrome142",
    "chrome145",
    "chrome146",
    "chrome99_android",
    "chrome131_android",
    "safari153",
    "safari155",
    "safari170",
    "safari172_ios",
    "safari180",
    "safari180_ios",
    "safari184",
    "safari184_ios",
    "safari260",
    "safari2601",
    "safari260_ios",
    "firefox133",
    "firefox135",
    "firefox144",
    "firefox147",
    "tor145",
    "chrome",
    "edge",
    "safari",
    "safari_ios",
    "safari_beta",
    "safari_ios_beta",
    "chrome_android",
    "firefox",
    "safari15_3",
    "safari15_5",
    "safari17_0",
    "safari17_2_ios",
    "safari18_0",
    "safari18_0_ios",
    "safari18_4",
    "safari18_4_ios",
]


@runtime_checkable
class ResponseProtocol(Protocol):
    status_code: int

    @property
    def content(self) -> bytes: ...
    @property
    def text(self) -> str: ...
    def json(self) -> JSONValue: ...


@runtime_checkable
class SessionProtocol(Protocol):
    """Protocol for HTTP sessions to support both curl_cffi and httpx."""

    async def aclose(self) -> None: ...
    async def close(self) -> None: ...
    async def get(self, url: str, **kwargs: object) -> ResponseProtocol: ...
    async def post(self, url: str, **kwargs: object) -> ResponseProtocol: ...


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
