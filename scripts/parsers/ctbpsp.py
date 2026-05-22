"""中国招标投标公共服务平台解析器."""

import json
from typing import List
from scripts.parser_base import BaseParser
from scripts.models import BiddingItem


class CtbpspParser(BaseParser):
    """ctbpsp.com 解析器 - 前端 Vue SPA, 通过后端 API 获取数据."""

    API_URL = "http://www.cebpubservice.com/ctpsp_iiss/searchbusinesstypebeforedooraction/getSearch.do"

    @property
    def platform_name(self) -> str:
        return "中国招标投标公共服务平台"

    @property
    def platform_url(self) -> str:
        return "https://ctbpsp.com"

    def search(self, keyword: str, max_pages: int = 3) -> List[BiddingItem]:
        items: List[BiddingItem] = []
        for page in range(1, max_pages + 1):
            params = {"keyWords": keyword, "pageNum": page, "pageSize": 20, "area": "浙江"}
            try:
                resp = self.fetcher.post(self.API_URL, data=params)
                data = resp.json()
            except (json.JSONDecodeError, Exception):
                continue

            results = data.get("data", {}).get("list", []) if isinstance(data, dict) else []
            if not results:
                break

            for row in results:
                item = self._parse_row(row)
                if item:
                    items.append(item)
            if len(results) < 20:
                break
        return items

    def _parse_row(self, row: dict) -> BiddingItem | None:
        title = self.clean_text(row.get("bulletinTitle", "") or row.get("title", ""))
        if not title:
            return None
        source_id = row.get("bulletinId", "") or row.get("id", "") or title
        publish_date = row.get("publishTime", "") or row.get("publishDate", "")
        if publish_date:
            publish_date = publish_date[:10].replace("/", "-")
        href = row.get("url", "") or row.get("bulletinUrl", "")

        region = "浙江"
        cities = ["杭州", "宁波", "温州", "嘉兴", "湖州", "绍兴", "金华", "衢州", "舟山", "台州", "丽水"]
        for city in cities:
            if city in title:
                region = city
                break

        return self.build_item(
            project_name=title,
            source_url=href if href.startswith("http") else f"https://ctbpsp.com{href}",
            source_id=str(source_id),
            publish_date=publish_date,
            region=region,
        )
