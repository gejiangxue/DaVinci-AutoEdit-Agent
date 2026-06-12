# DaVinci AutoEdit Agent

> 面向 Codex 的达芬奇自动剪辑 Agent：从任意视频、音频和图片素材出发，完成素材分析、文案创作、TTS、剪辑蓝图、DaVinci Resolve 时间线构建、成片审计与补拍建议。
>
> A DaVinci Resolve auto-editing agent for Codex that turns arbitrary video,
> audio, and image media into an approved script, TTS plan, edit blueprint,
> Resolve timeline, delivery audit, and pickup-shot report.

[![Codex Agent](https://img.shields.io/badge/Codex-Agent-111827)](https://github.com/openai/codex)
[![DaVinci Resolve](https://img.shields.io/badge/DaVinci_Resolve-18.5%2B-233A51)](https://www.blackmagicdesign.com/products/davinciresolve)
[![Auto Editing](https://img.shields.io/badge/AI-AutoEdit-7C3AED)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

## 中文

### 项目简介

`DaVinci AutoEdit Agent` 是一套可通过 GitHub 安装的 Codex skills
仓库。它不限制素材路径、拍摄设备、题材、语言、平台或视频时长。

用户指定素材位置和创作目标后，Agent 会：

```text
介绍完整流程
  -> 确认素材路径、题材和交付目标
  -> 询问用户自己的节奏与剪辑实践
  -> 检查 LLM、TTS 和 Resolve 配置
  -> 扫描视频、音频与图片
  -> 抽帧分析、结果审查和标签归类
  -> 确认素材审查结果
  -> 生成并确认文案
  -> 按需配置和生成 TTS
  -> 生成并确认剪辑蓝图
  -> 自动创建 Resolve 工程与时间线
  -> 审计空隙、重复、素材范围和写入结果
  -> 对照文案与成片输出必要补拍素材清单
```

所有创作性产物都会先在对话中展示，经用户确认后才落盘或进入下一阶段。
源素材始终视为只读，不会被自动修改。

### 内置 Skills

| Skill | 作用 |
| --- | --- |
| `davinci-autoedit-agent` | 端到端自动剪辑、阶段确认、素材分析、TTS、蓝图、交付与补拍审计 |
| `viral-video-writer` | 基于真实素材证据创作文案、旁白、标题和情绪结构 |
| `davinci-resolve-editor` | 安全操作 Resolve/MCP、构建时间线、调色并验证真实写入结果 |

### 安装

```bash
git clone https://github.com/liuluhaixiu/DaVinci-AutoEdit-Agent.git
cd davinci-autoedit-agent
python -m pip install -r requirements.txt
python scripts/install_skills.py
```

也可以直接让 Codex 安装：

```text
请从以下 GitHub 仓库安装全部 skills：
https://github.com/liuluhaixiu/DaVinci-AutoEdit-Agent
```

DaVinci Resolve MCP 独立使用上游版本，以便持续获得更新：

```bash
npx davinci-resolve-mcp setup
```

### 环境要求

- 支持本地 skills 的 Codex
- Python 3.10+
- 已加入 `PATH` 的 FFmpeg 和 FFprobe
- 可选：兼容 OpenAI 接口的多模态模型
- 可选：用户自己的 TTS HTTP API
- 可选：DaVinci Resolve Studio 18.5+
- 可选：[`davinci-resolve-mcp`](https://github.com/samuelgursky/davinci-resolve-mcp)

Resolve 免费版可能无法使用外部脚本接口。此时仍可完成素材分析、文案和剪辑蓝图。

### 配置

只有需要 API 功能时才创建 `.env`：

```bash
cp .env.example .env
```

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

所有 API、模型、声音、参考音频、素材路径、音乐库和 LUT 都由用户配置。

- 没有 LLM API：使用 Codex 可用的视觉能力或人工审查表。
- 不需要 TTS：跳过 TTS，采用同期声、音乐、字幕或无旁白结构。
- 没有 Resolve MCP：仅交付蓝图，或经用户确认后使用 Resolve Python API。

运行环境检查：

```bash
python skills/davinci-autoedit-agent/scripts/check_setup.py
```

### 使用示例

```text
调用 $davinci-autoedit-agent。
素材在 D:\Media\launch-event，音乐在 D:\Music。
制作一条 8 分钟的 YouTube 纪录片，主题是活动背后的工作人员。
节奏克制，使用 J-cut，不要旁白。
```

如果用户没有自己的剪辑实践，Agent 会询问一次，然后采用内置最佳实践。

### 关键原则

- 原始素材不可变。
- 每个创作阶段经确认后才落盘。
- 不因初步评分低而整体排除某个机位或素材来源。
- 审计镜头覆盖、相邻重复、源范围、帧原点、空隙和最终工程身份。
- 不把 API 测量成功误报为写入成功。
- 结构性修改使用新工程或新时间线。
- 不擅自修改用户已有音频、调色、BGM 和轨道。
- 成片后必须对照文案、时间线和完整素材库生成补拍建议。

### 仓库结构

```text
skills/
  davinci-autoedit-agent/
    SKILL.md
    scripts/
    references/
  viral-video-writer/
  davinci-resolve-editor/
scripts/
  install_skills.py
examples/
  project-brief.example.json
```

---

## English

### Overview

`DaVinci AutoEdit Agent` is a GitHub-installable Codex skills repository for
automated video editing with DaVinci Resolve. It makes no assumptions about
media location, camera, subject, language, platform, or duration.

After the user supplies media paths and a creative goal, the agent:

```text
Explains the workflow
  -> confirms media paths, subject, and delivery goal
  -> asks for the user's pacing and editing practices
  -> checks LLM, TTS, and Resolve configuration
  -> scans video, audio, and images
  -> extracts frames, reviews material, and assigns tags
  -> confirms the material review
  -> drafts and confirms the script
  -> optionally configures and generates TTS
  -> drafts and confirms the edit blueprint
  -> creates a Resolve project and timeline
  -> audits gaps, repetition, source bounds, and write results
  -> compares the finished cut with the script and recommends pickup shots
```

Every creative artifact is previewed in chat and requires explicit approval
before it is written or used by the next stage. Source media remains immutable.

### Bundled Skills

| Skill | Purpose |
| --- | --- |
| `davinci-autoedit-agent` | End-to-end auto editing, approval gates, media analysis, TTS, blueprint, delivery, and pickup-shot audit |
| `viral-video-writer` | Evidence-grounded narration, hooks, titles, and emotional structure |
| `davinci-resolve-editor` | Safe Resolve/MCP operation, timeline construction, grading, and write verification |

### Installation

```bash
git clone https://github.com/liuluhaixiu/DaVinci-AutoEdit-Agent.git
cd davinci-autoedit-agent
python -m pip install -r requirements.txt
python scripts/install_skills.py
```

Or ask Codex:

```text
Install all skills from:
https://github.com/liuluhaixiu/DaVinci-AutoEdit-Agent
```

Install the upstream Resolve MCP server separately to receive its updates:

```bash
npx davinci-resolve-mcp setup
```

### Requirements

- Codex with local skill support
- Python 3.10+
- FFmpeg and FFprobe on `PATH`
- Optional OpenAI-compatible multimodal model endpoint
- Optional user-provided TTS HTTP API
- Optional DaVinci Resolve Studio 18.5+
- Optional [`davinci-resolve-mcp`](https://github.com/samuelgursky/davinci-resolve-mcp)

The free edition of Resolve may not expose external scripting. Material
analysis, writing, and blueprint generation remain available.

### Configuration

Create `.env` only when API-backed features are needed:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

All APIs, models, voices, reference audio, media paths, music libraries, and
LUTs are user configuration.

- No LLM API: use available Codex vision or a manual review worksheet.
- No TTS: skip narration and design around production sound, music, captions,
  or silence.
- No Resolve MCP: deliver the blueprint or use the approved Resolve Python
  fallback.

Run the readiness check:

```bash
python skills/davinci-autoedit-agent/scripts/check_setup.py
```

### Example Prompt

```text
Use $davinci-autoedit-agent.
My footage is in D:\Media\launch-event and my music is in D:\Music.
Make an 8-minute YouTube documentary about the people behind the event.
Use restrained pacing, J-cuts, and no narration.
```

If the user has no editing practice of their own, the agent asks once and then
uses its documented best-practice profile.

### Core Principles

- Treat originals as immutable.
- Require approval before writing each creative stage.
- Never reject an entire camera or source family from weak early samples.
- Audit coverage, adjacent repetition, source bounds, frame origin, gaps, and
  final project identity.
- Never report a successful measurement as a successful write.
- Build structural revisions in a new project or timeline.
- Preserve user-owned audio, grades, BGM, and tracks unless authorized.
- After the cut, compare script, timeline, and inventory to produce an
  actionable pickup-shot report.

## Follow The Creator / 关注作者

- 抖音 / Douyin：`83476153115`
- B 站 / Bilibili：[space.bilibili.com/38505960](https://space.bilibili.com/38505960?spm_id_from=333.1007.0.0)

## Credits / 致谢

The Resolve integration guidance is designed for
[`samuelgursky/davinci-resolve-mcp`](https://github.com/samuelgursky/davinci-resolve-mcp),
licensed under MIT. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

达芬奇集成参考了 MIT 许可的 `davinci-resolve-mcp`。本项目与 Blackmagic
Design 无隶属或背书关系。

## License / 许可证

MIT. See [LICENSE](LICENSE).
