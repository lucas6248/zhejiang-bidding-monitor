# 浙江省球墨铸铁管招投标信息监控

自动抓取浙江省各公共资源交易平台中"球墨铸铁管"相关招投标信息，生成可在线浏览的 HTML 报告。

## 在线查看

报告页面: `https://<你的用户名>.github.io/zhejiang-bidding-monitor/`

## 数据来源

- 浙江省公共资源交易服务平台 (ggzy.zj.gov.cn) — 全省 11 地市统一平台
- 浙江政府采购网 (zfcg.czt.zj.gov.cn)
- 中国招标投标公共服务平台 (ctbpsp.com)
- 千里马招标网 (qianlima.com)
- 招标雷达 (zhaobiao.cn)

## 本地运行

```bash
pip install -r requirements.txt
python -c "from scripts.orchestrator import Orchestrator; from scripts.generate_report import generate_report; Orchestrator().run(); generate_report()"
```

## 自动更新

GitHub Actions 每天北京时间 9:00 自动抓取，结果发布到 GitHub Pages。

## 添加新平台

1. 在 `scripts/parsers/` 下创建新的解析器，继承 `BaseParser`
2. 实现 `platform_name`、`platform_url`、`search()` 方法
3. 在 `scripts/orchestrator.py` 中注册新解析器
