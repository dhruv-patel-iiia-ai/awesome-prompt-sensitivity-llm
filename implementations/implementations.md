# GitHub Implementations

This section contains open-source GitHub repositories and implementations
relevant to prompt sensitivity, prompt robustness, LLM evaluation, and
reliable prompt engineering.

These repositories can be studied to understand how researchers and
developers implement prompt evaluation and robustness experiments.

---

## 1. Prompt Robustness

### Evaluating the Robustness of Discrete Prompts

**Repository:**  
https://github.com/LivNLP/prompt-robustness

**Paper:**  
Evaluating the Robustness of Discrete Prompts

**Authors:** Yoichi Ishibashi, Danushka Bollegala, Katsuhito Sudoh,
Satoshi Nakamura

### Description

This repository contains code and experimental resources for studying the
robustness of discrete prompts.

The implementation includes experiments involving prompt learning and
analysis of the robustness of learned prompts.

### Relevance

This repository is directly relevant to prompt sensitivity because it
investigates how robust model behavior is when prompts are changed.

---

## 2. Promptfoo

### Promptfoo — LLM Evaluation Framework

**Repository:**  
https://github.com/promptfoo/promptfoo

**Website:**  
https://promptfoo.dev/

### Description

Promptfoo is an open-source CLI and library for evaluating LLM applications.
It allows users to test prompts and models systematically and compare
outputs across different prompts and test cases.

### Relevance

Promptfoo is highly relevant to this research because it can be used to
compare multiple prompt variants and evaluate whether changing a prompt
changes the quality or consistency of model outputs.

It supports side-by-side comparisons, automated scoring, and configurable
evaluation tests.

---

## 3. Hugging Face Transformers

### Transformers

**Repository:**  
https://github.com/huggingface/transformers

### Description

Transformers is an open-source machine-learning library containing
implementations of many transformer-based models and tools for natural
language processing.

### Relevance

Transformers can be used to run open-source language models and conduct
controlled prompt experiments.

Researchers can keep the model fixed while changing only the prompt and
then compare the resulting outputs.

---

## 4. EleutherAI Language Model Evaluation Harness

### lm-evaluation-harness

**Repository:**  
https://github.com/EleutherAI/lm-evaluation-harness

### Description

The Language Model Evaluation Harness is an open-source framework for
evaluating language models across standardized tasks and benchmarks.

### Relevance

It can be used to perform reproducible evaluations of language models across
multiple datasets and tasks.

This makes it useful for comparing model performance under different
evaluation conditions.

---

## 5. HELM

### Holistic Evaluation of Language Models

**Repository:**  
https://github.com/stanford-crfm/helm

### Description

HELM is a framework for holistic evaluation of language models across
multiple scenarios and metrics.

### Relevance

HELM is relevant because prompt sensitivity research requires systematic
evaluation rather than evaluating a single model response.

A framework such as HELM can help organize experiments and compare model
behavior using multiple metrics.

---

## 6. OpenAI Evals

### OpenAI Evals

**Repository:**  
https://github.com/openai/evals

### Description

OpenAI Evals is an open-source framework for evaluating LLMs and AI systems.

It provides a framework for creating and running evaluations using defined
evaluation criteria.

### Relevance

It can be used to create repeatable tests for LLM responses and investigate
whether different prompts produce different results.

---

# Comparison of Implementations

| Repository | Main Purpose | Relevance |
|---|---|---|
| prompt-robustness | Prompt robustness research | Very High |
| Promptfoo | Prompt and LLM evaluation | Very High |
| Transformers | Running transformer models | High |
| lm-evaluation-harness | Standardized LLM evaluation | High |
| HELM | Holistic LLM evaluation | High |
| OpenAI Evals | LLM evaluation framework | High |

---

# Recommended Implementation for This Research

For a practical prompt-sensitivity experiment, Promptfoo is particularly
useful because it allows multiple prompts to be evaluated against the same
test cases and provides mechanisms for comparing outputs.

A simple experimental design is:

```text
                 Test Questions
                       |
          +------------+------------+
          |            |            |
       Prompt A     Prompt B     Prompt C
          |            |            |
          +------------+------------+
                       |
                       ↓
                 Same LLM
                       |
          +------------+------------+
          |            |            |
       Output A     Output B     Output C
          |            |            |
          +------------+------------+
                       |
                       ↓
              Compare Outputs
                       |
                       ↓
             Measure Stability
