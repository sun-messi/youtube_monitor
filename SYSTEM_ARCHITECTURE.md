# YouTube 监控与翻译系统 - 系统架构设计

> **独立的系统设计文档** - 从零开始构建系统的完整参考
>
> 本文档描述系统的完整架构、数据流和核心功能
>
> 最后更新: 2025-12-21

---

## 📊 核心流程概览

```
┌─────────────────────────────────────────────────────────────────┐
│                    YouTube 监控与翻译系统                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  阶段 1: 视频发现与筛选                           │
    │  - 多频道 RSS 监控                                │
    │  - 发布时间过滤                                   │
    │  - 视频时长过滤                                   │
    │  - 重复检测（归档查询）                           │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  阶段 2: 内容获取                                 │
    │  - 字幕下载（多语言 Fallback）                   │
    │  - 视频元数据提取（标题、简介、发布日期）         │
    │  - YouTube 章节时间轴提取                        │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  阶段 3: 字幕处理                                 │
    │  - SRT 格式解析                                   │
    │  - 智能合并（句子边界 + 时间间隔）               │
    │  - 元数据注入（标题、简介、章节）                │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  阶段 4: AI 内容理解                              │
    │  - Claude 生成视频摘要                           │
    │  - 提取/生成章节时间轴                           │
    │  - 检测视频类型（访谈/演讲/其他）               │
    │  - 提取说话人信息                                │
    │  comment: 是否需要一个 Investing Skill Agent 专注于摘要？ │
    │  可以利用 Summary Skill Prompt 模板             │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  阶段 5: 章节智能处理                             │
    │  - 章节长度分析                                   │
    │  - 过短章节合并（< 3 分钟）                       │
    │  - 过长章节拆分（> 15 分钟）                      │
    │  - 句子边界完整性保证                             │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  阶段 6: 分章节翻译                               │
    │  - 按顺序逐段翻译，防止视频太长超出 token 限制   │
    │  - 上下文维护（前一段的最后 5 行原文和译文）      │
    │  - Claude 翻译（利用 Translator Agent 和翻译 Skill Prompt) │
    │  - 翻译失败重试（指数退避）                      │
    │  - 失败记录与标注                                 │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  阶段 7: 内容整合与输出                           │
    │  - Markdown 格式生成                             │
    │  - 摘要 + 翻译合并                                │
    │  - 文件命名与组织                                │
    │  - 归档记录更新                                  │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  阶段 7.5: 内容审查（可选）                       │
    │  - Review Agent 分段阅读从头梳理                 │
    │  - 去除拼写错误                                  │
    │  - 移除无关信息（如 "Translation completed!"）   │
    │  - 清理多余的 Part 标记                          │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  阶段 8: 通知与归档                               │
    │  - 邮件通知（HTML 格式）                         │
    │  - 归档数据持久化                                │
    │  - 处理日志记录                                  │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  阶段 9: 循环与调度                               │
    │  - 定时循环检查（可配置间隔）                    │
    │  - 可中断睡眠（Ctrl+C 响应）                     │
    │  - 单次运行模式支持                              │
    └─────────────────────────────────────────────────┘
```

---

## 📊 系统简化流程

```
RSS监控 → 视频筛选 → 字幕下载 → 字幕处理 → AI分析 → 章节优化 → 分段翻译 → 内容审查 → 输出生成 → 邮件通知 → 归档
```

---

## 🔄 核心数据流

### 数据结构

```python
# 视频基本信息
VideoInfo:
  - video_id: str
  - title: str
  - description: str
  - upload_date: str (YYYYMMDD)
  - duration_sec: int
  - uploader: str
  - url: str
  - chapters: List[(start_sec, title)]  # YouTube原生章节

# 字幕信息
SubtitleData:
  - raw_text: str  # 合并后的原始字幕
  - entries: List[(start_sec, end_sec, text)]  # 结构化条目
  - with_metadata: str  # 注入元数据后的版本

# 处理结果
ProcessResult:
  - video_id: str
  - title: str
  - summary: str  # AI生成的摘要
  - chapters: List[(start_sec, title)]  # 最终章节列表
  - video_type: str  # "interview" | "speech" | "other"
  - speakers: str  # 说话人信息
  - translations: Dict[chapter_idx, str]  # 各章节翻译
  - failed_chapters: List[dict]  # 失败的章节记录
  - markdown_output: str  # 最终输出内容
```

---

## 🎯 阶段设计

### 阶段 1: 视频发现与筛选

**功能**:
- 从多个频道的 RSS 源获取最新视频
- 按发布时间筛选 (配置: `lookback_hours`)
- 按视频时长筛选 (配置: `min_duration_minutes`)
- 查询归档记录避免重复处理

**输入**: 频道列表
**输出**: 待处理的视频 ID 列表
**配置参数**:
- `lookback_hours`: 20 (默认回溯时长)
- `min_duration_minutes`: 10 (最小视频时长)

**错误处理**:
- RSS 源无法访问时，记录日志并继续
- 时间解析失败时，跳过该视频
- 归档查询失败时，当作新视频处理

---

### 阶段 2: 内容获取

**功能**:
- 使用 yt-dlp 下载字幕文件
- 优先级: 手动字幕 → 自动字幕 → 任意 SRT
- 提取视频元数据 (标题、简介、发布日期、频道等)
- 提取 YouTube 原生章节时间轴

**输入**: 视频 ID
**输出**: VideoInfo 对象
**配置参数**:
- `subtitle_language`: "en" (字幕语言)

**依赖**: yt-dlp

---

### 阶段 3: 字幕处理

**功能**:
- 解析 SRT 格式字幕
- 智能合并相邻字幕条目 (基于时间间隔 + 句子边界)
- 注入视频元数据到字幕开头 (标题、简介、章节列表)

**输入**: 字幕文件路径
**输出**: SubtitleData 对象
**配置参数**:
- `subtitle_merge_interval`: 30 (秒，相邻字幕的合并阈值)

**规则**:
- 相邻字幕时间差 >= `subtitle_merge_interval` → 强制分段
- 文本以句号/问号/感叹号结尾 且时间差 > 2秒 → 分段

---

### 阶段 4: AI 内容总结

**功能**:
- 使用 Claude 生成视频摘要 (使用 Summary Skill) 需要一个 建立一个Investing Skill Agent 专注于摘要，因为/home/sunj11/projects/youtube-monitor-translator/channels.json主要是投资频道。读取/home/sunj11/projects/youtube-monitor-translator/prompts/yt-summary.md 给出skill 让它专供Investing的相关翻译
- 从摘要中提取/生成章节时间轴
- 检测视频类型 (访谈/演讲/其他)
- 提取说话人信息

**输入**: SubtitleData (带元数据)
**输出**: 摘要、章节列表、视频类型、说话人
**配置参数**:
- `claude_model`: "claude-sonnet-4-20250514"
- `claude_timeout_seconds`: 600

**Prompt**: 使用 `prompts/yt-summary.md` 模板

**Fallback**: 如果无法提取章节，按 900 秒 (15分钟) 自动切分

---

### 阶段 5: 章节智能处理

**功能**:
- 分析所有章节的时长分布
- 合并过短章节 (< 300 秒)
- 拆分过长章节 (> 900 秒) 在句子边界处
- 保证章节结束点是完整句子

**输入**: 章节列表、字幕数据
**输出**: 优化后的章节列表
**配置参数**:
- `min_chapter_duration`: 300 (秒)
- `max_chapter_duration`: 900 (秒)

**规则**:
- 合并: 连续多个过短章节 → 合并标题为 "Chapter1 + Chapter2 + ..."
- 拆分: 过长章节在句子边界处均匀拆分成多个部分
- 边界: 若章节不以标点结尾，继续向后扩展到下一个句号

---

### 阶段 6: 分章节翻译

**功能**:
- 按顺序逐章节翻译 利用Investing Skill Agent 
- 维护翻译上下文 (前一段的最后 N 行)
- 失败重试机制 (指数退避)
- 记录翻译失败的章节

**输入**: 章节列表、摘要、字幕、视频类型、说话人
**输出**: 各章节翻译结果 + 失败记录
**配置参数**:
- `context_lines`: 5 (翻译时保留的上文行数)
- `translation_max_tokens`: 100000 (单次翻译的 token 估计)
- `translation_max_retries`: 2 (最大重试次数)
- `translation_retry_delay`: 5 (秒，重试延迟)

**Prompt 模板**: `prompts/yt-translate.md` 包含以下占位符:
- `{{VIDEO_TYPE}}`: 视频类型
- `{{SPEAKERS}}`: 说话人列表
- `{{CHAPTER_TITLE}}`: 当前章节标题
- `{{TIME_RANGE}}`: 时间范围
- `{{SEGMENT_TEXT}}`: 原文内容
- `{{PREVIOUS_ORIGINAL}}`: 前一段原文 (最后 N 行)
- `{{PREVIOUS_TRANSLATION}}`: 前一段译文 (最后 N 行)

**重试策略**:
- 第 1 次重试: 等待 5 秒
- 第 2 次重试: 等待 10 秒
- 全部失败: 标记为失败并记录原因

---

### 阶段 7: 内容整合与输出

**功能**:
- 合并摘要 + 各章节翻译为单个 Markdown 文件
- 生成标准化的输出格式
- 清理文件名 (移除特殊字符、处理长度限制)
- 检测文件名冲突 (相同名称的文件)
- 更新归档记录

**输入**: ProcessResult
**输出**: Markdown 文件
**配置参数**:
- `output_dir`: "./ai_output"
- `filename_max_length`: 50

**输出格式**:
```
# {视频标题}

{简介}

原始链接: {url}

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
```

**文件命名规则**:
- 移除特殊字符: `<>:"/\|?*` 及 Unicode 引号
- 空格替换为下划线
- 长度限制: `filename_max_length` 字符
- 冲突检测: 若文件已存在，添加时间戳后缀

**目录结构**:
```
ai_output/
├── srt/{channel}/          # 原始字幕文件
├── clean/{channel}/        # 处理后字幕 (含元数据)
└── summary/{channel}/      # 最终 Markdown 输出
```

---

### 阶段 8: 内容审查 (可选)

**功能**:
- 读取生成的 Markdown 文件
- 移除拼写错误
- 移除与主题无关的信息 (如 "Translation completed!")
- 清理多余的 "Part 1", "Part 2" 标记

**输入**: Markdown 文件内容
**输出**: 清理后的内容

**实现**: 可使用专门的 Review Agent（分段阅读从头梳理，去除掉拼写错误，以及整合过程中或前面生成的跟主题无关的信息）

---

### 阶段 7.5: 翻译失败恢复 (可选备选方案)

**功能**:
- 当 Claude 翻译失败时，使用 Gemini API 作为备选方案
- 记录失败的章节和原因
- 支持部分失败恢复

**优先级**:
- 第 1 优先级: Claude CLI 翻译
- 第 2 优先级: Gemini API 翻译
- 第 3 优先级: 标记为失败

**配置**:
- `gemini_api_key`: Google Gemini API 密钥
- `gemini_model`: Gemini 模型选择
- `use_gemini_fallback`: 是否启用 Gemini 备选方案

---

### 阶段 9: 通知与归档

**功能**:
- 发送邮件通知 (可选)
- 更新归档记录 (记录已处理的视频)
- 记录处理日志

**输入**: ProcessResult、输出文件路径
**输出**: 无 (副作用: 邮件发送、文件更新)
**配置参数**:
- `email_enabled`: true/false (是否启用邮件通知)
- `email_sender`: 发件人邮箱地址
- `email_receiver`: 收件人邮箱地址
- `smtp_server`: SMTP 服务器地址
- `smtp_port`: SMTP 端口

**归档格式** (`youtube_archive.json`):
```json
{
  "video_id": {
    "title": "Video Title",
    "processed_at": "2025-12-21T10:30:00",
    "output_file": "./ai_output/summary/channel/video_translate.md",
    "failed_chapters": 0
  }
}
```

---

### 阶段 10: 循环与调度

**功能**:
- 定时循环检查新视频
- 支持单次运行和持续循环两种模式
- 可中断睡眠 (Ctrl+C 响应)

**配置参数**:
- `check_interval_hours`: 3 (循环检查间隔，0 表示单次运行)

**循环逻辑**:
```
while True:
    for channel in channels:
        videos = fetch_from_rss(channel)
        for video_id in videos:
            process_video(video_id)

    if check_interval_hours == 0:
        break

    sleep(check_interval_hours * 3600)  # 按秒睡眠以支持中断
```

---

## ⚙️ 配置系统

### 配置文件: `config_ai.json`

所有参数都在这个单一配置文件中定义，便于集中管理和调整。

#### **第一部分：视频发现与筛选**

```json
{
  "lookback_hours": 20,
  "min_duration_minutes": 10,
  "subtitle_language": "en"
}
```

- `lookback_hours` - RSS 源回溯时长（小时）。只处理最近 N 小时发布的视频，防止重复处理旧视频
- `min_duration_minutes` - 最小视频时长（分钟）。过滤掉过短的视频
- `subtitle_language` - 字幕语言代码（默认英文 "en"）

#### **第二部分：字幕处理**

```json
{
  "subtitle_merge_interval": 30
}
```

- `subtitle_merge_interval` - 字幕合并间隔（秒）。相邻字幕超过此时间则强制分段，提高可读性

#### **第三部分：AI 模型配置**

```json
{
  "claude_model": "claude-sonnet-4-20250514",
  "claude_timeout_seconds": 600
}
```

- `claude_model` - 使用的 Claude 模型。可选：
  - `claude-opus-4-20250514` - 最高质量，成本最高
  - `claude-sonnet-4-20250514` - 推荐，质量与成本平衡
  - `claude-3-5-haiku-latest` - 最快，质量较低
- `claude_timeout_seconds` - Claude CLI 超时时间（秒）。长文本翻译可能需要更长时间

#### **第四部分：章节优化**

```json
{
  "min_chapter_duration": 180,
  "max_chapter_duration": 900
}
```

- `min_chapter_duration` - 最小章节时长（秒，3 分钟）。过短的章节会被合并，减少翻译调用
- `max_chapter_duration` - 最大章节时长（秒，15 分钟）。过长的章节会被拆分，避免超出 token 限制

#### **第五部分：翻译配置**

```json
{
  "context_lines": 5,
  "translation_max_tokens": 4000,
  "translation_max_retries": 2,
  "translation_retry_delay": 5
}
```

- `context_lines` - 翻译时保留的前文行数。用于维持术语一致性和上下文连贯
- `translation_max_tokens` - 单次翻译的最大 token 估计值。用于判断是否需要拆分
- `translation_max_retries` - 翻译失败时的最大重试次数（指数退避）
- `translation_retry_delay` - 第一次重试的等待时间（秒），之后呈指数增长

#### **第六部分：输出与存储**

```json
{
  "output_dir": "./ai_output",
  "filename_max_length": 50,
  "archive_file": "./youtube_archive.json"
}
```

- `output_dir` - 输出目录路径。存放 SRT、清洁字幕、翻译输出等
- `filename_max_length` - 输出文件名最大长度（字符）。超过此长度会被截断，需配合冲突检测
- `archive_file` - 归档文件路径。记录已处理的视频 ID，防止重复处理

#### **第七部分：邮件通知**

```json
{
  "email_enabled": false,
  "email_sender": "sender@example.com",
  "email_receiver": "receiver@example.com",
  "smtp_server": "smtp.example.com",
  "smtp_port": 587
}
```

- `email_enabled` - 是否启用邮件通知（布尔值）
- `email_sender` - 发件人邮箱地址
- `email_receiver` - 收件人邮箱地址。可以和发件人相同，或指定其他收件人
- `smtp_server` - SMTP 服务器地址。根据邮箱提供商获取
- `smtp_port` - SMTP 端口。通常 587 (TLS) 或 465 (SSL)，根据提供商而定

#### **第八部分：循环调度**

```json
{
  "check_interval_hours": 3
}
```

- `check_interval_hours` - 循环检查间隔（小时）。设为 0 表示单次运行后退出，设为 3 表示每 3 小时检查一次

#### **第九部分：高级功能（可选）**

```json
{
  "use_gemini_fallback": false,
  "gemini_model": "gemini-1.5-pro",
  "enable_review_agent": false
}
```

- `use_gemini_fallback` - 是否启用 Gemini 备选方案。当 Claude 翻译失败时，尝试使用 Gemini API
- `gemini_model` - Gemini 模型版本（如果启用 Gemini）
- `enable_review_agent` - 是否启用内容审查 Agent。自动清理拼写错误和无关信息（实验性）

---

### 环境变量

这些敏感信息应该存储在环境变量中，而不是配置文件中：

| 变量名 | 用途 | 必需 |
|--------|------|------|
| `EMAIL_PASSWORD` | 邮箱授权码或应用密码 | 如果启用邮件通知 |

**注意**: Claude CLI 不需要 API Key，它使用自己的认证机制。

**如何设置环境变量**：

```bash
# Linux / macOS
export EMAIL_PASSWORD="your-password"

# Windows (PowerShell)
$env:EMAIL_PASSWORD = "your-password"

# 或在启动脚本中：
python process_ai.py
```

---

## 🔌 外部依赖

- **yt-dlp**: 视频信息和字幕下载
- **Claude CLI**: 调用 Claude 进行摘要和翻译
- **feedparser**: RSS 源解析
- **Standard Library**: 邮件发送、文件操作、日志等

---

## 🎯 核心功能清单

### 基础功能 (Priority: 必须实现)

- 多频道 RSS 监控 - 从配置的频道列表获取最新视频
- 视频时长过滤 - 过滤过短视频
- 字幕下载 - 使用 yt-dlp 下载英文字幕
- SRT 格式解析 - 提取时间戳和文本
- 智能字幕合并 - 基于时间间隔和句子边界合并
- 元数据注入 - 将标题、简介、章节信息注入字幕
- Claude 摘要生成 - 调用 Claude CLI 生成摘要
- 章节提取与 Fallback - 从摘要提取章节，失败时 15 分钟自动切分
- 分段翻译 - 按章节逐段翻译，保持上下文
- Markdown 输出生成 - 生成规范的输出文件
- 归档管理 - 记录已处理的视频
- 循环调度 - 支持定时检查和单次运行

### 高优先级功能 (Priority: 强烈建议实现)

- 过短章节合并逻辑 (< 180 秒) - 减少翻译调用次数
- 过长章节拆分逻辑 (> 900 秒) - 避免超出 token 限制
- 翻译失败重试 (主流程，指数退避) - 提高可靠性
- 翻译失败记录与标注 - 用户需要知道哪些失败了
- 文件名冲突检测 - 防止覆盖已有文件

### 中等优先级功能 (Priority: 可选但推荐)

- 内容审查 Agent - 清理拼写错误和无关信息
- 邮件通知 - 通知用户处理完成
- 多语言句子边界检测 - 支持中文、日文等

---

## 🤖 系统设计理念

### 关键设计决策

#### 1. 分段翻译而非整体翻译
- **原因**: 长视频可能超过 Claude 的 token 限制，导致翻译失败或超时
- **方案**: 按章节逐段翻译，每段维护前一段的最后 5 行作为上下文
- **优点**: 避免超时，保持上下文一致性，易于重试失败的章节

#### 2. 上下文维护机制
- **实现**: 每次翻译时传递前一段原文和译文的最后 5 行
- **占位符**: `{{PREVIOUS_ORIGINAL}}` 和 `{{PREVIOUS_TRANSLATION}}`
- **意义**: 保持术语一致、说话风格连贯

#### 3. Agent 架构考虑
系统可以分解为多个独立的 Agent，各负其责：

**Summary Agent** - 专注于摘要生成
- 输入: 带元数据的字幕
- 输出: 视频摘要、章节列表、视频类型、说话人
- 使用 Claude Summary Skill 专注于总结视频
- Prompt 模板: `prompts/yt-summary.md`

**Translator Agent** - 专注于分段翻译
- 输入: 原文章节 + 前文上下文
- 输出: 翻译结果 + 失败状态
- 支持多轮重试 (Claude → Gemini → 标记失败)
- Prompt 模板: `prompts/yt-translate.md`（7 个占位符）

**Review Agent** - 专注于内容审查
- 输入: 生成的 Markdown 文件
- 输出: 清理后的内容
- 职责:
  - 去除拼写错误
  - 移除无关信息 (如 "Translation completed!")
  - 清理多余的 Part 标记
  - 分段阅读从头梳理保证一致性

**Orchestrator** - 流程协调
- 职责: 管理各 Agent 的调度顺序
- 数据流: 检测 → 获取 → 处理 → 分析 → 优化 → 翻译 → 审查 → 通知

#### 4. 失败恢复策略 (分层方案)
第 1 层: Claude 翻译失败重试 (指数退避 5s → 10s → 标记失败)
第 2 层: Gemini API 备选 (当 Claude 仍失败时)
第 3 层: 标记为失败 (记录原因供后续审查)

#### 5. 配置驱动的设计
- 所有参数都应该可配置，避免硬编码
- 包括: 时长限制、字幕合并间隔、超时时间、重试次数等
- 便于不同场景下的调整和优化

---

## 📋 使用示例

```bash
# 单次运行 (处理所有频道新视频)
python main.py

# 持续循环运行 (每 3 小时检查一次)
python main.py --loop

# 处理单个视频
python main.py --video https://www.youtube.com/watch?v=VIDEO_ID

# 显示帮助
python main.py --help
```

---

## 🗂️ 项目文件结构

```
youtube_monitor/
├── main.py                      # 程序入口
├── config_ai.json               # 配置文件
├── channels.json                # 频道配置
├── youtube_archive.json         # 处理历史
│
├── core/
│   ├── video_discovery.py       # 阶段1: 视频发现
│   ├── content_fetcher.py       # 阶段2: 内容获取
│   ├── subtitle_processor.py    # 阶段3: 字幕处理
│   ├── ai_analyzer.py           # 阶段4: AI分析
│   ├── chapter_optimizer.py     # 阶段5: 章节优化
│   ├── translator.py            # 阶段6: 翻译
│   ├── output_generator.py      # 阶段7: 输出生成
│   └── pipeline.py              # 流程协调器
│
├── infrastructure/
│   ├── config.py                # 配置管理
│   ├── logger.py                # 日志系统
│   ├── archive.py               # 归档管理
│   └── notifier.py              # 邮件通知
│
├── utils/
│   ├── time_parser.py           # 时间戳解析
│   ├── srt_parser.py            # SRT文件解析
│   ├── file_utils.py            # 文件操作
│   └── retry_handler.py         # 重试逻辑
│
├── prompts/
│   ├── yt-summary.md            # 摘要生成 Prompt
│   └── yt-translate.md          # 翻译 Prompt
│
└── ai_output/                   # 输出目录
    ├── srt/
    ├── clean/
    └── summary/
```

---

## 📝 总结与建议

这个系统实现了完整的 YouTube 视频监控、字幕处理、AI 分析和翻译工作流。核心特点是：

1. **模块化设计**: 10 个独立的处理阶段，各自职责明确
2. **Agent 可分解性**: 可进一步分解为 Summary、Translator、Review 等 Agent
3. **配置驱动**: 所有参数都应该可配置，避免硬编码
4. **容错机制**: 多层失败恢复策略 (重试 → 备选方案 → 标记失败)
5. **可追溯**: 完整的归档、日志和失败记录

### 从零开始重写的建议

1. **分模块实现**: 按 10 个阶段顺序实现，每个阶段独立测试
2. **优先实现核心流程**: 视频发现 → 字幕处理 → 摘要生成 → 翻译 → 输出
3. **重点完善的功能**:
   - **章节优化**: 过短合并 (< 180s)、过长拆分 (> 900s)
   - **失败恢复**: 重试机制、Gemini 备选、失败记录
   - **内容审查**: Review Agent 清理输出
4. **配置优先级**: 将所有硬编码值都改为配置项
5. **测试覆盖**: 单元测试各个阶段，集成测试完整流程

### 关键实现要点 (必须正确实现)

- **翻译失败记录**: 用户需要知道哪些章节缺失，必须记录失败原因和时间戳
- **主流程重试机制**: 网络波动导致翻译失败，需要指数退避重试 (5s → 10s → 标记失败)
- **章节长度优化**: 过短/过长章节影响翻译质量和成本，合并/拆分逻辑很重要
- **文件名冲突检测**: 防止覆盖已有文件，使用时间戳或 ID 作为后缀

### 工作流程建议

```
从零开始 → 实现核心 10 个阶段 → 完善错误处理 → 优化章节处理
→ 加入重试机制 → 支持失败记录 → 集成 Review Agent → 完成
```

### Agent 架构演进建议

阶段 1: 单体应用 (process_ai.py 包含所有逻辑)
↓
阶段 2: 模块化 (分离为 core/、infrastructure/、utils/ 目录)
↓
阶段 3: Agent 化 (Summary、Translator、Review Agent 独立)
↓
阶段 4: 分布式 (可选，若需要并行处理多视频)

---

**版本**: v2.0 (重设计完整版)
**更新**: 2025-12-21
**状态**: 准备从零开始实现
