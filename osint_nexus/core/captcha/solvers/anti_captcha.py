from typing import Optional, Any, Dict
import time
import asyncio
import aiohttp
from osint_nexus.core.captcha.base import CaptchaSolver, CaptchaConfig, CaptchaSolveResult, CaptchaType, CaptchaServiceError, CaptchaTimeoutError

class AntiCaptchaSolver(CaptchaSolver):
    """Solver using Anti‑Captcha.com API."""

    BASE_URL = "https://api.anti-captcha.com"
    CREATE_TASK_URL = f"{BASE_URL}/createTask"
    GET_TASK_RESULT_URL = f"{BASE_URL}/getTaskResult"

    def __init__(
        self,
        config: CaptchaConfig,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        super().__init__("anti_captcha", config, session)
        if not config.anti_captcha_key:
            raise ValueError("Anti‑Captcha API key not set")

    async def health_check(self) -> bool:
        """Check balance via getBalance API."""
        url = f"{self.BASE_URL}/getBalance"
        payload = {"clientKey": self.config.anti_captcha_key}
        try:
            async with self._ensure_session().post(url, json=payload) as resp:
                data = await resp.json()
                balance = data.get("balance", 0)
                return balance > 0.01
        except Exception:  # pylint: disable=broad-except
            return False

    def estimate_cost(self, captcha_type: CaptchaType) -> float:
        """Anti‑Captcha prices (approx)."""
        pricing = {
            CaptchaType.RECAPTCHA_V2: 0.0009,
            CaptchaType.RECAPTCHA_V3: 0.0018,
            CaptchaType.HCAPTCHA: 0.0018,
            CaptchaType.TURNSTILE: 0.0027,
            CaptchaType.IMAGE_CAPTCHA: 0.0004,
            CaptchaType.CUSTOM: 0.004,
        }
        return pricing.get(captcha_type, 0.004)

    async def _solve_impl(
        self,
        site_key: str,
        url: str,
        captcha_type: CaptchaType,
        **kwargs: Any,
    ) -> CaptchaSolveResult:
        session = self._ensure_session()
        task_data = self._build_task_data(site_key, url, captcha_type, kwargs)

        # Create task
        payload = {
            "clientKey": self.config.anti_captcha_key,
            "task": task_data,
        }
        async with session.post(self.CREATE_TASK_URL, json=payload) as resp:
            data = await resp.json()
        if data.get("errorId") != 0:
            raise CaptchaServiceError(
                f"Task creation failed: {data.get('errorDescription', 'unknown')}"
            )
        task_id = data["taskId"]

        # Poll for result
        token = await self._poll_for_result(session, task_id)
        cost = self.estimate_cost(captcha_type)
        return CaptchaSolveResult(token=token, cost=cost, solver_name=self.name)

    def _build_task_data(
        self,
        site_key: str,
        url: str,
        captcha_type: CaptchaType,
        extra: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build the task data for Anti‑Captcha."""
        type_map = {
            CaptchaType.RECAPTCHA_V2: "NoCaptchaTaskProxyless",
            CaptchaType.RECAPTCHA_V3: "RecaptchaV3TaskProxyless",
            CaptchaType.HCAPTCHA: "HCaptchaTaskProxyless",
            CaptchaType.TURNSTILE: "TurnstileTaskProxyless",
        }
        task_type = type_map.get(captcha_type, "NoCaptchaTaskProxyless")
        task = {
            "type": task_type,
            "websiteURL": url,
        }
        if captcha_type == CaptchaType.RECAPTCHA_V2:
            task["websiteKey"] = site_key
        elif captcha_type == CaptchaType.RECAPTCHA_V3:
            task["websiteKey"] = site_key
            task["pageAction"] = extra.get("action", "verify")
            task["minScore"] = extra.get("min_score", 0.3)
        elif captcha_type == CaptchaType.HCAPTCHA:
            task["websiteKey"] = site_key
            task["data"] = extra.get("data_s", "")
        elif captcha_type == CaptchaType.TURNSTILE:
            task["websiteKey"] = site_key
        return task

    async def _poll_for_result(
        self, session: aiohttp.ClientSession, task_id: int
    ) -> str:
        """Poll Anti-Captcha until result is ready."""
        poll_payload = {
            "clientKey": self.config.anti_captcha_key,
            "taskId": task_id,
        }
        start_time = time.monotonic()
        while True:
            await asyncio.sleep(self.config.poll_interval)
            async with session.post(self.GET_TASK_RESULT_URL, json=poll_payload) as resp:
                data = await resp.json()
            
            token = self._handle_poll_response(data, start_time)
            if token:
                return token

    def _handle_poll_response(self, data: Dict[str, Any], start_time: float) -> Optional[str]:
        """Handle the poll response from Anti-Captcha."""
        if data.get("status") == "ready":
            solution = data["solution"]
            token = solution.get("gRecaptchaResponse") or solution.get("token")
            if token:
                return token
            raise CaptchaServiceError("No token in solution")
        
        if data.get("errorId") != 0:
            raise CaptchaServiceError(
                f"Polling error: {data.get('errorDescription')}"
            )
        if time.monotonic() - start_time > self.config.solve_timeout:
            raise CaptchaTimeoutError("Polling timed out")
        return None
