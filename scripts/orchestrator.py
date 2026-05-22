"""调度编排：搜索发现 + 详情页解析 + 直接抓取，合并结果."""
import os
from typing import List
from scripts.fetcher import Fetcher
from scripts.parser_base import BaseParser
from scripts.models import BiddingItem
from scripts.storage import Storage
from scripts.config import KEYWORD, MAX_PAGES_PER_SITE
from scripts.search_discovery import SearchDiscovery
from scripts.detail_parser import DetailParser
from scripts.parsers.zj_ggzy import ZjGgzyParser
from scripts.parsers.zj_zfcg import ZjZfcgParser
from scripts.parsers.ctbpsp import CtbpspParser
from scripts.parsers.qianlima import QianlimaParser
from scripts.parsers.zhaobiao_cn import ZhaobiaoCnParser


class Orchestrator:
    """编排所有数据源，去重合并."""

    def __init__(self):
        self.fetcher = Fetcher()
        self.storage = Storage()
        self.detail_parser = DetailParser(self.fetcher)
        self.direct_parsers: List[BaseParser] = [
            ZjGgzyParser(self.fetcher),
            ZjZfcgParser(self.fetcher),
            CtbpspParser(self.fetcher),
            QianlimaParser(self.fetcher),
            ZhaobiaoCnParser(self.fetcher),
        ]

    def run(self) -> dict:
        """执行全量搜索并合并."""
        all_items: List[BiddingItem] = []
        errors: List[str] = []

        # Phase 1: Search-based discovery + detail page parsing
        bing_key = os.environ.get("BING_API_KEY", "")
        if bing_key:
            print("\n[搜索发现] 通过 Bing API 搜索公告...")
            try:
                discovery = SearchDiscovery(bing_key)
                discovered = discovery.discover(KEYWORD)
                print(f"[搜索发现] 发现 {len(discovered)} 个链接")
                for i, d in enumerate(discovered):
                    url = d["url"]
                    print(f"  [{i+1}/{len(discovered)}] 解析: {url[:80]}...")
                    try:
                        item = self.detail_parser.parse(
                            url,
                            fallback_title=d.get("title", ""),
                            fallback_date=d.get("date_published", ""),
                            fallback_region=d.get("query_city", ""),
                        )
                        if item:
                            all_items.append(item)
                    except Exception as e:
                        errors.append(f"详情解析 {url}: {e}")
            except Exception as e:
                errors.append(f"搜索发现: {e}")
        else:
            print("\n[搜索发现] 未配置 BING_API_KEY，跳过")

        # Phase 2: Direct platform scraping
        for parser in self.direct_parsers:
            print(f"\n[{parser.platform_name}] 开始搜索...")
            try:
                items = parser.safe_parse(KEYWORD, MAX_PAGES_PER_SITE)
                print(f"[{parser.platform_name}] 获取到 {len(items)} 条结果")
                all_items.extend(items)
            except Exception as e:
                msg = f"{parser.platform_name}: {e}"
                print(f"  [ERROR] {msg}")
                errors.append(msg)

        all_items = self._dedup_cross_platform(all_items)
        new_items = self.storage.merge_new(all_items)
        print(f"\n总计: {len(all_items)} 条，新增: {len(new_items)} 条，错误: {len(errors)} 个")
        return {
            "total": len(all_items),
            "new": len(new_items),
            "items": [item.to_dict() for item in all_items],
            "errors": errors,
        }

    @staticmethod
    def _dedup_cross_platform(items: List[BiddingItem]) -> List[BiddingItem]:
        """跨平台去重（按项目名称前20字）."""
        seen = set()
        result = []
        for item in items:
            key = item.project_name[:20].strip()
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result
