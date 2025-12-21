#!/usr/bin/env python3
"""
批量审核所有 summary 文件
"""

import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.reviewer import review_content
from infrastructure.logger import setup_logger

logger = setup_logger("batch_review")


def batch_review_summaries(summary_dir: str, remove_garbage: bool = True):
    """
    批量审核所有 summary 文件

    Args:
        summary_dir: summary 目录路径
        remove_garbage: 是否删除 AI 废话
    """
    summary_path = Path(summary_dir)
    md_files = list(summary_path.rglob("*.md"))

    logger.info(f"找到 {len(md_files)} 个 Markdown 文件")

    reviewed_count = 0
    failed_count = 0

    for md_file in md_files:
        logger.info(f"审核: {md_file.name}")

        try:
            # 读取文件
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 审核
            reviewed = review_content(
                content,
                restructure=True,
                remove_garbage=remove_garbage,
                timeout=120
            )

            if reviewed and reviewed != content:
                # 写回文件
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(reviewed)
                logger.info(f"  ✓ 已更新: {md_file.name}")
                reviewed_count += 1
            else:
                logger.info(f"  - 无需更新: {md_file.name}")

        except Exception as e:
            logger.error(f"  ✗ 失败: {md_file.name} - {e}")
            failed_count += 1

    logger.info(f"\n审核完成: 更新 {reviewed_count} 个, 失败 {failed_count} 个")
    return reviewed_count, failed_count


if __name__ == "__main__":
    summary_dir = "./ai_output/summary"

    print("=" * 50)
    print("批量审核 Summary 文件")
    print("=" * 50)

    reviewed, failed = batch_review_summaries(summary_dir, remove_garbage=True)

    print(f"\n结果: 更新 {reviewed} 个, 失败 {failed} 个")
