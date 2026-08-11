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
- **限流/封锁**：连续抓取会 503（"Sorry... automated queries"），需放慢频率；**IP 被 Google 风控时是整页超时/503（本会话曾数小时不可达）——先检查本地代理**：curl -x socks5://127.0.0.1:<本地代理端口> -x 或 -x http://127.0.0.1:<本地代理端口>（clash/v2rayN 常见端口），带浏览器 UA 即可恢复。技能使用者环境若有代理，默认带上
- **XHR API**（列表/摘要，轻量）：`https://patents.google.com/xhr/query?url=q%3D<编码检索式>&exp=`，无需登录，比整页稳定
- **顺藤摸瓜**：读全文时重点看 "Families Citing this family"（被谁引用=后续布局者）、"Citations"（引用了谁=技术来源）、"Similar Documents"（近似文件）

## 检索平台三：论文调研（arXiv / OpenAlex，已跑通验证 2026-08）

专利之外还需查论文（背景技术、方法演进、数据集）。**直接跑脚本**：
`scripts/patent_search/paper_search.py --arxiv '"smoke detection" AND video' --openalex "kitchen smoke detection" --n 12 --out report.md`
（脚本在本机某个工作区；其他工作区可复制脚本，仅依赖标准库）

要点：
- **arXiv**：`https://export.arxiv.org/api/query?search_query=all:<检索词>&start=0&max_results=N&sortBy=relevance`，Atom XML。多词默认短语匹配，精确控制用引号+AND（`'"smoke detection" AND video'`）。注意用 https（http 301）。0 命中是合法结果（feed 无 entry），不是失败。
- **OpenAlex**：`https://api.openalex.org/works?search=<词>&per-page=N`，JSON（title/publication_year/primary_location.source.display_name/doi）。比 Semantic Scholar 稳。
- **Semantic Scholar**：无 key 极易 429（已验证多次），不要依赖；OpenAlex 可覆盖。
- 检索式模板：方法演进 `"smoke detection" AND video`；场景定位 `smoke AND cooking AND kitchen`（**命中 0 = 场景公开研究空白，是创造性论据**）；数据构建 `smoke AND synthetic AND training`；多模态对齐 `calibration cameras lasers`（通用时间对齐先例，主动排查）。
- 环境坑：curl 写 `/tmp/` 是会话专属目录，Python 读文件先 `cp` 到 `<local-home>/AppData/Local/Temp/`；中文乱码加 `PYTHONIOENCODING=utf-8`。

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

- **外文专利全文获取**：innojoy 导出的外文 PDF（EP/WO/US/JP）常是**扫描图片版、无文本层**（pypdf 提取为空），只能人工看或 OCR；自动化提取请优先 Google Patents 页面（有文本层）。Google Patents 整页抓取会 IP 级封禁（503/超时，数小时~数天恢复）；Espacenet 有 Cloudflare 防护；WIPO Patentscope 302 跳转。被封后降级：innojoy 网页端（用户手动看）+ 已知著录项分析 + 报告标注"全文待人工确认"。
- **摘要缺失时**：innojoy 列表接口 ABST 为空，LoadFullText 需图形验证码；不要在这上面耗时间，摘要用 Google Patents/人工确认补。
- 检索平台返回的中文乱码通常是 Windows 控制台编码问题：跑 Python 加 `PYTHONIOENCODING=utf-8`
- 商业平台（innojoy 等）接口会变，逆向步骤失效时回到浏览器手动操作 + 重新抓 JS 分析
- 独权被最接近文件覆盖时，把"区别特征"（如时间偏移/具体数值区间/标定方法）提升为独权必要特征
- 申请前提醒用户检查：在先公开（论文/公众号/开源）、实验数据支撑、发明人/申请人确认
