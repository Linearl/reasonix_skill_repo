# 参数、选择器与排障参考

本文档集中维护以下内容：

- 参数参考
- 已知站点自动选择器
- 故障排查

## 参数参考

- `--url`：必填（二选一），目标 URL。
- `--batch`：必填（二选一），批量 URL 的 JSON 文件路径（与 `--url` 二选一）。
- `--method`：可选，默认 `fetcher`。可选值：`fetcher`、`stealthy`、`dynamic`。
- `--output`：可选，输出文件路径（`.md` 或 `.txt`）。
- `--output-dir`：可选，默认 `.`。批量模式输出目录。
- `--css`：可选，默认自动检测。仅提取匹配元素（已知站点可自动选择器）。
- `--timeout`：可选，默认 `30000`，超时毫秒数。
- `--solve-cloudflare`：可选，默认 `false`，尝试解决 Cloudflare 挑战。
- `--cookies`：可选，默认自动查找，Cookies JSON 文件路径。
- `--format`：可选，默认 `markdown`。可选值：`markdown`、`text`、`html`。
- `--scroll`：可选，默认 `0`，页面滚动次数（每次间隔 2 秒）。
- `--save-html`：可选，同时保存完整原始 HTML 到指定路径。
- `--no-auto-selector`：可选，禁用已知站点自动 CSS 选择器检测。

## 已知站点自动选择器

- `zhuanlan.zhihu.com` → `.Post-RichTextContainer`（知乎专栏文章正文）
- `www.zhihu.com` → `.RichText`（知乎回答正文）
- `www.zhihu.com/org` → `.ContentItem-title a, h2 a`（知乎机构主页文章列表）
- `www.zhihu.com/column` → `h2.ContentItem-title a`（知乎专栏列表）
- `mp.weixin.qq.com` → `#js_content`（微信公众号文章）
- `juejin.cn` → `.article-content`（掘金技术文章）
- `www.jianshu.com` → `.article .show-content`（简书文章）
- `blog.csdn.net` → `#content_views`（CSDN 博客）

使用 `--no-auto-selector` 可禁用自动检测，或用 `--css` 手动覆盖。

## 故障排查

- `ModuleNotFoundError: scrapling`：脚本自动安装失败时，检查网络和代理后手动执行 `pip install "scrapling[all]"`，详见 `快速部署指南.md`。
- 找不到浏览器：执行 `scrapling install`，若不在 PATH 中参考 `快速部署指南.md`。
- 持续 403：尝试 `--method stealthy --solve-cloudflare`。
- 超时：增大 `--timeout 60000`。
- 内容为空：尝试 `--method dynamic`（JS 渲染页面）。
- 内容全是 CSS/JS 代码：使用 `--css` 指定正文选择器，或检查自动选择器。
- 重定向到登录页：需要凭据，按「凭据求助机制」操作。
- API 返回 `need_force_login`：改用 `--scroll` 滚动加载代替 API。
- 抓到列表页但没有结构化数据：增加提取脚本，解析标题 / 链接 / 发布时间并保存到 `过程资产/data/`。
- 已抓取大量文章但没有总结：继续完成步骤 7 和步骤 8，输出分析结果和报告。
- Markdown 转换混乱：使用 `--save-html` 保存 HTML 检查原始结构。
- 批量模式部分失败：查看 stderr 日志，重试失败项。
