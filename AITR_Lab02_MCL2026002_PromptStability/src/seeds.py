"""Seed controls used by every script (protocol v1, section 6)."""
import os
import random


def set_all_seeds(seed: int) -> None:
    """Seed Python, NumPy, PyTorch (CPU and CUDA) and transformers when they are installed."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass
    try:
        from transformers import set_seed
        set_seed(seed)
    except ImportError:
        pass


def generation_seed(item_index: int, prompt_index: int, sample_index: int) -> int:
    """Per-generation seed: 1000 * item + 10 * prompt + sample (protocol v1, section 6)."""
    return 1000 * item_index + 10 * prompt_index + sample_index
