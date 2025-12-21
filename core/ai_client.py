"""
AI CLI client helpers (Claude/OpenAI).
"""

from __future__ import annotations

import json
import logging
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_OPENAI_ARGS = ["responses", "create", "-m", "{model}", "-i", "-"]


def get_claude_cli_path() -> Path:
    """
    Find the latest Claude CLI binary from VSCode extensions.

    Returns:
        Path to the Claude CLI binary
    """
    extensions_dir = Path.home() / ".vscode-server/extensions"

    if not extensions_dir.exists():
        # Fallback if extensions directory doesn't exist
        return Path.home() / ".vscode-server/extensions/anthropic.claude-code-2.0.72-linux-x64/resources/native-binary/claude"

    # Find all claude-code extensions and get the latest one
    try:
        claude_extensions = sorted(
            [d for d in extensions_dir.iterdir() if d.name.startswith("anthropic.claude-code-")]
        )
        if claude_extensions:
            latest = claude_extensions[-1]  # Get the last (newest) version
            return latest / "resources/native-binary/claude"
    except Exception:
        pass  # If any error occurs, fall back to known version

    # Fallback to known version
    return Path.home() / ".vscode-server/extensions/anthropic.claude-code-2.0.72-linux-x64/resources/native-binary/claude"


def _normalize_provider(provider: Optional[str]) -> str:
    if not provider:
        return "claude"
    provider = provider.strip().lower()
    if provider in ("openai", "chatgpt"):
        return "openai"
    if provider == "claude":
        return "claude"
    return provider


def get_ai_provider(config: Any) -> str:
    provider = _normalize_provider(getattr(config, "ai_provider", None) if config else None)
    if provider not in ("claude", "openai"):
        logger.warning("Unknown ai_provider '%s', falling back to 'claude'", provider)
        return "claude"
    return provider


def get_ai_model(config: Any, provider: Optional[str] = None) -> Optional[str]:
    provider = provider or get_ai_provider(config)
    if not config:
        return None
    if provider == "openai":
        return getattr(config, "openai_model", None) or getattr(config, "ai_model", None)
    return getattr(config, "claude_model", None)


def get_ai_timeout(
    config: Any,
    provider: Optional[str] = None,
    override: Optional[int] = None
) -> int:
    if override is not None:
        return override
    provider = provider or get_ai_provider(config)
    if provider == "openai":
        return (
            getattr(config, "openai_timeout_seconds", None)
            or getattr(config, "claude_timeout_seconds", None)
            or 300
        )
    return getattr(config, "claude_timeout_seconds", None) or 300


def get_review_model(config: Any, provider: Optional[str] = None) -> Optional[str]:
    if config:
        review_model = getattr(config, "review_model", None)
        if review_model:
            return review_model
    provider = provider or get_ai_provider(config)
    if provider == "claude":
        return "claude-3-5-haiku-latest"
    return get_ai_model(config, provider=provider)


def get_claude_cli_command(config: Any) -> str:
    override = getattr(config, "claude_cli_command", None) if config else None
    if override:
        return override
    return str(get_claude_cli_path())


def _get_openai_cli_command(config: Any) -> str:
    return getattr(config, "openai_cli_command", None) if config else None or "openai"


def _get_openai_cli_args(config: Any) -> List[str]:
    if not config:
        return DEFAULT_OPENAI_ARGS.copy()
    args = getattr(config, "openai_cli_args", None)
    if isinstance(args, list):
        return [str(a) for a in args]
    if isinstance(args, str) and args.strip():
        return shlex.split(args)
    return DEFAULT_OPENAI_ARGS.copy()


def _substitute_args(
    args: List[str],
    prompt: str,
    model: Optional[str],
    include_prompt: bool
) -> List[str]:
    output: List[str] = []
    i = 0

    while i < len(args):
        arg = args[i]
        next_arg = args[i + 1] if i + 1 < len(args) else None

        if next_arg == "{model}" and not model:
            i += 2
            continue
        if next_arg == "{prompt}" and not include_prompt:
            i += 2
            continue

        if arg == "{model}":
            if model:
                output.append(model)
            i += 1
            continue
        if arg == "{prompt}":
            if include_prompt:
                output.append(prompt)
            i += 1
            continue

        if "{model}" in arg:
            if model:
                output.append(arg.replace("{model}", model))
            i += 1
            continue

        if "{prompt}" in arg:
            if include_prompt:
                output.append(arg.replace("{prompt}", prompt))
            i += 1
            continue

        output.append(arg)
        i += 1

    return output


def _extract_json_path(payload: Any, path: str) -> Any:
    current = payload
    for part in path.split("."):
        if not part:
            continue
        while part:
            match = re.match(r"([^\[]+)?(?:\[(\d+)\])?(.*)", part)
            if not match:
                current = current[part]
                break
            key, index, rest = match.groups()
            if key:
                current = current[key]
            if index is not None:
                current = current[int(index)]
            part = rest
    return current


def run_ai_prompt(
    prompt: str,
    config: Any,
    timeout: Optional[int] = None,
    model: Optional[str] = None,
    purpose: str = "default"
) -> str:
    provider = get_ai_provider(config)
    if model is None:
        model = get_review_model(config, provider) if purpose == "review" else get_ai_model(config, provider)
    timeout = get_ai_timeout(config, provider, override=timeout)

    if provider == "openai":
        return _run_openai_prompt(prompt, timeout, model, config)
    return _run_claude_prompt(prompt, timeout, model, config)


def _run_claude_prompt(
    prompt: str,
    timeout: int,
    model: Optional[str],
    config: Any
) -> str:
    use_stdin = bool(getattr(config, "claude_cli_use_stdin", False)) if config else False
    cmd = [get_claude_cli_command(config), "--output-format", "text"]

    if model:
        cmd.extend(["--model", model])

    if use_stdin:
        input_text = prompt
    else:
        cmd.extend(["-p", prompt])
        input_text = None

    try:
        result = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode != 0:
            logger.error("AI CLI error (claude): %s", result.stderr)
            return ""
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        logger.error("AI CLI timeout after %ss (claude)", timeout)
        return ""
    except FileNotFoundError:
        logger.error("Claude CLI not found. Make sure 'claude' is installed and in PATH.")
        return ""
    except Exception as exc:
        logger.error("AI CLI error (claude): %s", exc)
        return ""


def _run_openai_prompt(
    prompt: str,
    timeout: int,
    model: Optional[str],
    config: Any
) -> str:
    use_stdin = bool(getattr(config, "openai_cli_use_stdin", True)) if config else True
    args = _get_openai_cli_args(config)
    args = _substitute_args(args, prompt, model, include_prompt=not use_stdin)
    cmd = [_get_openai_cli_command(config)] + args
    input_text = prompt if use_stdin else None
    json_path = getattr(config, "openai_cli_output_json_path", None) if config else None

    try:
        result = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode != 0:
            logger.error("AI CLI error (openai): %s", result.stderr)
            return ""

        output = result.stdout.strip()
        if json_path:
            try:
                payload = json.loads(output)
                extracted = _extract_json_path(payload, json_path)
                if isinstance(extracted, str):
                    return extracted.strip()
                return json.dumps(extracted, ensure_ascii=False).strip()
            except Exception as exc:
                logger.error("OpenAI CLI JSON parse error: %s", exc)
                return ""

        return output
    except subprocess.TimeoutExpired:
        logger.error("AI CLI timeout after %ss (openai)", timeout)
        return ""
    except FileNotFoundError:
        logger.error("OpenAI CLI not found. Make sure the command is installed and in PATH.")
        return ""
    except Exception as exc:
        logger.error("AI CLI error (openai): %s", exc)
        return ""
