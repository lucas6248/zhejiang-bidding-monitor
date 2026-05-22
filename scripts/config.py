"""配置."""
import os

KEYWORD = "球墨铸铁管"
MAX_PAGES_PER_SITE = 3
BING_API_KEY = os.environ.get("BING_API_KEY", "")
ZHEJIANG_CITIES = [
    "杭州", "宁波", "温州", "嘉兴", "湖州", "绍兴",
    "金华", "衢州", "舟山", "台州", "丽水",
]
