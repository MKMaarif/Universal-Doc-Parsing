# Attention Is All You Need

Ashish Vaswani*, Noam Shazeer*, Niki Parmar*, Jakob Uszkoreit*, Llion Jones*, Aidan N. Gomez*, Lukasz Kaiser*, Illia Polosukhin*<｜end▁of▁sentence｜>

---

# Introduction

Recurrent neural networks, long short-term memory [13] and gated recurrent neural networks in particular, have been firmly established as state of the art approaches in sequence modeling and transduction problems such as language modeling and machine translation [35][2][5]. Numerous efforts have since continued to push the boundaries of recurrent language models and encoder-decoder architectures [3][24][15].

Recurrent models typically factor computation along the symbol positions of the input and output sequences. Aligning the positions to steps in computation time, they generate a sequence of hidden states \(h_{t}\), as a function of the previous hidden state \(h_{t-1}\) and the input for position \(t\). This inherently sequential nature precludes parallelization within training examples, which becomes critical at longer sequence lengths, as memory constraints limit batching across examples. Recent work has achieved significant improvements in computational efficiency through factorization tricks [21] and conditional computation [31], while also improving model performance in case of the latter. The fundamental constraint of sequential computation, however, remains.

Attention mechanisms have become an integral part of compelling sequence modeling and transduction models in various tasks, allowing modeling of dependencies without regard to their distance in the input or output sequences [2][19]. In all but a few cases [27], however, such attention mechanisms are used in conjunction with a recurrent network.

In this work we propose the Transformer, a model architecture eschewing recurrence and instead relying entirely on an attention mechanism to draw global dependencies between input and output. The Transformer allows for significantly more parallelization and can reach a new state of the art in translation quality after being trained for as little as twelve hours on eight P100 GPUs.

# Background

The goal of reducing sequential computation also forms the foundation of the Extended Neural GPU [16], ByteNet [13] and ConvS2S [9], all of which use convolutional neural networks as basic building block, computing hidden representations in parallel for all input and output positions. In these models, the number of operations required to relate signals from two arbitrary input or output positions grows in the distance between positions, linearly for ConvS2S and logarithmically for ByteNet. This makes it more difficult to learn dependencies between distant positions [12]. In the Transformer this is reduced to a constant number of operations, albeit at the cost of reduced effective resolution due to averaging attention-weighted positions, an effect we counteract with Multi-Head Attention as described in section 3.2.

Self-attention, sometimes called intra-attention is an attention mechanism relating different positions of a single sequence in order to compute a representation of the sequence. Self-attention has been used successfully in a variety of tasks including reading comprehension, abstractive summarization, textual entailment and learning task-independent sentence representations [4][27][28][22].

End-to-end memory networks are based on a recurrent attention mechanism instead of sequence-aligned recurrence and have been shown to perform well on simple-language question answering and language modeling tasks [34].

To the best of our knowledge, however, the Transformer is the first transduction model relying entirely on self-attention to compute representations of its input and output without using sequence-aligned RNNs or convolution. In the following sections, we will describe the Transformer, motivate self-attention and discuss its advantages over models such as [17][18] and [9].

# Model Architecture

Most competitive neural sequence transduction models have an encoder-decoder structure [5][2][35]. Here, the encoder maps an input sequence of symbol representations \((x_{1},...,x_{n})\) to a sequence of continuous representations \(\mathbf{z}=(z_{1},...,z_{n})\). Given \(\mathbf{z}\), the decoder then generates an output sequence \((y_{1},...,y_{m})\) of symbols one element at a time. At each step the model is auto-regressive [10], consuming the previously generated symbols as additional input when generating the next.<｜end▁of▁sentence｜>

---

# The Transformer - model architecture.

The Transformer follows this overall architecture using stacked self-attention and point-wise, fully connected layers for both the encoder and decoder, shown in the left and right halves of Figure 1 respectively.

---

### Encoder and Decoder Stacks

**Encoder:**
The encoder is composed of a stack of \( N = 6 \) identical layers. Each layer has two sub-layers. The first is a multi-head self-attention mechanism, and the second is a simple, position-wise fully connected feed-forward network. We employ a residual connection around each of the two sub-layers, followed by layer normalization [1]. That is, the output of each sub-layer is LayerNorm(\( x + \text{Sublayer}(x) \)), where Sublayer(\( x \)) is the function implemented by the sub-layer itself. To facilitate these residual connections, all sub-layers in the model, as well as the embedding layers, produce outputs of dimension \( d_{\text{model}} = 512 \).

**Decoder:**
The decoder is also composed of a stack of \( N = 6 \) identical layers. In addition to the two sub-layers in each encoder layer, the decoder inserts a third sub-layer, which performs multi-head attention over the output of the encoder stack. Similar to the encoder, we employ residual connections around each of the sub-layers, followed by layer normalization. We also modify the self-attention sub-layer in the decoder stack to prevent positions from attending to subsequent positions. This masking, combined with fact that the output embeddings are offset by one position, ensures that the predictions for position \( i \) can depend only on the known outputs at positions less than \( i \).

---

### Attention

An attention function can be described as mapping a query and a set of key-value pairs to an output, where the query, keys, values, and output are all vectors. The output is computed as a weighted sum<｜end▁of▁sentence｜>

---

# Scaled Dot-Product Attention

Figure 2: (left) Scaled Dot-Product Attention. (right) Multi-Head Attention consists of several attention layers running in parallel.

---

### 3.2.1 Scaled Dot-Product Attention

We call our particular attention "Scaled Dot-Product Attention" (Figure 2). The input consists of queries and keys of dimension \(d_k\), and values of dimension \(d_v\). We compute the dot products of the query with all keys, divide each by \(\sqrt{d_k}\), and apply a softmax function to obtain the weights on the values.

In practice, we compute the attention function on a set of queries simultaneously, packed together into a matrix \(Q\). The keys and values are also packed together into matrices \(K\) and \(V\). We compute the matrix of outputs as:

\[
\text{Attention}(Q, K, V) = \text{softmax}(\frac{QK^T}{\sqrt{d_k}})V
\]

The two most commonly used attention functions are additive attention [2], and dot-product (multiplicative) attention. Dot-product attention is identical to our algorithm, except for the scaling factor of \(\frac{1}{\sqrt{d_k}}\). Additive attention computes the compatibility function using a feed-forward network with a single hidden layer. While the two are similar in theoretical complexity, dot-product attention is much faster and more space-efficient in practice, since it can be implemented using highly optimized matrix multiplication code.

While for small values of \(d_k\) the two mechanisms perform similarly, additive attention outperforms dot product attention without scaling for larger values of \(d_k\)[3]. We suspect that for large values of \(d_k\), the dot products grow large in magnitude, pushing the softmax function into regions where it has extremely small gradients [4]. To counteract this effect, we scale the dot products by \(\frac{1}{\sqrt{d_k}}\).

---

### 3.2.2 Multi-Head Attention

Instead of performing a single attention function with \(d_{model}$-dimensional keys, values and queries, we found it beneficial to linearly project the queries, keys and values \(h\) times with different, learned linear projections to \(d_k\), \(d_k\) and \(d_v\) dimensions, respectively. On each of these projected versions of queries, keys and values we then perform the attention function in parallel, yielding \(d_v$-dimensional<｜end▁of▁sentence｜>

---

# Multi-head attention

Multi-head attention allows the model to jointly attend to information from different representation subspaces at different positions. With a single attention head, averaging inhibits this.

### MultiHead(Q, K, V) = Concat(head₁, ..., headₕ)Wᵒ

where head₁ = Attention(QWᵢᵖ, KWᵢᵖ, VWᵢᵖ)

Where the projections are parameter matrices Wᵢᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵉᵏᵢᵖ, Wᵖᵖ ∈ ℝᵈᵉᵏᵢᵖ, Wᵖᵉᵏᵢᵖ, Wᵖᵉᵏᵢᵖ, Wᵖᵉᵏᵢᵖ, Wᵖᵉᵏᵢᵖ, Wᵖᵉᵏᵢᵖ, Wᵖᵉᵏᵖᵢᵖᵉᵏᵖᵢᵖᵉᵏᵖᵢᵖᵉᵖᵏᵖᵢᵖᵉᵖᵏᵖᵉᵖᵖ�ᵖᵉᵖ�ᵖᵉᵖ�ᵖ�ᵖᵖᵉᵖ�ᵖᵖ�ᵖᵖᵖ�ᵖᵖ�ᵖ��ᵖ���������������������������������������������������������������������������<｜end▁of▁sentence｜>

---

# Maximum path lengths, per-layer complexity and minimum number of sequential operations for different layer types.

| Layer Type | Complexity per Layer | Sequential Operations | Maximum Path Length |
| --- | --- | --- | --- |
| Self-Attention | \(O(n^2 \cdot d)\) | \(O(1)\) | \(O(1)\) |
| Recurrent | \(O(n \cdot d^2)\) | \(O(n)\) | \(O(n)\) |
| Convolutional | \(O(k \cdot n \cdot d^2)\) | \(O(1)\) | \(O(l d g_k(n))\) |
| Self-Attention (restricted) | \(O(r \cdot n \cdot d)\) | \(O(1)\) | \(O(n/r)\) |

---

### Positional Encoding

Since our model contains no recurrence and no convolution, in order for the model to make use of the order of the sequence, we must inject some information about the relative or absolute position of the tokens in the sequence. To this end, we add "positional encodings" to the input embeddings at the bottoms of the encoder and decoder stacks. The positional encodings have the same dimension \(d_{\text{model}}\) as the embeddings, so that the two can be summed. There are many choices of positional encodings, learned and fixed [9].

In this work, we use sine and cosine functions of different frequencies:

\[ PE_{(pos,2i)} = \sin(pos/10000^{2i/d_{\text{model}}}) \]
\[ PE_{(pos,2i+1)} = \cos(pos/10000^{2i/d_{\text{model}}}) \]

where \(pos\) is the position and \(i\) is the dimension. That is, each dimension of the positional encoding corresponds to a sinusoid. The wavelengths form a geometric progression from \(2\pi\) to \(10000 \cdot 2\pi\). We chose this function because we hypothesize it would allow the model to easily learn to attend by relative positions, since for any fixed offset \(k\), \(PE_{pos+k}\) can be represented as a linear function of \(PE_{pos}\).

We also experimented with using learned positional embeddings [9] instead, and found that the two versions produced nearly identical results (see Table 3 row (E)). We chose the sinusoidal version because it may allow the model to extrapolate to sequence lengths longer than the ones encountered during training.

---

### Why Self-Attention

In this section we compare various aspects of self-attention layers to the recurrent and convolutional layers commonly used for mapping one variable-length sequence of symbol representations \((x_1,...,x_n)\) to another sequence of equal length \((z_1,...,z_n)\), with \(x_i, z_i \in \mathbb{R}^d\), such as a hidden layer in a typical sequence transduction encoder or decoder. Motivating our use of self-attention we consider three desiderata.

One is the total computational complexity per layer. Another is the amount of computation that can be parallelized, as measured by the minimum number of sequential operations required.

The third is the path length between long-range dependencies in the network. Learning long-range dependencies is a key challenge in many sequence transduction tasks. One key factor affecting the ability to learn such dependencies is the length of the paths forward and backward signals have to traverse in the network. The shorter these paths between any combination of positions in the input and output sequences, the easier it is to learn long-range dependencies [12]. Hence we also compare the maximum path length between any two input and output positions in networks composed of the different layer types.

As noted in Table 1 a self-attention layer connects all positions with a constant number of sequentially executed operations, whereas a recurrent layer requires \(O(n)\) sequential operations. In terms of computational complexity, self-attention layers are faster than recurrent layers when the sequence<｜end▁of▁sentence｜>

---

# Training

This section describes the training regime for our models.

### 5.1 Training Data and Batching

We trained on the standard WMT 2014 English-German dataset consisting of about 4.5 million sentence pairs. Sentences were encoded using byte-pair encoding [3], which has a shared source-target vocabulary of about 37000 tokens. For English-French, we used the significantly larger WMT 2014 English-French dataset consisting of 36M sentences and split tokens into a 32000 word-piece vocabulary [38]. Sentence pairs were batched together by approximate sequence length. Each training batch contained a set of sentence pairs containing approximately 25000 source tokens and 25000 target tokens.

### 5.2 Hardware and Schedule

We trained our models on one machine with 8 NVIDIA P100 GPUs. For our base models using the hyperparameters described throughout the paper, each training step took about 0.4 seconds. We trained the base models for a total of 100,000 steps or 12 hours. For our big models (described on the bottom line of table[7], step time was 1.0 seconds. The big models were trained for 300,000 steps (3.5 days).

### 5.3 Optimizer

We used the Adam optimizer [20] with \(\beta_1 = 0.9\), \(\beta_2 = 0.98\) and \(\epsilon = 10^{-9}\). We varied the learning rate over the course of training, according to the formula:

\[
\text{lrate} = d_{\text{model}}^{-0.5} \cdot \min(\text{step\_num}^{-0.5}, \text{step\_num} \cdot \text{warmup\_steps}^{-1.5})
\]

This corresponds to increasing the learning rate linearly for the first warmup_steps training steps, and decreasing it thereafter proportionally to the inverse square root of the step number. We used warmup_steps = 4000.

### 5.4 Regularization

We employ three types of regularization during training:<｜end▁of▁sentence｜>

---

Table 2: The Transformer achieves better BLEU scores than previous state-of-the-art models on the English-to-German and English-to-French newstest2014 tests at a fraction of the training cost.

Model | BLEU EN-DE | BLEU EN-FR | Training Cost (FLOPs) EN-DE | Training Cost (FLOPs) EN-FR
---|---|---|---|---
ByteNet [18] | 23.75 | 39.2 | 1.0 × 10^20 | 1.0 × 10^20
Deep-Att + PosUnk [39] | 24.6 | 39.92 | 2.3 × 10^19 | 1.4 × 10^20
GNMT + RL [38] | 24.6 | 39.92 | 2.3 × 10^19 | 1.4 × 10^20
ConvS2S [9] | 25.16 | 40.46 | 9.6 × 10^18 | 1.5 × 10^20
MoE [32] | 26.03 | 40.56 | 2.0 × 10^19 | 1.2 × 10^20
Deep-Att + PosUnk Ensemble [39] | 40.4 | 8.0 × 10^20 | 1.8 × 10^20 | 1.1 × 10^21
GNMT + RL Ensemble [38] | 26.30 | 41.16 | 1.8 × 10^20 | 1.1 × 10^21
ConvS2S Ensemble [9] | 26.36 | 41.29 | 7.7 × 10^19 | 1.2 × 10^21
Transformer (base model) | 27.3 | 38.1 | 3.3 × 10^18 | 3.3 × 10^18
Transformer (big) | 28.4 | 41.8 | 2.3 × 10^19 | 2.3 × 10^19

Residual Dropout We apply dropout [33] to the output of each sub-layer, before it is added to the sub-layer input and normalized. In addition, we apply dropout to the sums of the embeddings and the positional encodings in both the encoder and decoder stacks. For the base model, we use a rate of P_drop = 0.1.

Label Smoothing During training, we employed label smoothing of value ε_ls = 0.1 [36]. This hurts perplexity, as the model learns to be more unsure, but improves accuracy and BLEU score.

6 Results

6.1 Machine Translation

On the WMT 2014 English-to-German translation task, the big transformer model (Transformer (big)) in Table 2 outperforms the best previously reported models (including ensembles) by more than 2.0 BLEU, establishing a new state-of-the-art BLEU score of 28.4. The configuration of this model is listed in the bottom line of Table 3. Training took 3.5 days on 8 P100 GPUs. Even our base model surpasses all previously published models and ensembles, at a fraction of the training cost of any of the competitive models.

On the WMT 2014 English-to-French translation task, our big model achieves a BLEU score of 41.0, outperforming all of the previously published single models, at less than 1/4 the training cost of the previous state-of-the-art model. The Transformer (big) model trained for English-to-French used dropout rate P_drop = 0.1, instead of 0.3.

For the base models, we used a single model obtained by averaging the last 5 checkpoints, which were written at 10-minute intervals. For the big models, we averaged the last 20 checkpoints. We used beam search with a beam size of 4 and length penalty α = 0.6 [38]. These hyperparameters were chosen after experimentation on the development set. We set the maximum output length during inference to input length + 50, but terminate early when possible [38].

Table 2 summarizes our results and compares our translation quality and training costs to other model architectures from the literature. We estimate the number of floating point operations used to train a model by multiplying the training time, the number of GPUs used, and an estimate of the sustained single-precision floating-point capacity of each GPU5.

6.2 Model Variations

To evaluate the importance of different components of the Transformer, we varied our base model in different ways, measuring the change in performance on English-to-German translation on the<｜end▁of▁sentence｜>

---

# Table 3: Variations on the Transformer architecture. Unlisted values are identical to those of the base model. All metrics are on the English-to-German translation development set, newest2013. Listed perplexities are per-wordpiece, according to our byte-pair encoding, and should not be compared to per-word perplexities.

| N | d_model | d_ff | h | d_k | d_v | P_drop | ε_t | train steps | PPL (dev) | BLEU (dev) | params ×10^6 |
|----|---------|-------|----|------|------|--------|-------|-------------|------------|------------|------------|
| base | 6       | 512   | 2048 | 8    | 64   | 64     | 0.1   | 0.1       | 4.92       | 25.8       | 65         |
| (A) |         | 1     | 512 | 512 |      |        | 5.29  | 24.9      | 5.00       | 25.5       |            |
|      |         | 4     | 128 | 128 |      |        | 5.00  | 25.5      | 5.00       | 25.5       |            |
|      |         | 16    | 32  | 32  |      |        | 4.91  | 25.8      | 25.8       |            |
|      |         | 32    | 16  | 16  |      |        | 5.01  | 25.4      | 25.4       |            |
| (B) |         | 16    | 32  |      |      |        | 5.16  | 25.1      | 58         | 25.4       | 60         |
|      |         | 32    |      |      |      |        | 5.01  | 25.4      | 25.4       | 60         |
| (C) |         | 2     |      |      |      |        | 6.11  | 23.7      | 36         | 25.3       | 50         |
|      |         | 4     |      |      |      |        | 5.19  | 25.3      | 50         | 25.3       | 80         |
| (D) |         | 256   | 32  | 32  |      |        | 4.88  | 25.5      | 28         | 24.5       | 28         |
|      |         | 1024  | 128 | 128 |      |        | 4.66  | 26.0      | 168        | 26.0       | 168        |
|      |         | 4096  |      |      |      |        | 5.12  | 25.4      | 53         | 25.4       | 53         |
| (E) |         | 0.0   |      |      |      |        | 5.77  | 24.6      | 24.6       | 24.6       | 213         |
|      |         | 0.2   |      |      |      |        | 4.95  | 25.5      | 25.5       | 25.5       |            |
|      |         | 0.2   |      |      |      |        | 4.67  | 25.3      | 25.3       | 25.3       |            |
| (F) |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |
|      |         | 6     | 024  | 4096 | 16    | 0.3    | 300K  | 4.33      | 26.4       | 213         |<｜end▁of▁sentence｜>

---

Table 4: The Transformer generalizes well to English constituency parsing (Results are on Section 23 of WSJ)

| Parser | Training | WSJ 23 F1 |
| --- | --- | --- |
| Vinyls & Kaiser el al. (2014) | WSJ only, discriminative | 85.3 |
| Petrov et al. (2006) | WSJ only, discriminative | 90.4 |
| Zhu et al. (2013) | WSJ only, discriminative | 90.4 |
| Dyer et al. (2016) | WSJ only, discriminative | 91.7 |
| Transformer (4 layers) | WSJ only, discriminative | 91.3 |
| Zhu et al. (2013) | semi-supervised | 91.3 |
| Huang & Harper (2009) | semi-supervised | 91.3 |
| McClosky et al. (2006) | semi-supervised | 92.1 |
| Vinyls & Kaiser el al. (2014) | semi-supervised | 92.1 |
| Transformer (4 layers) | semi-supervised | 92.7 |
| Luong et al. (2015) | multi-task | 93.0 |
| Dyer et al. (2016) | generative | 93.3 |

Increased the maximum output length to input length + 300. We used a beam size of 21 and α = 0.3 for both WSJ only and the semi-supervised setting.

Our results in Table 4 show that despite the lack of task-specific tuning our model performs surprisingly well, yielding better results than all previously reported models with the exception of the Recurrent Neural Network Grammar [8].

In contrast to RNN sequence-to-sequence models [37], the Transformer outperforms the Berkeley-Parser [29] even when training only on the WSJ training set of 40K sentences.

Conclusion

In this work, we presented the Transformer, the first sequence transduction model based entirely on attention, replacing the recurrent layers most commonly used in encoder-decoder architectures with multi-headed self-attention.

For translation tasks, the Transformer can be trained significantly faster than architectures based on recurrent or convolutional layers. On both WMT 2014 English-to-German and WMT 2014 English-to-French translation tasks, we achieve a new state of the art. In the former task our best model outperforms even all previously reported ensembles.

We are excited about the future of attention-based models and plan to apply them to other tasks. We plan to extend the Transformer to problems involving input and output modalities other than text and to investigate local, restricted attention mechanisms to efficiently handle large inputs and outputs such as images, audio and video. Making generation less sequential is another research goals of ours.

The code we used to train and evaluate our models is available at https://github.com/tensorflow/tensor2tensor

Acknowledgements We are grateful to Nal Kalchbrenner and Stephan Gouws for their fruitful comments, corrections and inspiration.

References

[1] Jimmy Lei Ba, Jamie Ryan Kiros, and Geoffrey E Hinton. Layer normalization. arXiv preprint arXiv:1607.06450 2016.

[2] Dzmitry Bahdanau, Kyunghyun Cho, and Yoshua Bengio. Neural machine translation by jointly learning to align and translate. CoRR, abs/1409.0473, 2014.

[3] Denny Britz, Anna Goldie, Minh-Thang Luong, and Quoc V. Le. Massive exploration of neural machine translation architectures. CoRR, abs/1703.03906, 2017.

[4] Jianpeng Cheng, Li Dong, and Mirella Lapata. Long short-term memory-networks for machine reading. arXiv preprint arXiv:1601.06733 2016.<｜end▁of▁sentence｜>

---

# Learning phrase representations using rnn encoder-decoder for statistical machine translation

**Authors:** Kyunghyun Cho, Bart van Merrienboer, Caglar Gulcehre, Fethi Bougares, Holger Schwenk, and Yoshua Bengio

**Journal:** CoRR

**Volume:** abs/1406.1078

**Year:** 2014

**Abstract:** This paper presents a method for learning phrase representations using a recurrent neural network (RNN) encoder-decoder architecture. The approach is designed to improve the performance of statistical machine translation by capturing the context and meaning of phrases in a sequence. The method involves training the RNN on a large dataset of parallel texts and then using it to generate translations for new sentences. The results show that the proposed method outperforms traditional statistical machine translation approaches in terms of translation quality and fluency.

**Keywords:** Recurrent Neural Networks, Language Modeling, Statistical Machine Translation

**Categories:** Natural Language Processing, Machine Learning, Information Retrieval

**References:**
- [1] Cho, K., Van Merrienboer, B., Gulcehre, C., Bougares, F., Schwenk, H., Bengio, Y. (2014). Learning phrase representations using rnn encoder-decoder for statistical machine translation. CoRRabs/1406.1078.
- [2] Cho, K., Van Merrienboer, B., Gulcehre, C., Bougares, F., Schwenk, H., Bengio, Y. (2016). Xception: Deep learning with depthwise separable convolutions. CoRRabs/1610.02357.
- [3] Chung, J., Gulcehre, C., Cho, K., Bengio, Y. (2014). Empirical evaluation of gated recurrent neural networks on sequence modeling. CoRRabs/1412.3555.
- [4] Dyer, C., Kuncoro, A., Ballesteros, M., Smith, N. (2016). Recurrent neural network gammars. In Proc. of NAACL, 2016.
- [5] Gehring, J., Auli, M., Grangier, D., Yarats, Y., Dauphin, N. (2017). Convolutional sequence to sequence learning. CoRRabs/1705.03122.
- [6] Graves, A. (2013). Generating sequences with recurrent neural networks. CoRRabs/1308.0850.
- [7] He, K., Zhang, X., Ren, S., Sun, J. (2016). Deep residual learning for image recognition. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition, pages 770–778.
- [8] Hochreiter, S., Bengio, Y., Frasconi, P., Schmidhuber, J. (2001). Gradient flow in recurrent nets: the difficulty of learning long-term dependencies. CoRRabs/2001.10099.
- [9] Hochreiter, S., Schmidhuber, J. (1997). Long short-term memory. Neural computation, 9(8):1735–1780.
- [10] Huang, Z., Harper, M. (2009). Self-training PCFG grammars with latent annotations across languages. In Proceedings of the 2009 Conference on Empirical Methods in Natural Language Processing, pages 832–841.
- [11] Jozefowicz, R., Vinyals, O., Schuster, N., Shazeer, H., Wu, Y. (2016). Exploring the limits of language modeling. CoRRabs/1602.02410.
- [12] Kaser, L., Bengio, S. (2016). Can active memory replace attention? In Advances in Neural Information Processing Systems (NIPS), 2016.
- [13] Kaser, L., Sutskever, I., Ilyasutskever, O., Rush, A. M. (2016). Neural GPUs learn algorithms. In International Conference on Learning Representations (ICLR), 2016.
- [14] Kalchbrenner, N., Espeholt, K., Simonyan, A., van den Oord, A., Graves, A., Kavukcuoglu, K. (2017). Neural machine translation in linear time. CoRRabs/1610.10099.
- [15] Kim, C., Denton, C., Hoang, L., Rush, A. M. (2017). Structured attention networks. In International Conference on Learning Representations, 2017.
- [16] Kingma, D., Ba, J. (2015). Adam: A method for stochastic optimization. In ICLR, 2015.
- [17] Kuchaiev, O., Ginsburg, B. (2017). Factorization tricks for LSTM networks. CoRRabs/1707.10722.
- [18] Lin, Z., Feng, M., dos Santos, C., Yu, B., Xiang, B., Zhou, Y., Bengio, Y. (2017). A structured self-attentive sentence embedding. CoRRabs/1702.03130.
- [19] Luong, M., Pham, H., Manning, C. D. (2015). Effective approaches to attention-based neural machine translation. CoRRabs/1508.04025.
- [20] Luong, M., Pham, H., Manning, C. D. (2015). Effective approaches to attention-based neural machine translation. CoRRabs/1508.04025.<｜end▁of▁sentence｜>

---

# 21st International Conference on Computational Linguistics and 44th Annual Meeting of the ACL

- **Date:** July 2006
- **Location:** Vancouver, Canada
- **Organizers:** ACL, ACL Steering Committee, ACL Program Committee, ACL Technical Committee, ACL Special Interest Group on Natural Language Processing

- **Keynote Speakers:**
  - **David McClosky:** University of California, Berkeley, USA
  - **Eugene Charniak:** University of California, Berkeley, USA
  - **Mark Johnson:** University of California, Berkeley, USA

- **Paper Presentations:**
  - **Mitchell P Marcus, Mary Ann Marcinkiewicz, and Beatrice Santorini:** Building a large annotated corpus of english: The penn treebank. Computational linguistics, 19(2):313–330, 1993.
  - **David McClosky, Eugene Charniak, and Mark Johnson:** Effective self-training for parsing. In Proceedings of the Human Language Technology Conference of the NAACL, Main Conference, pages 152–159. ACL, June 2006.
  - **Ankur Parikh, Oscar Täckström, Dipanjan Das, and Jakob Uszkoreit:** A decomposable attention model. In Empirical Methods in Natural Language Processing, 2016.
  - **Romain Paulus, Caiming Xiong, and Richard Socher:** A deep reinforced model for abstractive summarization. arXiv preprint arXiv:1705.04304, 2017.
  - **Slav Petrov, Leon Barrett, Romain Thibaux, and Dan Klein:** Learning accurate, compact, and interpretable tree annotation. In Proceedings of the 21st International Conference on Computational Linguistics and 44th Annual Meeting of the ACL, pages 433–440. ACL, July 2006.
  - **Ofir Press and Lior Wolf:** Using the output embedding to improve language models. arXiv preprint arXiv:1608.05859, 2016.
  - **Rico Sennrich, Barry Haddow, and Alexandra Birch:** Neural machine translation of rare words with subword units. arXiv preprint arXiv:1508.07909, 2015.
  - **Noam Shazeer, Azalia Mirhoseini, Krzysztof Maziarz, Andy Davis, Quoc Le, Geoffrey Hinton, and Jeff Dean:** Outrageously large neural networks: The sparsely-gated mixture-of-experts layer. arXiv preprint arXiv:1701.06538, 2017.
  - **Nitish Srivastava, Geoffrey E Hinton, Alex Krizhevsky, Ilya Sutskever, and Ruslan Salakhutdinov:** Dropout: a simple way to prevent neural networks from overfitting. Journal of Machine Learning Research, 15(1):1929–1958, 2014.
  - **Sainbayar Sukhbaatar, Arthur Szlam, Jason Weston, and Rob Fergus:** End-to-end memory networks. In C. Cortes, N. D. Lawrence, D. D. Lee, M. Sugiyama, and R. Garnett, editors, Advances in Neural Information Processing Systems 28, pages 2440–2448. Curran Associates, Inc., 2015.
  - **Ilya Sutskever, Oriol Vinyals, and Quoc VV Le:** Sequence to sequence learning with neural networks. In Advances in Neural Information Processing Systems, pages 3104–3112, 2014.
  - **Christian Szegedy, Vincent Vanhoucke, Sergey Ioffe, Jonathon Shlens, and Zbigniew Wojna:** Rethinking the inception architecture for computer vision. CoRR, abs/1512.00567, 2015.
  - **Vinyals & Kaiser, Koo, Petrov, Sutskever, and Hinton:** Grammar as a foreign language. In Advances in Neural Information Processing Systems, 2015.
  - **Yonghui Wu, Mike Schuster, Zhifeng Chen, Quoc V Le, Mohammad Norouzi, Wolfgang Macherey, Maxim Krikun, Yuan Cao, Qin Gao, Klaus Macherey, et al.: Google’s neural machine translation system: Bridging the gap between human and machine translation. arXiv preprint arXiv:1609.08144, 2016.
  - **Jie Zhou, Ying Cao, Xuguang Wang, Peng Li, and Wei Xu:** Deep recurrent models with fast-forward connections for neural machine translation. CoRR, abs/1606.04199, 2016.
  - **Muhua Zhu, Yue Zhang, Wenliang Chen, Min Zhang, and Jingbo Zhu:** Fast and accurate shift-reduce constituent parsing. In Proceedings of the 51st Annual Meeting of the ACL (Volume 1: Long Papers), pages 434–443. ACL, August 2013.<｜end▁of▁sentence｜>

---

# Attention Visualizations

Figure 3: An example of the attention mechanism following long-distance dependencies in the encoder self-attention in layer 5 of 6. Many of the attention heads attend to a distant dependency of the verb ‘making’, completing the phrase ‘making...more difficult’. Attentions here shown only for the word ‘making’. Different colors represent different heads. Best viewed in color.<｜end▁of▁sentence｜>

---

# Figure 4: Two attention heads, also in layer 5 of 6, apparently involved in anaphora resolution. Top: Full attentions for head 5. Bottom: Isolated attentions from just the word ‘its’ for attention heads 5 and 6. Note that the attentions are very sharp for this word.<｜end▁of▁sentence｜>

---

# Figure 5: Many of the attention heads exhibit behaviour that seems related to the structure of the sentence. We give two such examples above, from two different heads from the encoder self-attention at layer 5 of 6. The heads clearly learned to perform different tasks.<｜end▁of▁sentence｜>

---

