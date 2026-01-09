"""
Reviewer Module - 审核和重组翻译内容

功能：
1. 章节重组：利用章节导航表时间戳重新划分翻译内容（Python 代码）
2. 删除 AI 废话：用 Sonnet 4 删除无关内容（可选，只删不改）
"""

import re
import logging
import subprocess
from typing import List, Tuple, Optional
from pathlib import Path

from core.ai_analyzer import CLAUDE_CLI

logger = logging.getLogger(__name__)


def parse_time_to_seconds(time_str: str) -> int:
    """
    解析时间字符串为秒数
    支持格式: "00:00", "0:00", "00:00:00", "1:23:45"
    """
    time_str = time_str.strip()
    parts = time_str.split(':')

    if len(parts) == 2:
        # MM:SS 或 M:SS
        minutes, seconds = int(parts[0]), int(parts[1])
        return minutes * 60 + seconds
    elif len(parts) == 3:
        # HH:MM:SS
        hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    else:
        return 0


def format_time(seconds: int) -> str:
    """秒数格式化为 MM:SS 或 HH:MM:SS"""
    if seconds >= 3600:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"


def parse_chapter_table(markdown_content: str) -> List[Tuple[int, int, str, str]]:
    """
    解析章节导航表，提取时间戳和标题

    返回: [(start_sec, end_sec, title, summary), ...]
    """
    chapters = []

    # 查找章节导航表
    # 格式: | 00:00-02:32 | 章节标题 | 一句话概括 |
    table_pattern = r'\|\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–]\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|'

    matches = re.findall(table_pattern, markdown_content)

    for match in matches:
        start_time, end_time, title, summary = match
        start_sec = parse_time_to_seconds(start_time)
        end_sec = parse_time_to_seconds(end_time)
        title = title.strip()
        summary = summary.strip()

        if start_sec < end_sec and title:
            chapters.append((start_sec, end_sec, title, summary))

    logger.info(f"解析到 {len(chapters)} 个章节")
    return chapters


def parse_translation_blocks(markdown_content: str) -> List[Tuple[int, int, str]]:
    """
    解析翻译内容中的时间戳块

    支持两种格式:
    1. 细分时间戳: **(0:00 - 1:20)**
    2. 章节标题: ### (0:00 - 15:00) Part 1

    返回: [(start_sec, end_sec, content), ...]
    """
    blocks = []

    # 提取翻译部分
    translation_match = re.search(r'## 📝 完整翻译\s*\n(.*?)(?=\n---|\Z)', markdown_content, re.DOTALL)
    if not translation_match:
        logger.warning("未找到翻译部分")
        return blocks

    translation_content = translation_match.group(1)

    # 先尝试匹配细分时间戳格式: **(0:00 - 1:20)**
    fine_pattern = r'\*\*\((\d{1,2}:\d{2}(?::\d{2})?)\s*[-–]\s*(\d{1,2}:\d{2}(?::\d{2})?)\)\*\*\s*\n(.*?)(?=\*\*\(\d{1,2}:\d{2}|\Z)'
    matches = re.findall(fine_pattern, translation_content, re.DOTALL)

    if matches:
        # 找到细分时间戳
        for match in matches:
            start_time, end_time, content = match
            start_sec = parse_time_to_seconds(start_time)
            end_sec = parse_time_to_seconds(end_time)
            content = content.strip()
            if content:
                blocks.append((start_sec, end_sec, content))
        logger.info(f"解析到 {len(blocks)} 个细分时间戳块")
    else:
        # 尝试匹配章节标题格式: ### (0:00 - 15:00) ... 或 ### (15:00 - End) ...
        chapter_pattern = r'###\s*\((\d{1,2}:\d{2}(?::\d{2})?)\s*[-–]\s*(\d{1,2}:\d{2}(?::\d{2})?|End)\)\s*[^\n]*\n+(.*?)(?=###\s*\(|\Z)'
        matches = re.findall(chapter_pattern, translation_content, re.DOTALL)

        for match in matches:
            start_time, end_time_str, content = match
            start_sec = parse_time_to_seconds(start_time)
            # 如果是 "End"，使用一个很大的数字（例如 999999）
            end_sec = 999999 if end_time_str == "End" else parse_time_to_seconds(end_time_str)
            content = content.strip()
            if content:
                blocks.append((start_sec, end_sec, content))
        logger.info(f"解析到 {len(blocks)} 个章节翻译块")

    return blocks


def restructure_translation(markdown_content: str) -> str:
    """
    用 Python 代码重组翻译章节（不依赖 AI）

    1. 解析章节导航表，提取时间戳和标题
    2. 解析翻译内容中的细分时间戳
    3. 按时间范围重新分配内容到各章节
    """
    chapters = parse_chapter_table(markdown_content)
    if not chapters:
        logger.warning("未找到章节导航表，跳过重组")
        return markdown_content

    blocks = parse_translation_blocks(markdown_content)
    if not blocks:
        logger.warning("未找到翻译时间戳块，跳过重组")
        return markdown_content

    # 构建新的翻译部分
    new_translation_lines = ["## 📝 完整翻译", ""]

    for start_sec, end_sec, title, summary in chapters:
        # 添加章节标题
        new_translation_lines.append(f"### ({format_time(start_sec)} - {format_time(end_sec)}) {title}")
        new_translation_lines.append(f"> {summary}")
        new_translation_lines.append("")

        # 找到属于这个章节的翻译块
        chapter_has_content = False
        for block_start, block_end, content in blocks:
            # 如果块的开始时间在章节范围内
            if block_start >= start_sec and block_start < end_sec:
                new_translation_lines.append(f"**({format_time(block_start)} - {format_time(block_end)})**")
                new_translation_lines.append("")
                new_translation_lines.append(content)
                new_translation_lines.append("")
                chapter_has_content = True

        if not chapter_has_content:
            new_translation_lines.append("*（此章节无翻译内容）*")
            new_translation_lines.append("")

    new_translation = "\n".join(new_translation_lines)

    # 替换原翻译部分
    result = replace_translation_section(markdown_content, new_translation)
    logger.info("章节重组完成")
    return result


def replace_translation_section(markdown_content: str, new_translation: str) -> str:
    """替换 markdown 中的翻译部分"""
    # 找到翻译部分的位置
    pattern = r'## 📝 完整翻译\s*\n.*?(?=\n---\s*\n\*生成时间|\Z)'

    if re.search(pattern, markdown_content, re.DOTALL):
        # 转义替换字符串中的反斜杠，避免被解释为正则表达式转义序列
        escaped_translation = new_translation.replace('\\', r'\\')
        result = re.sub(pattern, escaped_translation + "\n", markdown_content, flags=re.DOTALL)
        return result
    else:
        logger.warning("未找到翻译部分，无法替换")
        return markdown_content


def remove_fine_timestamps(markdown_content: str) -> str:
    """
    删除细分时间戳，只保留章节标题时间戳

    删除格式: **(0:00 - 1:20)**
    保留格式: ### (0:00 - 5:30) 章节标题

    这样避免细分时间戳与章节时间戳冲突
    """
    # 匹配细分时间戳行: **(MM:SS - MM:SS)** 后面可能有空行
    # 注意不要匹配章节标题 ### (...)
    pattern = r'\*\*\(\d{1,2}:\d{2}(?::\d{2})?\s*[-–]\s*\d{1,2}:\d{2}(?::\d{2})?\)\*\*\s*\n\s*\n?'

    original_len = len(markdown_content)
    result = re.sub(pattern, '', markdown_content)
    removed_count = (original_len - len(result)) // 20  # 估算删除的时间戳数量

    if removed_count > 0:
        logger.info(f"删除了约 {removed_count} 个细分时间戳")

    return result


def remove_ai_garbage(text: str, timeout: int = 120) -> Optional[str]:
    """
    用 Claude Sonnet 4 删除 AI 生成的废话

    严格限制：只删除，不添加，不改写

    删除内容：
    - "我已经完成翻译"
    - "让我来解释一下"
    - "以下是翻译结果"
    - "希望对你有帮助"
    - 其他与视频内容无关的 AI 废话
    """
    prompt = """你是一个文本清理工具。只做以下操作：

1. 删除与视频内容无关的 AI 废话，例如：
   - "我已经完成翻译"
   - "让我来解释一下"
   - "以下是翻译结果"
   - "希望对你有帮助"
   - AI 的自我介绍或总结
   - "根据您的要求"、"按照指示"等

2. 删除明显的语法错误（如乱码、重复词）

严格禁止：
- 不要修改视频翻译内容本身
- 不要删除时间戳 **(MM:SS - MM:SS)**
- 不要改写任何句子
- 不要添加任何内容
- 不要做翻译润色

直接输出清理后的文本，不要任何解释。

---

""" + text

    try:
        cmd = [
            str(CLAUDE_CLI),
            "-p", prompt,
            "--model", "claude-sonnet-4-20250514",
            "--output-format", "text"
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode == 0 and result.stdout.strip():
            cleaned = result.stdout.strip()
            # 简单验证：清理后的文本不应该比原文短太多
            if len(cleaned) > len(text) * 0.5:
                logger.info("AI 废话清理完成")
                return cleaned
            else:
                logger.warning("清理结果过短，放弃使用")
                return None
        else:
            logger.error(f"Sonnet 4 调用失败: {result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        logger.error(f"Sonnet 4 调用超时 ({timeout}s)")
        return None
    except Exception as e:
        logger.error(f"Sonnet 4 调用错误: {e}")
        return None


def review_content(
    markdown_content: str,
    restructure: bool = True,
    remove_garbage: bool = True,
    remove_timestamps: bool = True,
    timeout: int = 300
) -> str:
    """
    审核并优化翻译内容

    Args:
        markdown_content: 原始 Markdown 内容
        restructure: 是否重组章节（Python 代码）
        remove_garbage: 是否删除 AI 废话（Sonnet 4）
        remove_timestamps: 是否删除细分时间戳（保留章节标题时间戳）
        timeout: Sonnet 4 调用超时时间

    Returns:
        审核后的 Markdown 内容
    """
    result = markdown_content

    # 1. 章节重组（Python 代码，可靠）- 必须在删除时间戳之前执行
    if restructure:
        logger.info("开始章节重组...")
        result = restructure_translation(result)

    # 2. 删除细分时间戳（重组完成后删除，避免与章节时间戳冲突）
    if remove_timestamps:
        logger.info("删除细分时间戳...")
        result = remove_fine_timestamps(result)

    # 3. 删除 AI 废话（sonnet-4，可选）
    if remove_garbage:
        logger.info("开始清理 AI 废话...")
        cleaned = remove_ai_garbage(result, timeout)
        if cleaned:
            result = cleaned
        else:
            logger.warning("AI 废话清理失败，使用原内容")

    return result
