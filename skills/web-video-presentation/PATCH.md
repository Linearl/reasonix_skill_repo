# web-video-presentation 技能 — 来源说明

## 原始来源
- **仓库**: [ConardLi/garden-skills](https://github.com/ConardLi/garden-skills)（11.5k ⭐，MIT 协议）
- **原始路径**: `skills/web-video-presentation/`
- **获取时间**: 2026-08-24

## 修改说明
**无修改** — 直接复制自原始仓库，未做任何改动。

## 功能
把一篇文章或口播稿，做成"看起来像视频"的点击驱动 16:9 网页演示，可选合成口播音频。

## 亮点
- 固定 1920×1080 舞台，适合录屏
- 点击/键盘驱动，每个口播节拍对应一个视觉 step
- 内置 23 套主题（编辑、终端、工程、瑞士国际主义等）
- 可插拔 TTS（内置 MiniMax + OpenAI TTS，可换 ElevenLabs / edge-tts / Azure 等）

## TTS 配置
如果使用小米 MiMo TTS（OpenAI SDK 兼容）：
```bash
OPENAI_API_KEY=sk-c4a46xxxx  # 小米 MiMo API key
OPENAI_BASE_URL=https://api.xiaomimimo.com/v1
PRESENTATION_TTS=openai
```

## 许可证
MIT © ConardLi（原始作者）
