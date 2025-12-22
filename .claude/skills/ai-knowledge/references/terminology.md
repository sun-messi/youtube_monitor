# AI 术语词典

> 按主题分类的 AI/ML 术语，包含英文原文、中文翻译和简要解释。

---

## 1. 模型基础

### 大模型类型
| 术语 | 中文 | 解释 |
|------|------|------|
| LLM (Large Language Model) | 大语言模型 | 基于海量文本训练的语言模型，如 GPT、Claude |
| Foundation Model | 基础模型 | 可适配多种下游任务的预训练大模型 |
| Frontier Model | 前沿模型 | 最先进的 AI 模型，通常指 GPT-4、Claude 3.5 级别 |
| SLM (Small Language Model) | 小语言模型 | 参数较少但高效的模型，如 Phi、Gemma |
| Open-weight Model | 开放权重模型 | 公开模型权重的模型，如 LLaMA、Mistral |
| Multimodal Model | 多模态模型 | 处理文本、图像、音频等多种输入的模型 |

### 架构相关
| 术语 | 中文 | 解释 |
|------|------|------|
| Transformer | Transformer | 2017 年提出的注意力架构，现代 LLM 基础 |
| Attention | 注意力机制 | 模型关注输入不同部分的机制 |
| Self-attention | 自注意力 | 序列内部元素相互关注 |
| Cross-attention | 交叉注意力 | 不同序列间的注意力 |
| Multi-head Attention | 多头注意力 | 并行多个注意力头 |
| Decoder-only | 仅解码器 | GPT 系列架构，自回归生成 |
| Encoder-decoder | 编码器-解码器 | T5、BART 架构 |
| MoE (Mixture of Experts) | 混合专家 | 多个专家网络，稀疏激活，如 Mixtral |
| Dense Model | 稠密模型 | 每次推理激活全部参数 |
| Sparse Model | 稀疏模型 | 每次推理只激活部分参数 |

### 位置编码
| 术语 | 中文 | 解释 |
|------|------|------|
| Positional Encoding | 位置编码 | 为序列添加位置信息 |
| RoPE (Rotary Position Embedding) | 旋转位置编码 | LLaMA 等使用，支持长上下文 |
| ALiBi | ALiBi 位置编码 | 线性偏置，无需训练即可外推 |

---

## 2. 训练相关

### 训练阶段
| 术语 | 中文 | 解释 |
|------|------|------|
| Pre-training | 预训练 | 在大规模语料上的初始训练 |
| Post-training | 后训练 | 预训练后的优化阶段（SFT + RLHF） |
| Fine-tuning | 微调 | 在特定任务数据上继续训练 |
| SFT (Supervised Fine-Tuning) | 监督微调 | 使用标注数据微调 |
| Instruction Tuning | 指令微调 | 使用指令-回复对训练 |
| Continual Pre-training | 持续预训练 | 在新数据上继续预训练 |

### 对齐技术
| 术语 | 中文 | 解释 |
|------|------|------|
| Alignment | 对齐 | 使模型行为符合人类意图 |
| RLHF (Reinforcement Learning from Human Feedback) | 基于人类反馈的强化学习 | 使用人类偏好训练 |
| DPO (Direct Preference Optimization) | 直接偏好优化 | 无需 RM 的对齐方法 |
| PPO (Proximal Policy Optimization) | 近端策略优化 | RLHF 常用的 RL 算法 |
| Reward Model | 奖励模型 | 评估回复质量的模型 |
| Constitutional AI | 宪法 AI | Anthropic 提出的自我改进方法 |
| RLAIF | 基于 AI 反馈的强化学习 | 用 AI 代替人类提供反馈 |

### 训练参数
| 术语 | 中文 | 解释 |
|------|------|------|
| Parameter | 参数 | 模型可学习的权重数量 |
| Weights | 权重 | 神经网络中的参数值 |
| Gradient | 梯度 | 损失函数对参数的导数 |
| Backpropagation | 反向传播 | 计算梯度的算法 |
| Loss Function | 损失函数 | 衡量预测与目标差距 |
| Optimizer | 优化器 | 更新参数的算法（Adam、SGD） |
| Learning Rate | 学习率 | 参数更新步长 |
| Batch Size | 批次大小 | 每次更新使用的样本数 |
| Epoch | 训练轮次 | 完整遍历数据集一次 |

### 正则化
| 术语 | 中文 | 解释 |
|------|------|------|
| Overfitting | 过拟合 | 模型在训练集表现好但泛化差 |
| Regularization | 正则化 | 防止过拟合的技术 |
| Dropout | Dropout | 训练时随机丢弃神经元 |
| Weight Decay | 权重衰减 | L2 正则化 |

---

## 3. 推理相关

### 基础概念
| 术语 | 中文 | 解释 |
|------|------|------|
| Inference | 推理 | 使用训练好的模型生成输出 |
| Autoregressive | 自回归 | 逐 token 生成，每个依赖前面 |
| Token | Token | 文本的基本单位（词或子词） |
| Tokenizer | 分词器 | 文本到 token 的转换器 |
| BPE (Byte Pair Encoding) | 字节对编码 | 常用分词算法 |
| Context Window | 上下文窗口 | 模型能处理的最大 token 数 |
| Context Length | 上下文长度 | 同上 |

### 生成策略
| 术语 | 中文 | 解释 |
|------|------|------|
| Temperature | 温度 | 控制生成随机性，越高越随机 |
| Top-p (Nucleus Sampling) | Top-p 采样 | 从概率累积达 p 的 token 中采样 |
| Top-k | Top-k 采样 | 从概率最高的 k 个 token 中采样 |
| Greedy Decoding | 贪婪解码 | 每步选概率最高的 token |
| Beam Search | 束搜索 | 保留多个候选序列 |
| Sampling | 采样 | 按概率分布随机选择 |

### 推理优化
| 术语 | 中文 | 解释 |
|------|------|------|
| KV Cache | KV 缓存 | 缓存注意力计算结果加速生成 |
| Flash Attention | Flash Attention | 内存高效的注意力实现 |
| Speculative Decoding | 推测解码 | 小模型草稿 + 大模型验证 |
| Continuous Batching | 连续批处理 | 动态组织推理请求 |
| Paged Attention | 分页注意力 | vLLM 的内存管理技术 |
| Latency | 延迟 | 单次请求响应时间 |
| Throughput | 吞吐量 | 单位时间处理的请求数 |
| TTFT (Time to First Token) | 首 token 时间 | 开始生成的等待时间 |
| TPS (Tokens per Second) | 每秒 token 数 | 生成速度 |

---

## 4. 模型优化

### 压缩技术
| 术语 | 中文 | 解释 |
|------|------|------|
| Quantization | 量化 | 降低权重精度（FP16→INT8/INT4） |
| Distillation | 蒸馏 | 用大模型教小模型 |
| Pruning | 剪枝 | 移除不重要的参数 |
| GPTQ | GPTQ | 流行的量化方法 |
| AWQ | AWQ | 激活感知量化 |
| GGUF | GGUF | llama.cpp 使用的量化格式 |

### 高效微调
| 术语 | 中文 | 解释 |
|------|------|------|
| LoRA (Low-Rank Adaptation) | 低秩适应 | 只训练低秩矩阵 |
| QLoRA | QLoRA | 量化 + LoRA |
| Adapter | 适配器 | 插入小型可训练模块 |
| PEFT (Parameter-Efficient Fine-Tuning) | 参数高效微调 | 只更新少量参数 |
| Prefix Tuning | 前缀微调 | 只训练前缀向量 |

---

## 5. 能力与应用

### 推理能力
| 术语 | 中文 | 解释 |
|------|------|------|
| Reasoning | 推理 | 逻辑思考和问题解决能力 |
| Chain-of-Thought (CoT) | 思维链 | 逐步推理的提示技术 |
| Tree-of-Thought | 思维树 | 探索多个推理路径 |
| Self-consistency | 自一致性 | 多次采样取多数答案 |
| Test-time Compute | 测试时计算 | 推理时增加计算提升性能 |
| Inference-time Scaling | 推理时扩展 | o1 的核心技术 |

### RAG 与检索
| 术语 | 中文 | 解释 |
|------|------|------|
| RAG (Retrieval-Augmented Generation) | 检索增强生成 | 结合检索和生成 |
| Embedding | 嵌入向量 | 文本的向量表示 |
| Vector Database | 向量数据库 | 存储和检索嵌入的数据库 |
| Semantic Search | 语义搜索 | 基于含义的搜索 |
| Chunking | 分块 | 将文档切分为小块 |
| Reranking | 重排序 | 对检索结果二次排序 |

### Agent 与工具
| 术语 | 中文 | 解释 |
|------|------|------|
| Agent / Agentic AI | 智能体 | 自主规划执行任务的 AI |
| Tool Use | 工具使用 | 模型调用外部工具 |
| Function Calling | 函数调用 | 结构化的工具调用格式 |
| Computer Use | 计算机使用 | AI 操作计算机界面 |
| MCP (Model Context Protocol) | 模型上下文协议 | Anthropic 的工具标准 |
| Planning | 规划 | 分解任务制定计划 |
| ReAct | ReAct | 推理 + 行动的框架 |

### 提示工程
| 术语 | 中文 | 解释 |
|------|------|------|
| Prompt | 提示 | 给模型的输入指令 |
| Prompt Engineering | 提示工程 | 设计有效提示的技术 |
| System Prompt | 系统提示 | 设定模型角色和行为 |
| In-context Learning | 上下文学习 | 从提示中的例子学习 |
| Few-shot | 少样本 | 提供少量示例 |
| Zero-shot | 零样本 | 不提供示例 |
| One-shot | 单样本 | 提供一个示例 |

---

## 6. 安全与评估

### 安全相关
| 术语 | 中文 | 解释 |
|------|------|------|
| Safety | 安全 | 防止有害输出 |
| Hallucination | 幻觉 | 模型生成虚假信息 |
| Jailbreak | 越狱 | 绕过安全限制的攻击 |
| Red Teaming | 红队测试 | 主动寻找模型漏洞 |
| Guardrails | 护栏 | 输入输出过滤机制 |
| Content Moderation | 内容审核 | 过滤有害内容 |
| Responsible AI | 负责任 AI | AI 伦理和治理 |

### 评估相关
| 术语 | 中文 | 解释 |
|------|------|------|
| Benchmark | 基准测试 | 标准化评估数据集 |
| MMLU | MMLU | 多任务语言理解测试 |
| HumanEval | HumanEval | 代码生成评估 |
| GSM8K | GSM8K | 小学数学问题 |
| MATH | MATH | 竞赛级数学 |
| Perplexity | 困惑度 | 语言模型质量指标 |
| BLEU | BLEU | 翻译质量指标 |
| ROUGE | ROUGE | 摘要质量指标 |
| Win Rate | 胜率 | 模型对比的偏好比例 |
| Elo Rating | Elo 评分 | 类似棋类的排名系统 |

---

## 7. 基础设施

### 硬件
| 术语 | 中文 | 解释 |
|------|------|------|
| GPU | GPU | 图形处理器，AI 训练主力 |
| TPU | TPU | Google 的 AI 专用芯片 |
| NVIDIA H100 | H100 | 当前最强 AI GPU |
| NVIDIA B200 | B200 | 下一代 Blackwell GPU |
| HBM (High Bandwidth Memory) | 高带宽内存 | GPU 使用的高速内存 |
| NVLink | NVLink | GPU 间高速互连 |
| InfiniBand | InfiniBand | 数据中心高速网络 |

### 训练框架
| 术语 | 中文 | 解释 |
|------|------|------|
| PyTorch | PyTorch | 主流深度学习框架 |
| JAX | JAX | Google 的高性能框架 |
| DeepSpeed | DeepSpeed | 微软分布式训练库 |
| Megatron | Megatron | NVIDIA 大模型训练框架 |
| FSDP | FSDP | PyTorch 分布式训练 |

### 推理框架
| 术语 | 中文 | 解释 |
|------|------|------|
| vLLM | vLLM | 高效 LLM 推理引擎 |
| TensorRT-LLM | TensorRT-LLM | NVIDIA 推理优化 |
| llama.cpp | llama.cpp | CPU 推理框架 |
| Ollama | Ollama | 本地模型运行工具 |
| ONNX | ONNX | 模型交换格式 |

### 计算指标
| 术语 | 中文 | 解释 |
|------|------|------|
| FLOPS | 浮点运算次数 | 计算量单位 |
| FP32 / FP16 / BF16 | 浮点精度 | 32/16 位浮点数 |
| INT8 / INT4 | 整数精度 | 量化后的精度 |
| GPU Hours | GPU 小时 | 训练成本单位 |
| Compute | 算力 | 计算资源 |

---

## 8. 新兴概念 (2024-2025)

| 术语 | 中文 | 解释 |
|------|------|------|
| o1 / o3 | o1 / o3 | OpenAI 推理模型系列 |
| Inference-time Scaling | 推理时扩展 | 增加推理计算提升能力 |
| World Model | 世界模型 | 理解物理世界的模型 |
| Video Generation | 视频生成 | Sora、Runway 等 |
| AI Agents | AI 智能体 | 2024 年热门方向 |
| Synthetic Data | 合成数据 | AI 生成的训练数据 |
| Long Context | 长上下文 | 100K+ token 窗口 |
| Multimodal Reasoning | 多模态推理 | 跨模态的推理能力 |
| AI Coding | AI 编程 | Cursor、Copilot 等 |
| Model Collapse | 模型坍缩 | 用 AI 数据训练导致退化 |
