"""从知乎专栏 API 批量获取量子位文章列表并筛选大模型相关文章。"""

import json
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))


def fetch_column_articles(
    column_id: str = "qbitai",
    max_pages: int = 50,
    since_timestamp: Optional[int] = None,
) -> list[dict]:
    """通过知乎 API 获取专栏文章列表，使用 requests + cookies 绕过登录限制。"""
    import requests

    cookies_path = Path(__file__).parent / "zhihu_cookies.json"
    cookie_dict = {}
    if cookies_path.exists():
        raw_cookies = json.loads(cookies_path.read_text(encoding="utf-8"))
        cookie_dict = {c["name"]: c["value"] for c in raw_cookies}
        print(f"[cookies] 加载了 {len(cookie_dict)} 个 cookie", file=sys.stderr)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Referer": "https://www.zhihu.com/",
        "Accept": "application/json",
    }

    all_articles = []
    offset = 0
    page_size = 10

    for page in range(max_pages):
        url = f"https://www.zhihu.com/api/v4/columns/{column_id}/items?limit={page_size}&offset={offset}"
        print(
            f"[page {page+1}] offset={offset}, 已获取 {len(all_articles)} 篇",
            file=sys.stderr,
        )

        resp = requests.get(url, headers=headers, cookies=cookie_dict, timeout=30)
        if resp.status_code != 200:
            print(f"[error] Status {resp.status_code}, stopping", file=sys.stderr)
            break

        data = resp.json()
        articles = data.get("data", [])

        if not articles:
            need_login = data.get("need_force_login", False)
            if need_login:
                print("[error] API 要求登录，cookies 可能已失效", file=sys.stderr)
            else:
                print("[info] No more articles", file=sys.stderr)
            break

        for article in articles:
            created = article.get("created", 0)
            if since_timestamp and created < since_timestamp:
                print(f"[stop] 已到达截止日期之前的文章，停止获取", file=sys.stderr)
                return all_articles

            all_articles.append(
                {
                    "id": article.get("id"),
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "created": created,
                    "excerpt": article.get("excerpt", "")[:200],
                    "voteup_count": article.get("voteup_count", 0),
                    "comment_count": article.get("comment_count", 0),
                }
            )

        paging = data.get("paging", {})
        if paging.get("is_end", True):
            print("[info] Reached end of articles", file=sys.stderr)
            break

        offset += page_size
        time.sleep(0.5)

    return all_articles


def filter_llm_articles(articles: list[dict]) -> list[dict]:
    """筛选大模型/AI 相关文章。"""
    keywords = [
        "大模型",
        "模型",
        "LLM",
        "GPT",
        "Claude",
        "Gemini",
        "Llama",
        "DeepSeek",
        "龙虾",  # 知乎对大模型的谐称
        "Agent",
        "AI",
        "人工智能",
        "训练",
        "推理",
        "微调",
        "开源",
        "transformer",
        "语言模型",
        "多模态",
        "Sora",
        "OpenAI",
        "Anthropic",
        "Google",
        "Meta",
        "Qwen",
        "通义",
        "文心",
        "智谱",
        "百川",
        "Kimi",
        "生成式",
        "RAG",
        "MCP",
        "向量",
        "嵌入",
        "token",
        "参数",
        "基座",
        "对齐",
        "RLHF",
        "DPO",
        "上下文",
        "context",
        "机器人",
        "robot",
    ]

    filtered = []
    for article in articles:
        title = article.get("title", "")
        excerpt = article.get("excerpt", "")
        text = title + " " + excerpt
        if any(kw.lower() in text.lower() for kw in keywords):
            filtered.append(article)

    return filtered


def main() -> None:
    import datetime

    # 近两个月：从 2026年1月11日 到 2026年3月11日
    two_months_ago = datetime.datetime(2026, 1, 11, tzinfo=datetime.timezone.utc)
    since_ts = int(two_months_ago.timestamp())

    print(f"[config] 获取 {two_months_ago.date()} 以来的文章", file=sys.stderr)
    print(f"[config] 截止时间戳: {since_ts}", file=sys.stderr)

    articles = fetch_column_articles(
        column_id="qbitai",
        max_pages=80,
        since_timestamp=since_ts,
    )

    print(f"\n[result] 共获取 {len(articles)} 篇文章（近两个月）", file=sys.stderr)

    llm_articles = filter_llm_articles(articles)
    print(f"[result] 其中大模型相关: {len(llm_articles)} 篇", file=sys.stderr)

    output = {
        "total_articles": len(articles),
        "llm_articles_count": len(llm_articles),
        "llm_articles": llm_articles,
        "all_articles": articles,
    }

    output_path = (
        Path(__file__).parent.parent.parent.parent.parent
        / "爬虫配置"
        / "qbitai_articles.json"
    )
    output_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[saved] {output_path}", file=sys.stderr)

    print("\n--- 大模型相关文章 ---", file=sys.stderr)
    for i, a in enumerate(llm_articles[:30], 1):
        ts = datetime.datetime.fromtimestamp(a["created"], tz=datetime.timezone.utc)
        print(f"{i:3d}. [{ts.strftime('%m-%d')}] {a['title'][:60]}", file=sys.stderr)
        print(f"     {a['url']}", file=sys.stderr)


if __name__ == "__main__":
    main()
