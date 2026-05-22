"""统一招投标信息数据模型."""

from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class BiddingItem:
    """一条招投标公告."""

    project_name: str
    source_platform: str          # 发布平台名称
    source_url: str               # 原文链接
    source_id: str                # 公告唯一ID
    publish_date: str = ""        # 发布日期 YYYY-MM-DD
    deadline: str = ""            # 投标截止时间
    budget: str = ""              # 预算金额
    bidder: str = ""              # 招标人
    agency: str = ""              # 代理机构
    contact_person: str = ""      # 联系人
    contact_phone: str = ""       # 联系电话
    specs: str = ""               # 规格型号
    qualifications: str = ""      # 资质要求
    region: str = ""              # 所属地市
    fetched_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def unique_key(self) -> str:
        return f"{self.source_platform}:{self.source_id}"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BiddingItem":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
