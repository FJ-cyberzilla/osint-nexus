import asyncio
import time
from typing import Any

import aiohttp

from osint_nexus.core.captcha.base import (
    CaptchaConfig,
    CaptchaServiceError,
    CaptchaSolver,
    CaptchaSolveResult,
    CaptchaTimeoutError,
    CaptchaType,
)
from osint_nexus.core.config import get_config


class TwoCaptchaSolver(CaptchaSolver):
    """Solver using 2Captcha.com API."""

    def __init__(
        self,
        config: CaptchaConfig,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        super().__init__("2captcha", config, session)
        if not config.two_captcha_key:
            raise ValueError("2Captcha API key not set")
        service_urls = get_config().service_urls
        self.base_url = service_urls["two_captcha"]
        self.poll_url = service_urls["two_captcha_res"]

    async def health_check(self) -> bool:
        """Check balance via getBalance API."""
        url = f"{self.base_url}/res.php"
        # Cast values to str to be compatible with aiohttp.ClientSession.get params requirements
        params: dict[str, str] = {
            "key": str(self.config.two_captcha_key),
            "action": "getbalance",
            "json": "1",
        }
        try:
            async with self._ensure_session().get(url, params=params) as resp:
                data = await resp.json()
                balance = float(data.get("balance", 0))
                return balance > 0.01
        except Exception:  # pylint: disable=broad-except
            return False

    def estimate_cost(self, captcha_type: CaptchaType) -> float:
        """Prices from 2captcha (approximate)."""
        pricing = {
            CaptchaType.RECAPTCHA_V2: 0.001,
            CaptchaType.RECAPTCHA_V3: 0.002,
            CaptchaType.HCAPTCHA: 0.002,
            CaptchaType.TURNSTILE: 0.003,
            CaptchaType.IMAGE_CAPTCHA: 0.0005,
            CaptchaType.CUSTOM: 0.005,
        }
        return pricing.get(captcha_type, 0.005)

    async def _solve_impl(
        self,
        site_key: str,
        url: str,
        captcha_type: CaptchaType,
        **kwargs: Any,
    ) -> CaptchaSolveResult:
        session = self._ensure_session()
        method = self._get_method(captcha_type)
        submit_params = self._build_submit_params(site_key, url, captcha_type, method, kwargs)

        # 1. Submit captcha
        submit_url = f"{self.base_url}/in.php"
        async with session.post(submit_url, data=submit_params) as resp:
            data = await resp.json()
        if data.get("status") != 1:
            raise CaptchaServiceError(f"Submission failed: {data.get('request', 'unknown error')}")
        captcha_id = data["request"]

        # 2. Poll for result
        token = await self._poll_for_result(session, captcha_id)
        cost = self.estimate_cost(captcha_type)
        return CaptchaSolveResult(token=token, cost=cost, solver_name=self.name)

    def _get_method(self, captcha_type: CaptchaType) -> str:
        """Map captcha type to 2captcha method."""
        mapping = {
            CaptchaType.RECAPTCHA_V2: "userrecaptcha",
            CaptchaType.RECAPTCHA_V3: "userrecaptcha",
            CaptchaType.HCAPTCHA: "hcaptcha",
            CaptchaType.TURNSTILE: "turnstile",
            CaptchaType.IMAGE_CAPTCHA: "base64",
        }
        return mapping.get(captcha_type, "userrecaptcha")

    def _build_submit_params(
        self,
        site_key: str,
        url: str,
        captcha_type: CaptchaType,
        method: str,
        extra: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the submit payload for 2captcha."""
        params = {
            "key": self.config.two_captcha_key,
            "method": method,
            "googlekey": site_key,
            "pageurl": url,
            "json": 1,
        }
        if captcha_type == CaptchaType.RECAPTCHA_V3:
            params["version"] = "v3"
            params["action"] = extra.get("action", "verify")
        elif captcha_type == CaptchaType.HCAPTCHA:
            params["data-s"] = extra.get("data_s", "")
        elif captcha_type == CaptchaType.TURNSTILE:
            params["sitekey"] = site_key
        return params

    async def _poll_for_result(self, session: aiohttp.ClientSession, captcha_id: str) -> str:
        """Poll 2captcha until result is ready."""
        poll_params: dict[str, str] = {
            "key": str(self.config.two_captcha_key),
            "action": "get",
            "id": captcha_id,
            "json": "1",
        }
        start_time = time.monotonic()
        while True:
            await asyncio.sleep(self.config.poll_interval)
            async with session.get(self.poll_url, params=poll_params) as resp:
                data = await resp.json()

            result = self._handle_poll_response(data, start_time)
            if result:
                return result

    def _handle_poll_response(self, data: dict[str, Any], start_time: float) -> str | None:
        """Handle the poll response from 2captcha."""
        if data.get("status") == 1:
            return str(data["request"])
        if data.get("request") == "CAPCHA_NOT_READY":
            return None
        if "ERROR" in data.get("request", ""):
            raise CaptchaServiceError(f"Solving error: {str(data['request'])}")
        if time.monotonic() - start_time > self.config.solve_timeout:
            raise CaptchaTimeoutError("Polling timed out")
        # logger.warning("Unexpected poll response: %s", data) # logger needs to be imported or handled
        return None
