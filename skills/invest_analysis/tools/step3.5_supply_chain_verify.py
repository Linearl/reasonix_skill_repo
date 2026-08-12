#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Step3.5: Supply Chain Verification Tool
交叉验证 Step2 的产业链假设是否在财报和新闻中得到证实

使用方法:
    python step3.5_supply_chain_verify.py \\
        --supply-chain ../step2/02_产业链挖掘_*.md \\
        --analysis ../step3/analysis/ \\
        --news ../step4/classified/ \\
        --output ../step3.5/

功能:
    1. 读取Step2的产业链结构
    2. 读取Step3c的财报分析结果
    3. 读取Step4b的分类新闻
    4. 交叉验证供应关系
    5. 识别瓶颈和风险
"""

import os
import sys
import json
import yaml
import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from collections import defaultdict
import argparse

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SupplyChainVerifier:
    """产业链验证器"""

    def __init__(
        self, supply_chain_file: str, analysis_dir: str, news_dir: str, output_dir: str
    ):
        """
        初始化验证器

        Args:
            supply_chain_file: Step2的产业链文档路径
            analysis_dir: Step3c的分析报告目录
            news_dir: Step4b的分类新闻目录
            output_dir: 输出目录
        """
        self.supply_chain_file = Path(supply_chain_file)
        self.analysis_dir = Path(analysis_dir)
        self.news_dir = Path(news_dir)
        self.output_dir = Path(output_dir)

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "analysis").mkdir(exist_ok=True)
        (self.output_dir / "report").mkdir(exist_ok=True)

        self.supply_chain = {}  # 产业链结构
        self.analysis_reports = {}  # 财报分析结果
        self.news_data = {}  # 新闻分类数据
        self.verification_results = []  # 验证结果

    def load_supply_chain(self) -> bool:
        """
        从Step2的产业链文档解析供应链结构

        Returns:
            bool: 是否成功加载
        """
        try:
            if not self.supply_chain_file.exists():
                logger.error(f"产业链文件不存在: {self.supply_chain_file}")
                return False

            with open(self.supply_chain_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 使用正则表达式提取供应链关系
            # 格式示例: 公司A (产品/服务) -> 公司B
            pattern = r"([^\n]+?)\s*(?:\(([^)]+)\))?\s*[-→]\s*([^\n]+)"
            matches = re.findall(pattern, content)

            for supplier, product, customer in matches:
                supplier = supplier.strip()
                customer = customer.strip()
                product = product.strip() if product else "通用产品"

                if supplier not in self.supply_chain:
                    self.supply_chain[supplier] = {"customers": [], "products": []}

                self.supply_chain[supplier]["customers"].append(customer)
                self.supply_chain[supplier]["products"].append(product)

            logger.info(f"成功加载产业链: {len(self.supply_chain)}个供应商")
            return True

        except Exception as e:
            logger.error(f"加载产业链失败: {e}")
            return False

    def load_analysis_reports(self) -> bool:
        """
        加载Step3c的财报分析结果

        Returns:
            bool: 是否成功加载
        """
        try:
            if not self.analysis_dir.exists():
                logger.warning(f"分析目录不存在: {self.analysis_dir}")
                return False

            # 扫描所有.md文件
            for md_file in self.analysis_dir.glob("*.md"):
                company_name = md_file.stem.replace("03_", "")

                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # 提取关键信息
                self.analysis_reports[company_name] = {
                    "file": str(md_file),
                    "content": content,
                    "customers": self._extract_customers(content),
                    "suppliers": self._extract_suppliers(content),
                    "revenue_items": self._extract_revenue_items(content),
                }

            logger.info(f"成功加载{len(self.analysis_reports)}份财报分析")
            return True

        except Exception as e:
            logger.error(f"加载分析报告失败: {e}")
            return False

    def load_news_data(self) -> bool:
        """
        加载Step4b的分类新闻

        Returns:
            bool: 是否成功加载
        """
        try:
            if not self.news_dir.exists():
                logger.warning(f"新闻目录不存在: {self.news_dir}")
                return False

            # 扫描所有YAML文件
            for yaml_file in self.news_dir.glob("*.yaml"):
                company_name = yaml_file.stem.replace("_news_classified", "")

                with open(yaml_file, "r", encoding="utf-8") as f:
                    news_list = yaml.safe_load(f)

                if isinstance(news_list, list):
                    # 提取与供应链相关的新闻
                    keywords = [
                        "合作",
                        "战略合作",
                        "供货",
                        "供应",
                        "采购",
                        "订单",
                        "客户",
                        "中标",
                        "签约",
                        "partnership",
                        "cooperation",
                        "supply",
                    ]
                    partnership_news = [
                        n for n in news_list if any(k in str(n) for k in keywords)
                    ]
                    self.news_data[company_name] = partnership_news

            logger.info(f"加载{len(self.news_data)}家公司的新闻数据")
            return True

        except Exception as e:
            logger.error(f"加载新闻数据失败: {e}")
            return False

    def verify_relationships(self) -> List[Dict]:
        """
        验证产业链关系

        Returns:
            List[Dict]: 验证结果列表
        """
        results = []

        for supplier, details in self.supply_chain.items():
            for customer in details["customers"]:
                result = {
                    "supplier": supplier,
                    "customer": customer,
                    "products": details.get("products", []),
                    "verification": self._check_mutual_mention(supplier, customer),
                    "news_confirmation": self._check_news_confirmation(
                        supplier, customer
                    ),
                    "confidence": 0,
                    "risks": [],
                }

                # 计算置信度
                evidence_count = 0
                if result["verification"]["in_financial_reports"]:
                    evidence_count += 2
                if result["news_confirmation"]:
                    evidence_count += 1

                result["confidence"] = min(100, evidence_count * 25)  # 0-100分

                # 识别风险
                if result["confidence"] < 50:
                    result["risks"].append("关系确认度低，可能不存在业务关系")

                results.append(result)

        self.verification_results = results
        return results

    def identify_bottlenecks(self) -> Dict[str, List]:
        """
        识别产业链中的瓶颈位置

        Returns:
            Dict: 瓶颈识别结果
        """
        bottlenecks = {
            "single_supplier": [],  # 单一供应商
            "single_customer": [],  # 单一客户
            "critical_position": [],  # 关键位置
        }

        # 统计每个公司的供应商和客户数量
        supplier_count = defaultdict(int)
        customer_count = defaultdict(int)

        for result in self.verification_results:
            supplier_count[result["supplier"]] += 1
            customer_count[result["customer"]] += 1

        # 识别瓶颈
        for supplier, count in supplier_count.items():
            if count == 1:
                bottlenecks["single_supplier"].append(
                    {"company": supplier, "risk": "只有一个客户，客户流失风险大"}
                )

        for customer, count in customer_count.items():
            if count == 1:
                bottlenecks["single_customer"].append(
                    {"company": customer, "risk": "只有一个供应商，供应中断风险大"}
                )

        return bottlenecks

    def generate_verification_report(self) -> None:
        """
        生成验证报告
        """
        output_file = self.output_dir / "report" / "03.5_供应链验证表.md"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# Step3.5 产业链验证表\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("## 验证结果汇总\n\n")
            f.write(
                "| 供应商 | 客户 | 产品 | 财报确认 | 新闻确认 | 置信度 | 风险等级 |\n"
            )
            f.write(
                "|--------|------|------|---------|---------|--------|----------|\n"
            )

            for result in self.verification_results:
                supplier = result["supplier"]
                customer = result["customer"]
                products = ", ".join(result["products"][:2])  # 最多显示2个
                financial = (
                    "✅" if result["verification"]["in_financial_reports"] else "❌"
                )
                news = "✅" if result["news_confirmation"] else "❌"
                confidence = f"{result['confidence']}%"
                risk_level = self._assess_risk_level(result)

                f.write(
                    f"| {supplier} | {customer} | {products} | {financial} | {news} | {confidence} | {risk_level} |\n"
                )

            # 瓶颈识别
            bottlenecks = self.identify_bottlenecks()

            f.write("\n## 瓶颈位置识别\n\n")

            if bottlenecks["single_supplier"]:
                f.write("### 单一供应商风险\n")
                for item in bottlenecks["single_supplier"]:
                    f.write(f"- **{item['company']}**: {item['risk']}\n")
                f.write("\n")

            if bottlenecks["single_customer"]:
                f.write("### 单一客户风险\n")
                for item in bottlenecks["single_customer"]:
                    f.write(f"- **{item['company']}**: {item['risk']}\n")
                f.write("\n")

            f.write("## 建议\n\n")
            f.write("- 🔴 **置信度<50%**: 需要进一步调查或等待更多确认\n")
            f.write("- 🟡 **置信度50-75%**: 保持关注，但存在不确定性\n")
            f.write("- 🟢 **置信度>75%**: 供应链关系基本确认，可以投资\n")

        logger.info(f"验证报告已生成: {output_file}")

    def generate_risk_map(self) -> None:
        """
        生成供应链风险地图
        """
        output_file = self.output_dir / "report" / "03.5_供应链风险地图.md"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# Step3.5 供应链风险地图\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # 按风险等级分类
            high_risk = [r for r in self.verification_results if r["confidence"] < 50]
            medium_risk = [
                r for r in self.verification_results if 50 <= r["confidence"] < 75
            ]
            low_risk = [r for r in self.verification_results if r["confidence"] >= 75]

            f.write(f"## 风险分布\n\n")
            f.write(f"- 🔴 高风险: {len(high_risk)}条关系\n")
            f.write(f"- 🟡 中风险: {len(medium_risk)}条关系\n")
            f.write(f"- 🟢 低风险: {len(low_risk)}条关系\n\n")

            if high_risk:
                f.write("## 高风险关系\n\n")
                for r in high_risk:
                    f.write(f"⚠️  {r['supplier']} → {r['customer']}\n")
                    f.write(f"   - 置信度: {r['confidence']}%\n")
                    for risk in r["risks"]:
                        f.write(f"   - {risk}\n")
                    f.write("\n")

        logger.info(f"风险地图已生成: {output_file}")

    def _check_mutual_mention(self, supplier: str, customer: str) -> Dict:
        """
        检查财报中的互相提及
        """
        supplier_key = self._find_report_key(supplier)
        customer_key = self._find_report_key(customer)

        supplier_content = (
            self.analysis_reports.get(supplier_key, {}).get("content", "")
            if supplier_key
            else ""
        )
        customer_content = (
            self.analysis_reports.get(customer_key, {}).get("content", "")
            if customer_key
            else ""
        )

        supplier_mentions_customer, supplier_evidence = self._find_mentions(
            supplier_content, customer
        )
        customer_mentions_supplier, customer_evidence = self._find_mentions(
            customer_content, supplier
        )

        evidence = supplier_evidence + customer_evidence

        return {
            "in_financial_reports": supplier_mentions_customer
            or customer_mentions_supplier,
            "customer_mentioned_supplier": customer_mentions_supplier,
            "supplier_mentioned_customer": supplier_mentions_customer,
            "evidence": evidence,
        }

    def _check_news_confirmation(self, supplier: str, customer: str) -> bool:
        """
        检查新闻中的确认
        """
        supplier_key = self._find_report_key(supplier)
        customer_key = self._find_report_key(customer)

        news_sources = []
        if supplier_key and supplier_key in self.news_data:
            news_sources.extend(self.news_data[supplier_key])
        if customer_key and customer_key in self.news_data:
            news_sources.extend(self.news_data[customer_key])

        for item in news_sources:
            text = f"{item.get('title', '')} {item.get('content_summary', '')}"
            if self._name_in_text(supplier, text) and self._name_in_text(
                customer, text
            ):
                return True
        return False

    @staticmethod
    def _extract_customers(content: str) -> List[str]:
        """从内容中提取客户名称"""
        pattern = r"客户[：:]\s*([^\n]+)"
        matches = re.findall(pattern, content)
        return [m.strip() for m in matches]

    @staticmethod
    def _extract_suppliers(content: str) -> List[str]:
        """从内容中提取供应商名称"""
        pattern = r"供应商[：:]\s*([^\n]+)"
        matches = re.findall(pattern, content)
        return [m.strip() for m in matches]

    @staticmethod
    def _extract_revenue_items(content: str) -> List[str]:
        """从内容中提取收入项目"""
        pattern = r"收入[：:]\s*([^\n]+)"
        matches = re.findall(pattern, content)
        return [m.strip() for m in matches]

    def _find_report_key(self, company_name: str) -> Optional[str]:
        """根据公司名在分析报告中定位key"""
        if company_name in self.analysis_reports:
            return company_name
        for key in self.analysis_reports.keys():
            if company_name in key or key in company_name:
                return key
        return None

    @staticmethod
    def _name_variants(name: str) -> List[str]:
        variants = {name}
        for suffix in ["股份有限公司", "有限公司", "股份"]:
            if name.endswith(suffix):
                variants.add(name.replace(suffix, ""))
        return list(variants)

    def _name_in_text(self, name: str, text: str) -> bool:
        return any(v in text for v in self._name_variants(name))

    def _find_mentions(self, content: str, target: str) -> Tuple[bool, List[str]]:
        if not content:
            return False, []
        evidence = []
        for line in content.splitlines():
            if self._name_in_text(target, line):
                evidence.append(line.strip())
            if len(evidence) >= 3:
                break
        return (len(evidence) > 0), evidence

    @staticmethod
    def _assess_risk_level(result: Dict) -> str:
        """评估风险等级"""
        confidence = result["confidence"]
        if confidence >= 75:
            return "🟢 低风险"
        elif confidence >= 50:
            return "🟡 中风险"
        else:
            return "🔴 高风险"


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Step3.5: 产业链验证",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python step3.5_supply_chain_verify.py \\
    --supply-chain ../step2/02_产业链挖掘_人形机器人_YYYYQx.md \\
    --analysis ../step3/analysis/ \\
    --news ../step4/classified/ \\
    --output ../step3.5/
        """,
    )

    parser.add_argument(
        "--supply-chain", "-s", required=True, help="Step2产业链文件路径"
    )
    parser.add_argument("--analysis", "-a", required=True, help="Step3c分析报告目录")
    parser.add_argument("--news", "-n", required=True, help="Step4b分类新闻目录")
    parser.add_argument("--output", "-o", default="../step3.5/", help="输出目录")

    args = parser.parse_args()

    verifier = SupplyChainVerifier(
        supply_chain_file=args.supply_chain,
        analysis_dir=args.analysis,
        news_dir=args.news,
        output_dir=args.output,
    )

    # 执行验证流程
    if not verifier.load_supply_chain():
        logger.error("加载产业链失败")
        return 1

    verifier.load_analysis_reports()
    verifier.load_news_data()
    verifier.verify_relationships()
    verifier.generate_verification_report()
    verifier.generate_risk_map()

    logger.info("产业链验证完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
