"""浙江政府采购网解析器."""

import re
from typing import List
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from scripts.parser_base import BaseParser
from scripts.models import BiddingItem

class ZjZfcgParser(BaseParser):
    """zfcg.czt.zj.gov.cn 解析器."""

    CATEGORY_URL = "https://zfcg.czt.zj.gov.cn/site/category"

    DISTRICT_CODES = {
        "339900": "省本级", "330100": "杭州", "330200": "宁波",
        "330300": "温州", "330400": "嘉兴", "330500": "湖州",
        "330600": "绍兴", "330700": "金华", "330800": "衢州",
        "330900": "舟山", "331000": "台州", "331100": "丽水",
    }

    @property
    def platform_name(self) -> str:
        return "浙江政府采购网"

    @property
    def platform_url(self) -> str:
        return "https://zfcg.czt.zj.gov.cn"

    def search(self, keyword: str, max_pages: int = 3) -> List[BiddingItem]:
        items: List[BiddingItem] = []
        for district_code, region_name in self.DISTRICT_CODES.items():
            for page in range(1, max_pages + 1):
                params = {
                    "isProvince": "false" if district_code != "339900" else "true",
                    "districtCode": district_code,
                    "parentId": "600233",
                    "pageNo": page,
                }
                try:
                    resp = self.fetcher.get(self.CATEGORY_URL, params=params)
                except Exception:
                    continue

                soup = BeautifulSoup(resp.text, "lxml")
                rows = soup.select("ul.list-content li, div.result-item, li.news-item")
                if not rows:
                    break

                for row in rows:
                    item = self._parse_row(row, region_name, keyword)
                    if item:
                        items.append(item)
        return items

    def _parse_row(self, row, region: str, keyword: str) -> BiddingItem | None:
        row_text = row.get_text(" ", strip=True)
        if not row_text or keyword not in row_text:
            return None
        link = row.find("a")
        if not link:
            return None
        href = link.get("href", "")
        title = self.clean_text(link.get_text() or link.get("title", ""))
        if not title:
            return None

        text = self.clean_text(row_text)
        publish_date = ""
        m = re.search(r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})", text)
        if m:
            publish_date = m.group(1).replace("年", "-").replace("月", "-").replace("/", "-").rstrip("日")

        source_id = ""
        m2 = re.search(r"articleId=([^&]+)", href)
        if m2:
            source_id = m2.group(1)

        return self.build_item(
            project_name=title,
            source_url=urljoin(self.platform_url, href) if not href.startswith("http") else href,
            source_id=source_id or title,
            publish_date=publish_date,
            region=region,
        )
