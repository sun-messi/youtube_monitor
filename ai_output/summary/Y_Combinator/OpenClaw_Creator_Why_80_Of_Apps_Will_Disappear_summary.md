# OpenClaw Creator: Why 80% Of Apps Will Disappear

## 📹 视频信息

- **频道**: Y Combinator
- **发布日期**: 2026-02-07
- **时长**: 22:36
- **原始链接**: [https://www.youtube.com/watch?v=4uzGDAoNOZc](https://www.youtube.com/watch?v=4uzGDAoNOZc)

---

> 本文内容整理自 OpenClaw 创始人彼得·斯坦伯格（Peter Steinberger）与 YC 的拉斐尔·沙德（Raphael Schaad）在 Y Combinator 频道的访谈对话。

## TL;DR

OpenClaw 创始人详解为何本地运行的 AI Agent 将取代 80% 的 App——因为它能控制你的整台电脑，而非困在云端沙盒里。

---

## 📑 章节导航表

| 时间戳 | 章节标题 | 一句话概括 |
|--------|----------|-----------|
| 00:00-03:00 | OpenClaw 爆火与起源 | GitHub 16万星，社区衍生 Maltbook 等项目，机器人甚至雇佣人类完成现实任务 |
| 03:00-07:00 | 本地运行的核心优势 | 与云端 AI 的根本区别：能控制烤箱、Tesla、灯光、床温——"你的机器能做什么，它就能做什么" |
| 07:00-11:00 | Aha Moment：语音消息事件 | Agent 自主发现音频文件、用 curl 调 OpenAI API 转录，展现创造性问题解决能力 |
| 11:00-15:00 | 80% App 将消失 | 健身追踪、待办事项、数据管理类 App 都可被 Agent 替代，只有需要传感器的 App 存活 |
| 15:00-19:00 | 开发哲学：反 MCP、反 Claude Code | 用 Codex 而非 Claude Code 编码，跳过 MCP 协议用 CLI 替代，多仓库副本并行开发 |
| 19:00-22:36 | Soul.md 与 AI 人格 | 身份文件、灵魂文件定义 Agent 人格；记忆以 Markdown 本地存储，数据主权归用户 |

---

## 📊 核心论点

### 1. 本地运行 vs 云端运行：Agent 能力的根本分野

- **核心内容**：Peter 认为 OpenClaw 与所有前代 AI 助手的核心区别在于它运行在用户本地电脑上。云端 AI（如 ChatGPT）只能在沙盒中操作有限功能，而本地 Agent 可以控制鼠标、键盘，连接智能家居（烤箱、Tesla、Sonos、床温控制器）。"Your machine can do anything that you can do with the machine"——这句话定义了能力边界的根本差异。
- **关键概念**：本地优先架构、设备控制权、沙盒突破、全栈 Agent
- **实际意义**：云端 AI 公司面临被本地 Agent 釜底抽薪的风险；硬件厂商需要为 Agent 控制开放 API；隐私敏感场景（医疗、金融）将优先采用本地方案。

### 2. 80% App 将被 Agent 取代

- **核心内容**：Peter 直言大部分"数据管理类"App 将消失。以 MyFitnessPal 为例：Agent 知道你在 Smashburger，自动记录饮食，调整健身计划增加有氧——不需要专门的健身 App。待办事项 App 同理："I just tell it, hey, remind me of this"。只有需要硬件传感器的 App（如相机、GPS）可能存活。
- **关键概念**：App 消亡、数据管理自动化、传感器护城河、自然交互
- **实际意义**：SaaS 公司需重新思考产品形态——从独立 App 转向 Agent 可调用的服务；App Store 的商业模式面临结构性挑战。

### 3. 创造性问题解决：AI 编码能力溢出到现实

- **核心内容**：Peter 的 Aha Moment 来自一次意外：他在摩洛哥给 Agent 发语音消息，Agent 没有预置语音处理功能，但它自主分析文件头、用 ffmpeg 转换格式、通过 curl 调用 OpenAI Whisper API 完成转录——全程9秒。更聪明的是，它选择不安装本地 Whisper（需要下载模型太慢），而是走云端 API。Peter 的洞察："Coding is really creative problem solving that maps very well back into the real world."
- **关键概念**：涌现行为、创造性推理、工具链自组装、编码即通用问题解决
- **实际意义**：证明了足够好的代码模型本质上就是通用问题解决器；Agent 的能力边界不再取决于预置功能，而是取决于底层模型的推理能力。

### 4. 群体智能 vs 中心化超级智能

- **核心内容**：Raphael 指出一个有趣的趋势转变：所有人都在追求"中心化的上帝智能"，但 OpenClaw 过去两周展现的是"群体智能"——Bot 之间对话（Maltbook）、Bot 代表用户雇佣人类完成任务、专业化 Bot 分工（私人生活 Bot + 工作 Bot + 关系 Bot）。Peter 类比人类社会：一个人连觅食都困难，但作为群体可以造 iPhone、上太空。
- **关键概念**：群体智能、Bot-to-Bot 交互、Agent 专业化、社会化 AI
- **实际意义**：Agent 生态将从单一助手演化为多 Agent 协作网络；新的商业模式——"Agent 中介"可能出现。

### 5. 反主流开发哲学：No MCP, No Claude Code, No Git Branches

- **核心内容**：Peter 选择 Codex 而非 Claude Code（"I don't think I could have built the thing with Claude Code"），因为 Codex 在决策前会扫描更多文件。他完全跳过 MCP 协议，用自建的 makeporter 将 MCP 转换为 CLI——"Humans, no insane human tries to call an MCP manually"。他也不用 Git 分支或 work trees，而是同一仓库的多个副本都在 main 分支上，同时开10个 Codex 实例并行开发。
- **关键概念**：CLI 优先、反 MCP、并行编码、复杂度最小化、Codex vs Claude Code
- **实际意义**：挑战了当前 AI 编码工具的主流范式；证明简单工具链（CLI + 多副本）在高产出场景下可能优于精巧的 Git workflow。

### 6. 数据主权与记忆所有权

- **核心内容**：OpenClaw 的记忆存储为本地 Markdown 文件，用户完全拥有和控制。Peter 指出大模型公司试图通过记忆功能将用户锁定在各自的数据孤岛中——你无法把 ChatGPT 的记忆导出给另一个 AI。OpenClaw 的设计刻意打破这种锁定。Peter 坦言这些记忆文件"super sensible"——人们很快会把 Agent 用于非常私密的个人问题解决。
- **关键概念**：数据主权、记忆可移植性、Markdown 存储、隐私保护、数据孤岛打破
- **实际意义**：数据可移植性将成为 AI Agent 的核心竞争维度；用户对隐私的需求将推动本地优先方案；大模型公司的记忆锁定策略面临开源替代威胁。

---

## 🏢 提及的公司/产品

| 公司名 | 讨论语境 | 重要性 |
|--------|----------|--------|
| OpenClaw | 本期核心主角，开源本地 AI Agent，GitHub 16万星 | ⭐⭐⭐ |
| Anthropic (Claude Code) | Peter 明确表示不用 Claude Code 开发，偏好 Codex | ⭐⭐ |
| OpenAI (Codex/ChatGPT) | Peter 的主要开发工具，也是 Whisper API 提供者 | ⭐⭐⭐ |
| Y Combinator | 访谈频道，Equipment Share 等公司孵化器 | ⭐ |
| Maltbook | OpenClaw 社区衍生项目，Bot-to-Bot 对话平台 | ⭐⭐ |
| Tesla | 作为 Agent 可控制的智能设备示例 | ⭐ |
| WhatsApp | OpenClaw 最初的消息界面 | ⭐ |
| Discord | Peter 将 Agent 放入公开 Discord 展示功能 | ⭐ |

---

## 💬 经典金句

> "Your machine can do anything that you can do with the machine."
> — Raphael Schaad

> "Coding is really creative problem solving that maps very well back into the real world."
> — Peter Steinberger

> "I think 80% of them are going away. Why do I need My Fitness Pal? My agent already knows that I'm making bad decisions."
> — Peter Steinberger

> "Humans, no insane human tries to call an MCP manually. You just want to use CLIs."
> — Peter Steinberger

> "The one file that's not open source is my soul.md. So far nobody cracked that one file."
> — Peter Steinberger

---

## 👤 主要人物

### Peter Steinberger

**身份**：OpenClaw 创始人兼开发者
**背景**：连续创业者，曾退休后因 AI 热潮重返开发。擅长 iOS/macOS 开发，GitHub 活跃度极高（40+ 项目）。从奥地利远程开发，非硅谷出身。
**核心观点**：本地运行的 AI Agent 将取代 80% 的 App；MCP 协议不必要，CLI 才是正道；Codex 比 Claude Code 更适合大型项目开发；数据主权应归用户所有。

### Raphael Schaad

**身份**：Y Combinator 合伙人
**背景**：YC 内部负责与创业者对话的合伙人，对 AI Agent 趋势高度关注。
**核心观点**：群体智能正在取代中心化超级智能的叙事；模型公司可能被商品化，真正的价值在于记忆和 harness 层。

---

## 📺 视频类型

**访谈对话**
