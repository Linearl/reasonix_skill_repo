---
name: image-ocr-to-docs
description: 批量 OCR 图片转可检索文档：PaddleOCR + 放大预处理（游戏截图/攻略图），输出同名 .md 或汇总清单，含双引擎交叉验证
---

# 图片批量 OCR 转文档（Image OCR to Docs）

把图片目录批量 OCR 成可检索文字（生成同名 .md 或汇总清单），用于攻略截图、聊天记录、票据等图文资料的文字化。流程源自 个人工作目录 的 ocr_all_images.py，并集成了游戏截图（GBA 240x160 小字）的放大预处理经验。

## 适用场景

- 图文攻略里的游戏截图/教学截图 → 文字化，让 grep 可检索
- 网页抓取下来的图片 → 提取文字
- 任何"一堆图片要转文字"的批处理

## 环境依赖

- `paddleocr`（推荐，3.x）+ `paddlepaddle`；备选 `rapidocr-onnxruntime`（旧版 API 返回 `(result, elapse)` 元组，需适配）
- `Pillow`（放大预处理）

## 执行流程

1. **确认目标目录**：列出图片清单（`ls`），确认扩展名和数量，`--dry-run` 预览
2. **写脚本执行**（核心逻辑）：

```python
# -*- coding: utf-8 -*-
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')  # Windows 必须，防 GBK 乱码
from PIL import Image, ImageOps, ImageEnhance
from paddleocr import PaddleOCR

IMG_DIR = "图片目录"
ocr = PaddleOCR(lang="ch")

def ocr_one(path):
    img = Image.open(path).convert("L")
    img = ImageOps.autocontrast(img)
    img = img.resize((img.width*4, img.height*4), Image.LANCZOS)  # 小字/截图放大 4x
    img = ImageEnhance.Contrast(img).enhance(1.3)
    tmp = path + "_x4.png"
    img.save(tmp)
    res = ocr.predict(tmp)
    os.remove(tmp)
    texts = []
    for line in res:
        if isinstance(line, dict) and "rec_texts" in line:
            for i, t in enumerate(line["rec_texts"]):
                conf = line["rec_scores"][i] if i < len(line["rec_scores"]) else 0
                if conf >= 0.45:
                    texts.append(t)
    return texts
```

3. **输出两份产物**：
   - 每张图生成同名 `.md`（`# 文件名` + `> OCR自动识别` + 代码块包住文本）——逐图同名 md 模式
   - 或合并成 `ocr_results.txt`（`===== 文件名 =====` 分隔）——适合人工复核
4. **人工复核**（重要！）：OCR 对游戏 UI 小字/艺术字会有错别字（如"撒菱"→"撒萎"、"垃圾射击"→"垃圾射击"）。**用第二个 OCR 引擎交叉验证低置信度项**（`rapidocr_onnxruntime` + `PaddleOCR` 双跑），或裁剪局部放大再识别。把修正后的结果写回文档，并标注 `（OCR）` 来源
5. **结构化整合**：把 OCR 文字按主题整合进目标 md（如技能名→教学点清单），并留原始图片引用

## 关键经验（踩坑记录）

1. **Windows 控制台编码**：必须 `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')`，否则中文输出乱码；写入文件一律 `encoding="utf-8"`
2. **游戏截图放大**：240x160 的 GBA 截图直接 OCR 几乎必失败；灰度化 + autocontrast + 4x LANCZOS 放大 + 对比度 1.3 后成功率显著提升；仍不行就裁剪目标区域放大 6-8x
3. **置信度阈值**：游戏小字建议 0.45；低置信度（<0.8）的词务必人工确认，常是形近字错误（菱/萎、气/萎）
4. **双引擎交叉验证**：rapidocr 1.4.4 API 是 `engine(img) -> (result, elapse)`；paddleocr 3.x API 是 `ocr.predict(img) -> list[dict]`。同一张图双跑，取交集/高置信
5. **PaddleOCR 初始化噪音**：日志会刷 `ReduceMeanCheckIfOneDNNSupport` 等 onnx 警告，用 `2>&1 | grep -v` 过滤，不影响结果
6. **临时文件清理**：放大用的 `_x4.png` 用完即删，不留垃圾

## 完成检查

- [ ] 每张图都产出了文字（或明确标注"无文字"）
- [ ] 低置信度词已人工/双引擎确认
- [ ] 结果已整合进目标文档，图片引用保留
- [ ] 临时文件已清理
