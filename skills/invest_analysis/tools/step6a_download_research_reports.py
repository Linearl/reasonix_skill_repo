#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Step6a: Research Report Download Tool
自动搜索和下载各大券商对上市公司的研究报告

使用方法:
    python step6a_download_research_reports.py --input ../step2/02_标的清单.yaml --output ../step6/reports

功能:
    1. 读取Step2生成的标的清单YAML文件
    2. 从多个数据源搜索研报（巨潮资讯、East Choice、雪球等）
    3. 筛选主流券商和最新报告（过去3-6个月）
    4. 下载PDF研报文件
    5. 生成研报索引和元数据
"""

import os
import sys
import yaml
import json
import logging
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import argparse
import requests
from urllib.parse import quote
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ResearchReportDownloader:
    """研报下载器"""

    # 主流券商列表（按影响力排序）
    MAJOR_BROKERS = [
        "中信证券",
        "海通证券",
        "中泰证券",
        "招商证券",
        "申万宏源",
        "华泰证券",
        "东吴证券",
        "东北证券",
        "国信证券",
        "浙商证券",
        "广发证券",
        "民生证券",
        "中金公司",
        "国盛证券",
        "长城证券",
        "华安证券",
    ]

    # 数据源配置
    DATA_SOURCES = {
        "cninfo": {
            "name": "巨潮资讯",
            "url": "https://www.cninfo.com.cn/new/hisAnnouncement/query",
            "enabled": True,
        },
        "xueqiu": {
            "name": "雪球",
            "url": "https://xueqiu.com/stock/search.json",
            "enabled": False,  # 需要额外认证
        },
        "eastmoney": {
            "name": "东方财富",
            "url": "https://data.eastmoney.com/other/gongaognxjl",
            "enabled": False,  # 需要额外处理
        },
    }

    def __init__(
        self,
        input_file: str,
        output_dir: str,
        lookback_days: int = 180,
        skip_existing: bool = True,
    ):
        """
        初始化下载器

        Args:
            input_file: Step2的标的清单YAML文件路径
            output_dir: 输出目录路径
            lookback_days: 往回查看的天数（默认180天=6个月）
            skip_existing: 是否跳过已存在的文件
        """
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.lookback_days = lookback_days
        self.skip_existing = skip_existing
        self.stocks = []
        self.reports_downloaded = []

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Referer": "https://www.cninfo.com.cn",
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
                logger.info(f"✅ 成功加载 {len(self.stocks)} 只股票")
                return True
        except Exception as e:
            logger.error(f"❌ 加载标的清单失败: {e}")
            return False

    def _is_a_share(self, stock: Dict) -> bool:
        """判断是否为A股标的"""
        market = str(stock.get("market", "")).strip().upper()
        if market in {"A", "A股", "CN", "CN-A", "A-SHARE"}:
            return True
        code = str(stock.get("code", "")).strip()
        return code.isdigit() and len(code) == 6

    def search_cninfo_reports(self, code: str, name: str) -> List[Dict]:
        """
        从巨潮资讯搜索研报

        Args:
            code: 股票代码
            name: 股票名称

        Returns:
            List[Dict]: 研报列表
        """
        try:
            code = str(code).zfill(6)
            exchange = "sh" if code.startswith(("6", "9")) else "sz"
            stock_param = f"{code},{exchange}"

            # 构建查询参数
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=self.lookback_days)).strftime(
                "%Y-%m-%d"
            )

            payload = {
                "pageNum": 1,
                "pageSize": 100,
                "tabName": "fulltext",
                "column": "szse" if exchange == "sz" else "sse",
                "stock": stock_param,
                "searchkey": "研究报告",
                "category": "research_report",
                "seDate": f"{start_date}~{end_date}",
                "sortName": "announceTime",
                "sortType": "desc",
            }

            response = self.session.post(
                self.DATA_SOURCES["cninfo"]["url"], data=payload, timeout=20
            )
            response.raise_for_status()
            data = response.json()
            announcements = (
                data.get("announcements", []) if isinstance(data, dict) else []
            )

            # 过滤研报
            reports = []
            for ann in announcements:
                title = ann.get("announcementTitle", "")
                if "研究报告" in title or "投资评级" in title:
                    # 提取券商名称
                    broker = self._extract_broker(title)
                    if broker and broker in self.MAJOR_BROKERS:
                        reports.append(
                            {
                                "title": title,
                                "broker": broker,
                                "date": self._parse_date(ann.get("announcementTime")),
                                "url": ann.get("adjunctUrl", ""),
                                "ann_id": ann.get("id", ""),
                                "source": "cninfo",
                            }
                        )

            logger.info(f"从巨潮资讯找到 {len(reports)} 份研报: {code}_{name}")
            return reports

        except Exception as e:
            logger.warning(f"⚠️ 巨潮资讯查询失败 {code}_{name}: {e}")
            return []

    def download_report(self, report: Dict, code: str, name: str) -> Optional[Dict]:
        """
        下载单份研报

        Args:
            report: 研报信息字典
            code: 股票代码
            name: 股票名称

        Returns:
            Optional[Dict]: 下载结果，失败返回None
        """
        try:
            # 创建股票目录
            stock_dir = self.output_dir / f"{code}_{name}"
            stock_dir.mkdir(parents=True, exist_ok=True)

            # 构建文件名
            date_str = report["date"].replace("-", "")
            broker = report.get("broker", "unknown")
            filename = f"{date_str}_{broker}.pdf"
            filepath = stock_dir / filename

            # 如果文件已存在，跳过
            if self.skip_existing and filepath.exists():
                logger.info(f"⏭️  已存在，跳过: {filename}")
                return {
                    "status": "skipped",
                    "path": str(filepath),
                    "filename": filename,
                }

            # 构建下载URL
            if report["source"] == "cninfo":
                download_url = f"https://static.cninfo.com.cn/{report['url']}"

                # 下载文件
                logger.info(f"下载中: {filename}...")
                response = self.session.get(download_url, stream=True, timeout=30)
                response.raise_for_status()

                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024 * 128):
                        if chunk:
                            f.write(chunk)

                logger.info(f"✅ 下载成功: {filename}")
                return {
                    "status": "success",
                    "path": str(filepath),
                    "filename": filename,
                    "broker": broker,
                    "date": report["date"],
                }

            time.sleep(0.5)  # 礼貌地延迟请求

        except Exception as e:
            logger.warning(f"❌ 下载失败 {filename}: {e}")
            return None

    def download_all(self) -> Dict[str, List]:
        """
        下载所有股票的研报

        Returns:
            Dict: 下载结果统计
        """
        results = {"success": [], "failed": [], "skipped": [], "not_found": []}

        for idx, stock in enumerate(self.stocks, 1):
            code = stock.get("code", "")
            name = stock.get("name", "")

            if not code or not name:
                logger.warning(f"跳过无效的股票: {stock}")
                continue

            # 检查是否为A股（只有A股支持自动化）
            if not self._is_a_share(stock):
                logger.info(f"⊗ 非A股标的，跳过自动下载研报: {code}_{name}")
                results["not_found"].append(
                    {"code": code, "name": name, "reason": "非A股"}
                )
                continue

            logger.info(f"\n[{idx}/{len(self.stocks)}] 处理: {code}_{name}")

            # 搜索研报
            reports = self.search_cninfo_reports(code, name)

            if not reports:
                logger.info(f"📭 未找到研报: {code}_{name}")
                results["not_found"].append(
                    {"code": code, "name": name, "reason": "无研报"}
                )
                continue

            # 下载每份研报（只下载最新的3份）
            for report in reports[:3]:
                result = self.download_report(report, code, name)

                if result:
                    if result["status"] == "success":
                        results["success"].append(
                            {
                                "code": code,
                                "name": name,
                                "broker": report.get("broker"),
                                "date": report.get("date"),
                                "path": result["path"],
                                "filename": result["filename"],
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                    elif result["status"] == "skipped":
                        results["skipped"].append(
                            {
                                "code": code,
                                "name": name,
                                "broker": report.get("broker"),
                                "date": report.get("date"),
                                "path": result["path"],
                                "filename": result["filename"],
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                else:
                    results["failed"].append(
                        {
                            "code": code,
                            "name": name,
                            "broker": report.get("broker"),
                            "date": report.get("date"),
                        }
                    )

        return results

    def save_metadata(self, results: Dict) -> None:
        """
        保存下载元数据

        Args:
            results: 下载结果字典
        """
        metadata_file = self.output_dir / "research_reports_metadata.json"
        metadata = {
            "download_time": datetime.now().isoformat(),
            "lookback_days": self.lookback_days,
            "total_stocks": len(self.stocks),
            "successful_downloads": len(results["success"]),
            "skipped_downloads": len(results["skipped"]),
            "failed_downloads": len(results["failed"]),
            "not_found_count": len(results["not_found"]),
            "results": results,
        }

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 元数据已保存到: {metadata_file}")

    def generate_index(self, results: Dict) -> None:
        """
        生成研报索引YAML

        Args:
            results: 下载结果字典
        """
        index_file = self.output_dir / "research_reports_index.yaml"

        index_data = {
            "generate_time": datetime.now().isoformat(),
            "lookback_days": self.lookback_days,
            "total_reports": len(results["success"]) + len(results["skipped"]),
            "reports": [],
        }

        # 按股票分组
        reports_by_stock = {}
        for report in results["success"] + results["skipped"]:
            key = f"{report['code']}_{report['name']}"
            if key not in reports_by_stock:
                reports_by_stock[key] = []
            reports_by_stock[key].append(
                {
                    "broker": report.get("broker"),
                    "date": report.get("date"),
                    "path": report.get("path"),
                    "filename": report.get("filename"),
                    "status": "success" if report in results["success"] else "skipped",
                }
            )

        for stock_key, stock_reports in sorted(reports_by_stock.items()):
            index_data["reports"].append(
                {
                    "stock": stock_key,
                    "report_count": len(stock_reports),
                    "latest_date": max(r["date"] for r in stock_reports),
                    "brokers": list(set(r["broker"] for r in stock_reports)),
                    "reports": stock_reports,
                }
            )

        with open(index_file, "w", encoding="utf-8") as f:
            yaml.dump(index_data, f, allow_unicode=True, sort_keys=False)

        logger.info(f"✅ 研报索引已保存到: {index_file}")

    def generate_report(self, results: Dict) -> None:
        """
        生成下载报告

        Args:
            results: 下载结果字典
        """
        report_file = self.output_dir / "step6a_download_report.md"

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("# Step6a 研报下载报告\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**查看周期**: 过去 {self.lookback_days} 天\n")
            f.write(f"**总股票数**: {len(self.stocks)}\n")
            f.write(f"**成功下载**: {len(results['success'])} 份\n")
            f.write(f"**已存在跳过**: {len(results['skipped'])} 份\n")
            f.write(f"**下载失败**: {len(results['failed'])} 份\n")
            f.write(f"**未找到研报**: {len(results['not_found'])} 只股票\n\n")

            if results["success"]:
                f.write("## ✅ 成功下载的研报\n\n")
                f.write("| 股票 | 券商 | 日期 | 文件 |\n")
                f.write("|------|------|------|------|\n")
                for item in sorted(
                    results["success"], key=lambda x: x["date"], reverse=True
                ):
                    f.write(
                        f"| {item['code']}_{item['name']} | {item.get('broker', '-')} | {item.get('date', '-')} | {item['filename']} |\n"
                    )

            if results["skipped"]:
                f.write("\n## ⏭️ 已存在跳过的研报\n\n")
                f.write("| 股票 | 券商 | 日期 | 文件 |\n")
                f.write("|------|------|------|------|\n")
                for item in sorted(
                    results["skipped"], key=lambda x: x["date"], reverse=True
                ):
                    f.write(
                        f"| {item['code']}_{item['name']} | {item.get('broker', '-')} | {item.get('date', '-')} | {item['filename']} |\n"
                    )

            if results["failed"]:
                f.write("\n## ❌ 下载失败的研报\n\n")
                f.write("| 股票 | 券商 | 日期 | 原因 |\n")
                f.write("|------|------|------|------|\n")
                for item in results["failed"]:
                    f.write(
                        f"| {item['code']}_{item['name']} | {item.get('broker', '-')} | {item.get('date', '-')} | 网络/API错误 |\n"
                    )

            if results["not_found"]:
                f.write("\n## 📭 未找到研报的股票\n\n")
                for item in results["not_found"]:
                    reason = item.get("reason", "未知")
                    f.write(f"- {item['code']}_{item['name']}: {reason}\n")
                f.write(
                    "\n**建议**: 手动从券商官网或东方财富、雪球等第三方平台搜索这些股票的研报\n"
                )

            f.write("\n## 📊 统计信息\n\n")
            f.write(f"- **数据来源**: 巨潮资讯(CNINFO)\n")
            f.write(f"- **券商覆盖**: 仅主流券商（{len(self.MAJOR_BROKERS)}家）\n")
            f.write(f"- **查看周期**: 过去 {self.lookback_days} 天\n")
            f.write(
                f"- **下载时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )

            f.write("## ℹ️ 说明\n\n")
            f.write("- 本脚本仅从 **巨潮资讯** 自动化下载，覆盖 **A股** 上市公司\n")
            f.write("- 对于 **香港股票**，需要手动从 HKEXnews、雪球、富途等平台搜索\n")
            f.write("- 研报来自主流券商（15+家），筛选了过去 6 个月内的最新报告\n")
            f.write("- 单只股票最多下载近期 3 份研报，避免冗余\n")

        logger.info(f"✅ 下载报告已生成: {report_file}")

    @staticmethod
    def _extract_broker(title: str) -> Optional[str]:
        """从标题中提取券商名称"""
        for broker in ResearchReportDownloader.MAJOR_BROKERS:
            if broker in title:
                return broker
        return None

    @staticmethod
    def _parse_date(timestamp_ms) -> str:
        """解析毫秒级时间戳为日期字符串"""
        try:
            if isinstance(timestamp_ms, str):
                timestamp_ms = int(timestamp_ms)
            return datetime.fromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d")
        except:
            return datetime.now().strftime("%Y-%m-%d")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Step6a: 下载上市公司研究报告",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认路径（过去6个月）
  python step6a_download_research_reports.py
  
  # 指定自定义路径
  python step6a_download_research_reports.py \\
    --input ../step2/02_标的清单.yaml \\
    --output ../step6/reports \\
    --days 180
    
  # 只查看过去3个月
  python step6a_download_research_reports.py --days 90
        """,
    )

    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="../step2/02_标的清单.yaml",
        help="Step2标的清单YAML文件路径",
    )

    parser.add_argument(
        "--output", "-o", type=str, default="../step6/reports", help="输出目录路径"
    )

    parser.add_argument(
        "--days", "-d", type=int, default=180, help="往回查看的天数（默认180天=6个月）"
    )

    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="是否跳过已存在的文件",
    )

    args = parser.parse_args()

    # 创建下载器并执行
    logger.info("=" * 60)
    logger.info("Step6a 研报下载工具 - 启动")
    logger.info("=" * 60)

    downloader = ResearchReportDownloader(
        input_file=args.input,
        output_dir=args.output,
        lookback_days=args.days,
        skip_existing=args.skip_existing,
    )

    if not downloader.load_stock_list():
        return 1

    logger.info(f"开始下载，查看周期: 过去 {args.days} 天...")
    results = downloader.download_all()

    downloader.save_metadata(results)
    downloader.generate_index(results)
    downloader.generate_report(results)

    # 打印统计
    logger.info("\n" + "=" * 60)
    logger.info("📊 下载完成统计")
    logger.info("=" * 60)
    logger.info(f"✅ 成功下载: {len(results['success'])} 份")
    logger.info(f"⏭️  已存在跳过: {len(results['skipped'])} 份")
    logger.info(f"❌ 下载失败: {len(results['failed'])} 份")
    logger.info(f"📭 未找到研报: {len(results['not_found'])} 只股票")
    logger.info("=" * 60 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
