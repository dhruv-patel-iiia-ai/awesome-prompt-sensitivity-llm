# Datasets and Benchmarks

This collection contains datasets and benchmarks that can be used to study
Large Language Model (LLM) performance, prompt sensitivity, reasoning
stability, truthfulness, and reliability.

These resources are useful for experiments in which the same task is given
to an LLM using different prompt formulations and the resulting outputs are
compared.

---

## 1. BIG-bench

**Full Name:** Beyond the Imitation Game Benchmark (BIG-bench)

**Source:** Google Research / BIG-bench

**Link:**  
https://github.com/google/BIG-bench

### Description

BIG-bench is a large collaborative benchmark containing more than 200 tasks
designed to evaluate and probe the capabilities and limitations of language
models.

The benchmark covers diverse areas including reasoning, mathematics,
language understanding, common sense, science, and other capabilities.

### Use in This Research

BIG-bench can be used to evaluate whether different prompt formulations
produce different performance levels across a broad range of tasks.

For example, the same BIG-bench task can be evaluated using multiple
semantically equivalent prompts and the resulting scores can be compared.

---

## 2. MMLU

**Full Name:** Measuring Massive Multitask Language Understanding

**Source:** Hendrycks et al.

**Link:**  
https://github.com/hendrycks/test

### Description

MMLU is a benchmark designed to evaluate language models across many
different subjects, including humanities, social sciences, STEM, and other
knowledge areas.

### Use in This Research

MMLU can be used to investigate whether prompt wording and prompt structure
affect model performance across different academic subjects.

Researchers can compare model answers obtained from different versions of
the same question prompt.

---

## 3. TruthfulQA

**Full Name:** TruthfulQA: Measuring How Models Mimic Human Falsehoods

**Source:** Lin, Hilton, and Evans

**Link:**  
https://github.com/sylinrl/TruthfulQA

### Description

TruthfulQA is a benchmark designed to measure whether language models
generate truthful answers rather than reproducing common human
misconceptions.

The benchmark includes questions together with reference answers and
evaluation methods.

### Use in This Research

TruthfulQA is particularly relevant to the reliability aspect of this
research.

Different prompt formulations can be used for the same question to
investigate whether prompt changes affect the truthfulness and consistency
of generated answers.

---

## 4. PubMedQA

**Full Name:** PubMedQA: A Dataset for Biomedical Research Question Answering

**Source:** Jin et al.

**Link:**  
https://github.com/pubmedqa/pubmedqa

### Description

PubMedQA is a biomedical question-answering dataset based on research
articles from PubMed.

The dataset contains research questions and answers categorized into
different answer types.

### Use in This Research

PubMedQA is useful for studying prompt sensitivity in scientific and
research-oriented question answering.

Different prompts can be applied to the same biomedical research question
to determine whether the generated conclusion remains stable.

---

## 5. GSM8K

**Full Name:** Grade School Math 8K

**Source:** OpenAI Research

**Link:**  
https://github.com/openai/grade-school-math

### Description

GSM8K is a dataset of approximately 8.5K grade-school mathematical word
problems designed to evaluate multi-step mathematical reasoning.

### Use in This Research

GSM8K can be used to investigate the effect of prompt formulation on
reasoning performance.

For example, researchers can compare direct prompting, chain-of-thought
prompting, and alternative equivalent instructions and measure whether the
final answers remain consistent.

---

## 6. ARC

**Full Name:** AI2 Reasoning Challenge

**Source:** Allen Institute for AI

**Link:**  
https://allenai.org/data/arc

### Description

The AI2 Reasoning Challenge is a dataset designed to evaluate advanced
question-answering and reasoning capabilities.

It contains grade-school science questions that require reasoning rather
than simple retrieval.

### Use in This Research

ARC can be used to study whether changes in prompt wording influence
scientific reasoning performance and answer consistency.

---

# Recommended Experimental Use

The datasets above can be used to construct a prompt-sensitivity
experiment.

A basic experimental procedure is:

1. Select questions from a benchmark.
2. Create multiple semantically equivalent prompts.
3. Send the prompts to the same LLM.
4. Record all generated answers.
5. Compare the answers across prompt variants.
6. Measure answer consistency.
7. Analyze whether the final research conclusion changes.

For example:

```text
Question:
What is the primary cause of X?

Prompt A:
What is the primary cause of X?

Prompt B:
Explain the main reason that causes X.

Prompt C:
What factor is primarily responsible for X?
