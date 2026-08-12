#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Step3a: Financial Report Download Tool
从巨潮资讯(CNINFO)自动下载A股上市公司的年报和季报
说明: 仅支持A股（CNINFO）。港股会自动跳过并提示手动下载。

使用方法:
    python step3a_download_reports.py --input ../step2/02_标的清单.yaml --output ../step3/financials

功能:
    1. 读取Step2生成的标的清单YAML文件
    2. 从巨潮资讯获取每家公司的最新年报和季报
    3. 按公司代码和名称组织到输出目录
    4. 生成下载日志和元数据
    5. 对港股标的自动跳过（需手动补充）
"""

import os
import sys
import yaml
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ReportDownloader:
    """财报下载器"""

    # CNINFO API 配置（示例，实际需要根据最新API调整）
    CNINFO_BASE_URL = "https://www.cninfo.com.cn/new/api"

    # 报告类型代码
    REPORT_TYPES = {
        "annual": "1",  # 年报
        "q1": "2",  # 一季报
        "q2": "3",  # 半年报
        "q3": "4",  # 三季报
    }

    def __init__(self, input_file: str, output_dir: str, skip_existing: bool = True):
        """
        初始化下载器

        Args:
            input_file: Step2的标的清单YAML文件路径
            output_dir: 输出目录路径
            skip_existing: 是否跳过已存在的文件
        """
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.skip_existing = skip_existing
        self.stocks = []
        self.download_log = []

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

    def create_stock_directory(self, code: str, name: str) -> Path:
        """
        为每只股票创建目录

        Args:
            code: 股票代码
            name: 股票名称

        Returns:
            Path: 股票目录路径
        """
        stock_dir = self.output_dir / f"{code}_{name}"
        stock_dir.mkdir(parents=True, exist_ok=True)
        return stock_dir

    def download_report(
        self, code: str, name: str, report_type: str = "annual"
    ) -> Optional[Dict[str, str]]:
        """
        下载单个报告

        Args:
            code: 股票代码（6位数字）
            name: 股票名称
            report_type: 报告类型（annual/q1/q2/q3）

        Returns:
            Optional[str]: 下载后的文件路径，失败返回None
        """
        stock_dir = self.create_stock_directory(code, name)

        logger.info(
            f"准备下载 {code}_{name} 的{self._get_report_type_name(report_type)}..."
        )

        try:
            announcements = self._query_cninfo_announcements(code)
            report = self._select_report(announcements, report_type)

            if not report:
                logger.warning(f"未找到{code}_{name}的{report_type}报告")
                return None

            report_date = report.get("announcementTime", "")
            date_str = (
                datetime.fromtimestamp(int(report_date) / 1000).strftime("%Y%m%d")
                if report_date
                else datetime.now().strftime("%Y%m%d")
            )
            filename = f"{date_str}_{report_type}.pdf"
            filepath = stock_dir / filename

            if self.skip_existing and filepath.exists():
                logger.info(f"已存在，跳过: {filepath}")
                return {"status": "skipped", "path": str(filepath)}

            download_url = f"https://static.cninfo.com.cn/{report['adjunctUrl']}"
            self._download_file(download_url, filepath)
            logger.info(f"已下载: {filepath}")
            return {"status": "success", "path": str(filepath)}

        except Exception as e:
            logger.error(f"下载{code}_{name}的{report_type}报告失败: {e}")
            return None

    def download_all(self) -> Dict[str, List[str]]:
        """
        下载所有股票的报告

        Returns:
            Dict: 下载结果统计
        """
        results = {"success": [], "failed": [], "skipped": []}

        for stock in self.stocks:
            code = stock.get("code", "")
            name = stock.get("name", "")

            if not code or not name:
                logger.warning(f"跳过无效的股票: {stock}")
                continue

            if not self._is_a_share(stock):
                logger.info(f"非A股标的，跳过自动下载: {code}_{name}")
                results["skipped"].append(
                    {
                        "code": code,
                        "name": name,
                        "type": "all",
                        "path": "",
                        "reason": "non_a_share",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                continue

            # 为每种报告类型下载
            for report_type in ["annual", "q3", "q2", "q1"]:
                result = self.download_report(code, name, report_type)

                if result and result.get("status") == "success":
                    results["success"].append(
                        {
                            "code": code,
                            "name": name,
                            "type": report_type,
                            "path": result["path"],
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                elif result and result.get("status") == "skipped":
                    results["skipped"].append(
                        {
                            "code": code,
                            "name": name,
                            "type": report_type,
                            "path": result["path"],
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                else:
                    results["failed"].append(
                        {"code": code, "name": name, "type": report_type}
                    )

        return results

    def save_metadata(self, results: Dict) -> None:
        """
        保存下载元数据

        Args:
            results: 下载结果字典
        """
        metadata_file = self.output_dir / "download_metadata.json"
        metadata = {
            "download_time": datetime.now().isoformat(),
            "total_stocks": len(self.stocks),
            "successful_downloads": len(results["success"]),
            "failed_downloads": len(results["failed"]),
            "results": results,
        }

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"元数据已保存到: {metadata_file}")

    def generate_report(self, results: Dict) -> None:
        """
        生成下载报告

        Args:
            results: 下载结果字典
        """
        report_file = self.output_dir / "step3a_download_report.md"

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("# Step3a 财报下载报告\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**总股票数**: {len(self.stocks)}\n")
            f.write(f"**成功下载**: {len(results['success'])}\n")
            f.write(f"**下载失败**: {len(results['failed'])}\n\n")

            if results["success"]:
                f.write("## ✅ 成功下载的报告\n\n")
                for item in results["success"]:
                    f.write(
                        f"- {item['code']}_{item['name']}: {item['type']} ({item['path']})\n"
                    )

            if results["failed"]:
                f.write("\n## ❌ 下载失败的报告\n\n")
                for item in results["failed"]:
                    f.write(f"- {item['code']}_{item['name']}: {item['type']}\n")
                f.write("\n**建议**: 检查网络连接，或手动从巨潮资讯下载这些报告\n")

            if results["skipped"]:
                f.write("\n## ⏭️ 已存在跳过的报告\n\n")
                for item in results["skipped"]:
                    reason = item.get("reason", "")
                    reason_text = f" | reason: {reason}" if reason else ""
                    f.write(
                        f"- {item['code']}_{item['name']}: {item['type']} ({item['path']}){reason_text}\n"
                    )

        logger.info(f"下载报告已生成: {report_file}")

    @staticmethod
    def _get_report_type_name(report_type: str) -> str:
        """获取报告类型的中文名称"""
        names = {"annual": "年报", "q3": "三季报", "q2": "半年报", "q1": "一季报"}
        return names.get(report_type, report_type)

    @staticmethod
    def _normalize_code(code: str) -> str:
        return code.zfill(6)

    @staticmethod
    def _get_exchange(code: str) -> str:
        code = code.zfill(6)
        return "sh" if code.startswith("6") or code.startswith("9") else "sz"

    def _query_cninfo_announcements(self, code: str) -> List[Dict]:
        """从巨潮资讯获取公告列表"""
        url = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
        code = self._normalize_code(code)
        exchange = self._get_exchange(code)
        stock_param = f"{code},{exchange}"
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

        payload = {
            "pageNum": 1,
            "pageSize": 50,
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

    def _select_report(
        self, announcements: List[Dict], report_type: str
    ) -> Optional[Dict]:
        """根据报告类型选择最新公告"""
        keywords = {
            "annual": ["年度报告"],
            "q1": ["第一季度报告"],
            "q2": ["半年度报告"],
            "q3": ["第三季度报告"],
        }
        excludes = ["摘要", "英文", "修订", "更正"]

        def match_title(title: str, allow_abstract: bool) -> bool:
            if not any(k in title for k in keywords.get(report_type, [])):
                return False
            if not allow_abstract and any(e in title for e in excludes):
                return False
            return True

        candidates = [
            a
            for a in announcements
            if match_title(a.get("announcementTitle", ""), False)
        ]
        if not candidates:
            candidates = [
                a
                for a in announcements
                if match_title(a.get("announcementTitle", ""), True)
            ]

        if not candidates:
            return None

        candidates.sort(key=lambda x: x.get("announcementTime", 0), reverse=True)
        return candidates[0]

    def _download_file(self, url: str, filepath: Path) -> None:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with self.session.get(url, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 128):
                    if chunk:
                        f.write(chunk)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Step3a: 从巨潮资讯下载财报",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认路径
  python step3a_download_reports.py
  
  # 指定自定义路径
  python step3a_download_reports.py \\
    --input ../step2/02_标的清单.yaml \\
    --output ../step3/financials
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
        "--output", "-o", type=str, default="../step3/financials", help="输出目录路径"
    )

    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="是否跳过已存在的文件",
    )

    args = parser.parse_args()

    # 创建下载器并执行
    downloader = ReportDownloader(
        input_file=args.input, output_dir=args.output, skip_existing=args.skip_existing
    )

    if not downloader.load_stock_list():
        return 1

    results = downloader.download_all()
    downloader.save_metadata(results)
    downloader.generate_report(results)

    # 打印统计
    logger.info(f"========== 下载完成 ==========")
    logger.info(f"成功: {len(results['success'])}")
    logger.info(f"失败: {len(results['failed'])}")
    logger.info(f"==============================")

    return 0


if __name__ == "__main__":
    sys.exit(main())
