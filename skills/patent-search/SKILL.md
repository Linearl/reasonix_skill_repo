---
name: patent-search
description: 专利检索与可专利性分析：innojoy/Google Patents 自动化检索、检索式设计、对比文件分级、新颖性/创造性评估与交底书撰写
---

# 专利检索与可专利性分析 Playbook

## 何时使用
用户要求"检索专利/查现有技术/FTO/评估新颖性/写交底书/找对比文件"时使用。支持从想法评估到交底书产出的完整流程。

## 流程总览
1. **梳理技术方案**：把用户构思拆成技术特征表（问题/手段/改进点/应用），确定检索主题词
2. **多平台检索**：innojoy（中国库为主）+ Google Patents（全球+中文）交叉验证
3. **对比文件精读**：抓取最接近文件的全文（Google Patents HTML 或用户下载的 PDF）
4. **逐特征比对**：特征表 × 对比文件，标出"已公开/未公开"
5. **输出**：评估报告（新颖性/创造性结论+权利要求布局建议）→ 技术交底书（背景/方案/实施例/权利要求初稿）

## 检索平台一：innojoy（大为，中国专利）

### 自动化接口（2026-08 逆向验证可用）
- **登录**：POST `https://www.innojoy.com/front/user/userManager`
  ```json
  {"requestModule":"UserManager","userConfig":{"Action":"Login","EMail":"<账号>","AreaCode":"","Password":"<密码>","GUID":"","ChkCode":"","userAgent":"Mozilla/5.0","remember":true,"OperType":""},"systemConfig":{"SystemTitle":null}}
  ```
  首次登录无需验证码（失败 ≥3 次才出现图形验证码）。登录前先 GET `https://www.innojoy.com/search/index.html` 建立会话。成功返回 `Option.GUID`（作为后续 userId 参数）。
- **检索**：POST `https://www.innojoy.com/client/interface.aspx`
  ```json
  {"requestModule":"PatentSearch","userId":"<登录GUID>","patentSearchConfig":{"Query":"<检索式>","TreeQuery":"","Database":"fmzl,fmsq,syxx","Action":"Search","DBOnly":0,"Page":1,"IsPatentList":true,"PageSize":20,"GUID":"","Sortby":"","AddOnes":"","DelOnes":"","RemoveOnes":"","SmartSearch":""}}
  ```
  返回 `Option.PatentList`（每件含 PNM/AN/AD/PD/TI/ABST(空)/PATMS/INNTMS/DB/DN/RNO/LLS 等）+ `Option.Count`（命中数）。
- **分页**：第 2 页起必须携带上一页响应 `Option.GUID` 作为 `patentSearchConfig.GUID`
- **限流规避**（关键经验）：连续检索会报"请从首页开始检索"/"发生错误，请稍后重试"——**每个检索式用独立 Session 重新登录**，检索间 sleep 3~5s，失败按 5s/15s/30s 退避重试
- **全文/摘要**：列表接口 ABST 为空；`LoadFullText` 触发图形验证码，不适合自动化。需要全文时用 Google Patents 或让用户从 innojoy 网页端下载 PDF
- **数据库代码**：fmzl=发明、fmsq=发明申请、syxx=实用新型、wgzl=外观、CN="fmsq,wgzl,syxx,fmzl"、US="usapp,uspat,uspat1,usdes"、EP="epapp,eppat"、WO="wopat"
- **字段代码**：TI=名称、ABST=摘要、PA/PATMS=申请人、INN/INNTMS=发明人、PNM=公开号、AN=申请号、AD=申请日、PD=公开日、DN=文档号、LLS=法律状态、DB=库代码

### 可用脚本
工作区 `scripts/patent_search/innojoy_search.py`（登录+单条/批量检索+JSON 输出）+ `queries.txt`（检索式模板）。用法：
```bash
INNOJOY_EMAIL=<账号> INNOJOY_PASSWORD=<密码> python innojoy_search.py --list queries.txt --out results
```
账号通过环境变量或 `--email/--password` 传入，**不要把密码写进代码/文档**。

## 检索平台二：Google Patents

- **列表检索**：`https://patents.google.com/xhr/query?url=q%3D<URL编码检索式>&exp=` 返回 JSON（id/title/snippet/priority_date/assignee 等），无需登录
- **全文**：`https://patents.google.com/patent/<公开号>/en`（或 `/zh`）返回可读 HTML 文本，含 Abstract/Description/Claims/背景技术/引证与被引（Families Citing / Similar Documents 是扩展对比文件的金矿）
- **限流**：连续抓取会 503（"Sorry... automated queries"），需放慢频率（每次间隔数秒~数十秒），或改用 curl 带浏览器 UA
- **顺藤摸瓜**：读全文时重点看 "Families Citing this family"（被谁引用=后续布局者）、"Citations"（引用了谁=技术来源）、"Similar Documents"（近似文件）

## 检索式设计
- **中文 innojoy**：`TI=(油烟机 or 吸油烟机) and ABST=(烟感 or 传感器) and ABST=(摄像头 or 视觉)`；字段用英文括号 `()`，and/or/not 支持
- **英文 Google Patents**：`"smoke sensor" camera training label rangehood`（带引号精确匹配）
- **组合策略**：①核心交集（主题词×关键手段）②问题词（标注/训练/数据集）③空白验证词（滞后/时间偏移/对齐——命中 0 或无关=创新点成立）④发明人/申请人全景
- **中文+英文都要检**，中日（富士工業等日企）也常出相关方案

## 对比文件分级与评估
- **★★★ 最接近**：同技术路线（读全文）——直接决定新颖性
- **★★ 相关**：方向相近（至少读摘要/权利要求）
- **★ 参考**：行业布局背景
- 评估输出包含：逐特征比对表（特征×对比文件）、新颖性结论（哪个特征保住了）、创造性风险（审查员可能的组合方式）、权利要求布局建议（独权放什么特征、从权放什么、避让什么）

## 输出模板
1. `docs/patent_search_report_<主题>.md`：检索概况（平台/检索式/命中数）→ 分级清单 → 关键发现 → 建议
2. `docs/patent_<主题>_evaluation.md`：可专利性评估（对比文件分析+逐特征比对+结论）
3. `docs/patent_<主题>_disclosure.md`：技术交底书（技术领域/背景技术/发明内容/实施例/附图说明/权利要求初稿/待补实验数据）

## 经验教训
- 检索平台返回的中文乱码通常是 Windows 控制台编码问题：跑 Python 加 `PYTHONIOENCODING=utf-8`
- 商业平台（innojoy 等）接口会变，逆向步骤失效时回到浏览器手动操作 + 重新抓 JS 分析
- 独权被最接近文件覆盖时，把"区别特征"（如时间偏移/具体数值区间/标定方法）提升为独权必要特征
- 申请前提醒用户检查：在先公开（论文/公众号/开源）、实验数据支撑、发明人/申请人确认
