# AI 模型架构详解

> 主流 AI 模型的架构设计、核心组件和技术细节。

---

## 1. Transformer 架构

### 核心思想
2017 年 Google 提出，用**纯注意力机制**替代 RNN/CNN，成为现代 AI 的基石。

### 原始架构 (Encoder-Decoder)
```
输入序列 → [Encoder] → 隐藏表示 → [Decoder] → 输出序列

Encoder (N 层):
  └─ Multi-Head Self-Attention
  └─ Feed-Forward Network
  └─ Layer Normalization
  └─ Residual Connection

Decoder (N 层):
  └─ Masked Multi-Head Self-Attention
  └─ Cross-Attention (连接 Encoder)
  └─ Feed-Forward Network
```

### 关键组件

#### Self-Attention
```
Attention(Q, K, V) = softmax(QK^T / √d_k) · V

- Q (Query): 查询向量
- K (Key): 键向量
- V (Value): 值向量
- d_k: 键的维度（缩放因子）
```

**直观理解**: 每个 token 可以"看到"序列中所有其他 token，根据相关性加权聚合信息。

#### Multi-Head Attention
```
MultiHead(Q, K, V) = Concat(head_1, ..., head_h) · W^O

每个 head 学习不同的注意力模式：
- 语法关系
- 语义关系
- 位置关系
```

#### Position Encoding
由于 Attention 本身无位置信息，需要额外编码：
- **Sinusoidal**: 原始论文，正弦/余弦函数
- **Learned**: 可学习的位置嵌入
- **RoPE**: 旋转位置编码（LLaMA）
- **ALiBi**: 线性偏置（无需训练）

#### Feed-Forward Network (FFN)
```
FFN(x) = GELU(xW_1 + b_1)W_2 + b_2

- 通常 d_ff = 4 × d_model
- 每个位置独立计算
```

#### Layer Normalization
```
LayerNorm(x) = (x - μ) / σ · γ + β

- Pre-Norm: LayerNorm 在注意力之前（GPT-2+）
- Post-Norm: LayerNorm 在注意力之后（原始）
```

---

## 2. Decoder-Only 架构 (GPT 系列)

### 核心特点
- 只有 Decoder，无 Encoder
- **自回归生成**: 逐 token 预测下一个
- **Causal Masking**: 只能看到之前的 token

### 架构
```
输入 tokens → Embedding + Position → [Decoder Blocks × N] → LM Head → 概率分布

Decoder Block:
  └─ LayerNorm
  └─ Causal Self-Attention
  └─ LayerNorm
  └─ Feed-Forward (MLP)
  └─ Residual Connections
```

### 典型参数 (GPT-3 175B)
| 组件 | 数值 |
|------|------|
| 层数 (N) | 96 |
| 隐藏维度 (d_model) | 12288 |
| 注意力头数 (h) | 96 |
| FFN 维度 (d_ff) | 49152 |
| 上下文长度 | 2048 |
| 参数量 | 175B |

### 代表模型
- **GPT 系列**: GPT-2, GPT-3, GPT-4
- **Claude 系列**: Constitutional AI 训练
- **LLaMA 系列**: 开源高效
- **Mistral 系列**: 滑动窗口注意力

---

## 3. Mixture of Experts (MoE)

### 核心思想
用多个"专家"网络替代单一 FFN，每次只激活部分专家，实现**稀疏计算**。

### 架构
```
输入 → Router → 选择 Top-K 专家 → 专家计算 → 加权合并

MoE Layer:
  └─ Router Network (线性层)
  └─ Expert Networks (N 个 FFN)
  └─ Top-K Gating
```

### 关键技术

#### Router (门控机制)
```
Gate(x) = softmax(x · W_g)
选择 Top-K 个得分最高的专家
```

#### Load Balancing
防止所有 token 都选择同一专家：
- **Auxiliary Loss**: 鼓励均匀分布
- **Expert Capacity**: 限制每个专家的容量

### 典型配置 (Mixtral 8x7B)
| 配置 | 数值 |
|------|------|
| 专家数量 | 8 |
| 每次激活 | 2 |
| 单专家参数 | 7B |
| 总参数 | 47B |
| 激活参数 | ~13B |

### 优势
- **计算效率**: 激活参数远少于总参数
- **容量增加**: 总参数多，知识存储大
- **推理成本**: 与小模型相当

### 代表模型
- **Mixtral 8x7B / 8x22B**: Mistral AI
- **Switch Transformer**: Google
- **GPT-4** (传闻): MoE 架构

---

## 4. 注意力优化

### Flash Attention
**问题**: 标准 Attention 需要 O(N²) 内存存储注意力矩阵

**解决**: IO-aware 算法，分块计算，避免存储完整矩阵

```
标准 Attention:
  1. 计算 QK^T (N×N 矩阵)
  2. 存储到 HBM
  3. 计算 softmax
  4. 乘以 V

Flash Attention:
  1. 分块加载 Q, K, V 到 SRAM
  2. 在 SRAM 中计算
  3. 增量更新结果
  4. 避免完整 N×N 矩阵
```

**收益**:
- 内存: O(N²) → O(N)
- 速度: 2-4x 加速
- 支持更长上下文

### Grouped Query Attention (GQA)
**问题**: Multi-Head Attention 的 KV Cache 太大

**解决**: 多个 Q 头共享 K/V 头

```
MHA: heads = 32, KV heads = 32
GQA: heads = 32, KV heads = 8 (4 个 Q 共享 1 个 KV)
MQA: heads = 32, KV heads = 1 (所有 Q 共享 1 个 KV)
```

**代表**: LLaMA 2/3, Mistral

### Sliding Window Attention
**问题**: 全局注意力计算量大

**解决**: 每个 token 只关注局部窗口

```
窗口大小 W = 4096
Token i 只关注 [i-W, i] 范围
```

**代表**: Mistral, Longformer

---

## 5. 位置编码

### Rotary Position Embedding (RoPE)
```
将位置信息编码为旋转矩阵：
q_m · k_n^T 包含相对位置 (m-n) 信息

优势:
- 相对位置建模
- 外推性好
- 长度泛化能力
```

**使用**: LLaMA, Mistral, Qwen

### ALiBi (Attention with Linear Biases)
```
注意力分数 = QK^T - m × |i-j|

距离越远，惩罚越大
无需训练，直接外推
```

**使用**: MPT, BLOOM

---

## 6. 长上下文技术

### 挑战
- 注意力复杂度 O(N²)
- KV Cache 内存增长
- 位置编码外推

### 解决方案

#### RoPE 外推
```
原始 RoPE: 训练 4K, 推理 4K
NTK-aware RoPE: 训练 4K, 推理 32K
YaRN: 更好的长度泛化
```

#### 位置插值
```
将长序列的位置映射到训练范围内
训练 4K → 线性插值 → 推理 32K
```

### 典型长度
| 模型 | 上下文长度 |
|------|-----------|
| GPT-3 | 4K |
| GPT-4 | 8K / 128K |
| Claude 3 | 200K |
| Gemini 1.5 | 1M |
| LLaMA 3 | 8K (→ 128K) |

---

## 7. 推理优化

### KV Cache
**问题**: 自回归生成时重复计算

**解决**: 缓存已生成 token 的 K/V

```
生成 token N+1 时:
- 只计算新 token 的 Q, K, V
- 拼接历史 KV Cache
- 计算注意力
```

**内存占用**:
```
KV Cache = 2 × num_layers × seq_len × hidden_dim × precision
128K 上下文 + 70B 模型 + FP16 ≈ 100GB
```

### Speculative Decoding
```
1. 小模型 (Draft) 快速生成 N 个 token
2. 大模型 (Target) 并行验证
3. 接受正确的，拒绝错误的
4. 从错误处继续
```

**加速**: 2-3x (取决于接受率)

### Continuous Batching
```
传统: 固定 batch，等最长请求完成
连续: 动态加入/移除请求

优势: 提高 GPU 利用率 10-20x
```

---

## 8. 模型对比

| 模型 | 架构 | 参数 | 上下文 | 特点 |
|------|------|------|--------|------|
| GPT-4 | Decoder + MoE? | ~1.8T? | 128K | 闭源最强 |
| Claude 3.5 Sonnet | Decoder | ~100B? | 200K | 高性价比 |
| LLaMA 3 405B | Decoder | 405B | 128K | 开源最强 |
| Mixtral 8x22B | MoE | 141B/39B | 64K | 开源 MoE |
| Gemini 1.5 Pro | Decoder | ? | 1M | 超长上下文 |
| Mistral Large | Decoder | 123B | 128K | 欧洲最强 |

---

## 9. 多模态架构

### 视觉编码器 + LLM
```
图像 → Vision Encoder (ViT/CLIP) → Projection → LLM

代表: LLaVA, GPT-4V
```

### 原生多模态
```
图像 patch + 文本 token 统一处理
共享 Transformer

代表: Gemini, Chameleon
```

### 视频模型
```
视频 → 帧采样 → 视觉编码 → 时序建模 → LLM

代表: GPT-4V (视频), Gemini 2.0
```
