#!/usr/bin/env python3
"""
发送 Summary 邮件通知
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from infrastructure.notifier import send_update_email
from infrastructure.logger import setup_logger

logger = setup_logger("send_email")


def collect_summary_files(summary_dir: str):
    """收集所有 summary 文件信息"""
    summary_path = Path(summary_dir)
    md_files = list(summary_path.rglob("*.md"))

    video_infos = []
    for md_file in md_files:
        # 提取频道名和标题
        channel = md_file.parent.name
        title = md_file.stem.replace("_translate", "").replace("_", " ")

        video_infos.append({
            "file_path": str(md_file),
            "channel": channel,
            "title": title
        })

    return video_infos


if __name__ == "__main__":
    summary_dir = "./ai_output/summary"

    print("=" * 50)
    print("发送 Summary 邮件通知")
    print("=" * 50)

    video_infos = collect_summary_files(summary_dir)
    print(f"找到 {len(video_infos)} 个翻译文件")

    if video_infos:
        success = send_update_email(video_infos)
        if success:
            print("✅ 邮件发送成功！")
        else:
            print("❌ 邮件发送失败")
    else:
        print("没有文件需要发送")
