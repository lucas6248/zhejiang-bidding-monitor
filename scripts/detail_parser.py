"""详情页解析器：从公告详情页提取结构化数据."""
import re
from typing import Optional
from bs4 import BeautifulSoup
from scripts.fetcher import Fetcher
from scripts.models import BiddingItem
from scripts.search_discovery import _get_platform_name, ZHEJIANG_CITIES


class DetailParser:
    """从公开的公告详情页提取结构化字段."""

    def __init__(self, fetcher: Optional[Fetcher] = None):
        self.fetcher = fetcher or Fetcher()

    def parse(self, url: str, fallback_title: str = "",
              fallback_date: str = "", fallback_region: str = "") -> Optional[BiddingItem]:
        """抓取并解析详情页."""
        try:
            resp = self.fetcher.get(url)
            html = resp.text
        except Exception:
            return None

        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(" ", strip=True)

        title = self._extract_title(soup, text) or fallback_title
        if not title:
            return None

        platform = _get_platform_name(url)
        publish_date = self._extract_pub_date(soup, text) or fallback_date
        deadline = self._extract_deadline(text)
        budget = self._extract_budget(text)
        region = self._extract_region(soup, text) or fallback_region

        return BiddingItem(
            project_name=title,
            source_platform=platform,
            source_url=url,
            source_id=self._extract_id(url) or title,
            publish_date=publish_date,
            deadline=deadline,
            budget=budget,
            bidder=self._extract_bidder(text),
            agency=self._extract_agency(text),
            contact_person=self._extract_contact_person(text),
            contact_phone=self._extract_phone(text),
            specs=self._extract_specs(text),
            region=region,
        )

    @staticmethod
    def _extract_title(soup: BeautifulSoup, text: str) -> str:
        # Meta tags first (most reliable)
        for meta in soup.find_all("meta"):
            name = (meta.get("name") or "").lower()
            if name in ("articletitle", "title"):
                t = meta.get("content", "").strip()
                if t:
                    return t

        # HTML title
        title_tag = soup.find("title")
        if title_tag:
            t = title_tag.get_text(strip=True)
            t = re.sub(r"\s*[-–—|].*", "", t)
            if len(t) > 5:
                return t

        # H1 or class name with "title"
        for cls in ["title", "article-title", "news-title", "detail-title"]:
            el = soup.find(class_=cls)
            if el:
                t = el.get_text(strip=True)
                if len(t) > 10:
                    return t
        return ""

    @staticmethod
    def _extract_pub_date(soup: BeautifulSoup, text: str) -> str:
        for meta in soup.find_all("meta"):
            name = (meta.get("name") or "").lower()
            if name in ("pubdate", "publishdate", "date"):
                d = meta.get("content", "").strip()[:10]
                if re.match(r"\d{4}", d):
                    return d

        for pat in [r"信息时间[：:]\s*(\d{4}-\d{1,2}-\d{1,2})",
                     r"发布时间[：:]\s*(\d{4}-\d{1,2}-\d{1,2})",
                     r"发布日期[：:]\s*(\d{4}-\d{1,2}-\d{1,2})"]:
            m = re.search(pat, text)
            if m:
                return m.group(1)
        return ""

    @staticmethod
    def _extract_deadline(text: str) -> str:
        for pat in [r"截止[时间日].*?(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})",
                     r"投标.*?截止.*?(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})",
                     r"开标[时间日].*?(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})"]:
            m = re.search(pat, text)
            if m:
                d = m.group(1)
                return d.replace("年", "-").replace("月", "-").replace("/", "-").rstrip("日")
        return ""

    @staticmethod
    def _extract_budget(text: str) -> str:
        for pat in [r"预算[金金额价]?\s*[:：]?\s*(\d+\.?\d*)\s*[万元亿]",
                     r"控制价\s*[:：]?\s*(\d+\.?\d*)\s*[万元亿]",
                     r"中标[金金额价]?\s*[:：]?\s*(\d+\.?\d*)\s*[万元亿]"]:
            m = re.search(pat, text)
            if m:
                unit = "万元"
                if "亿" in m.group(0):
                    unit = "亿元"
                return f"{m.group(1)}{unit}"
        return ""

    @staticmethod
    def _extract_region(soup: BeautifulSoup, text: str) -> str:
        for meta in soup.find_all("meta"):
            name = (meta.get("name") or "").lower()
            if name == "columnname":
                content = meta.get("content", "")
                for city in ZHEJIANG_CITIES:
                    if city in content:
                        return city

        for city in ZHEJIANG_CITIES:
            if city in text[:500]:
                return city
        return ""

    @staticmethod
    def _extract_bidder(text: str) -> str:
        for pat in [r"招标人[：:]\s*(.+?)(?:[，,\n]|$)",
                     r"采购人[：:]\s*(.+?)(?:[，,\n]|$)",
                     r"招标单位[：:]\s*(.+?)(?:[，,\n]|$)"]:
            m = re.search(pat, text)
            if m:
                return m.group(1).strip()
        return ""

    @staticmethod
    def _extract_agency(text: str) -> str:
        for pat in [r"代理机构[：:]\s*(.+?)(?:[，,\n]|$)",
                     r"招标代理[：:]\s*(.+?)(?:[，,\n]|$)",
                     r"采购代理[：:]\s*(.+?)(?:[，,\n]|$)"]:
            m = re.search(pat, text)
            if m:
                return m.group(1).strip()
        return ""

    @staticmethod
    def _extract_contact_person(text: str) -> str:
        for pat in [r"联系人[：:]\s*(.+?)(?:[，,\n]|$)",
                     r"项目联系人[：:]\s*(.+?)(?:[，,\n]|$)"]:
            m = re.search(pat, text)
            if m:
                return m.group(1).strip()
        return ""

    @staticmethod
    def _extract_phone(text: str) -> str:
        for pat in [r"(?:电话|联系电话|联系方式)[：:]\s*(.+?)(?:[，,\n]|$)"]:
            m = re.search(pat, text)
            if m:
                return m.group(1).strip()
        m = re.search(r"1[3-9]\d{9}", text)
        return m.group(0) if m else ""

    @staticmethod
    def _extract_specs(text: str) -> str:
        for pat in [r"(?:DN\d{2,4}[×xX].+?)(?:[，,。\n]|$)",
                     r"规格型号[：:]\s*(.+?)(?:[，,\n]|$)"]:
            m = re.search(pat, text)
            if m:
                return m.group(1).strip()
        m = re.search(r"球墨铸铁管.+?(?:采购|招标)", text)
        return m.group(0).rstrip("采购招标") if m else ""

    @staticmethod
    def _extract_id(url: str) -> str:
        for pat in [r"[?&]id=([^&]+)", r"articleId=([^&]+)",
                     r"/([a-f0-9]{32})", r"/([a-f0-9-]{36})",
                     r"item-view-id-(\d+)"]:
            m = re.search(pat, url)
            if m:
                return m.group(1)
        return ""
