# gpt-image-2 技能 — 修改说明

## 原始来源
- **仓库**: [ConardLi/garden-skills](https://github.com/ConardLi/garden-skills)（11.5k ⭐，MIT 协议）
- **原始路径**: `skills/gpt-image-2/`
- **获取时间**: 2026-08-24

## 我们的修改

### 1. 添加 MiniMax 图片生成适配脚本
**新增文件**: `scripts/minimax-adapter.js`（8058 bytes）

**修改原因**: gpt-image-2 原版只支持 OpenAI 兼容 API，但用户只有 MiniMax Token Plan key（MiniMax 的图片生成 API 是异步任务式，不兼容 OpenAI 格式）。

**适配方案**: 
- 把 MiniMax 的异步任务 API 包装成 OpenAI 兼容的同步格式
- 支持 `--prompt`、`--model`、`--size`、`--n`、`--json` 参数
- 自动创建 MiniMax 图片任务 → 轮询结果 → 下载图片 → 保存 PNG
- 输出 OpenAI 格式的 JSON（`created` + `data[].b64_json`）

**依赖**: `MINIMAX_TOKEN_PLAN_KEY` 环境变量（MiniMax Token Plan API key）

### 2. 环境变量配置
**修改文件**: `scripts/shared.js`（未修改，仅通过 minimax-adapter.js 外部调用）

**配置方式**:
```bash
ENABLE_GARDEN_IMAGEGEN=1
MINIMAX_TOKEN_PLAN_KEY=sk-cp-xxxx  # MiniMax Token Plan key
MINIMAX_IMAGE_MODEL=image-01       # MiniMax 图片模型
```

## 使用方式

### Mode A（MiniMax 本地生图）
```bash
node ~/.reasonix/skills/gpt-image-2/scripts/minimax-adapter.js \
  --prompt "一只可爱的猫咪" \
  --image output.png \
  --json
```

### Mode B/C（不使用 MiniMax）
与原始技能行为一致，不调用 minimax-adapter.js。

## 凭据管理
- MiniMax key 存储在 `global-workspace/credential/garden-image-tts-keys.md`
- 环境变量模板：`global-workspace/credential/garden.env`
- **每天免费额度**: 120 张图片

## 许可证
MIT © ConardLi（原始作者）
