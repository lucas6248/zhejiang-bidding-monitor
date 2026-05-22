"""HTTP 请求封装：UA 伪装、重试、超时."""

import time
import requests
from typing import Optional


class FetchError(Exception):
    """抓取失败异常."""
    pass


class Fetcher:
    """HTTP 请求客户端."""

    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 3

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
    }

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.timeout = timeout

    def get(self, url: str, params: Optional[dict] = None) -> requests.Response:
        """GET 请求（带重试）."""
        last_error = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
                resp.raise_for_status()
                resp.encoding = self._detect_encoding(resp)
                return resp
            except requests.RequestException as e:
                last_error = e
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY * attempt)
        raise FetchError(f"GET {url} failed after {self.MAX_RETRIES} retries: {last_error}")

    def post(self, url: str, data: Optional[dict] = None,
             json: Optional[dict] = None) -> requests.Response:
        """POST 请求（带重试）."""
        last_error = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                resp = self.session.post(
                    url, data=data, json=json, timeout=self.timeout
                )
                resp.raise_for_status()
                resp.encoding = self._detect_encoding(resp)
                return resp
            except requests.RequestException as e:
                last_error = e
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY * attempt)
        raise FetchError(f"POST {url} failed after {self.MAX_RETRIES} retries: {last_error}")

    @staticmethod
    def _detect_encoding(resp: requests.Response) -> str:
        """自动检测编码，优先识别 GBK/UTF-8."""
        if resp.encoding and resp.encoding.lower() != "iso-8859-1":
            return resp.encoding
        content = resp.content[:1024]
        if b"charset=gb" in content.lower() or b"charset=gbk" in content.lower():
            return "gbk"
        if b"charset=utf-8" in content.lower() or b"charset=utf8" in content.lower():
            return "utf-8"
        return resp.apparent_encoding or "utf-8"
