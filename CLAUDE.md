# YouTube 监控与翻译系统 - 开发蓝图

> **AI 驱动的全自动开发指南**
>
> 本文档是给 Claude Code 的完整开发指令，用于从零构建整个系统
>
> 最后更新: 2025-12-21

---

## 🎯 项目愿景

构建一个**全自动的 YouTube 视频监控与翻译系统**，能够：
- 🔍 自动监控 16 个高质量技术/商业频道
- 📥 智能下载并处理英文字幕
- 🤖 使用 Claude AI 生成高质量中文翻译
- 📊 生成结构化的 Markdown 文档
- 📧 完成后自动通知用户

**核心价值**: 让用户无需手动操作，即可获得高质量的中文翻译内容，节省大量时间。

---

## 🌊 核心流程概览

```
┌─────────────────────────────────────────────────────────────────┐
│                   全自动处理流程（10 个阶段）                      │
└─────────────────────────────────────────────────────────────────┘

RSS 监控 → 视频筛选 → 字幕下载 → 字幕处理 → AI 分析
    ↓
章节优化 → 分段翻译 → 内容审查 → 输出生成 → 邮件通知 → 归档
```

**处理阶段详解**:

| 阶段 | 功能 | 关键技术 |
|------|------|---------|
| 1️⃣ 视频发现 | RSS 监控 + 时长/时间过滤 | feedparser |
| 2️⃣ 内容获取 | 字幕下载 + 元数据提取 | yt-dlp |
| 3️⃣ 字幕处理 | SRT 解析 + 智能合并 | 自研算法 |
| 4️⃣ AI 分析 | 摘要 + 章节 + 说话人识别 | Claude CLI |
| 5️⃣ 章节优化 | 过短合并 + 过长拆分 | 智能算法 |
| 6️⃣ 分段翻译 | 上下文维护 + 失败重试 | Claude CLI |
| 7️⃣ 内容整合 | Markdown 生成 + 文件组织 | 模板引擎 |
| 8️⃣ 内容审查 | 质量检查 + 错误清理 | Claude Agent |
| 9️⃣ 通知归档 | 邮件通知 + 数据持久化 | SMTP |
| 🔟 循环调度 | 定时检查 + 持续运行 | 调度器 |

---

## 🛠️ 技术架构

### 核心技术栈

```
┌─────────────────────────────────────┐
│         应用层（Python 3.11+）       │
├─────────────────────────────────────┤
│  Claude CLI │  yt-dlp  │ feedparser │
│  (subprocess)│ (字幕)   │   (RSS)    │
├─────────────────────────────────────┤
│         基础设施层                   │
│  logging  │  json  │  email  │ pytest│
└─────────────────────────────────────┘
```

**依赖清单**:
```bash
yt-dlp>=2024.0.0       # 视频/字幕下载
feedparser>=6.0.0      # RSS 解析
python-dotenv>=1.0.0   # 环境变量
pytest>=8.0.0          # 单元测试
```

**环境要求**:
```bash
# Claude CLI 必须已安装（通过 VS Code 扩展或独立安装）

# 可选环境变量（如启用邮件）
export EMAIL_PASSWORD="your-app-password"
```

---

## 📐 系统架构设计

完整架构参考: [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)

### 模块划分

```
youtube-monitor-translator/
├── 🎯 主程序
│   └── main.py                      # 程序入口 + 命令行接口
│
├── 🧠 核心业务逻辑（core/）
│   ├── video_discovery.py           # 阶段1: 视频发现
│   ├── content_fetcher.py           # 阶段2: 内容获取
│   ├── subtitle_processor.py        # 阶段3: 字幕处理
│   ├── ai_analyzer.py               # 阶段4: AI分析
│   ├── chapter_optimizer.py         # 阶段5: 章节优化
│   ├── translator.py                # 阶段6: 翻译引擎
│   ├── output_generator.py          # 阶段7: 输出生成
│   └── pipeline.py                  # 流程协调器
│
├── 🏗️ 基础设施（infrastructure/）
│   ├── config.py                    # 配置管理
│   ├── logger.py                    # 日志系统
│   ├── archive.py                   # 归档管理
│   └── notifier.py                  # 邮件通知
│
├── 🔧 工具函数（utils/）
│   ├── time_parser.py               # 时间戳处理
│   ├── srt_parser.py                # SRT 解析
│   ├── file_utils.py                # 文件操作
│   └── retry_handler.py             # 重试逻辑
│
├── 🤖 AI Prompt（prompts/）
│   ├── yt-summary.md                # 摘要生成
│   └── yt-translate.md              # 翻译模板
│
├── ✅ 测试套件（tests/）
│   ├── test_infrastructure.py
│   ├── test_core_basic.py
│   ├── test_ai_modules.py
│   └── test_pipeline.py
│
├── 📊 配置文件
│   ├── config_ai.json               # 系统配置
│   ├── channels.json                # 频道列表（已存在）
│   └── youtube_archive.json         # 处理历史（自动生成）
│
└── 📁 输出目录（ai_output/）
    ├── srt/{channel}/               # 原始字幕
    ├── clean/{channel}/             # 处理后字幕
    └── summary/{channel}/           # 最终输出
```

---

## 🤖 Claude Code 扩展

### Agent 架构

```
用户请求 → Agent (tech-investment-analyst)
              ↓
         加载 Skills:
         ├── ai-knowledge
         └── investment-knowledge
              ↓
         执行任务
```

### 文件结构

```
.claude/
├── agents/
│   └── tech-investment-analyst.md    # AI PhD + VC 专家 Agent
│
├── skills/
│   ├── ai-knowledge/                 # AI/ML 知识库
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── terminology.md        # 术语词典
│   │       ├── papers.md             # 经典论文
│   │       ├── architectures.md      # 模型架构
│   │       └── companies.md          # 公司/人物
│   │
│   ├── investment-knowledge/         # VC/投资知识库
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── terminology.md        # 投资术语
│   │       ├── investors.md          # 投资人信息
│   │       └── frameworks.md         # 分析框架
│   │
│   └── skill-creator/                # Skill 创建工具
│       └── SKILL.md
│
└── commands/
    └── sync.md                       # /sync 命令
```

### 使用方式

```bash
# 启动专业 Agent
claude --agent tech-investment-analyst

# 使用 /sync 命令同步到 GitHub
/sync
```

### Agent 能力

**tech-investment-analyst**:
- **AI 技术**: 深度理解 LLM、Foundation Model、Inference、Training
- **投资视角**: 熟悉 VC 投资逻辑、估值框架、市场分析
- **覆盖频道**: a16z, All-In, 20VC, No Priors, Acquired

---

## 🗺️ 开发路线图

### Phase 1: 基础设施搭建 🏗️

**目标**: 建立项目骨架和配置系统

**📖 参考文档**:
- [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - 基础设施架构设计、配置系统、日志系统、归档机制

**任务清单**:
1. ✅ 创建项目目录结构（所有文件夹）
2. ✅ 创建 `config_ai.json` 配置文件模板
3. ✅ 实现 `infrastructure/config.py` - 配置加载器
4. ✅ 实现 `infrastructure/logger.py` - 日志系统
5. ✅ 实现 `infrastructure/archive.py` - 归档管理
6. ✅ 创建 `tests/test_infrastructure.py` - 基础测试
7. ✅ 创建 `requirements.txt` - 依赖清单

**完成标准**:
```bash
pytest tests/test_infrastructure.py -v  # 全部通过
```

**关键实现**:

**config_ai.json**:
```json
{
  "lookback_hours": 20,
  "min_duration_minutes": 10,
  "subtitle_language": "en",
  "subtitle_merge_interval": 30,

  "claude_model": "claude-sonnet-4-20250514",
  "claude_timeout_seconds": 600,

  "min_chapter_duration": 180,
  "max_chapter_duration": 900,

  "context_lines": 5,
  "translation_max_tokens": 4000,
  "translation_max_retries": 2,
  "translation_retry_delay": 5,

  "output_dir": "./ai_output",
  "filename_max_length": 50,
  "archive_file": "./youtube_archive.json",

  "email_enabled": false,
  "check_interval_hours": 3
}
```

**infrastructure/config.py**:
```python
from dataclasses import dataclass
from typing import List
import json
import os

@dataclass
class Config:
    """系统配置数据类"""
    # 视频发现
    lookback_hours: int
    min_duration_minutes: int
    subtitle_language: str

    # 字幕处理
    subtitle_merge_interval: int

    # AI 配置
    claude_model: str
    claude_timeout_seconds: int

    # 章节优化
    min_chapter_duration: int
    max_chapter_duration: int

    # 翻译配置
    context_lines: int
    translation_max_tokens: int
    translation_max_retries: int
    translation_retry_delay: int

    # 输出配置
    output_dir: str
    filename_max_length: int
    archive_file: str

    # 邮件通知
    email_enabled: bool

    # 调度
    check_interval_hours: int

    # 频道列表
    channels: List[dict]

def load_config(config_path: str = "config_ai.json") -> Config:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        Config 对象
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)

    # 加载频道列表
    with open("channels.json", 'r', encoding='utf-8') as f:
        channels_data = json.load(f)

    config_data['channels'] = channels_data['channels']

    return Config(**config_data)
```

---

### Phase 2: 视频发现与获取 📥

**目标**: 实现视频监控和内容获取

**📖 参考文档**:
- [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - 视频发现流程、字幕处理流程、数据结构定义

**任务清单**:
1. ✅ 实现 `utils/time_parser.py` - 时间戳工具
2. ✅ 实现 `utils/srt_parser.py` - SRT 解析器
3. ✅ 实现 `core/video_discovery.py` - RSS 监控
4. ✅ 实现 `core/content_fetcher.py` - yt-dlp 集成
5. ✅ 实现 `core/subtitle_processor.py` - 字幕处理
6. ✅ 创建 `tests/test_core_basic.py` - 核心测试

**完成标准**:
```bash
pytest tests/test_core_basic.py -v  # 全部通过
python -c "from core.content_fetcher import download_subtitle; print(download_subtitle('TEST_VIDEO_ID'))"  # 成功下载
```

**核心数据结构**:
```python
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class VideoInfo:
    """视频基本信息"""
    video_id: str
    title: str
    description: str
    upload_date: str  # YYYYMMDD
    duration_sec: int
    uploader: str
    url: str
    chapters: List[Tuple[int, str]]  # (start_sec, title)

@dataclass
class SubtitleEntry:
    """单条字幕"""
    start_sec: float
    end_sec: float
    text: str

@dataclass
class SubtitleData:
    """字幕处理结果"""
    raw_text: str                    # 合并后原文
    entries: List[SubtitleEntry]     # 结构化条目
    with_metadata: str               # 含元数据版本
```

**关键函数签名**:
```python
# core/video_discovery.py
def fetch_channel_videos(channel_id: str, lookback_hours: int) -> List[str]:
    """从频道 RSS 获取视频 ID 列表"""
    pass

def filter_by_duration(video_ids: List[str], min_minutes: int) -> List[str]:
    """按时长过滤视频"""
    pass

# core/content_fetcher.py
def fetch_video_info(video_id: str) -> VideoInfo:
    """获取视频完整信息（使用 yt-dlp）"""
    pass

def download_subtitle(video_id: str, language: str = "en") -> str:
    """下载字幕文件，返回路径"""
    pass

# core/subtitle_processor.py
def parse_srt(srt_path: str) -> List[SubtitleEntry]:
    """解析 SRT 文件"""
    pass

def merge_subtitles(entries: List[SubtitleEntry], merge_interval: int) -> str:
    """智能合并字幕（时间间隔 + 句子边界）"""
    pass

def inject_metadata(subtitle_text: str, video_info: VideoInfo) -> str:
    """注入视频元数据到字幕开头"""
    pass
```

---

### Phase 3: AI 集成 🤖

**目标**: 接入 Claude CLI 实现智能分析和翻译

**📖 参考文档**:
- [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - AI 分析流程、翻译流程、Prompt 设计原则

**任务清单**:
1. ✅ 创建 `prompts/yt-summary.md` - 摘要 Prompt
2. ✅ 创建 `prompts/yt-translate.md` - 翻译 Prompt
3. ✅ 实现 `core/ai_analyzer.py` - AI 分析引擎
4. ✅ 实现 `core/chapter_optimizer.py` - 章节优化
5. ✅ 实现 `core/translator.py` - 翻译引擎
6. ✅ 实现 `utils/retry_handler.py` - 重试逻辑
7. ✅ 创建 `tests/test_ai_modules.py` - AI 测试

**完成标准**:
```bash
pytest tests/test_ai_modules.py -v  # 全部通过（使用 Mock）
python -c "from core.ai_analyzer import analyze_video; ..."  # 真实调用成功
```

**Prompt 模板**:

> ⚠️ **重要**: 下面是 Prompt 的基本结构说明。实际项目中已存在更详细、更生产化的 Prompt 模板文件：
> - **[prompts/yt-summary.md](prompts/yt-summary.md)** - 完整的视频分析和摘要生成 Prompt
> - **[prompts/yt-translate.md](prompts/yt-translate.md)** - 完整的高质量翻译 Prompt
>
> Claude Code 应直接使用这些文件中的 Prompt，而非这里的简化示例。

**prompts/yt-summary.md** (核心结构示例):
```markdown
你是一个视频内容分析专家。请分析以下 YouTube 视频字幕，完成以下任务：

1. **生成视频摘要**（200-300 字，中文）
2. **提取/生成章节时间轴**（格式：时间戳 - 章节标题）
3. **检测视频类型**（interview/speech/other）
4. **提取说话人信息**（如果是访谈或多人对话）

视频信息已在字幕开头注入。

字幕内容：
{{SUBTITLE_WITH_METADATA}}

请以 JSON 格式返回：
{
  "summary": "视频摘要内容（中文）",
  "chapters": [
    {"start_sec": 0, "title": "章节标题"}
  ],
  "video_type": "interview",
  "speakers": "Speaker 1, Speaker 2"
}
```

**详细 Prompt 特性** (参考 prompts/yt-summary.md)：
- ✅ 支持自动提取视频描述中的预定义章节
- ✅ 生成章节导航表格（包含时间戳、标题、概括）
- ✅ 提取核心论点（按视频长度自动调整数量）
- ✅ 识别公司、产品和人物信息
- ✅ 提取经典金句和主要发言人背景

**prompts/yt-translate.md**:
```markdown
你是专业的英译中翻译专家。请将以下视频字幕翻译成中文。

视频类型: {{VIDEO_TYPE}}
说话人: {{SPEAKERS}}

当前章节: {{CHAPTER_TITLE}}
时间范围: {{TIME_RANGE}}

翻译要求：
1. 保持术语一致性（参考上文译文）
2. 符合中文表达习惯
3. 保留专业术语的英文原文（如 AI、API、LLM 等）
4. 不要添加任何解释或评论

上文原文（最后 {{CONTEXT_LINES}} 行）：
{{PREVIOUS_ORIGINAL}}

上文译文（最后 {{CONTEXT_LINES}} 行）：
{{PREVIOUS_TRANSLATION}}

---

待翻译内容：
{{SEGMENT_TEXT}}

---

请直接输出翻译结果，不要包含任何其他内容。
```

**核心实现**:

**core/ai_analyzer.py**:
```python
import subprocess
import json
from dataclasses import dataclass

@dataclass
class AnalysisResult:
    """AI 分析结果"""
    summary: str
    chapters: List[Tuple[int, str]]
    video_type: str
    speakers: str

def analyze_video(subtitle_with_metadata: str, config: Config) -> AnalysisResult:
    """
    使用 Claude CLI 分析视频内容

    Args:
        subtitle_with_metadata: 含元数据的字幕文本
        config: 系统配置

    Returns:
        AnalysisResult 对象
    """
    # 读取 prompt 模板
    with open("prompts/yt-summary.md", 'r', encoding='utf-8') as f:
        prompt_template = f.read()

    # 填充模板
    prompt = prompt_template.replace("{{SUBTITLE_WITH_METADATA}}", subtitle_with_metadata)

    # 调用 Claude CLI
    result = subprocess.run(
        ['claude', '--print', '-p', prompt],
        capture_output=True,
        text=True,
        timeout=config.claude_timeout_seconds
    )

    # 解析 JSON 结果
    result_json = json.loads(result.stdout)

    return AnalysisResult(
        summary=result_json['summary'],
        chapters=[(c['start_sec'], c['title']) for c in result_json['chapters']],
        video_type=result_json['video_type'],
        speakers=result_json['speakers']
    )
```

**core/translator.py**:
```python
import subprocess
from dataclasses import dataclass

@dataclass
class TranslationResult:
    """翻译结果"""
    chapter_idx: int
    translation: str
    success: bool
    error: Optional[str] = None

def translate_chapter(
    chapter_text: str,
    chapter_title: str,
    time_range: str,
    previous_context: dict,
    analysis: AnalysisResult,
    config: Config
) -> TranslationResult:
    """
    翻译单个章节（带重试机制，使用 Claude CLI）

    Args:
        chapter_text: 章节原文
        chapter_title: 章节标题
        time_range: 时间范围（如 "00:00-05:30"）
        previous_context: 上文上下文
        analysis: AI 分析结果
        config: 系统配置

    Returns:
        TranslationResult 对象
    """
    # 读取并填充 prompt 模板
    with open("prompts/yt-translate.md", 'r', encoding='utf-8') as f:
        prompt_template = f.read()

    prompt = prompt_template \
        .replace("{{VIDEO_TYPE}}", analysis.video_type) \
        .replace("{{SPEAKERS}}", analysis.speakers) \
        .replace("{{CHAPTER_TITLE}}", chapter_title) \
        .replace("{{TIME_RANGE}}", time_range) \
        .replace("{{SEGMENT_TEXT}}", chapter_text) \
        .replace("{{CONTEXT_LINES}}", str(config.context_lines)) \
        .replace("{{PREVIOUS_ORIGINAL}}", previous_context.get("original", "")) \
        .replace("{{PREVIOUS_TRANSLATION}}", previous_context.get("translation", ""))

    # 重试逻辑
    for attempt in range(config.translation_max_retries + 1):
        try:
            result = subprocess.run(
                ['claude', '--print', '-p', prompt],
                capture_output=True,
                text=True,
                timeout=config.claude_timeout_seconds
            )

            return TranslationResult(
                chapter_idx=0,  # 由调用方设置
                translation=result.stdout,
                success=True
            )

        except Exception as e:
            if attempt < config.translation_max_retries:
                time.sleep(config.translation_retry_delay * (2 ** attempt))
            else:
                return TranslationResult(
                    chapter_idx=0,
                    translation="",
                    success=False,
                    error=str(e)
                )
```

---

### Phase 4: 输出与整合 📝

**目标**: 生成最终输出并整合所有模块

**📖 参考文档**:
- [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - 输出生成流程、Markdown 格式规范、邮件通知架构

**任务清单**:
1. ✅ 实现 `core/output_generator.py` - Markdown 生成器
2. ✅ 实现 `infrastructure/notifier.py` - 邮件通知模块
3. ✅ 实现 `core/pipeline.py` - 流程协调器
4. ✅ 实现 `main.py` - 程序入口
5. ✅ 创建 `tests/test_pipeline.py` - 集成测试

**完成标准**:
```bash
pytest tests/ -v                           # 所有测试通过
python main.py --video TEST_VIDEO_ID       # 成功处理测试视频
ls ai_output/summary/                      # 输出文件存在
cat youtube_archive.json                   # 归档记录正确
```

**Markdown 输出格式**:
```markdown
# {视频标题}

{视频简介}

原始链接: {url}
发布日期: {upload_date}
时长: {duration}

---

## 摘要

{AI生成的摘要}

---

## 完整翻译

### (00:00 - 05:30) Chapter 1 Title

{翻译内容}

### (05:30 - 10:00) Chapter 2 Title

{翻译内容}

---

## 处理日志

- 总章节数: N
- 成功翻译: N
- 失败章节: N

{如果有失败章节，列出详情}
```

**core/pipeline.py**:
```python
def process_video(video_id: str, config: Config, archive: Archive) -> bool:
    """
    处理单个视频的完整流程

    Args:
        video_id: YouTube 视频 ID
        config: 系统配置
        archive: 归档管理器

    Returns:
        是否成功
    """
    logger = logging.getLogger(__name__)

    try:
        # 阶段 2: 内容获取
        logger.info(f"[{video_id}] 获取视频信息...")
        video_info = fetch_video_info(video_id)
        subtitle_path = download_subtitle(video_id, config.subtitle_language)

        # 阶段 3: 字幕处理
        logger.info(f"[{video_id}] 处理字幕...")
        subtitle_data = process_subtitle(subtitle_path, video_info, config)

        # 阶段 4: AI 分析
        logger.info(f"[{video_id}] 分析视频内容...")
        analysis = analyze_video(subtitle_data.with_metadata, config)

        # 阶段 5: 章节优化
        logger.info(f"[{video_id}] 优化章节...")
        optimized_chapters = optimize_chapters(
            analysis.chapters,
            subtitle_data.entries,
            config
        )

        # 阶段 6: 翻译
        logger.info(f"[{video_id}] 翻译 {len(optimized_chapters)} 个章节...")
        translations, failed = translate_all_chapters(
            optimized_chapters,
            subtitle_data.entries,
            analysis,
            config
        )

        # 阶段 7: 输出生成
        logger.info(f"[{video_id}] 生成输出...")
        markdown = generate_markdown(
            video_info,
            analysis,
            optimized_chapters,
            translations,
            failed
        )
        output_path = save_output(markdown, video_info, config)

        # 阶段 9: 归档
        archive.mark_processed(
            video_id,
            video_info.title,
            output_path,
            len(failed)
        )

        logger.info(f"[{video_id}] 处理完成: {video_info.title}")
        return True

    except Exception as e:
        logger.error(f"[{video_id}] 处理失败: {e}")
        return False
```

**infrastructure/notifier.py** (邮件通知模块):

> 🎯 **重要**: 项目中已存在完整的邮件发送实现 ([email_sender.py](email_sender.py) 330+ 行)。
> 下面的 `infrastructure/notifier.py` 可以直接改造现有的 `email_sender.py`，或创建包装模块。

```python
from typing import List, Dict, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import logging

logger = logging.getLogger(__name__)

def send_update_email(video_infos: List[Dict]) -> bool:
    """
    发送视频处理完成通知邮件

    Args:
        video_infos: 视频信息列表，每项包含:
            - file_path: str, Markdown 文件路径
            - channel: str, 频道名称
            - title: str, 视频标题
            - url: str, 原始 YouTube URL (可选)

    Returns:
        bool: 是否发送成功
    """
    try:
        from email_config import (
            EMAIL_SENDER, EMAIL_RECEIVER, EMAIL_PASSWORD,
            SMTP_SERVER, SMTP_PORT, MAIL_ENABLE
        )
    except ImportError:
        logger.warning("⚠️ 找不到 email_config.py，邮件功能已禁用")
        return False

    if not MAIL_ENABLE or not video_infos:
        return False

    try:
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = f"[YouTube 更新] 处理了 {len(video_infos)} 个新视频"

        # 生成 HTML 邮件内容
        html_body = _generate_html_body(video_infos)
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        # 可选：添加 Markdown 文件作为附件
        for info in video_infos:
            file_path = info.get('file_path')
            if file_path:
                _attach_file(msg, file_path)

        # 发送邮件
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        logger.info(f"✅ 邮件发送成功 ({len(video_infos)} 个视频)")
        return True

    except Exception as e:
        logger.error(f"❌ 邮件发送失败: {e}")
        return False


def _generate_html_body(video_infos: List[Dict]) -> str:
    """
    生成 Newsletter 风格的 HTML 邮件正文

    包含：
    - 顶部目录 (TOC) 导航
    - 详细内容（每个视频的 Markdown 转 HTML）
    - 响应式设计，支持移动端

    Args:
        video_infos: 视频信息列表

    Returns:
        str: HTML 格式邮件内容
    """
    from datetime import datetime
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
h1, h2 {{ color: #333; }}
.header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
.toc-section {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
.toc-item {{ margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #e0e0e0; }}
.video-section {{ margin-bottom: 30px; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; }}
</style>
</head>
<body>
<div class="header">
  <h1>📺 YouTube AI 摘要/翻译更新</h1>
  <p>更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
  <p>处理视频数: {len(video_infos)} 个</p>
</div>

<div class="toc-section">
  <h2>📬 目录导航</h2>
  {''.join([f'<div class="toc-item"><a href="#video-{i}">[{i}] {info.get("title", "未知")}</a></div>' for i, info in enumerate(video_infos, 1)])}
</div>

<div class="divider">📋 详细内容</div>
"""

    # 添加每个视频的详细内容
    for i, info in enumerate(video_infos, 1):
        file_path = info.get('file_path')
        html += f'<div class="video-section" id="video-{i}">\n'
        html += f'<h2>📺 [{i}] {info.get("title", "未知")}</h2>\n'

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    html += f'<pre>{content}</pre>\n'
            except Exception as e:
                html += f'<p style="color: red;">文件读取失败: {e}</p>\n'

        html += '</div>\n'

    html += """
</body>
</html>
"""
    return html


def _extract_video_summary(file_path: str) -> Dict:
    """
    从 Markdown 文件提取视频摘要信息

    Returns:
        dict: {'title': str, 'tldr': str, 'original_link': str}
    """
    import re
    summary = {'title': '未知标题', 'tldr': '', 'original_link': ''}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')

            # 提取标题
            for line in lines:
                if line.startswith('# '):
                    summary['title'] = line.replace('# ', '').strip()
                    break

            # 提取 TL;DR
            for i, line in enumerate(lines):
                if 'TL;DR' in line:
                    if i + 1 < len(lines):
                        summary['tldr'] = lines[i + 1].strip()[:200]
                    break

            # 提取链接
            for line in lines:
                if 'http' in line:
                    match = re.search(r'https?://[^\s]+', line)
                    if match:
                        summary['original_link'] = match.group(0)
                        break

    except Exception as e:
        logger.debug(f"提取摘要失败: {e}")

    return summary


def _attach_file(msg: MIMEMultipart, file_path: str):
    """将文件作为附件添加到邮件"""
    from email.mime.base import MIMEBase
    from email import encoders
    import os

    try:
        with open(file_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())

        encoders.encode_base64(part)
        filename = os.path.basename(file_path)
        part.add_header('Content-Disposition', f'attachment; filename= {filename}')
        msg.attach(part)

    except Exception as e:
        logger.error(f"附加文件失败: {e}")
```

**邮件配置文件** (email_config.py):
```python
"""
邮件配置文件（Git 忽略，不上传 GitHub）
"""

# Gmail SMTP 配置
EMAIL_SENDER = "your-email@gmail.com"
EMAIL_RECEIVER = "recipient@gmail.com"
EMAIL_PASSWORD = "your-app-password"  # Gmail 应用专用密码

# SMTP 服务器配置
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# 邮件启用标志
MAIL_ENABLE = False  # 开发时默认禁用，需要时设置为 True
```

**在 pipeline.py 中集成邮件通知**:
```python
# 在 process_video() 函数的最后添加：

# 阶段 9: 邮件通知
if config.email_enabled:
    from infrastructure.notifier import send_update_email
    video_summary = {
        'file_path': output_path,
        'channel': video_info.uploader,
        'title': video_info.title,
        'url': video_info.url
    }
    send_update_email([video_summary])
```

**requirements.txt 更新**:
```bash
# 添加可选的 Markdown 转 HTML 支持
markdown>=3.0.0  # 用于更好的 HTML 邮件格式（可选）
```

---

**main.py**:
```python
import argparse
import time
from infrastructure.config import load_config
from infrastructure.archive import Archive
from core.pipeline import process_video
from core.video_discovery import fetch_channel_videos, filter_new_videos

def main():
    """程序入口"""
    parser = argparse.ArgumentParser(
        description="YouTube 视频监控与翻译系统"
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="持续循环运行"
    )
    parser.add_argument(
        "--video",
        help="处理单个视频 ID"
    )
    args = parser.parse_args()

    # 加载配置
    config = load_config()
    archive = Archive(config.archive_file)

    # 单视频模式
    if args.video:
        process_video(args.video, config, archive)
        return

    # 循环模式
    while True:
        for channel in config.channels:
            video_ids = fetch_channel_videos(
                channel["channel_id"],
                config.lookback_hours
            )
            new_videos = filter_new_videos(video_ids, archive)

            for video_id in new_videos:
                process_video(video_id, config, archive)

        if not args.loop or config.check_interval_hours == 0:
            break

        time.sleep(config.check_interval_hours * 3600)

if __name__ == "__main__":
    main()
```

---

## 📋 开发规范

### 代码风格

**强制要求**:
1. ✅ **所有函数必须有 type hints**（参数和返回值）
2. ✅ **所有函数必须有 docstring**（Google 风格）
3. ✅ **使用 logging 记录日志**（禁止 print）
4. ✅ **使用 dataclass 定义数据结构**
5. ✅ **所有配置从 config_ai.json 读取**（禁止硬编码）

**示例**:
```python
from dataclasses import dataclass
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class VideoInfo:
    """视频基本信息"""
    video_id: str
    title: str

def fetch_video_info(video_id: str) -> Optional[VideoInfo]:
    """
    获取视频元数据

    Args:
        video_id: YouTube 视频 ID

    Returns:
        VideoInfo 对象，失败返回 None
    """
    logger.info(f"Fetching video: {video_id}")
    # 实现...
```

### 错误处理

**强制要求**:
1. ✅ **翻译失败必须记录到 failed_chapters**（章节索引 + 标题 + 错误）
2. ✅ **网络请求必须使用重试机制**（指数退避，最多 2 次）
3. ✅ **文件名冲突添加时间戳后缀**（格式: `name_20251221_103045.md`）
4. ✅ **所有异常必须 log.error() 记录**

### 测试覆盖

**强制要求**:
1. ✅ **每个模块必须有对应测试文件**
2. ✅ **测试覆盖：正常路径 + 边界条件 + 错误处理**
3. ✅ **使用 Mock 减少外部依赖**（API、文件 IO）
4. ✅ **集成测试使用真实短视频**（5-10 分钟）

**运行测试**:
```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_config.py -v

# 显示覆盖率
pytest --cov=core --cov=infrastructure tests/
```

---

## 🔍 调试与验证

### 开发阶段调试

**使用测试视频**:
```python
# 在 config_ai.json 中添加
{
  "test_mode": true,
  "test_video_id": "dQw4w9WgXcQ"  # 替换为实际短视频
}
```

**日志级别**:
```python
# infrastructure/logger.py
import logging

def setup_logger(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
```

**Mock AI 调用**:
```python
# tests/conftest.py
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_claude_cli():
    """Mock Claude CLI 调用（减少开发成本）"""
    with patch("subprocess.run") as mock:
        mock.return_value.stdout = '{"summary": "test"}'
        mock.return_value.returncode = 0
        yield mock
```

### 验收测试

**完成所有 Phase 后运行**:
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 确保 Claude CLI 可用
claude --version

# 3. 运行所有测试
pytest tests/ -v

# 4. 处理单个测试视频
python main.py --video TEST_VIDEO_ID

# 5. 验证输出
ls -lh ai_output/summary/
cat youtube_archive.json

# 6. 检查日志
tail -f logs/app.log
```

**预期结果**:
- ✅ 所有测试通过
- ✅ 输出目录有 Markdown 文件
- ✅ 归档记录包含视频信息
- ✅ Markdown 格式规范
- ✅ 翻译质量良好
- ✅ 日志无严重错误

---

## 🚀 启动开发

### 给 Claude Code 的完整 Prompt

```
你好，Claude Code！请按照 CLAUDE.md 的指引，从零开始构建整个 YouTube 监控与翻译系统。

阅读以下文档了解完整背景：
1. SYSTEM_ARCHITECTURE.md（系统架构设计）
2. CLAUDE.md（开发蓝图，本文件）
3. channels.json（频道列表）
4. config_ai.json（系统配置）

开发要求：
1. 严格按照 Phase 1 → Phase 2 → Phase 3 → Phase 4 的顺序实现
2. 每个函数必须有 type hints 和 docstring（Google 风格）
3. 每个模块完成后必须写对应测试
4. 运行 pytest 确保通过后再进入下一阶段
5. 所有配置从 config_ai.json 读取，禁止硬编码
6. **每个开发阶段都应先阅读 SYSTEM_ARCHITECTURE.md 中对应部分，理解设计意图后再编写代码**

现在开始 Phase 1：创建项目结构和基础设施模块。

请逐步完成，每完成一个阶段向我报告进度。开始吧！
```

---

## 📚 附录

### 常见问题

**Q1: yt-dlp 下载失败**
```bash
pip install -U yt-dlp
yt-dlp --cookies-from-browser chrome VIDEO_URL
```

**Q2: Claude CLI 超时**
```json
{
  "claude_timeout_seconds": 1200,
  "max_chapter_duration": 600
}
```

**Q3: 字幕语言不可用**
```python
try:
    download_subtitle(video_id, "en")
except:
    download_subtitle(video_id, "en", auto=True)
```

### 扩展功能（基础版完成后）

1. **Review Agent** - 内容质量审查
2. **Gemini Fallback** - 备选翻译方案
3. **Web UI** - Flask 可视化界面
4. **数据库存储** - PostgreSQL 替代 JSON
5. **并行处理** - 多视频同时处理
6. **Docker 容器化** - 简化部署
7. **监控告警** - Prometheus + Grafana

---

**版本**: v1.0
**更新**: 2025-12-21
**状态**: 🚀 准备启动开发
**作者**: AI 辅助生成
**License**: MIT

---

> **"From zero to production, powered by Claude"**
>
> 这份蓝图将指引 Claude Code 自动化完成整个系统的开发。
> 让我们见证 AI 驱动的软件工程的力量！
