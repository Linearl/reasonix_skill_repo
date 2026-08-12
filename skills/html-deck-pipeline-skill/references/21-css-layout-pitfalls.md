---
description: CSS 布局陷阱与调试经验：常见 CSS 布局问题、缓存陷阱与调试方法
---
# CSS 布局陷阱与调试经验

## 一、CSS 缓存陷阱（P0）

### 症状
- 修改 CSS 文件后，浏览器渲染不变，看起来"没生效"
- serve.py 正常运行，HTML 更新正常，但 CSS 样式停留在旧版

### 原因
- 浏览器对 CSS 文件有强缓存策略，即使 serve.py 重新读取文件，浏览器可能仍使用缓存版本
- Chrome DevTools MCP 的 `navigate_page` 默认行为也可能命中缓存

### 解决方案
- **硬刷新**：`Ctrl+Shift+R`（Windows）/ `Cmd+Shift+R`（Mac）
- **DevTools 中禁用缓存**：F12 → Network → Disable cache（勾选）
- **URL 缓存破坏**：在 URL 后加 `?v=<timestamp>` 强制重新加载
- **DevTools MCP 调试时**：优先用 `new_page` 打开带时间戳参数的新页面，避免缓存干扰

### 经验教训
- 如果 CSS 修改在用户浏览器中生效但 DevTools 测试窗口未生效，首先怀疑缓存
- 修改 CSS 后，建议同时在用户浏览器和 DevTools 中验证

## 二、`display: grid` 继承陷阱（P1）

### 症状
- 卡片内文本每行只显示 2-3 个字，换行异常
- 卡片宽度足够，但文本没有利用可用空间
- `flex: 1` 设置了但卡片实际宽度远小于容器

### 原因
- `css/common/components.css` 中 `.flow-step` 类定义了 `display: grid`
- 该样式被所有使用 `.flow-step` 类的页面继承
- Grid 布局将内容限制在单个 grid cell 中，文本无法扩展到整个卡片宽度

### 解决方案
- 在章节 CSS（如 `style/ch02.css`）中覆盖：`.flow-step { display: block; }`
- 使用 Chrome DevTools 的 `evaluate_script` 检查 computed style 确认问题：
  ```javascript
  const step = document.querySelector('.flow-step');
  getComputedStyle(step).display; // 如果返回 "grid" 则确认问题
  ```

### 调试技巧
- 在 DevTools 中执行以下脚本可快速定位 display 来源：
  ```javascript
  const step = document.querySelector('.flow-step');
  for (const sheet of document.styleSheets) {
    for (const rule of sheet.cssRules) {
      if (rule.type === CSSRule.STYLE_RULE && rule.style.display) {
        if (step.matches(rule.selectorText)) {
          console.log(rule.selectorText, rule.style.display, sheet.href);
        }
      }
    }
  }
  ```

## 三、Grid 列数与子元素数量不匹配（P1）

### 症状
- Grid 容器中子元素没有均匀分布
- 部分列为空白，子元素被压缩到较小宽度

### 原因
- `grid-template-columns` 定义的列数与实际子元素数量不一致
- 例如：定义了 9 列（`1fr auto 1fr auto 1fr auto 1fr auto 1fr`）但只有 5 个内容元素 + 4 个分隔符

### 解决方案
- 当子元素数量可变或需要灵活分布时，优先使用 **flex 布局**：
  ```css
  .container { display: flex; align-items: stretch; gap: 6px; }
  .item { flex: 1; }
  .separator { flex: 0 0 auto; }
  ```
- Flex 布局自动等分可用空间，不需要手动计算列数

### 经验教训
- Grid 适合固定列数的布局（如表格、固定栅格）
- Flex 适合等分或自适应内容的布局（如步骤流、卡片行）
- 修改 Grid 布局时，务必确认子元素数量与列定义匹配

## 四、Auto-scale 误触发（P0）

### 症状

- 页面内容实际能放下，但 auto-scale 仍然触发（缩放到 ~95%）
- 缩小后反而出现纵向滚动条，内容显示不全
- `scrollHeight` 比 `clientHeight` 大 20-40px，但实际内容并未溢出

### 根因

- `scrollHeight` 在复杂 grid/flex 布局中不可靠——它可能报告比实际内容更大的值
- 原因：浏览器内部对 grid gap、flex 间距、伪元素的计算方式与 `getBoundingClientRect()` 不一致
- 实测案例：`scrollHeight=715` vs 实际内容底部 656px + padding 22.4px = 678.4px，差 36px

### 解决方案
用 `getBoundingClientRect()` 测量实际内容高度，替代 `scrollHeight`：

```javascript
// 旧方案（不可靠）
const scrollH = slideEl.scrollHeight;
const clientH = slideEl.clientHeight;
if (scrollH > clientH + 4) { /* scale */ }

// 新方案（可靠）
const clientH = slideEl.clientHeight;
const slideTop = slideEl.getBoundingClientRect().top;
let maxBottom = 0;
for (const child of slideEl.children) {
  const childBottom = child.getBoundingClientRect().bottom - slideTop;
  if (childBottom > maxBottom) maxBottom = childBottom;
}
const padBottom = parseFloat(getComputedStyle(slideEl).paddingBottom) || 0;
const contentH = maxBottom + padBottom;
if (contentH > clientH + 2) { /* scale */ }
```

### 验证方法

- 在 DevTools 中执行：`getBoundingClientRect()` 测量 vs `scrollHeight` 对比
- 如果 `scrollHeight - clientHeight > 10` 但 `contentH - clientHeight < 2`，确认为误触发

### 二级根因：字体加载时序

即使换用 `getBoundingClientRect()`，auto-scale 仍可能误触发。原因：

- `requestAnimationFrame` 在 CSS/字体完全加载前就执行了测量
- 字体加载后文本 reflow，实际内容高度比首次测量时矮 20-40px
- 首次测量时 contentH > clientH，触发缩放；字体加载后内容本可以放下

**解决方案**：在 `requestAnimationFrame` 内等待 `document.fonts.ready`：

```javascript
requestAnimationFrame(() => {
  Promise.resolve(document.fonts.ready).then(() => {
    // 此时字体已加载，测量结果准确
    const clientH = slideEl.clientHeight;
    // ... getBoundingClientRect 测量 ...
  });
});
```

注意：`Promise.resolve(document.fonts.ready)` 用 `Promise.resolve` 包装，因为 `document.fonts` 在某些环境下可能未定义（如导出模板的 iframe）。

### 经验教训

- `scrollHeight` 适合简单块级布局，不适合 grid/flex 复杂嵌套
- 测量内容高度时，`getBoundingClientRect()` 是最可靠的方式
- **必须等待字体加载后再测量**——`requestAnimationFrame` 不保证字体已就绪
- 已修复 deck.js 的 `applyAutoScale()` 和导出模板中的两处同类逻辑
- 典型案例：页面 2.8、2.3、2.5 均因此问题触发误缩放

## 五、Chrome DevTools MCP 调试要点（P2）

### 缓存绕过
- `navigate_page` 的 `ignoreCache` 参数可能对某些资源无效
- 最可靠的方式是 `new_page` 打开带查询参数的新 URL

### 状态检查
- 使用 `evaluate_script` 检查 computed style 比截图更精确
- 关键检查项：`display`、`width`、`flex`、`min-width`、`max-width`

### 多页面管理
- 调试时可能打开多个页面，注意用 `select_page` 切换到正确的页面
- 调试完成后关闭多余页面，避免混淆

## 六、导出 HTML 样式丢失与错排陷阱（P0）

### 症状
- 导出后的 HTML 文件用 `file://` 打开，部分页面样式丢失（背景色相同、组件尺寸错误）
- 页面比例变形，deck 不保持 16:9（如视口 1536×773 时 deck 为 1.99:1 而非 1.78:1）
- 字体大小/主题与导出时不一致

### 根因 A：导出 CSS 覆盖破坏 16:9 约束

导出模板中的 CSS 覆盖（`deck.js` 的 `exportToSingleHTML()`）：

```css
/* 旧版（有问题） */
#deck-shell { display: block; height: 100vh; overflow: hidden; padding: 0; }
.deck { max-width: none; border-radius: 0; box-shadow: none; }
```

- `display: block` 取代了 live preview 的 `display: grid`，失去网格约束和居中
- `.deck { max-width: none }` 移除宽度上限，`width: 100%` 强制填满视口宽度
- 即使 `aspect-ratio: 16/9` + `max-height: 100%` 存在，CSS 规范下显式 `width` 优先于 aspect-ratio 的宽度调整——高度被截断，但宽度不缩减
- 结果：deck = 视口宽 × 100vh，在非 16:9 视口上变形

**修复**：

```css
/* 新版 */
#deck-shell { display: flex; justify-content: center; align-items: center; height: 100vh; overflow: hidden; padding: 0; }
.deck { max-width: calc(100vh * 16 / 9); border-radius: 0; box-shadow: none; }
```

- `display: flex` + `justify-content: center`：居中 + 完善的 children 约束传导
- `max-width: calc(100vh * 16 / 9)`：用视口高度反推最大宽度，硬保证 16:9

### 根因 B：内联 JS 覆盖导出时的 theme/fontsize

导出 HTML 内联 JS 的 `getFontsize()` 在 `file://` 下无 localStorage 时，回退到硬编码默认值（如 `"standard"`），覆盖了导出时 `<html>` 标签上写入的 `data-font-size="high-contrast"`：

```javascript
// 旧版（有问题）
function getFontsize() {
  try { ... localStorage ... } catch(e) {}
  return DEFAULT_FONTSIZE;  // ← file:// 下总返回 "standard"，忽略导出时的设置
}
document.documentElement.setAttribute('data-font-size', getFontsize());
```

**修复**：回退到 HTML 属性值：

```javascript
// 新版
function getFontsize() {
  try { ... localStorage ... } catch(e) {}
  return document.documentElement.getAttribute('data-font-size') || DEFAULT_FONTSIZE;
}
```

### 根因 C：部分特定 CSS 选择器全部失效（最隐蔽）

Live preview 中 `deck.js` 的 `setPart()` 会动态更新 `#deck-shell.className` 为 `part-ch02` / `part-ch03` 等，使得 `.part-ch02 .card`、`.part-ch04 .compare-row` 等选择器生效。

导出 HTML 中 `#deck-shell` 的 class 硬编码为 `part-ch01`，且内联 JS 只做 slide 显隐切换，**不更新 shell class**。结果：

- `.part-ch02 .bg-method`、`.part-ch03 .bg-pipeline` 等背景样式全部丢失
- `.part-ch04 .compare-row`、`.part-ch05 .vs-badge` 等组件尺寸回退到 components.css 默认值
- 所有 ch02-ch05 的 slide 都使用 ch01 的命名空间样式（bg 渐变、布局参数等）

**修复**：注入 slide→part 映射数组 + `show()` 中动态切换：

```javascript
const SLIDE_PARTS = ["ch01","ch01",...,"ch05","ch05"];  // 导出时从 slides-config.json 生成

function show(i) {
  // ...
  document.getElementById('deck-shell').className = SLIDE_PARTS[i] ? 'part-' + SLIDE_PARTS[i] : 'part-ch01';
  // ...
}
```

### 调试方法

1. 检查 deck 比例：`getComputedStyle(deck).aspectRatio` + `deck.clientWidth / deck.clientHeight`
2. 检查 shell 类名：`document.getElementById('deck-shell').className` — 翻页后应随 part 变化
3. 检查部分特定样式是否生效：用 `evaluate_script` 测量特定组件（如 `.compare-row` 的 `grid-template-columns`）
4. 对比 live preview 与导出文件的 computed style：在 DevTools 中并排打开两个页面

### 经验教训

- 导出模板的 CSS 覆盖必须保留关键约束（aspect-ratio、max-width/max-height、min-height）
- 导出内联 JS 的状态初始化应以 HTML 属性为首选来源（用户导出时的选择），localStorage 为次（导出后用户在 file:// 中的修改）
- 导出文件丢失 live preview 的"运行时行为"（如 `setPart()` 动态更新 shell class），必须在导出模板中用等效逻辑补齐
- **不要假设"CSS 在 `<style>` 里" = "CSS 在生效"**——必须验证祖先选择器（如 `.part-chXX`）在运行时是否匹配
