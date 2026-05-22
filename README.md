# 浙江省球墨铸铁管招投标信息监控

自动抓取浙江省各公共资源交易平台中"球墨铸铁管"相关招投标信息，生成可在线浏览的 HTML 报告。

## 在线查看

报告页面: `https://lucas6248.github.io/zhejiang-bidding-monitor/`

## 数据来源

系统通过两层机制获取数据：

**搜索发现层**：通过 Bing Search API 搜索"球墨铸铁管 招标 + 城市名"，发现分散在各平台的公告链接
**详情解析层**：抓取公开的公告详情页，提取结构化数据（项目名称、预算、截止时间等）
**直接抓取层**：原有的 5 个平台解析器（需针对实际网站调优）

数据实际发布于：
- 各地市公共资源交易平台
- 水务公司采购门户
- 乐采云、浙企采等商业平台
- 浙江政府采购网

## 开启自动搜索

项目使用 Bing Web Search API 自动发现招标公告。

1. 前往 [Azure Portal](https://portal.azure.com) 创建 Bing Search 资源（免费层：1000次/月）
2. 获取 API Key
3. 在 GitHub 仓库 Settings → Secrets and variables → Actions 添加 Secret：
   - Name: `BING_API_KEY`
   - Value: 你的 Bing API Key

配置后，每天工作流会自动通过搜索发现新公告并更新报告。

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 不配置 BING_API_KEY 时仅运行直接抓取器
python -c "
from scripts.orchestrator import Orchestrator
from scripts.generate_report import generate_report
Orchestrator().run()
generate_report()
"

# 配置 BING_API_KEY 后启用搜索发现
export BING_API_KEY=your_key_here
# 然后运行上述命令
```

## 自动更新

GitHub Actions 每天北京时间 9:00 自动抓取，结果自动部署到 GitHub Pages。

## 项目结构

```
├── .github/workflows/daily-scrape.yml  # 定时抓取工作流
├── scripts/
│   ├── models.py          # 数据模型 (BiddingItem)
│   ├── fetcher.py         # HTTP 客户端（UA伪装、重试、编码检测）
│   ├── config.py          # 配置（关键词、城市列表）
│   ├── storage.py         # JSON 持久化 + 去重
│   ├── parser_base.py     # 解析器抽象基类
│   ├── search_discovery.py # Bing 搜索发现模块
│   ├── detail_parser.py   # 详情页解析器
│   ├── orchestrator.py    # 调度编排
│   ├── generate_report.py # HTML 报告生成
│   └── parsers/
│       ├── zj_ggzy.py     # 浙江公共资源交易平台
│       ├── zj_zfcg.py     # 浙江政府采购网
│       ├── ctbpsp.py      # 中国招标投标公共服务平台
│       ├── qianlima.py    # 千里马招标网
│       └── zhaobiao_cn.py # 招标雷达
├── data/results.json      # 历史数据
└── docs/index.html        # 报告页面
```

## 添加新平台

1. 在 `scripts/parsers/` 下创建新的解析器，继承 `BaseParser`
2. 实现 `platform_name`、`platform_url`、`search()` 方法
3. 在 `scripts/orchestrator.py` 中注册新解析器
