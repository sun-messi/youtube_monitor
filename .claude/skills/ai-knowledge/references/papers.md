# AI 经典论文与里程碑

> 按时间线整理的 AI/ML 领域重要论文和技术突破。

---

## 深度学习基础 (2012-2016)

### AlexNet (2012)
- **论文**: "ImageNet Classification with Deep Convolutional Neural Networks"
- **作者**: Alex Krizhevsky, Ilya Sutskever, Geoffrey Hinton
- **意义**: 开启深度学习革命，CNN 在 ImageNet 上大幅领先
- **关键技术**: ReLU, Dropout, GPU 训练

### Seq2Seq (2014)
- **论文**: "Sequence to Sequence Learning with Neural Networks"
- **作者**: Ilya Sutskever, Oriol Vinyals, Quoc V. Le (Google)
- **意义**: 奠定机器翻译和序列生成基础
- **关键技术**: Encoder-Decoder 架构

### Attention 机制 (2014-2015)
- **论文**: "Neural Machine Translation by Jointly Learning to Align and Translate"
- **作者**: Dzmitry Bahdanau, Kyunghyun Cho, Yoshua Bengio
- **意义**: 引入注意力机制，解决长序列问题
- **关键技术**: Attention, Alignment

### ResNet (2015)
- **论文**: "Deep Residual Learning for Image Recognition"
- **作者**: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun (Microsoft)
- **意义**: 残差连接解决深层网络训练问题
- **关键技术**: Skip Connection, 152 层网络

### Batch Normalization (2015)
- **论文**: "Batch Normalization: Accelerating Deep Network Training"
- **作者**: Sergey Ioffe, Christian Szegedy (Google)
- **意义**: 加速训练，成为标准组件

---

## Transformer 时代 (2017-2019)

### Attention Is All You Need (2017) ⭐
- **论文**: "Attention Is All You Need"
- **作者**: Vaswani et al. (Google Brain)
- **意义**: **现代 AI 最重要的论文**，Transformer 架构
- **关键技术**: Self-attention, Multi-head Attention, Positional Encoding
- **影响**: GPT, BERT, LLaMA 等所有主流模型的基础

### BERT (2018)
- **论文**: "BERT: Pre-training of Deep Bidirectional Transformers"
- **作者**: Jacob Devlin et al. (Google)
- **意义**: 双向预训练，NLU 里程碑
- **关键技术**: Masked Language Model, Next Sentence Prediction

### GPT (2018)
- **论文**: "Improving Language Understanding by Generative Pre-Training"
- **作者**: Alec Radford et al. (OpenAI)
- **意义**: 生成式预训练的开端
- **关键技术**: Decoder-only Transformer, 自回归生成

### GPT-2 (2019)
- **论文**: "Language Models are Unsupervised Multitask Learners"
- **作者**: OpenAI
- **意义**: 证明规模化的威力，零样本能力
- **关键技术**: 1.5B 参数，多任务学习

### T5 (2019)
- **论文**: "Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer"
- **作者**: Google
- **意义**: 统一的 Text-to-Text 框架
- **关键技术**: Encoder-Decoder, 多任务预训练

---

## 大模型爆发 (2020-2022)

### GPT-3 (2020) ⭐
- **论文**: "Language Models are Few-Shot Learners"
- **作者**: OpenAI
- **意义**: **开启大模型时代**，展示涌现能力
- **关键技术**: 175B 参数，In-context Learning, Few-shot
- **影响**: 证明规模定律，催生 ChatGPT

### Scaling Laws (2020) ⭐
- **论文**: "Scaling Laws for Neural Language Models"
- **作者**: Jared Kaplan et al. (OpenAI)
- **意义**: **理论基础**，模型规模与性能的幂律关系
- **关键发现**: 参数量、数据量、计算量的最优配比

### CLIP (2021)
- **论文**: "Learning Transferable Visual Models From Natural Language Supervision"
- **作者**: OpenAI
- **意义**: 多模态的突破，图文对齐
- **关键技术**: 对比学习, 4 亿图文对

### Codex (2021)
- **论文**: "Evaluating Large Language Models Trained on Code"
- **作者**: OpenAI
- **意义**: AI 编程的起点，GitHub Copilot 基础
- **关键技术**: 代码预训练, HumanEval 评估

### InstructGPT (2022) ⭐
- **论文**: "Training language models to follow instructions with human feedback"
- **作者**: OpenAI
- **意义**: **RLHF 里程碑**，ChatGPT 的技术基础
- **关键技术**: SFT + Reward Model + PPO

### Chinchilla (2022)
- **论文**: "Training Compute-Optimal Large Language Models"
- **作者**: DeepMind
- **意义**: 修正 Scaling Laws，强调数据量
- **关键发现**: 参数量和数据量应等比例增长

### Chain-of-Thought (2022) ⭐
- **论文**: "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"
- **作者**: Jason Wei et al. (Google)
- **意义**: **推理能力突破**，简单有效的提示技术
- **关键技术**: 逐步推理, "Let's think step by step"

### Constitutional AI (2022)
- **论文**: "Constitutional AI: Harmlessness from AI Feedback"
- **作者**: Anthropic
- **意义**: 自我改进的对齐方法
- **关键技术**: AI 自我批评和修正

---

## 多模态与推理 (2023-2024)

### GPT-4 (2023) ⭐
- **论文**: "GPT-4 Technical Report"
- **作者**: OpenAI
- **意义**: **多模态前沿模型**，接近人类水平
- **关键技术**: 大规模 RLHF, 多模态理解

### LLaMA (2023) ⭐
- **论文**: "LLaMA: Open and Efficient Foundation Language Models"
- **作者**: Meta
- **意义**: **开源模型里程碑**，开启开源生态
- **关键技术**: 高效训练，RoPE, SwiGLU

### Flash Attention (2022-2023)
- **论文**: "FlashAttention: Fast and Memory-Efficient Exact Attention"
- **作者**: Tri Dao et al. (Stanford)
- **意义**: 推理优化的核心技术
- **关键技术**: IO-aware 算法，2-4x 加速

### LoRA (2021, 广泛应用于 2023)
- **论文**: "LoRA: Low-Rank Adaptation of Large Language Models"
- **作者**: Edward J. Hu et al. (Microsoft)
- **意义**: 高效微调的标准方法
- **关键技术**: 低秩分解，0.1% 参数

### Mixtral (2023)
- **论文**: "Mixtral of Experts"
- **作者**: Mistral AI
- **意义**: MoE 架构的成功应用
- **关键技术**: 8x7B 专家，稀疏激活

### DPO (2023)
- **论文**: "Direct Preference Optimization: Your Language Model is Secretly a Reward Model"
- **作者**: Stanford
- **意义**: 简化 RLHF 流程
- **关键技术**: 无需单独训练 Reward Model

### Gemini (2023)
- **论文**: "Gemini: A Family of Highly Capable Multimodal Models"
- **作者**: Google DeepMind
- **意义**: 原生多模态，与 GPT-4 竞争
- **关键技术**: 多模态预训练

---

## 推理革命 (2024-2025)

### Claude 3 (2024)
- **作者**: Anthropic
- **意义**: Opus 达到 GPT-4 级别，Sonnet 高性价比
- **关键技术**: 200K 上下文，Constitutional AI

### o1 (2024) ⭐
- **作者**: OpenAI
- **意义**: **推理能力飞跃**，测试时计算扩展
- **关键技术**: Chain-of-Thought 内置, 思考 token, GRPO 训练
- **影响**: 开启 Inference-time Scaling 时代
- **训练方法**: 使用 GRPO（Group Relative Policy Optimization）替代传统 PPO，无需价值函数，特别适合可验证奖励任务（如数学、代码）

### Llama 3 (2024)
- **作者**: Meta
- **意义**: 开源追赶闭源
- **关键技术**: 405B 参数，15T tokens

### Gemini 2.0 (2024)
- **作者**: Google DeepMind
- **意义**: 原生多模态 + Agent 能力
- **关键技术**: 实时视频，Project Astra

### Vision Transformer (ViT) (2020) ⭐
- **论文**: "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale"
- **作者**: Alexey Dosovitskiy et al. (Google Research)
- **意义**: 将 Transformer 成功应用于计算机视觉，证明注意力机制的通用性
- **关键技术**: Patch Embedding（16x16 图像块转换为 token 序列），CLS token 用于分类
- **创新点**: 降低归纳偏置，让模型从数据中学习视觉模式而非依赖卷积操作
- **影响**: 在大规模数据上超越传统 CNN，开启多模态 Transformer 时代，催生 CLIP、DALL-E 等视觉-语言模型

### LLaVA (2023)
- **论文**: "Visual Instruction Tuning"
- **作者**: Microsoft, University of Wisconsin
- **意义**: 开源视觉语言模型的里程碑
- **关键技术**: 将 Vision Encoder 的 image tokens 与文本 tokens 连接后输入 LLM
- **影响**: 推动开源 VLM 生态发展

### Bradley-Terry Model
- **意义**: 偏好对比较的数学基础，奖励模型训练的核心
- **应用**: RLHF 中的成对偏好比较
- **公式**: P(i > j) = exp(r_i) / (exp(r_i) + exp(r_j))
- **关键**: 模型输出两个分数并以成对方式训练，推理时只给一个输出

### GRPO (2024)
- **论文**: "Group Relative Policy Optimization"
- **意义**: 推理模型训练的关键算法，o1、DeepSeek 等模型的核心技术
- **关键优势**:
  - 无需训练价值函数（Value Function），简化训练流程
  - 特别适合可验证奖励任务（数学、代码等有标准答案的问题）
  - 只需保留策略模型和参考模型，降低资源消耗
- **改进版本**: GRPO Done Right（移除归一化项，解决长度偏差问题），DAPO（针对推理模型的变体）
- **对比 PPO**: PPO 需要价值函数估计基线，GRPO 使用组内相对优势直接对比

### Masked Diffusion Models (MDM) (2024+)
- **意义**: 将图像扩散模型范式迁移到文本生成，实现并行生成
- **核心思想**: 将图像噪声替换为文本掩码 token，固定步数（如 10 步）并行去掩码
- **关键优势**:
  - 推理速度提升 10 倍（相比自回归逐 token 生成）
  - 特别适合代码补全等"填空"任务
- **代表公司**: Inception（商业化先锋）
- **对比自回归**: 训练仍可并行，但推理时必须顺序生成；扩散模型训练和推理都可并行

---

## 里程碑时间线

```
2012  AlexNet        - 深度学习起点
2014  Seq2Seq        - 序列生成基础
2015  ResNet         - 深层网络训练
2017  Transformer    - 现代 AI 基石 ⭐
2018  BERT/GPT       - 预训练时代
2020  GPT-3          - 大模型时代 ⭐
2020  Vision Transformer - Transformer 进入视觉 ⭐
2020  Scaling Laws   - 理论基础 ⭐
2022  InstructGPT    - RLHF + ChatGPT ⭐
2022  Chain-of-Thought - 推理突破 ⭐
2023  GPT-4          - 多模态前沿 ⭐
2023  LLaMA          - 开源爆发 ⭐
2023  LLaVA          - 开源 VLM 里程碑
2024  o1             - 推理革命 ⭐
2024  GRPO           - 推理模型训练算法
2024+ Masked Diffusion - 并行文本生成
```

---

## 重要研究机构

| 机构 | 代表工作 |
|------|----------|
| **OpenAI** | GPT 系列, CLIP, Codex, o1 |
| **Google Brain/DeepMind** | Transformer, BERT, Gemini, AlphaFold |
| **Anthropic** | Constitutional AI, Claude |
| **Meta AI** | LLaMA, OPT, Segment Anything |
| **Stanford** | Alpaca, DPO, Flash Attention |
| **UC Berkeley** | RLHF 早期工作, LMSys |
| **Mistral** | Mixtral, 开源 MoE |
