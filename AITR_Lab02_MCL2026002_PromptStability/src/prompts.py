"""Prompt construction (protocol v1, section 1). Returns chat messages; the model's chat template is applied later."""
from pathlib import Path

from src.data import Item, format_context

ROOT = Path(__file__).resolve().parents[1]


def load_prompts(path=ROOT / "configs" / "prompts.yaml"):
    import yaml
    return yaml.safe_load(open(path))


def available_prompt_ids(prompts):
    return sorted(k for k, v in prompts["prompts"].items() if isinstance(v, str))


def build_messages(item: Item, prompt_id: str, prompts: dict):
    """Chat messages for one PubMedQA item.

    prompt_id: "P0".."P5" (evidence + question) or "question_only" (question, no evidence).
    Raises if the authors' conclusion (long_answer) would appear in the prompt.
    """
    if prompt_id == "question_only":
        user = prompts["question_only"].format(question=item.question)
    else:
        template = prompts["prompts"].get(prompt_id)
        if not isinstance(template, str):
            raise KeyError(f"prompt {prompt_id!r} is not defined in prompts.yaml")
        user = template.format(context=format_context(item.contexts), question=item.question)
    if item.long_answer.strip() and item.long_answer.strip() in user:
        raise ValueError(f"{item.pubid}: long_answer found in prompt {prompt_id}")
    return [{"role": "system", "content": prompts["system"]}, {"role": "user", "content": user}]


def build_gsm8k_messages(problem: dict, prompts: dict):
    """Chat messages for one GSM8K problem (dict from data.load_gsm8k)."""
    return [{"role": "system", "content": prompts["gsm8k_system"]},
            {"role": "user", "content": prompts["gsm8k_cot"].format(question=problem["question"])}]
