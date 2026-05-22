"""解析器抽象基类."""

import re
from abc import ABC, abstractmethod
from html import unescape
from typing import List
from scripts.models import BiddingItem
from scripts.fetcher import Fetcher


class ParseError(Exception):
    """解析失败异常."""
    pass


class BaseParser(ABC):
    """平台解析器基类."""

    def __init__(self, fetcher: Fetcher):
        self.fetcher = fetcher

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """平台名称，用作 source_platform."""
        ...

    @property
    @abstractmethod
    def platform_url(self) -> str:
        """平台首页 URL."""
        ...

    @abstractmethod
    def search(self, keyword: str, max_pages: int = 3) -> List[BiddingItem]:
        """搜索关键词，返回招投标公告列表."""
        ...

    def build_item(self, **kwargs) -> BiddingItem:
        """创建 BiddingItem，自动填充 source_platform."""
        kwargs.setdefault("source_platform", self.platform_name)
        return BiddingItem(**kwargs)

    @staticmethod
    def clean_text(text: str) -> str:
        """清洗文本：去 HTML 实体、合并空白."""
        text = unescape(text or "")
        return re.sub(r"\s+", " ", text).strip()

    def safe_parse(self, keyword: str, max_pages: int = 3) -> List[BiddingItem]:
        """安全的搜索封装，异常不中断."""
        try:
            return self.search(keyword, max_pages)
        except Exception as e:
            print(f"[{self.platform_name}] 搜索失败: {e}")
            return []
