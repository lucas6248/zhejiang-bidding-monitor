"""数据持久化：管理 results.json 的读写和去重."""

import json
from pathlib import Path
from typing import List, Set
from scripts.models import BiddingItem

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_FILE = DATA_DIR / "results.json"


class Storage:
    """管理招投标历史数据."""

    def __init__(self, data_file: Path = DATA_FILE):
        self.data_file = data_file
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_file.exists():
            self._write([])

    def load_all(self) -> List[dict]:
        """加载全部历史数据."""
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write(self, items: List[dict]):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

    def get_existing_keys(self) -> Set[str]:
        """获取已有记录的唯一键集合."""
        items = self.load_all()
        return {
            f"{item.get('source_platform', '')}:{item.get('source_id', '')}"
            for item in items
        }

    def merge_new(self, new_items: List[BiddingItem]) -> List[BiddingItem]:
        """合并新数据，返回真正新增的条目."""
        existing_keys = self.get_existing_keys()
        truly_new = [
            item for item in new_items
            if item.unique_key not in existing_keys
        ]
        if truly_new:
            all_items = self.load_all()
            all_items.extend(item.to_dict() for item in truly_new)
            self._write(all_items)
        return truly_new

    def get_recent(self, days: int = 7) -> List[BiddingItem]:
        """获取近 N 天的数据."""
        import datetime
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        all_items = self.load_all()
        recent = []
        for d in all_items:
            pub_date = d.get("publish_date", "")
            if pub_date >= cutoff:
                recent.append(BiddingItem.from_dict(d))
        return sorted(recent, key=lambda x: x.publish_date, reverse=True)

    def get_count(self) -> int:
        return len(self.load_all())
