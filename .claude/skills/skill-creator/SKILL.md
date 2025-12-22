---
name: skill-creator
description: 创建新的 Claude Code skill。运行 /skill-creator 后按提示输入 skill 名称和路径。
---

# Skill Creator

用于创建新的 Claude Code skill 的工具。

## 使用方法

当用户想创建新 skill 时：

1. 询问 skill 名称（使用 hyphen-case，如 `my-new-skill`）
2. 询问保存路径（默认 `.claude/skills`）
3. 运行 `init_skill.py` 脚本创建模板

## 创建流程

```bash
python .claude/skills/skill-creator/scripts/init_skill.py <skill-name> --path <path>
```

## Skill 目录结构

创建的 skill 包含：

- `SKILL.md` - 主文档（必需），包含 YAML frontmatter
- `scripts/` - 可执行脚本目录
- `references/` - 参考文档目录
- `assets/` - 资源文件目录

## 验证 Skill

```bash
python .claude/skills/skill-creator/scripts/quick_validate.py <skill-directory>
```

## 打包 Skill

```bash
python .claude/skills/skill-creator/scripts/package_skill.py <skill-directory> [--output <dir>]
```

## SKILL.md 编写规范

1. 必须包含 YAML frontmatter（`---` 包裹）
2. 必需字段：`name`（hyphen-case）、`description`（简短描述）
3. 使用祈使语气编写指令
4. 保持简洁，详细内容放到 references 目录
