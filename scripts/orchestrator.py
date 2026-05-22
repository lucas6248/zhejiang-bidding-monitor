"""调度编排：依次运行所有解析器，合并结果."""

from typing import List
from scripts.fetcher import Fetcher
from scripts.parser_base import BaseParser
from scripts.models import BiddingItem
from scripts.storage import Storage
from scripts.config import KEYWORD, MAX_PAGES_PER_SITE
from scripts.parsers.zj_ggzy import ZjGgzyParser
from scripts.parsers.zj_zfcg import ZjZfcgParser
from scripts.parsers.ctbpsp import CtbpspParser
from scripts.parsers.qianlima import QianlimaParser
from scripts.parsers.zhaobiao_cn import ZhaobiaoCnParser


class Orchestrator:
    """编排所有解析器执行、去重、合并."""

    def __init__(self):
        self.fetcher = Fetcher()
        self.storage = Storage()
        self.parsers: List[BaseParser] = [
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

        for parser in self.parsers:
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
        print(f"\n总计: {len(all_items)} 条，新增: {len(new_items)} 条，错误: {len(errors)} 个平台")
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
