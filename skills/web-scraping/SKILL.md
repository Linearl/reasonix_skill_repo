---
name: web-scraping
description: 从任意网页抓取完整内容并整理为 Markdown：探测 SSR/API、处理限流、CDP 复用 Chrome 登录态、图片本地化
---

# 网页内容抓取 playbook

目标：从任意网页抓取完整内容，整理为多份 Markdown 文档（文字 + 图片本地化）。基于 B 站专栏文集抓取的实战经验（22 篇、1912 张图、0 失败）。

## 1. 探测页面类型

1. 用 `web_fetch` 抓 URL。
2. 返回有实质内容的文本/HTML → 直接解析。
3. 返回"空壳"HTML（只有 `<div id="app">`、大量 `<script>`，无正文）→ 是 **CSR/JS 渲染**，正文由 JS 调 API 填充。此时 `web_fetch` 无用，进入第 2 步。

## 2. 找数据 API

- 打开目标页，用浏览器 DevTools Network 面板（或 F12 → XHR 过滤）看页面发了哪些 JSON 请求。
- 找到接口后先手工 curl 验证：`curl -s -A "<UA>" -H "Referer: https://<域名>/" "<API_URL>"`。
- 实例：B 站专栏
  - 文集列表：`https://api.bilibili.com/x/article/list/web/articles?id=<文集id>`（URL `rl964642` → id=964642）
  - 文章正文：`https://api.bilibili.com/x/article/view?id=<文章id>` → `data.content` 是 **Quill Delta JSON**（`{"ops":[...]}`），不是 HTML；`insert` 为字符串=段落文本，`insert.native-image.url`=图片
- 留意响应中的 `code` 字段：`0` 成功；`-509` 限流；`-352` 签名/风控失败；`-101` 未登录。

## 3. 处理限流（-509 等）

- `-509 请求过于频繁` 是 **IP 级限流**，匿名请求最容易触发；带完整 cookie（如 `buvid3`）可显著缓解。
- 应对顺序：
  1. 先访问 `https://www.bilibili.com/` 用 `curl -c cookies.txt` 拿匿名 cookie，请求带 `-b cookies.txt` + `Referer`。
  2. 间隔 2–4 秒 + 指数退避重试（等待 10s、18s、26s…）。
  3. 仍不行 → 复用浏览器登录态（第 4 步），登录后基本无限流。
- 需要 wbi 签名时参考 `MediaCrawler 的 `media_platform/bilibili/help.py`` 的 `BilibiliSign`（md5(query+salt)，salt 由 img_key/sub_key 按固定 64 位置换表生成；img_key/sub_key 从 `https://api.bilibili.com/x/web-interface/nav` 的 `wbi_img` 或页面 localStorage 的 `wbi_img_urls` 取）。

## 4. CDP 复用 Chrome 登录态（推荐）

前提：本机 Chrome 已登录目标站点。

1. 关闭 Chrome，用**原用户数据目录**带调试参数重启（保留原目录才有登录态）：
   `chrome.exe --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="C:\Users\<user>\AppData\Local\Google\Chrome\User Data" --restore-last-session`
   - Chrome 150+ 必须加 `--remote-allow-origins=*`，否则 playwright 连不上。
2. **关键坑**：Reasonix 的 bash 工具在命令退出时会杀掉进程组，Chrome 会被连带关闭（表现为"打开后很快关闭"）。启动 Chrome 的 bash 调用必须设 `preserve_background_processes: true`。
3. 用 playwright 连接：
   ```python
   browser = await playwright.chromium.connect_over_cdp("http://127.0.0.1:9222")
   ctx = browser.contexts[0]
   cookies = await ctx.cookies(['https://www.bilibili.com'])
   cookie_str = '; '.join(f"{c['name']}={c['value']}" for c in cookies)
   ```
   - 若页面未打开目标站，先 `ctx.new_page()` + `goto`。
   - 登录态 cookie 出现标志：`SESSDATA`、`DedeUserID` 在列表里。
4. 不要把 cookie 写进代码/日志；用完的临时文件（含 cookie）最后删除。
5. 不要尝试读 Chrome 的 `Cookies` SQLite 文件——运行中被独占锁定，复制即 PermissionError。

## 5. 抓取与转换

- 写脚本批量抓（不要逐篇 web_fetch，会限流）：循环 API、`fs.existsSync` 断点续传、每篇间隔 2–4 秒。
- Delta → Markdown：文本 op 按 `\n` 分段；图片 op 输出 `![](相对路径)`。
- md 结构：`# 标题` + 引用行（原文链接、作者、发布日期）+ 正文。文件名 `NN-标题.md`，非法字符 `\/:*?"<>|` 替换为 `_`。

## 6. 图片本地化（用户偏好：尽量本地保存）

- 建 `<输出目录>/images/NN/` 子目录，按文章顺序命名 `001.jpg`。
- 并发 8 下载，headers 带 `User-Agent` + `Referer: https://www.bilibili.com/`。
- 校验：`<1KB` 视为下载失败删除并记录；最后核对 md 里每个 `![](images/...)` 引用都有对应文件。
- 输出总目录建 `README.md` 目录页（文集名、作者、原文链接、各篇链接）。

## 7. 环境杂项（Windows）

- bash 里 `/tmp` 不可靠（git-bash 映射问题），用工作区相对目录；注意脚本相对路径基于 cwd，避免目录嵌套（`.bili_tmp/raw` 变成 `.bili_tmp/.bili_tmp/raw` 的坑）。
- `taskkill //F //IM chrome.exe` 强制结束 Chrome 是可行的（会丢未保存标签，但 Chrome 可恢复会话）。
- 图片/文字总量大时放后台任务（`run_in_background`）并定期 `bash_output` 看进度。
