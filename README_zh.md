# YouTube Monitor & Translator

> **AI 驱动的全自动 YouTube 视频监控与翻译系统**

[English](README.md)

自动监控 YouTube 频道，下载英文字幕，使用 Claude AI 生成高质量中文翻译和结构化摘要。

## 功能特性

- **自动监控** - RSS 订阅监控 16+ 高质量技术/商业频道
- **智能字幕处理** - SRT 解析 + 智能合并（按时间间隔和句子边界）
- **AI 分析** - 自动生成摘要、章节、说话人识别
- **高质量翻译** - 分段翻译 + 上下文维护 + 术语一致性
- **细分时间戳** - ~1分钟粒度，便于快速定位内容
- **内容审核** - 章节重组 + AI 废话清理
- **邮件通知** - 处理完成自动发送邮件

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 确保 Claude CLI 可用

```bash
claude --version
```

### 3. 处理单个视频

```bash
python main.py --video VIDEO_ID
```

### 4. 监控所有频道

```bash
# 单次运行
python main.py

# 持续循环（每 N 小时检查一次）
python main.py --loop
```

## 项目架构

```
youtube-monitor-translator/
├── core/                    # 核心业务逻辑
│   ├── video_discovery.py   # Stage 1: RSS 监控
│   ├── content_fetcher.py   # Stage 2: 字幕下载
│   ├── subtitle_processor.py # Stage 3: 字幕处理
│   ├── ai_analyzer.py       # Stage 4: AI 分析
│   ├── chapter_optimizer.py # Stage 5: 章节优化
│   ├── translator.py        # Stage 6: 翻译引擎
│   ├── reviewer.py          # Stage 6.5: 内容审核
│   ├── output_generator.py  # Stage 7: 输出生成
│   └── pipeline.py          # 流程协调器
├── infrastructure/          # 基础设施
│   ├── config.py            # 配置管理
│   ├── logger.py            # 日志系统
│   ├── archive.py           # 归档管理
│   └── notifier.py          # 邮件通知
├── utils/                   # 工具函数
├── prompts/                 # AI Prompt 模板
├── tests/                   # 测试套件
├── ai_output/               # 输出目录
│   ├── srt/                 # 原始字幕
│   ├── clean/               # 处理后字幕
│   └── summary/             # 最终翻译
├── config_ai.json           # 系统配置
└── channels.json            # 频道列表
```

## Claude Code 集成

### Agent

使用专业 Agent 分析科技投资内容：

```bash
claude --agent tech-investment-analyst
```

**tech-investment-analyst**: AI PhD + VC 背景的视频分析专家
- 深度理解 AI 技术（LLM, Transformer, Inference）
- 熟悉 VC 投资逻辑（估值, ARR, 融资阶段）
- 覆盖频道: a16z, All-In, 20VC, No Priors, Acquired

### Skills

| Skill | 内容 |
|-------|------|
| `ai-knowledge` | AI/ML 术语、公司、论文、技术趋势 |
| `investment-knowledge` | VC 术语、投资人、分析框架 |
| `skill-creator` | 创建新 Skill 的工具 |

### Commands

| 命令 | 功能 |
|------|------|
| `/sync` | 同步更改到 GitHub |

---

## 处理流程

```
RSS 监控 → 视频筛选 → 字幕下载 → 字幕处理 → AI 分析
    ↓
章节优化 → 分段翻译 → 内容审核 → 输出生成 → 邮件通知
```

| 阶段 | 功能 | 技术 |
|------|------|------|
| 1. 视频发现 | RSS 监控 + 时长过滤 | feedparser |
| 2. 内容获取 | 字幕下载 + 元数据 | yt-dlp |
| 3. 字幕处理 | SRT 解析 + 智能合并 | 自研算法 |
| 4. AI 分析 | 摘要 + 章节 + 说话人 | Claude CLI |
| 5. 章节优化 | 过短合并 / 过长拆分 | 智能算法 |
| 6. 分段翻译 | 上下文维护 + 重试 | Claude CLI |
| 6.5. 内容审核 | 章节重组 + AI 清理 | Python + haiku |
| 7. 输出生成 | Markdown 生成 | 模板引擎 |

## 配置说明

编辑 `config_ai.json`：

```json
{
  "claude_model": "claude-sonnet-4-20250514",
  "claude_timeout_seconds": 600,
  "min_duration_minutes": 10,
  "min_chapter_duration": 180,
  "max_chapter_duration": 900,
  "context_lines": 5,
  "review_enabled": true,
  "review_remove_ai_garbage": true,
  "email_enabled": false,
  "check_interval_hours": 5
}
```

### 模型选项

| 模型 | 用途 | 说明 |
|------|------|------|
| `claude-opus-4-20250514` | 最佳质量 | 最贵 |
| `claude-sonnet-4-20250514` | 推荐 | 平衡质量与成本 |
| `claude-3-5-haiku-latest` | 快速 | 用于审核模块 |

## 输出示例

生成的 Markdown 包含：

```markdown
# 视频标题

## 视频信息
- 频道: xxx
- 发布日期: 2025-01-01
- 时长: 45:30

## TL;DR
一句话总结...

## 章节导航表
| 时间戳 | 章节标题 | 一句话概括 |
|--------|----------|-----------|
| 00:00-05:30 | 开场 | ... |

## 完整翻译

### (0:00 - 5:30) 开场
> 章节概括

**(0:00 - 1:15)**
翻译内容...

**(1:15 - 2:30)**
翻译内容...
```

## 监控频道

默认监控频道（可在 `channels.json` 中配置）：

- a16z
- All-In Podcast
- Lex Fridman
- Dwarkesh Patel
- No Priors
- 20VC with Harry Stebbings
- ...

## 邮件通知

1. 复制配置模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 或创建 `email_config.py`：
```python
EMAIL_SENDER = "your-email@gmail.com"
EMAIL_RECEIVER = "recipient@gmail.com"
EMAIL_PASSWORD = "your-app-password"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
MAIL_ENABLE = True
```

3. 在 `config_ai.json` 中启用：
```json
{
  "email_enabled": true
}
```

## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_pipeline.py -v
```

## 开发文档

- [CLAUDE.md](CLAUDE.md) - 完整开发蓝图（给 AI 的指南）
- [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - 系统架构设计
- [FINAL_STATUS.md](FINAL_STATUS.md) - 项目状态报告

## 技术栈

- **Python 3.11+**
- **Claude CLI** - AI 分析和翻译
- **yt-dlp** - 视频/字幕下载
- **feedparser** - RSS 解析
- **pytest** - 单元测试

## License

MIT

---

**v2.0.0** - 全面重构版本，模块化架构，专业代码规范
