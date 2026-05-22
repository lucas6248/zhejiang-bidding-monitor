"""招标雷达解析器."""

import re
from typing import List
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from scripts.parser_base import BaseParser
from scripts.models import BiddingItem


class ZhaobiaoCnParser(BaseParser):
    """zhaobiao.cn 解析器."""

    SEARCH_URL = "https://www.zhaobiao.cn/search"

    @property
    def platform_name(self) -> str:
        return "招标雷达"

    @property
    def platform_url(self) -> str:
        return "https://www.zhaobiao.cn"

    def search(self, keyword: str, max_pages: int = 3) -> List[BiddingItem]:
        items: List[BiddingItem] = []
        for page in range(1, max_pages + 1):
            params = {"keyword": keyword, "area": "浙江", "page": page}
            try:
                resp = self.fetcher.get(self.SEARCH_URL, params=params)
            except Exception:
                continue

            soup = BeautifulSoup(resp.text, "lxml")
            results = soup.select("div.result-item, li.search-result, div[class*='result']")
            if not results:
                break

            for r in results:
                link = r.find("a")
                if not link:
                    continue
                href = link.get("href", "")
                title = self.clean_text(link.get_text())
                if not title:
                    continue

                text = self.clean_text(r.get_text(" ", strip=True))
                m = re.search(r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})", text)
                publish_date = m.group(1).replace("年", "-").replace("月", "-").replace("/", "-").rstrip("日") if m else ""

                items.append(self.build_item(
                    project_name=title,
                    source_url=urljoin(self.platform_url, href) if not href.startswith("http") else href,
                    source_id=title,
                    publish_date=publish_date,
                ))
        return items
