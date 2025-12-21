#!/usr/bin/env python3
"""
邮件发送模块
用于发送更新通知邮件

Based on working implementation from /home/sunj11/youtube_monitor/email_sender.py
"""

import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False

logger = logging.getLogger(__name__)


def _extract_video_summary(file_path: str) -> dict:
    """
    从 Markdown 文件中提取视频简介信息

    Args:
        file_path: Markdown 文件路径

    Returns:
        包含 title 和 tldr 的字典
    """
    summary = {
        'title': '未知标题',
        'tldr': '暂无摘要',
        'original_link': ''
    }

    if not file_path or not os.path.exists(file_path):
        return summary

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')

        # 提取标题（第一行 # Title）
        for line in lines:
            if line.startswith('# '):
                summary['title'] = line.replace('# ', '').strip()
                break

        # 提取 TL;DR 部分（通常在 ## 后）
        in_tldr = False
        tldr_lines = []

        for i, line in enumerate(lines):
            if 'TL;DR' in line and line.startswith('#'):
                in_tldr = True
                continue

            # 当遇到下一个 ## 开头的行时，停止提取 TL;DR
            if in_tldr and line.startswith('##') and 'TL;DR' not in line:
                break

            if in_tldr and line.strip():
                # 跳过标题行，收集非空内容
                if not line.startswith('#'):
                    tldr_lines.append(line.strip())

        if tldr_lines:
            summary['tldr'] = ' '.join(tldr_lines)[:200]  # 限制长度为 200 字符

        # 提取原始链接
        for line in lines:
            if '原始链接：' in line or 'Original URL:' in line or '原始链接:' in line:
                # 提取 URL
                if 'http' in line:
                    url_start = line.find('http')
                    url_end = line.find(' ', url_start)
                    if url_end == -1:
                        url_end = len(line)
                    summary['original_link'] = line[url_start:url_end]
                break

        return summary

    except Exception as e:
        logger.debug(f"提取摘要失败 {file_path}: {e}")
        return summary


def send_update_email(video_infos: list) -> bool:
    """
    发送字幕更新邮件

    Args:
        video_infos: 视频信息列表，每项可以是:
                    - dict: {file_path, channel, title, url}
                    - str: 文件路径（向后兼容）

    Returns:
        是否成功发送
    """
    try:
        # 动态导入配置以支持热加载
        import email_config

        if not email_config.MAIL_ENABLE:
            logger.info("📧 邮件发送已禁用")
            return False

        if not video_infos:
            logger.info("📧 没有新文件要发送")
            return False

        # 创建邮件对象
        msg = MIMEMultipart()
        msg['From'] = email_config.EMAIL_SENDER
        msg['To'] = email_config.EMAIL_RECEIVER
        msg['Date'] = formatdate(localtime=True)

        # 邮件主题
        msg['Subject'] = f"[YouTube 更新] 处理了 {len(video_infos)} 个新视频"

        # 邮件正文 - 读取 md 文件并转为 HTML
        body_html = _generate_html_body(video_infos)
        msg.attach(MIMEText(body_html, 'html', 'utf-8'))

        # 添加附件
        for info in video_infos:
            file_path = info.get('file_path', info) if isinstance(info, dict) else info
            if file_path and os.path.exists(file_path):
                _attach_file(msg, file_path)

        # 发送邮件
        logger.info(f"\n{'='*60}")
        logger.info(f"📧 发送邮件到: {email_config.EMAIL_RECEIVER}")
        logger.info(f"   视频数: {len(video_infos)} 个")

        server = smtplib.SMTP(email_config.SMTP_SERVER, email_config.SMTP_PORT)
        server.starttls()
        server.login(email_config.EMAIL_SENDER, email_config.EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        logger.info(f"✅ 邮件发送成功")
        logger.info(f"{'='*60}\n")
        return True

    except FileNotFoundError:
        logger.warning("⚠️ 找不到 email_config.py，请按照说明进行配置")
        return False
    except Exception as e:
        logger.error(f"❌ 邮件发送失败: {e}")
        return False


def _generate_html_body(video_infos: list) -> str:
    """
    生成 Newsletter 风格的 HTML 邮件正文
    包含：顶部目录 (TOC) + 详细内容 + 原始链接

    Args:
        video_infos: 视频信息列表，每项包含 {file_path, channel, title, url}
                    或者简单的文件路径字符串（向后兼容）

    Returns:
        HTML 格式的邮件正文
    """
    html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 20px; background: #fff; }
h1, h2, h3, h4 { color: #333; }
h1 { border-bottom: 2px solid #333; padding-bottom: 10px; }
h2 { border-bottom: 1px solid #ddd; padding-bottom: 5px; margin-top: 0; }
h3 { color: #555; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
th { background-color: #f5f5f5; }
blockquote { border-left: 4px solid #4CAF50; margin: 10px 0; padding-left: 15px; color: #666; background: #f9f9f9; }
code { background: #f5f5f5; padding: 2px 5px; border-radius: 3px; }
pre { background: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }
hr { border: none; border-top: 1px solid #ddd; margin: 20px 0; }
.header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
.header h1 { color: white; border-bottom: none; }
.header p { margin: 5px 0; opacity: 0.9; }
.toc-section { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; border: 1px solid #e0e0e0; }
.toc-section h2 { color: #333; margin-top: 0; }
.toc-item { margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #e0e0e0; }
.toc-item:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
.toc-item a { color: #1a73e8; text-decoration: none; font-weight: 500; font-size: 16px; }
.toc-item a:hover { text-decoration: underline; }
.toc-summary { color: #666; font-size: 13px; margin: 8px 0 0 0; line-height: 1.5; }
.video-section { margin-bottom: 30px; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; background: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.video-meta { background: #f8f9fa; padding: 10px 15px; border-radius: 5px; margin-bottom: 15px; }
.video-meta a { color: #1a73e8; text-decoration: none; }
.video-meta a:hover { text-decoration: underline; }
.channel-badge { display: inline-block; background: #e3f2fd; color: #1565c0; padding: 3px 10px; border-radius: 15px; font-size: 12px; margin-right: 10px; }
.divider { margin: 40px 0; padding: 20px 0 0 0; border-top: 2px solid #ddd; text-align: center; color: #999; font-size: 12px; }
</style>
</head>
<body>
<div class="header">
<h1>📺 YouTube AI 摘要/翻译更新</h1>
<p>更新时间: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + f"""</p>
<p>处理视频数: {len(video_infos)} 个</p>
</div>
"""

    # 第一阶段：收集所有视频信息并生成目录
    parsed_videos = []
    for i, info in enumerate(video_infos, 1):
        # 支持新旧两种格式
        if isinstance(info, dict):
            file_path = info.get('file_path', '')
            channel = info.get('channel', '未知频道')
            title = info.get('title', '未知标题')
            url = info.get('url', '')
        else:
            # 向后兼容：直接传文件路径
            file_path = info
            filename = os.path.basename(file_path)
            title = filename.replace('_translate.md', '').replace('_clean.txt', '').replace('_', ' ')
            channel = '未知频道'
            url = ''

        # 提取视频简介
        summary = _extract_video_summary(file_path)
        parsed_videos.append({
            'index': i,
            'file_path': file_path,
            'channel': channel,
            'title': title,
            'url': url,
            'tldr': summary['tldr'],
            'original_link': summary['original_link']
        })

    # 生成目录 (TOC)
    html += '<div class="toc-section">\n'
    html += '<h2>📬 目录导航</h2>\n'
    for video in parsed_videos:
        html += '<div class="toc-item">\n'
        html += f'<span class="channel-badge">📢 {video["channel"]}</span>\n'
        html += f'<a href="#video-{video["index"]}">[{video["index"]}] {video["title"]}</a>\n'
        if video['tldr'] and video['tldr'] != '暂无摘要':
            html += f'<p class="toc-summary">{video["tldr"]}</p>\n'
        html += '</div>\n'
    html += '</div>\n'

    # 第二阶段：生成详细内容
    html += '<div class="divider">📋 详细内容</div>\n'

    for video in parsed_videos:
        html += f'<div class="video-section" id="video-{video["index"]}">\n'
        html += f'<h2>📺 [{video["index"]}] {video["title"]}</h2>\n'

        # 视频元信息
        html += '<div class="video-meta">\n'
        html += f'<span class="channel-badge">📢 {video["channel"]}</span>\n'
        if video['url']:
            html += f'<a href="{video["url"]}" target="_blank">🔗 观看原视频</a>\n'
        if video['original_link']:
            html += f'<a href="{video["original_link"]}" target="_blank">🔗 原始链接</a>\n'
        html += '</div>\n'

        if video['file_path'] and os.path.exists(video['file_path']):
            try:
                with open(video['file_path'], 'r', encoding='utf-8') as f:
                    md_content = f.read()

                # 转换 markdown 为 HTML
                if HAS_MARKDOWN:
                    html_content = markdown.markdown(
                        md_content,
                        extensions=['tables', 'fenced_code', 'nl2br']
                    )
                else:
                    html_content = f'<pre style="white-space: pre-wrap;">{md_content}</pre>'

                html += html_content
            except Exception as e:
                html += f'<p style="color: red;">[读取文件失败: {e}]</p>'
        else:
            html += f'<p style="color: orange;">[文件不存在: {video["file_path"]}]</p>'

        html += '</div>\n'

    html += """
<hr>
<p style="color: #666; font-size: 12px; text-align: center;">--- 由 YouTube AI Pipeline 自动生成 ---</p>
</body>
</html>
"""
    return html


def _attach_file(msg: MIMEMultipart, file_path: str):
    """
    将文件作为附件添加到邮件

    Args:
        msg: 邮件对象
        file_path: 文件路径
    """
    try:
        with open(file_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())

        # 编码附件
        encoders.encode_base64(part)

        # 添加头部
        filename = os.path.basename(file_path)
        part.add_header('Content-Disposition', f'attachment; filename= {filename}')

        msg.attach(part)
        logger.debug(f"   ✓ 附加文件: {filename}")

    except Exception as e:
        logger.error(f"   ✗ 附加文件失败 {file_path}: {e}")


# Compatibility functions for the new system

def load_email_config():
    """Load email configuration from email_config.py."""
    @dataclass
    class EmailConfig:
        enabled: bool
        smtp_server: str
        smtp_port: int
        sender_email: str
        sender_password: str
        recipient_email: str

    try:
        import email_config
        return EmailConfig(
            enabled=email_config.MAIL_ENABLE,
            smtp_server=email_config.SMTP_SERVER,
            smtp_port=email_config.SMTP_PORT,
            sender_email=email_config.EMAIL_SENDER,
            sender_password=email_config.EMAIL_PASSWORD,
            recipient_email=email_config.EMAIL_RECEIVER
        )
    except ImportError:
        return EmailConfig(
            enabled=False,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            sender_email="",
            sender_password="",
            recipient_email=""
        )


def send_notification(email_config, video_infos: List[Dict]) -> object:
    """
    Send notification using EmailConfig object.

    Args:
        email_config: EmailConfig object
        video_infos: List of video info dicts

    Returns:
        NotificationResult-like object
    """
    @dataclass
    class NotificationResult:
        success: bool
        message: str

    if not email_config.enabled or not video_infos:
        return NotificationResult(success=False, message="Email disabled or no videos")

    result = send_update_email(video_infos)
    if result:
        return NotificationResult(success=True, message=f"Sent {len(video_infos)} videos")
    else:
        return NotificationResult(success=False, message="Failed to send email")
