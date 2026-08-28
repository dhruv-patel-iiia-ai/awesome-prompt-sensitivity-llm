# Tools and Libraries

This section contains useful tools and software libraries for researching
prompt sensitivity and the stability of LLM-generated research conclusions.

---

## 1. Python

**Website:**  
https://www.python.org/

### Description

Python is a general-purpose programming language widely used for artificial
intelligence, machine learning, natural language processing, and data
analysis.

### Use in This Research

Python can be used to:

- Send prompts to LLM APIs
- Store model responses
- Compare outputs from different prompts
- Calculate consistency scores
- Perform statistical analysis
- Generate graphs and visualizations

---

## 2. Hugging Face Transformers

**Repository:**  
https://github.com/huggingface/transformers

### Description

Transformers is an open-source library providing implementations and
pre-trained models for natural language processing and machine learning.

### Use in This Research

Transformers can be used to run and evaluate different language models
locally or through supported inference systems.

It can help researchers test multiple prompts using the same model and
compare the resulting outputs.

---

## 3. OpenAI API

**Documentation:**  
https://platform.openai.com/docs/

### Description

The OpenAI API provides programmatic access to OpenAI models.

### Use in This Research

The API can be used to submit multiple versions of a prompt to the same
model and collect the generated responses.

For example:

```text
Prompt A → Model → Answer A
Prompt B → Model → Answer B
Prompt C → Model → Answer C
