"""通过 Bing Search API 发现招投标公告链接."""
import os
import re
import requests
from typing import List, Optional
from urllib.parse import urlparse, parse_qs
from scripts.models import BiddingItem

BING_API_URL = "https://api.bing.microsoft.com/v7.0/search"
ZHEJIANG_CITIES = [
    "杭州", "宁波", "温州", "嘉兴", "湖州", "绍兴",
    "金华", "衢州", "舟山", "台州", "丽水",
]

PLATFORM_DOMAINS = {
    "ggzy.zj.gov.cn": "浙江省公共资源交易服务平台",
    "zfcg.czt.zj.gov.cn": "浙江政府采购网",
    "ctbpsp.com": "中国招标投标公共服务平台",
    "cebpubservice.com": "中国招标投标公共服务平台",
    "qianlima.com": "千里马招标网",
    "zhaobiao.cn": "招标雷达",
    "qzygjy.com": "衢州市阳光交易服务平台",
    "lecaiyun.com": "乐采云平台",
    "z7cai.com": "浙企采综合采购服务平台",
    "tzpre.com": "台州市产权交易所",
    "sz-water.com.cn": "深圳阳光采购平台",
    "jxtb.org.cn": "江西招标网",
    "gov.cn": "政府采购平台",
}


def _get_platform_name(url: str) -> str:
    for domain, name in PLATFORM_DOMAINS.items():
        if domain in url:
            return name
    return urlparse(url).netloc


class SearchDiscovery:
    """通过 Bing 搜索 API 发现招投标公告."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("BING_API_KEY", "")
        if not self.api_key:
            raise ValueError("BING_API_KEY is required")

    def discover(self, keyword: str = "球墨铸铁管") -> List[dict]:
        """搜索并返回发现的公告列表."""
        all_results: List[dict] = []
        seen_urls = set()

        for city in ZHEJIANG_CITIES:
            query = f"{keyword} 招标 {city}"
            results = self._search(query)
            for r in results:
                url = r.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    r["query_city"] = city
                    all_results.append(r)

        query = f"{keyword} 招标 浙江"
        results = self._search(query)
        for r in results:
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                r["query_city"] = "浙江"
                all_results.append(r)

        return all_results

    def _search(self, query: str, count: int = 15) -> List[dict]:
        params = {"q": query, "count": count, "mkt": "zh-CN", "freshness": "Week"}
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        try:
            resp = requests.get(BING_API_URL, headers=headers, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("webPages", {}).get("value", []):
                results.append({
                    "url": item.get("url", ""),
                    "title": item.get("name", ""),
                    "snippet": item.get("snippet", ""),
                    "date_published": item.get("dateLastCrawled", ""),
                })
            return results
        except Exception:
            return []

    def extract_items(self, keyword: str = "球墨铸铁管") -> List[BiddingItem]:
        """搜索并转换为 BiddingItem 列表."""
        discovered = self.discover(keyword)
        items = []
        for d in discovered:
            title = d.get("title", "")
            url = d.get("url", "")
            snippet = d.get("snippet", "")
            if not title or not url:
                continue
            if keyword not in title and keyword not in snippet:
                continue

            platform = _get_platform_name(url)
            region = self._extract_region(title + snippet)
            if not region:
                region = d.get("query_city", "")

            source_id = self._extract_id(url) or url

            items.append(BiddingItem(
                project_name=title,
                source_platform=platform,
                source_url=url,
                source_id=source_id,
                publish_date=self._extract_date(snippet + title),
                deadline=self._extract_deadline(snippet),
                budget=self._extract_budget(title + snippet),
                region=region,
            ))
        return items

    @staticmethod
    def _extract_region(text: str) -> str:
        for city in ZHEJIANG_CITIES:
            if city in text:
                return city
        return ""

    @staticmethod
    def _extract_date(text: str) -> str:
        m = re.search(r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})", text)
        if m:
            return m.group(1).replace("年", "-").replace("月", "-").replace("/", "-").rstrip("日")
        return ""

    @staticmethod
    def _extract_deadline(text: str) -> str:
        for pat in [r"截止[时间日].*?(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})",
                     r"投标.*?(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})"]:
            m = re.search(pat, text)
            if m:
                d = m.group(1)
                return d.replace("年", "-").replace("月", "-").replace("/", "-").rstrip("日")
        return ""

    @staticmethod
    def _extract_budget(text: str) -> str:
        for pat in [r"预算[金金额价]?\s*[:：]?\s*(\d+\.?\d*)\s*万元?",
                     r"(\d+\.?\d*)\s*万元",
                     r"控制价.*?(\d+\.?\d*)\s*万元"]:
            m = re.search(pat, text)
            if m:
                return f"{m.group(1)}万元"
        return ""

    @staticmethod
    def _extract_id(url: str) -> str:
        for pat in [r"[?&]id=([^&]+)", r"articleId=([^&]+)",
                     r"/([a-f0-9]{32})", r"/([a-f0-9-]{36})",
                     r"item-view-id-(\d+)"]:
            m = re.search(pat, url)
            if m:
                return m.group(1)
        return ""
