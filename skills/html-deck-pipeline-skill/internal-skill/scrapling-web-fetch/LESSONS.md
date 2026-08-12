# Scrapling Web Fetch — 经验教训

> 本文档记录使用 Scrapling 抓取网页过程中积累的经验教训。
> **每次执行 skill 后应检查本文档，看是否需要补充新的经验。**

---

## 1. SPA 页面内容提取

**问题：** 知乎、微信公众号等 SPA 页面的 HTML 包含大量 `<script>`、`<style>` 标签，直接转 Markdown 会得到大量 CSS/JS 代码而非正文。

**解决：** `html_to_markdown()` 必须在转换前先移除 `<script>`、`<style>`、`<noscript>`、`<head>`、`<nav>`、`<footer>` 标签及其内容。

**最佳实践：** 对已知站点使用 CSS 选择器精确提取正文区域（如知乎文章用 `.Post-RichTextContainer`），而非处理整个页面 HTML。

---

## 2. Cookie 获取与 httpOnly 限制

**问题：** `document.cookie` 无法获取 httpOnly 标记的 cookie。知乎的核心认证 token `z_c0` 是 httpOnly 的，因此用 `document.cookie` 导出的 cookie 无法用于 API 认证。

**解决：** 
- 对于**页面抓取**：`document.cookie` 导出的 cookie 配合 StealthyFetcher/DynamicFetcher 足够（浏览器会正确处理）
- 对于 **API 调用**：需从浏览器 DevTools → Network → 请求头中提取完整 Cookie（包含 httpOnly），或使用浏览器模式直接渲染页面

**最佳实践：** 优先使用浏览器渲染模式（stealthy/dynamic）而非直接调用 API。当需要 API 认证时，指导用户从 DevTools Network 面板获取完整 Cookie。

---

## 3. 知乎 API 分页机制

**问题：** 知乎 API (`/api/v4/columns/{id}/items`) 第一页不需认证，但第 2 页起返回 `need_force_login: true`，即使带了 cookie 也不行。原因是知乎 API 需要加密的 `x-zse-96` 请求头，该头由前端 JS 动态生成。

**解决：** 放弃 API 分页方案，改用**滚动加载**方式：通过 StealthyFetcher 的 `page_action` 模拟鼠标滚动，触发页面的无限滚动加载，然后提取渲染后的 DOM 内容。

**最佳实践：** 对于有反爬机制的站点，浏览器模拟（含滚动）比直接调用 API 更可靠。

---

## 4. 登录态处理策略

**问题：** 遇到需要登录的网站时反复重试不会改善结果，只会浪费时间。

**解决：** 当检测到需要登录时，应立即停止重试，转而指导用户获取 cookie：
1. 告知用户需要 cookie
2. 提供获取 cookie 的具体步骤（浏览器 F12 → Console → `document.cookie`）
3. 用户提供后保存到 JSON 文件
4. 使用 `--cookies` 参数继续抓取

**识别登录需求的信号：**
- 页面重定向到登录页（URL 包含 `signin`、`login`）
- API 返回 `need_force_login: true`
- 页面内容为空或仅包含框架代码
- HTTP 401/403 状态码

---

## 5. 过程资产保存

**问题：** 抓取的网页内容如果只保存为 Markdown，丢失了原始 HTML 结构，排查问题时缺乏上下文。

**解决：** 使用 `--save-html` 参数同时保存原始 HTML。建议的过程资产保存规则：
- 原始 HTML → `{name}.html`（用于调试和回溯）
- 提炼内容 → `{name}.md`（用于阅读和后续处理）
- 批量模式下 `--save-html` 指向一个目录，自动按文件名存储

---

## 6. 已知站点 CSS 选择器

| 站点 | 内容类型 | CSS 选择器 |
|------|----------|-----------|
| zhuanlan.zhihu.com | 文章正文 | `.Post-RichTextContainer` |
| www.zhihu.com | 回答正文 | `.RichText` |
| www.zhihu.com/column | 文章列表 | `h2.ContentItem-title a` |
| www.zhihu.com/org | 机构文章 | `.ContentItem-title a, h2 a` |
| mp.weixin.qq.com | 公众号文章 | `#js_content` |
| juejin.cn | 掘金文章 | `.article-content` |
| www.jianshu.com | 简书文章 | `.article .show-content` |
| blog.csdn.net | CSDN 博客 | `#content_views` |

> 脚本已内置这些选择器的自动检测（`detect_site_selector()`），使用 `--no-auto-selector` 可禁用。

---

## 7. 滚动加载（Infinite Scroll）

**适用场景：** 知乎专栏主页、机构主页等使用无限滚动加载内容的页面。

**实现方式：** `--scroll N` 参数指定滚动次数，每次间隔 2 秒。内部通过 `page_action` 调用 `window.scrollTo(0, document.body.scrollHeight)` 实现。

**注意事项：**
- `page_action` 在 `wait` 延迟之前执行
- 滚动次数需要根据目标内容量估算（每次滚动通常加载 10-20 条）
- 建议配合 CSS 选择器使用，避免提取整页冗余内容

---

## 8. 方法选择决策树

```
需要抓取内容
├─ 目标站点有反爬保护？
│  ├─ 是 → 需要登录？
│  │  ├─ 是 → stealthy + cookies + (可选 scroll)
│  │  └─ 否 → stealthy (+ --solve-cloudflare 如果是 Cloudflare)
│  └─ 否 → fetcher（最快）
├─ 页面需要 JS 渲染？
│  ├─ 是 → dynamic + (可选 cookies)
│  └─ 否 → fetcher
└─ 需要加载更多内容（无限滚动）？
   └─ 是 → stealthy/dynamic + --scroll N
```

---

## 9. 常见坑

| 坑 | 表现 | 解决 |
|----|------|------|
| StealthyFetcher 返回 SPA 骨架 | 内容全是 JS/CSS 代码 | 增加 `--scroll` 或使用 CSS 选择器 |
| 文章 URL 跳转到登录页 | 内容为空或为登录表单 | 加载 cookies：`--cookies` |
| API 第 2 页返回空数据 | `need_force_login` | 改用滚动加载而非 API |
| Fetcher 模式不带 cookies | 需要认证的站点返回 403 | 改用 stealthy/dynamic |
| html_to_markdown 输出混乱 | 大量样式代码混入 | 使用 CSS 选择器精确定位正文 |
| 批量模式部分失败 | 网络波动或限流 | 检查 stderr 日志，重试失败项 |

---

## 10. 知乎滚动加载的认证限制

**问题：** 知乎专栏页面的无限滚动机制在 Headless 浏览器中滚动后仍然只显示初始 10 篇文章。页面同时出现"加载更多"和"到底了"标记，说明滚动触发了加载检测，但加载请求被拒绝。

**原因：** 无限滚动内部调用的 AJAX 请求也需要完整的认证 cookie（包括 httpOnly 的 `z_c0`），仅靠 `document.cookie` 导出的 cookie 不足以完成认证。

**解决方案优先级：**
1. **让用户从 DevTools → Application → Cookies 导出全部 cookie**（包括 httpOnly），特别是 `z_c0`
2. **使用 DevTools → Network → 复制请求头的 Cookie 字段**，这包含所有 cookie
3. 如果以上都不行，**接受 10 篇文章的限制**，通过多次访问不同时间段的内容来扩展覆盖范围

---

## 11. save-html 应保存完整页面

**问题：** 当同时使用 `--css` 选择器和 `--save-html` 时，旧版本只保存 CSS 选择器匹配到的内容片段，而非完整的页面 HTML，导致调试困难。

**解决：** 修改 fetch 函数返回 `(status, selected_content, full_html)` 三元组，`--save-html` 始终保存 `full_html`（完整页面），输出仍使用 CSS 筛选后的内容。

---

## 12. Playwright 中不要用 time.sleep()

**问题：** 在 `page_action` 回调中使用 `time.sleep()` 会阻塞 Python 线程，但不会让浏览器处理事件（如网络请求、DOM 更新）。

**解决：** 使用 `page.wait_for_timeout(ms)` 代替 `time.sleep()`，这允许浏览器事件循环继续处理。

---

## 13. 自动安装机制

**问题：** 在新环境或未安装 Scrapling 的机器上运行 `fetch_page.py` 会直接报 `ModuleNotFoundError` 并退出，用户需要手动查文档安装。

**解决：** 在 `main()` 入口添加 `ensure_scrapling()` 函数，运行时自动检测 `import scrapling`，若缺失则依次执行 `pip install "scrapling[all]"` 和 `scrapling install`（浏览器依赖）。安装失败时输出提示并引导用户查阅快速部署指南。

**注意事项：**
- `scrapling install` 使用 `Scripts/scrapling` 路径定位，避免 PATH 不在环境变量中的问题
- 浏览器依赖安装失败不会阻止脚本运行（`fetcher` 模式仍可用），仅 `stealthy`/`dynamic` 受影响
- 安装完成后会验证 `import scrapling` 是否成功

---

## 变更日志

| 日期 | 内容 |
|------|------|
| 2026-03-11 | 初始版本：总结知乎抓取全流程经验 |
| 2026-03-11 | 补充：知乎滚动加载认证限制、save-html 完整页面、Playwright sleep 问题 |
| 2026-03-12 | 补充：自动安装机制、返回类型注解修复、快速部署指南集成 |
