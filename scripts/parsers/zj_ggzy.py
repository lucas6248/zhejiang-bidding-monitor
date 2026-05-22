"""浙江省公共资源交易服务平台解析器."""

import re
from typing import List
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from scripts.parser_base import BaseParser, ParseError
from scripts.models import BiddingItem


class ZjGgzyParser(BaseParser):
    """ggzy.zj.gov.cn 解析器 - 全省 11 地市统一平台."""

    SEARCH_URL = "https://ggzy.zj.gov.cn/jyxx/search.html"
    CITIES = ["杭州", "宁波", "温州", "嘉兴", "湖州", "绍兴",
              "金华", "衢州", "舟山", "台州", "丽水"]

    @property
    def platform_name(self) -> str:
        return "浙江省公共资源交易服务平台"

    @property
    def platform_url(self) -> str:
        return "https://ggzy.zj.gov.cn"

    def search(self, keyword: str, max_pages: int = 3) -> List[BiddingItem]:
        items: List[BiddingItem] = []
        for page in range(1, max_pages + 1):
            try:
                resp = self.fetcher.get(self.SEARCH_URL, params={
                    "keyword": keyword, "pageNo": page, "pageSize": 20,
                })
            except Exception:
                resp = self._try_post_search(keyword, page)

            soup = BeautifulSoup(resp.text, "lxml")
            rows = self._extract_rows(soup)
            if not rows:
                break

            for row in rows:
                item = self._parse_row(row)
                if item:
                    items.append(item)
            if len(rows) < 20:
                break
        return items

    def _try_post_search(self, keyword: str, page: int):
        urls = [
            "https://ggzy.zj.gov.cn/rest/notice/search",
            "https://ggzy.zj.gov.cn/api/tradeinfo/list",
        ]
        payload = {"keyword": keyword, "pageNum": page, "pageSize": 20, "ggType": "zbgg"}
        for url in urls:
            try:
                return self.fetcher.post(url, json=payload)
            except Exception:
                continue
        raise ParseError("所有搜索方式均失败")

    def _extract_rows(self, soup: BeautifulSoup) -> list:
        selectors = [
            "ul.list-content li", "div.search-result li",
            "table.result-table tbody tr", "div.news-list ul li",
            "div.notice-list li", "li[class*='list']",
        ]
        for sel in selectors:
            rows = soup.select(sel)
            if rows:
                return rows
        return []

    def _parse_row(self, row) -> BiddingItem | None:
        row_text = row.get_text(" ", strip=True)
        if not row_text or len(row_text) < 10:
            return None
        link = row.find("a")
        if not link:
            return None
        href = link.get("href", "")
        title = self.clean_text(link.get_text() or link.get("title", ""))
        if not title:
            return None

        text = self.clean_text(row_text)
        return self.build_item(
            project_name=title,
            source_url=urljoin(self.platform_url, href) if not href.startswith("http") else href,
            source_id=self._extract_id(href) or title,
            publish_date=self._extract_date(text),
            deadline=self._extract_deadline(text),
            budget=self._extract_budget(text),
            region=self._extract_region(text, title),
        )

    @staticmethod
    def _extract_date(text: str) -> str:
        m = re.search(r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})", text)
        if m:
            return m.group(1).replace("年", "-").replace("月", "-").replace("/", "-").rstrip("日")
        return ""

    @staticmethod
    def _extract_deadline(text: str) -> str:
        for pat in [r"截止[时间日].*?(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})",
                     r"投标.*?截止.*?(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})"]:
            m = re.search(pat, text)
            if m:
                d = m.group(1)
                return d.replace("年", "-").replace("月", "-").replace("/", "-").rstrip("日")
        return ""

    @staticmethod
    def _extract_budget(text: str) -> str:
        for pat in [r"预算[金金额价].*?(\d+\.?\d*)\s*万元",
                     r"控制价.*?(\d+\.?\d*)\s*万元"]:
            m = re.search(pat, text)
            if m:
                return f"{m.group(1)}万元"
        return ""

    def _extract_region(self, text: str, title: str) -> str:
        combined = title + text
        for city in self.CITIES:
            if city in combined:
                return city
        return ""

    @staticmethod
    def _extract_id(href: str) -> str:
        for pat in [r"[?&]id=([^&]+)", r"articleId=([^&]+)", r"/([a-f0-9]{32})"]:
            m = re.search(pat, href)
            if m:
                return m.group(1)
        return ""
