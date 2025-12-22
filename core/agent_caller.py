"""
Agent 调用模块 - 通过 Claude CLI 调用专业 Agent

使用方式:
    from core.agent_caller import call_agent

    response = call_agent(
        agent_name="tech-investment-analyst",
        prompt="分析这段视频内容"
    )
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 项目根目录（确保能找到 .claude/agents/）
PROJECT_ROOT = Path(__file__).parent.parent


def get_claude_cli_path() -> Path:
    """
    获取最新的 Claude CLI 路径

    Returns:
        Path to Claude CLI binary

    Raises:
        FileNotFoundError: 如果找不到 Claude CLI
    """
    extensions_dir = Path.home() / ".vscode-server/extensions"

    if not extensions_dir.exists():
        raise FileNotFoundError("VSCode extensions directory not found")

    # 查找所有 claude-code 扩展，选择最新版本
    claude_extensions = sorted([
        d for d in extensions_dir.iterdir()
        if d.name.startswith("anthropic.claude-code-")
    ])

    if claude_extensions:
        cli_path = claude_extensions[-1] / "resources/native-binary/claude"
        if cli_path.exists():
            return cli_path

    raise FileNotFoundError("Claude CLI not found in VSCode extensions")


def call_agent(
    agent_name: str,
    prompt: str,
    timeout: int = 600,
    output_format: str = "text",
    cwd: Optional[Path] = None
) -> str:
    """
    调用 Claude Agent

    Agent 会自动加载其配置的 skills (在 .claude/agents/*.md 中定义)

    Args:
        agent_name: Agent 名称 (如 "tech-investment-analyst")
        prompt: 任务 prompt
        timeout: 超时秒数 (默认 10 分钟)
        output_format: 输出格式 "text" 或 "json"
        cwd: 工作目录 (默认使用项目根目录)

    Returns:
        Agent 输出内容

    Example:
        >>> response = call_agent(
        ...     "tech-investment-analyst",
        ...     "解释什么是 ARR 和 RLHF"
        ... )
        >>> print(response)
    """
    try:
        cli_path = get_claude_cli_path()
    except FileNotFoundError as e:
        logger.error(f"Claude CLI not found: {e}")
        return ""

    cmd = [
        str(cli_path),
        "-p",
        "--agent", agent_name,
        "--output-format", output_format,
        prompt
    ]

    work_dir = cwd or PROJECT_ROOT

    logger.info(f"Calling agent '{agent_name}' from {work_dir}")
    logger.debug(f"Command: {' '.join(cmd[:5])}...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=work_dir
        )

        if result.returncode != 0:
            logger.error(f"Agent '{agent_name}' error (code {result.returncode}): {result.stderr}")
            return ""

        output = result.stdout.strip()
        logger.info(f"Agent '{agent_name}' returned {len(output)} characters")
        return output

    except subprocess.TimeoutExpired:
        logger.error(f"Agent '{agent_name}' timeout after {timeout}s")
        return ""
    except Exception as e:
        logger.error(f"Agent '{agent_name}' call failed: {e}")
        return ""


def call_agent_with_file(
    agent_name: str,
    prompt_file: Path,
    input_content: str,
    timeout: int = 600
) -> str:
    """
    使用 prompt 模板文件调用 Agent

    Args:
        agent_name: Agent 名称
        prompt_file: Prompt 模板文件路径
        input_content: 要替换 $ARGUMENTS 的内容
        timeout: 超时秒数

    Returns:
        Agent 输出内容
    """
    if not prompt_file.exists():
        logger.error(f"Prompt file not found: {prompt_file}")
        return ""

    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_template = f.read()

    # 替换占位符
    if "$ARGUMENTS" in prompt_template:
        full_prompt = prompt_template.replace("$ARGUMENTS", input_content)
    else:
        full_prompt = f"{prompt_template}\n\n---\n\n{input_content}"

    return call_agent(agent_name, full_prompt, timeout)


# 预定义的 Agent 名称常量
AGENT_TECH_INVESTMENT = "tech-investment-analyst"


if __name__ == "__main__":
    # 简单测试
    import sys

    logging.basicConfig(level=logging.INFO)

    test_prompt = sys.argv[1] if len(sys.argv) > 1 else "解释什么是 ARR"

    print(f"Testing agent call with prompt: {test_prompt}")
    print("-" * 50)

    response = call_agent(AGENT_TECH_INVESTMENT, test_prompt, timeout=120)

    if response:
        print(response)
    else:
        print("Error: No response from agent")
