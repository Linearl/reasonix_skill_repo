#!/usr/bin/env python3
"""
小红书用户画像分析脚本
基于 MediaCrawler 采集的数据进行多维度用户画像分析
"""

import json
import pandas as pd
from collections import Counter
from datetime import datetime
from typing import Dict, List, Tuple


def load_jsonl(file_path: str) -> pd.DataFrame:
    """加载 JSONL 文件为 DataFrame"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return pd.DataFrame(data)


def get_fans_level(fans_count: int) -> str:
    """根据粉丝数判断账号等级"""
    if fans_count < 1000:
        return '素人'
    elif fans_count < 10000:
        return '小达人'
    elif fans_count < 100000:
        return '中腰部博主'
    else:
        return '头部博主'


def analyze_basic_info(creators_df: pd.DataFrame) -> Dict:
    """分析用户基础信息"""
    if creators_df.empty:
        return {}

    creator = creators_df.iloc[0]
    fans = creator.get('fans_count', 0)

    return {
        'nickname': creator.get('nickname', ''),
        'desc': creator.get('desc', ''),
        'fans_count': fans,
        'fans_level': get_fans_level(fans),
        'follows_count': creator.get('follows', 0),
        'total_fav': creator.get('total_fav', 0),
    }


def analyze_content(notes_df: pd.DataFrame) -> Dict:
    """分析用户内容特征"""
    if notes_df.empty:
        return {}

    # 话题标签分析
    all_tags = []
    for tags in notes_df['tag_list'].dropna():
        if isinstance(tags, list):
            all_tags.extend(tags)
    top_tags = Counter(all_tags).most_common(20)

    # 内容长度
    notes_df['title_len'] = notes_df['title'].fillna('').str.len()
    notes_df['desc_len'] = notes_df['desc'].fillna('').str.len()

    # 媒体类型
    type_dist = notes_df['type'].value_counts().to_dict()

    # 发布时间分析
    notes_df['publish_time'] = pd.to_datetime(notes_df['time'], unit='ms', errors='coerce')
    hour_dist = notes_df['publish_time'].dt.hour.value_counts().sort_index().to_dict()
    weekday_dist = notes_df['publish_time'].dt.weekday.value_counts().sort_index().to_dict()

    return {
        'note_count': len(notes_df),
        'top_tags': top_tags,
        'avg_title_len': notes_df['title_len'].mean(),
        'avg_desc_len': notes_df['desc_len'].mean(),
        'media_type_dist': type_dist,
        'hour_dist': hour_dist,
        'weekday_dist': weekday_dist,
    }


def analyze_engagement(notes_df: pd.DataFrame) -> Dict:
    """分析笔记互动数据"""
    if notes_df.empty:
        return {}

    # 计算总互动量
    notes_df['total_engagement'] = (
        notes_df['liked_count'].fillna(0) +
        notes_df['collected_count'].fillna(0) +
        notes_df['comment_count'].fillna(0)
    )

    # 爆款判定（互动量 > 均值 + 2倍标准差）
    mean_eng = notes_df['total_engagement'].mean()
    std_eng = notes_df['total_engagement'].std()
    threshold = mean_eng + 2 * std_eng
    viral_notes = notes_df[notes_df['total_engagement'] > threshold]

    # 最高互动笔记
    top_note = notes_df.loc[notes_df['total_engagement'].idxmax()] if len(notes_df) > 0 else None

    return {
        'avg_likes': notes_df['liked_count'].mean(),
        'avg_collects': notes_df['collected_count'].mean(),
        'avg_comments': notes_df['comment_count'].mean(),
        'engagement_std': std_eng,
        'viral_rate': len(viral_notes) / len(notes_df),
        'top_note': {
            'title': top_note['title'] if top_note is not None else '',
            'engagement': top_note['total_engagement'] if top_note is not None else 0,
        } if top_note is not None else None,
    }


def analyze_comments(comments_df: pd.DataFrame) -> Dict:
    """分析评论区数据，生成受众画像"""
    if comments_df.empty:
        return {}

    # 评论者统计
    commenters = comments_df.groupby('user_id').agg({
        'nickname': 'first',
        'content': 'count',
    }).reset_index()
    commenters.columns = ['user_id', 'nickname', 'comment_count']

    # 活跃评论者（>= 3次）
    active_commenters = commenters[commenters['comment_count'] >= 3]

    # 情感分析（简单关键词匹配）
    positive_keywords = ['好看', '喜欢', '赞', '棒', '美', '爱', '收藏', '关注', '支持', '加油', '太', '好']
    negative_keywords = ['不好', '差', '丑', '假', '骗', '垃圾', '难看', '失望']

    def classify_sentiment(text):
        text = str(text)
        pos = sum(1 for k in positive_keywords if k in text)
        neg = sum(1 for k in negative_keywords if k in text)
        if pos > neg:
            return '正面'
        elif neg > pos:
            return '负面'
        return '中性'

    comments_df['sentiment'] = comments_df['content'].apply(classify_sentiment)
    sentiment_dist = comments_df['sentiment'].value_counts(normalize=True).to_dict()

    # 作者回复率
    if 'is_author' in comments_df.columns:
        author_replies = comments_df[comments_df['is_author'] == True]
        reply_rate = len(author_replies) / len(comments_df)
    else:
        reply_rate = 0

    # 评论关键词（简单字频）
    all_comments_text = ''.join(comments_df['content'].astype(str).tolist())
    # 这里简化处理，实际可用 jieba 分词
    word_counts = Counter(all_comments_text).most_common(50)

    return {
        'total_comments': len(comments_df),
        'unique_commenters': len(commenters),
        'active_commenters': len(active_commenters),
        'sentiment_dist': sentiment_dist,
        'author_reply_rate': reply_rate,
        'top_commenters': commenters.nlargest(10, 'comment_count').to_dict('records'),
    }


def generate_report(
    basic_info: Dict,
    content_analysis: Dict,
    engagement_analysis: Dict,
    comment_analysis: Dict
) -> str:
    """生成用户画像报告"""

    report = []
    report.append("# 小红书用户画像报告")
    report.append(f"\n生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    report.append("---\n")

    # 一、基础信息
    report.append("## 一、基础信息\n")
    report.append("| 指标 | 数值 |")
    report.append("|------|------|")
    report.append(f"| 昵称 | {basic_info.get('nickname', '-')} |")
    report.append(f"| 粉丝数 | {basic_info.get('fans_count', 0):,} |")
    report.append(f"| 账号等级 | {basic_info.get('fans_level', '-')} |")
    report.append(f"| 关注数 | {basic_info.get('follows_count', 0):,} |")
    report.append(f"| 获赞与收藏 | {basic_info.get('total_fav', 0):,} |")
    report.append(f"| 签名 | {basic_info.get('desc', '-')} |")
    report.append("")

    # 二、内容分析
    report.append("## 二、内容分析\n")
    report.append(f"### 2.1 概况")
    report.append(f"- 笔记总数：{content_analysis.get('note_count', 0)}")
    report.append(f"- 平均标题长度：{content_analysis.get('avg_title_len', 0):.0f} 字")
    report.append(f"- 平均正文长度：{content_analysis.get('avg_desc_len', 0):.0f} 字")
    report.append("")

    # 热门话题
    top_tags = content_analysis.get('top_tags', [])
    if top_tags:
        report.append("### 2.2 热门话题 TOP 10\n")
        report.append("| 话题 | 出现次数 |")
        report.append("|------|----------|")
        for tag, count in top_tags[:10]:
            report.append(f"| {tag} | {count} |")
        report.append("")

    # 三、互动分析
    report.append("## 三、互动分析\n")
    report.append("| 指标 | 数值 |")
    report.append("|------|------|")
    report.append(f"| 平均点赞 | {engagement_analysis.get('avg_likes', 0):.0f} |")
    report.append(f"| 平均收藏 | {engagement_analysis.get('avg_collects', 0):.0f} |")
    report.append(f"| 平均评论 | {engagement_analysis.get('avg_comments', 0):.0f} |")
    report.append(f"| 爆款率 | {engagement_analysis.get('viral_rate', 0):.1%} |")
    report.append("")

    # 四、受众画像
    report.append("## 四、受众画像（评论区分析）\n")
    report.append("### 4.1 评论概况\n")
    report.append("| 指标 | 数值 |")
    report.append("|------|------|")
    report.append(f"| 总评论数 | {comment_analysis.get('total_comments', 0):,} |")
    report.append(f"| 独立评论者 | {comment_analysis.get('unique_commenters', 0):,} |")
    report.append(f"| 活跃评论者 | {comment_analysis.get('active_commenters', 0):,} |")
    report.append(f"| 作者回复率 | {comment_analysis.get('author_reply_rate', 0):.1%} |")
    report.append("")

    # 情感分布
    sentiment_dist = comment_analysis.get('sentiment_dist', {})
    if sentiment_dist:
        report.append("### 4.2 情感分布\n")
        report.append("| 情感 | 占比 |")
        report.append("|------|------|")
        for sentiment, ratio in sentiment_dist.items():
            report.append(f"| {sentiment} | {ratio:.1%} |")
        report.append("")

    # 五、总结
    report.append("## 五、总结\n")
    report.append("### 内容特点")
    report.append(f"- 主要领域：{', '.join([t[0] for t in top_tags[:3]]) if top_tags else '未知'}")
    report.append(f"- 内容风格：{'图文为主' if content_analysis.get('media_type_dist', {}).get('normal', 0) > content_analysis.get('media_type_dist', {}).get('video', 0) else '视频为主'}")
    report.append("")
    report.append("### 受众特征")
    report.append(f"- 受众规模：{comment_analysis.get('unique_commenters', 0)} 位独立评论者")
    report.append(f"- 互动氛围：{'积极' if sentiment_dist.get('正面', 0) > 0.5 else '中性'}")
    report.append("")

    return '\n'.join(report)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='小红书用户画像分析')
    parser.add_argument('--data-dir', default='data/xhs', help='数据目录路径')
    parser.add_argument('--output', default='user_profile_report.md', help='报告输出路径')
    args = parser.parse_args()

    print("🔍 小红书用户画像分析工具")
    print("=" * 50)

    # 加载数据
    print("\n📊 加载数据...")
    try:
        creators_df = load_jsonl(f'{args.data_dir}/creators.jsonl')
        notes_df = load_jsonl(f'{args.data_dir}/notes.jsonl')
        comments_df = load_jsonl(f'{args.data_dir}/comments.jsonl')
    except FileNotFoundError as e:
        print(f"❌ 数据文件不存在: {e}")
        print("请先运行 MediaCrawler 采集数据")
        return

    print(f"  - 创作者信息: {len(creators_df)} 条")
    print(f"  - 笔记数据: {len(notes_df)} 条")
    print(f"  - 评论数据: {len(comments_df)} 条")

    # 分析
    print("\n⏳ 分析中...")
    basic_info = analyze_basic_info(creators_df)
    content_analysis = analyze_content(notes_df)
    engagement_analysis = analyze_engagement(notes_df)
    comment_analysis = analyze_comments(comments_df)

    # 生成报告
    print("\n📝 生成报告...")
    report = generate_report(basic_info, content_analysis, engagement_analysis, comment_analysis)

    # 保存报告
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ 报告已保存至: {args.output}")

    # 打印摘要
    print("\n" + "=" * 50)
    print("📋 分析摘要")
    print(f"  用户: {basic_info.get('nickname', '-')}")
    print(f"  粉丝: {basic_info.get('fans_count', 0):,} ({basic_info.get('fans_level', '-')})")
    print(f"  笔记: {content_analysis.get('note_count', 0)} 篇")
    print(f"  平均互动: {engagement_analysis.get('avg_likes', 0):.0f} 赞 / {engagement_analysis.get('avg_collects', 0):.0f} 藏 / {engagement_analysis.get('avg_comments', 0):.0f} 评")
    print(f"  评论者: {comment_analysis.get('unique_commenters', 0)} 人")


if __name__ == '__main__':
    main()
