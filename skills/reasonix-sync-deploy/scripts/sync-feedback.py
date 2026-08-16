#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pull 后检查/反馈模板生成器（台式机 WIN-20230124GEV 建议，2026-08-16 落地）

用途：Pull 任务执行后自动运行本脚本，在 feedback\\ 生成
      pull-review-<周>-<本机计算机名>.md 检查/反馈模板；
      各机按模板完成检查后填写，主力机下轮 Organize 时纳入处理。

用法：
  python sync-feedback.py            # 生成本周模板（覆盖同周旧模板）
  python sync-feedback.py --week 2026-W33
"""
import argparse
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync_common as C


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", default=None)
    args = ap.parse_args()

    root = C.sync_root()
    machine = C.machine_name(C.load_config())
    week = args.week or C.iso_week()
    fb_dir = root / "feedback"
    fb_dir.mkdir(parents=True, exist_ok=True)
    out = fb_dir / f"pull-review-{week}-{machine}.md"

    # 本机 Pull 后状态（尽力统计，读不到就留空）
    home = Path(C.reasonix_home())
    n_facts = len([f for f in (home / "memory" / "global").glob("*.md") if f.name != "MEMORY.md"]) if (home / "memory" / "global").is_dir() else 0
    n_skills = sum(1 for d in (home / "skills").iterdir()) if (home / "skills").is_dir() else 0
    has_cred = (home / "global-workspace" / "credential").is_dir()

    now = C.now_iso()
    content = f"""# Pull 检查与反馈模板：{machine}（{week}）

- 生成：{now}（Pull 任务执行后自动生成，`sync-feedback.py`）
- 说明：本文件是**待办提示**。按下方清单检查后，把「检查结果」「发现的问题」「对体系的建议」填进第三、四节，保存即成为反馈报告。主力机下轮 Organize 时可见 `feedback\\` 目录。

## 一、本次 Pull 摘要

```
（Pull 输出摘要可粘贴到这里；本机当前：全局记忆 {n_facts} 条、技能 {n_skills} 个、凭据收口 {'✓ 已完成' if has_cred else '✗ 未完成'}）
```

## 二、检查清单（对照 dist\\PULL-GUIDE.md）

- [ ] 技能生效：`%APPDATA%\\reasonix\\skills\\` 出现新技能目录，会话中技能索引可见
- [ ] 记忆可 recall：提及新记忆主题能检索到
- [ ] 机器特定条目按需处理：dist 中 ⚠️ 条目本机用不到的保留无害或 forget
- [ ] 本机环境记忆（local-env-notes 等）缺失/过时则补充，不发布到 dist
- [ ] 凭据收口：本机明文凭据在 `global-workspace\\credential\\`，记忆/技能无明文

## 三、检查结果与发现的问题

（填写：本次 Pull 是否正常？覆盖/保留是否符合预期？有无异常？）

## 四、对体系的建议

（填写：脚本/流程/文档的改进建议，主力机处理）

## 五、备注

（可选）
"""
    C.atomic_write(out, content)
    print(f"== 反馈模板已生成: {out}")
    C.log("feedback", f"week={week} machine={machine} -> {out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
