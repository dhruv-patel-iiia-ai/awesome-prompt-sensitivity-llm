# Research Papers

A curated collection of scholarly papers related to prompt sensitivity,
prompt robustness, prompting strategies, reasoning consistency, and the
reliability of LLM-generated conclusions.

---

## 1. Foundational Papers

### Language Models are Few-Shot Learners

**Brown, T. B., Mann, B., Ryder, N., et al. (2020)**  
*Language Models are Few-Shot Learners*  
NeurIPS 2020.

[Paper](https://arxiv.org/abs/2005.14165)

This foundational paper introduced GPT-3 and demonstrated the ability of
large language models to perform tasks through few-shot prompting.

---

### Calibrate Before Use: Improving Few-Shot Performance of Language Models

**Zhao, Z., Wallace, E., Feng, S., Klein, D., & Singh, S. (2021)**  
*Calibrate Before Use: Improving Few-Shot Performance of Language Models*  
ICML 2021.

[Paper](https://arxiv.org/abs/2102.09690)

This paper demonstrates that prompt choices can significantly influence
few-shot model performance and proposes calibration to reduce these effects.

---

### Fantastically Ordered Prompts and Where to Find Them

**Lu, Y., Bartolo, M., Moore, A., Riedel, S., & Stenetorp, P. (2022)**  
*Fantastically Ordered Prompts and Where to Find Them: Overcoming Few-Shot
Prompt Order Sensitivity*  
ACL 2022.

[Paper](https://aclanthology.org/2022.acl-long.556/)

This study shows that changing the order of examples in a prompt can
substantially change LLM performance.

---

## 2. Prompt Sensitivity and Robustness

### ProSA: Assessing and Understanding the Prompt Sensitivity of LLMs

**Zhuo, T. Y., et al. (2024)**  
*ProSA: Assessing and Understanding the Prompt Sensitivity of LLMs*  
Findings of EMNLP 2024.

[Paper](https://aclanthology.org/2024.findings-emnlp.108/)

This paper directly investigates prompt sensitivity and proposes methods for
measuring how LLM outputs change under different prompts.

---

### What Did I Do Wrong? Quantifying LLMs' Sensitivity and Consistency to Prompt Engineering

**Errica, F., et al. (2025)**  
*What Did I Do Wrong? Quantifying LLMs' Sensitivity and Consistency to Prompt
Engineering*  
NAACL 2025.

[Paper](https://aclanthology.org/2025.naacl-long.73/)

This work studies how prompt engineering affects LLM sensitivity and
consistency and proposes quantitative evaluation approaches.

---

### Flaw or Artifact? Rethinking Prompt Sensitivity in Evaluating LLMs

**Hua, W., et al. (2025)**  
*Flaw or Artifact? Rethinking Prompt Sensitivity in Evaluating LLMs*  
EMNLP 2025.

[Paper](https://aclanthology.org/2025.emnlp-main.1006/)

This paper examines whether observed prompt sensitivity reflects genuine model
behavior or artifacts introduced by evaluation procedures.

---

### When Punctuation Matters: A Large-Scale Comparison of Prompt Robustness Methods for LLMs

**Seleznyov, A., et al. (2025)**  
*When Punctuation Matters: A Large-Scale Comparison of Prompt Robustness
Methods for LLMs*  
Findings of EMNLP 2025.

[Paper](https://aclanthology.org/2025.findings-emnlp.1109/)

This research investigates the effect of seemingly minor formatting and
punctuation changes on LLM performance.

---

### Measuring LLMs' Sensitivity to Paraphrased Opinion Prompts

**Alhetelah, B., & Ahmad, I. (2026)**  
*Measuring LLMs' Sensitivity to Paraphrased Opinion Prompts*  
WASSA 2026.

[Paper](https://aclanthology.org/2026.wassa-1.5/)

This work investigates whether semantically similar paraphrased prompts can
produce different LLM outputs.

---

### Understanding the Prompt Sensitivity

**Liu, Y., & Chu, X. (2026)**  
*Understanding the Prompt Sensitivity*  
ACL 2026.

[Paper](https://aclanthology.org/2026.acl-long.2053/)

This research investigates why LLM behavior can change when prompts are
modified while attempting to preserve their meaning.

---

## 3. Prompting and Reasoning Stability

### Self-Consistency Improves Chain of Thought Reasoning in Language Models

**Wang, X., Wei, J., Schuurmans, D., et al. (2023)**  
*Self-Consistency Improves Chain of Thought Reasoning in Language Models*  
ICLR 2023.

[Paper](https://arxiv.org/abs/2203.11171)

This paper introduces self-consistency, which samples multiple reasoning
paths and selects a consistent answer to improve reasoning reliability.

---

### Least-to-Most Prompting Enables Complex Reasoning in Large Language Models

**Zhou, D., Schärli, N., Hou, L., et al. (2023)**  
*Least-to-Most Prompting Enables Complex Reasoning in Large Language Models*  
ICLR 2023.

[Paper](https://arxiv.org/abs/2205.10625)

This paper investigates structured prompting for complex reasoning tasks and
shows how prompt decomposition can affect model performance.

---

### Large Language Models are Zero-Shot Reasoners

**Kojima, T., Gu, S. S., Reid, M., Matsuo, Y., & Iwasawa, Y. (2022)**  
*Large Language Models are Zero-Shot Reasoners*  
NeurIPS 2022.

[Paper](https://arxiv.org/abs/2205.11916)

This work demonstrates that adding appropriate reasoning instructions to
prompts can substantially change LLM reasoning performance.

---

### Chain-of-Thought Prompting Elicits Reasoning in Large Language Models

**Wei, J., Wang, X., Schuurmans, D., et al. (2022)**  
*Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*  
NeurIPS 2022.

[Paper](https://arxiv.org/abs/2201.11903)

This foundational work shows that prompting models to generate intermediate
reasoning steps can improve performance on complex reasoning tasks.

---

## 4. Prompt Engineering and In-Context Learning

### A Survey on In-context Learning

**Dong, Q., Li, L., Dai, D., et al. (2024)**  
*A Survey on In-context Learning*  
ACM Computing Surveys.

[Paper](https://arxiv.org/abs/2301.00234)

This survey provides a broad overview of in-context learning and factors
affecting its effectiveness.

---

### Pre-train, Prompt, and Predict: A Systematic Survey of Prompting Methods in Natural Language Processing

**Liu, P., Yuan, W., Fu, J., Jiang, Z., Hayashi, H., & Neubig, G. (2023)**  
*Pre-train, Prompt, and Predict: A Systematic Survey of Prompting Methods in
Natural Language Processing*  
ACM Computing Surveys.

[Paper](https://arxiv.org/abs/2107.13586)

This survey organizes prompting techniques and provides important
background for understanding prompt-dependent model behavior.

---

### The Power of Scale for Parameter-Efficient Prompt Tuning

**Lester, B., Al-Rfou, R., & Constant, N. (2021)**  
*The Power of Scale for Parameter-Efficient Prompt Tuning*  
EMNLP 2021.

[Paper](https://aclanthology.org/2021.emnlp-main.243/)

This paper investigates prompt tuning and demonstrates how model scale
affects the effectiveness of prompt-based adaptation.

---

## 5. LLM Evaluation and Reliability

### TruthfulQA: Measuring How Models Mimic Human Falsehoods

**Lin, S., Hilton, J., & Evans, O. (2022)**  
*TruthfulQA: Measuring How Models Mimic Human Falsehoods*  
ACL 2022.

[Paper](https://aclanthology.org/2022.acl-long.229/)

This benchmark evaluates whether language models generate truthful answers,
which is relevant to the reliability of generated research conclusions.

---

### HELM: Holistic Evaluation of Language Models

**Liang, P., Bommasani, R., Lee, T., et al. (2023)**  
*Holistic Evaluation of Language Models*  
Transactions on Machine Learning Research.

[Paper](https://arxiv.org/abs/2211.09110)

HELM provides a comprehensive framework for evaluating language models
across multiple dimensions and scenarios.

---

### Beyond Accuracy: Behavioral Testing of NLP Models with CheckList

**Ribeiro, M. T., Wu, T., Guestrin, C., & Singh, S. (2020)**  
*Beyond Accuracy: Behavioral Testing of NLP Models with CheckList*  
ACL 2020.

[Paper](https://aclanthology.org/2020.acl-main.442/)

This work introduces behavioral testing methods that can be useful for
studying model robustness beyond standard accuracy measurements.

---

### On the Dangers of Stochastic Parrots: Can Language Models Be Too Big?

**Bender, E. M., Gebru, T., McMillan-Major, A., & Shmitchell, S. (2021)**  
*On the Dangers of Stochastic Parrots: Can Language Models Be Too Big?*  
FAccT 2021.

[Paper](https://dl.acm.org/doi/10.1145/3442188.3445922)

This paper discusses important limitations and risks associated with large
language models, including issues relevant to reliability and responsible
use.

---

## 6. Recent and Related Research

### On the Opportunities and Risks of Foundation Models

**Bommasani, R., Hudson, D. A., Adeli, E., et al. (2021)**  
*On the Opportunities and Risks of Foundation Models*  

[Paper](https://arxiv.org/abs/2108.07258)

This broad survey discusses capabilities, limitations, evaluation, and risks
of foundation models.

---

### Sparks of Artificial General Intelligence: Early Experiments with GPT-4

**Bubeck, S., Chandrasekaran, V., Eldan, R., et al. (2023)**  
*Sparks of Artificial General Intelligence: Early Experiments with GPT-4*

[Paper](https://arxiv.org/abs/2303.12712)

This study evaluates GPT-4 across many tasks and provides context for
understanding the capabilities and limitations of modern LLMs.

---

### Language Models Don't Always Say What They Think

**Turpin, M., Michael, J., Perez, E., & Bowman, S. R. (2023)**  
*Language Models Don't Always Say What They Think: Unfaithful Explanations
in Chain-of-Thought Prompting*

[Paper](https://arxiv.org/abs/2305.04388)

This research examines whether generated reasoning explanations reliably
represent the actual factors influencing model answers.

---

### Large Language Models as Simulators

**Shanahan, M., McDonell, K., & Reynolds, L. (2023)**  
*Role Play with Large Language Models*  

[Paper](https://arxiv.org/abs/2305.16367)

This work discusses how prompting and contextual framing can influence the
behavior and outputs of language models.

---

## Relevance to This Repository

These papers collectively cover the main dimensions of the research topic:

- Prompt sensitivity
- Prompt robustness
- Prompt ordering
- Prompt paraphrasing
- Few-shot learning
- In-context learning
- Chain-of-thought reasoning
- Self-consistency
- LLM evaluation
- Truthfulness
- Reliability
- Reproducibility

The collection will be expanded and refined as additional verified research
resources are identified.
