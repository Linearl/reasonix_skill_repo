#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Step4a: News Search & Collection Tool
从多个数据源自动搜索和收集A股/港股上市公司的新闻、公告和事件
说明: 巨潮资讯公告仅适用于A股；港股自动跳过公告抓取。

使用方法:
    python step4a_search_news.py \\
        --input ../step2/02_标的清单.yaml \\
        --output ../step4/raw_data/ \\
        --days 60

功能:
    1. 读取Step2生成的标的清单
    2. 从巨潮资讯搜索官方公告（仅A股）
    3. 从新闻平台搜索行业和公司新闻
    4. 从事件日历获取重要事件
    5. 汇总并去重
"""

import os
import sys
import yaml
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import argparse
from collections import defaultdict
from urllib.parse import quote
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET
import html

import requests

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NewsCollector:
    """新闻收集器"""

    # 数据源配置
    SOURCES = {
        "cninfo": "巨潮资讯",  # 官方公告
        "news": "新闻网站",  # 新闻媒体
        "events": "事件日历",  # 重要事件
    }

    def __init__(self, input_file: str, output_dir: str, days: int = 60):
        """
        初始化收集器

        Args:
            input_file: Step2的标的清单YAML文件
            output_dir: 输出目录
            days: 搜索的历史天数
        """
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.days = days
        self.stocks = []
        self.all_news = {}  # {code_name: [news_items]}
        self.dedup_set = set()  # 用于去重

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://www.cninfo.com.cn/new/index",
            }
        )

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_stock_list(self) -> bool:
        """
        加载标的清单

        Returns:
            bool: 是否成功加载
        """
        try:
            with open(self.input_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.stocks = data if isinstance(data, list) else []
                logger.info(f"成功加载{len(self.stocks)}只股票")
                return True
        except Exception as e:
            logger.error(f"加载标的清单失败: {e}")
            return False

    def _is_a_share(self, stock: Dict) -> bool:
        """
        判断是否为A股标的

        规则:
        - market 显式标注为 A/CN/A股
        - 或代码为6位数字
        """
        market = str(stock.get("market", "")).strip().upper()
        if market in {"A", "A股", "CN", "CN-A", "A-SHARE"}:
            return True

        code = str(stock.get("code", "")).strip()
        return code.isdigit() and len(code) == 6

    def search_cninfo_announcements(self, code: str, name: str) -> List[Dict]:
        """
        从巨潮资讯搜索官方公告

        Args:
            code: 股票代码
            name: 股票名称

        Returns:
            List[Dict]: 公告列表
        """
        announcements = []

        logger.info(f"搜索{code}_{name}的巨潮公告...")

        try:
            data = self._cninfo_query(code)
            for item in data:
                ann_time = item.get("announcementTime")
                date_str = (
                    datetime.fromtimestamp(int(ann_time) / 1000).strftime("%Y-%m-%d")
                    if ann_time
                    else ""
                )
                announcements.append(
                    {
                        "date": date_str,
                        "source": "cninfo",
                        "source_name": self.SOURCES["cninfo"],
                        "title": item.get("announcementTitle", ""),
                        "content_summary": item.get("announcementTitle", ""),
                        "url": f"https://static.cninfo.com.cn/{item.get('adjunctUrl','')}",
                        "category": "announcement",
                    }
                )

        except Exception as e:
            logger.warning(f"搜索{code}公告失败: {e}")

        return announcements

    def search_news_websites(self, name: str) -> List[Dict]:
        """
        从新闻网站搜索新闻

        Args:
            name: 股票名称

        Returns:
            List[Dict]: 新闻列表
        """
        news_list = []

        logger.info(f"搜索关于{name}的新闻...")

        try:
            rss_url = f"https://www.bing.com/news/search?q={quote(name)}&format=rss"
            resp = self.session.get(rss_url, timeout=20)
            resp.raise_for_status()

            root = ET.fromstring(resp.text)
            for item in root.findall(".//item"):
                title = item.findtext("title", default="").strip()
                link = item.findtext("link", default="").strip()
                pub_date = item.findtext("pubDate", default="").strip()
                desc = item.findtext("description", default="").strip()

                date_str = ""
                if pub_date:
                    try:
                        date_str = parsedate_to_datetime(pub_date).strftime("%Y-%m-%d")
                    except Exception:
                        date_str = ""

                news_list.append(
                    {
                        "date": date_str,
                        "source": "news",
                        "source_name": "Bing News",
                        "title": html.unescape(title),
                        "content_summary": html.unescape(desc)[:200],
                        "url": link,
                        "category": "news",
                    }
                )

        except Exception as e:
            logger.warning(f"搜索{name}新闻失败: {e}")

        return news_list

    def search_events(self, code: str, name: str) -> List[Dict]:
        """
        从事件日历搜索重要事件

        Args:
            code: 股票代码
            name: 股票名称

        Returns:
            List[Dict]: 事件列表
        """
        events = []

        logger.info(f"搜索{code}_{name}的重要事件...")

        try:
            data = self._cninfo_query(code)
            keywords = {
                "earnings": ["业绩预告", "业绩快报", "定期报告", "年度报告"],
                "dividend": ["分红", "派息", "送股", "转增"],
                "meeting": ["股东大会", "业绩说明会", "投资者关系"],
                "contract": ["重大合同", "中标", "签约", "战略合作"],
            }

            for item in data:
                title = item.get("announcementTitle", "")
                ann_time = item.get("announcementTime")
                date_str = (
                    datetime.fromtimestamp(int(ann_time) / 1000).strftime("%Y-%m-%d")
                    if ann_time
                    else ""
                )
                event_type = None
                for k, words in keywords.items():
                    if any(w in title for w in words):
                        event_type = k
                        break
                if not event_type:
                    continue

                events.append(
                    {
                        "date": date_str,
                        "source": "events",
                        "source_name": self.SOURCES["events"],
                        "title": title,
                        "content_summary": title,
                        "url": f"https://static.cninfo.com.cn/{item.get('adjunctUrl','')}",
                        "category": "event",
                        "event_type": event_type,
                    }
                )

        except Exception as e:
            logger.warning(f"搜索{code}事件失败: {e}")

        return events

    def deduplicate(self, news_item: Dict) -> bool:
        """
        检查是否重复

        Args:
            news_item: 新闻项目

        Returns:
            bool: 是否已存在（重复）
        """
        # 使用标题作为去重键
        key = f"{news_item.get('title', '')}_{news_item.get('date', '')}"

        if key in self.dedup_set:
            return True

        self.dedup_set.add(key)
        return False

    def collect_all(self) -> None:
        """
        收集所有新闻
        """
        for stock in self.stocks:
            code = stock.get("code", "")
            name = stock.get("name", "")

            if not code or not name:
                logger.warning(f"跳过无效的股票: {stock}")
                continue

            stock_key = f"{code}_{name}"
            self.all_news[stock_key] = []

            # 从各数据源搜索
            announcements = []
            if self._is_a_share(stock):
                announcements = self.search_cninfo_announcements(code, name)
            else:
                logger.info(f"非A股标的，跳过CNINFO公告: {code}_{name}")
            news_list = self.search_news_websites(name)
            events = self.search_events(code, name)

            # 合并并去重
            all_items = announcements + news_list + events

            for item in all_items:
                if not self.deduplicate(item):
                    self.all_news[stock_key].append(item)

            logger.info(
                f"{stock_key}: 收集到{len(self.all_news[stock_key])}条新闻/事件"
            )

    def save_raw_data(self) -> None:
        """
        保存原始数据为YAML格式
        """
        for stock_key, news_items in self.all_news.items():
            output_file = self.output_dir / f"{stock_key}_news_raw.yaml"

            # 按日期排序
            sorted_items = sorted(
                news_items, key=lambda x: x.get("date", ""), reverse=True
            )

            with open(output_file, "w", encoding="utf-8") as f:
                yaml.dump(sorted_items, f, ensure_ascii=False, allow_unicode=True)

            logger.info(f"原始新闻已保存: {output_file}")

    def save_index(self) -> None:
        """
        保存新闻索引
        """
        index = {
            "search_time": datetime.now().isoformat(),
            "search_days": self.days,
            "total_stocks": len(self.stocks),
            "total_news_items": sum(len(items) for items in self.all_news.values()),
            "stocks": {},
        }

        for stock_key, news_items in self.all_news.items():
            index["stocks"][stock_key] = {
                "count": len(news_items),
                "file": f"{stock_key}_news_raw.yaml",
                "categories": self._count_categories(news_items),
            }

        index_file = self.output_dir / "news_index.yaml"
        with open(index_file, "w", encoding="utf-8") as f:
            yaml.dump(index, f, ensure_ascii=False, allow_unicode=True)

        logger.info(f"索引已保存: {index_file}")

    def generate_summary_report(self) -> None:
        """
        生成汇总报告
        """
        report_file = self.output_dir / "step4a_collection_report.md"

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("# Step4a 新闻收集报告\n\n")
            f.write(f"**收集时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**搜索周期**: 过去{self.days}天\n\n")

            f.write(f"## 统计信息\n\n")
            f.write(f"- **搜索股票数**: {len(self.stocks)}\n")
            total_items = sum(len(items) for items in self.all_news.values())
            f.write(f"- **收集新闻总数**: {total_items}\n")
            f.write(f"- **去重后**: {len(self.dedup_set)}\n\n")

            f.write("## 按股票统计\n\n")
            for stock_key, news_items in self.all_news.items():
                categories = self._count_categories(news_items)
                f.write(f"### {stock_key}\n")
                f.write(f"- 总数: {len(news_items)}\n")
                for cat, count in categories.items():
                    f.write(f"  - {cat}: {count}\n")
                f.write("\n")

        logger.info(f"汇总报告已生成: {report_file}")

    @staticmethod
    def _count_categories(news_items: List[Dict]) -> Dict[str, int]:
        """
        统计不同类别的新闻

        Args:
            news_items: 新闻项目列表

        Returns:
            Dict: 类别统计
        """
        categories = defaultdict(int)
        for item in news_items:
            category = item.get("category", "unknown")
            categories[category] += 1
        return dict(categories)

    @staticmethod
    def _normalize_code(code: str) -> str:
        return code.zfill(6)

    @staticmethod
    def _get_exchange(code: str) -> str:
        code = code.zfill(6)
        return "sh" if code.startswith("6") or code.startswith("9") else "sz"

    def _cninfo_query(self, code: str) -> List[Dict]:
        """查询巨潮资讯公告列表"""
        url = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
        code = self._normalize_code(code)
        exchange = self._get_exchange(code)
        stock_param = f"{code},{exchange}"
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=self.days)).strftime("%Y-%m-%d")

        payload = {
            "pageNum": 1,
            "pageSize": 30,
            "tabName": "fulltext",
            "column": "szse" if exchange == "sz" else "sse",
            "stock": stock_param,
            "searchkey": "",
            "secid": "",
            "plate": "",
            "category": "",
            "trade": "",
            "seDate": f"{start_date}~{end_date}",
            "sortName": "announceTime",
            "sortType": "desc",
        }

        resp = self.session.post(url, data=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        return data.get("announcements", []) if isinstance(data, dict) else []


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Step4a: 从多个数据源搜索新闻和事件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认参数（搜索过去60天）
  python step4a_search_news.py \\
    --input ../step2/02_标的清单.yaml \\
    --output ../step4/raw_data/
  
  # 自定义搜索周期
  python step4a_search_news.py \\
    --input ../step2/02_标的清单.yaml \\
    --output ../step4/raw_data/ \\
    --days 30
        """,
    )

    parser.add_argument(
        "--input", "-i", default="../step2/02_标的清单.yaml", help="Step2标的清单"
    )
    parser.add_argument("--output", "-o", default="../step4/raw_data/", help="输出目录")
    parser.add_argument("--days", "-d", type=int, default=60, help="搜索的历史天数")

    args = parser.parse_args()

    collector = NewsCollector(
        input_file=args.input, output_dir=args.output, days=args.days
    )

    if not collector.load_stock_list():
        return 1

    collector.collect_all()
    collector.save_raw_data()
    collector.save_index()
    collector.generate_summary_report()

    logger.info("新闻收集完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
