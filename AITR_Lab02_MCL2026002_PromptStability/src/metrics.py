"""Evaluation metrics (protocol v1, section 7). Pure Python, no numpy needed.

Labels are strings: "yes" | "no" | "maybe" | "invalid".
"""
import math
import random
from collections import Counter
from itertools import combinations

GOLD_LABELS = ("yes", "no", "maybe")
ALL_LABELS = GOLD_LABELS + ("invalid",)


# ---------- accuracy-type metrics ----------
def accuracy(gold, pred):
    if len(gold) != len(pred) or not gold:
        raise ValueError("gold and pred must be non-empty and the same length")
    return sum(g == p for g, p in zip(gold, pred)) / len(gold)


def macro_f1(gold, pred, labels=GOLD_LABELS):
    """Mean F1 over the gold classes. An "invalid" prediction is a miss for its gold class
    and a false positive for no class (unlike sklearn, which would add it as a fourth class)."""
    if len(gold) != len(pred) or not gold:
        raise ValueError("gold and pred must be non-empty and the same length")
    f1s = []
    for c in labels:
        tp = sum(g == c and p == c for g, p in zip(gold, pred))
        fp = sum(g != c and p == c for g, p in zip(gold, pred))
        fn = sum(g == c and p != c for g, p in zip(gold, pred))
        f1s.append(0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
    return sum(f1s) / len(f1s)


def maxp_avgp_cps(per_prompt_scores):
    """Mizrahi et al. [13]: MaxP, AvgP and CPS = MaxP * (1 - (MaxP - AvgP))."""
    maxp = max(per_prompt_scores)
    avgp = sum(per_prompt_scores) / len(per_prompt_scores)
    return {"MaxP": maxp, "AvgP": avgp, "CPS": maxp * (1 - (maxp - avgp))}


# ---------- aggregation ----------
def majority_vote(labels, tie_break):
    """Most common valid label. Invalid labels do not vote. A tie, or no valid label, returns tie_break."""
    votes = Counter(l for l in labels if l != "invalid")
    if not votes:
        return tie_break
    top = votes.most_common()
    if len(top) > 1 and top[0][1] == top[1][1]:
        return tie_break
    return top[0][0]


# ---------- disagreement / stability ----------
def gini(labels, categories=ALL_LABELS):
    n = len(labels)
    if n == 0:
        raise ValueError("empty label list")
    c = Counter(labels)
    unknown = set(c) - set(categories)
    if unknown:
        raise ValueError(f"unknown labels {unknown}")
    return 1.0 - sum((c[k] / n) ** 2 for k in categories)


def decompose(labels_by_prompt, categories=ALL_LABELS):
    """Per-item split G = W + B (exact for equal group sizes).

    labels_by_prompt: {prompt_id: [labels of that prompt's k samples]}.
    W = mean within-prompt Gini; B = mean squared distance of each prompt's distribution from the pooled one.
    """
    groups = list(labels_by_prompt.values())
    sizes = {len(g) for g in groups}
    if len(sizes) != 1 or 0 in sizes:
        raise ValueError(f"all prompts need the same non-zero number of samples, got {sizes}")
    k = sizes.pop()
    dists = [[Counter(g)[c] / k for c in categories] for g in groups]
    pooled = [sum(d[i] for d in dists) / len(dists) for i in range(len(categories))]
    W = sum(1 - sum(x * x for x in d) for d in dists) / len(dists)
    B = sum(sum((d[i] - pooled[i]) ** 2 for i in range(len(categories))) for d in dists) / len(dists)
    G = gini([l for g in groups for l in g], categories)
    return {"G": G, "W": W, "B": B}


def bias_corrected_W(labels_by_prompt, categories=ALL_LABELS):
    """Sensitivity analysis (protocol v1 section 8): W multiplied by k/(k-1)."""
    k = len(next(iter(labels_by_prompt.values())))
    return decompose(labels_by_prompt, categories)["W"] * k / (k - 1)


def s_prompt(items):
    """items: list of {prompt_id: [labels]} (one per item). Returns sum(B)/sum(G), or nan if sum(G) == 0."""
    parts = [decompose(it) for it in items]
    sg = sum(p["G"] for p in parts)
    return float("nan") if sg == 0 else sum(p["B"] for p in parts) / sg


def conclusion_stability(labels):
    """Review Eq. 4 with D = 0/1 label mismatch: 1 - mean mismatch over all pairs."""
    n = len(labels)
    if n < 2:
        raise ValueError("need at least two outputs")
    pairs = list(combinations(labels, 2))
    return 1 - sum(a != b for a, b in pairs) / len(pairs)


# ---------- uncertainty and tests ----------
def bootstrap_ci(units, stat_fn, n_resamples=2000, seed=7, alpha=0.05):
    """Percentile bootstrap over units (items). stat_fn(list_of_units) -> float. Returns (point, low, high)."""
    rng = random.Random(seed)
    point = stat_fn(units)
    stats = []
    for _ in range(n_resamples):
        s = stat_fn([units[rng.randrange(len(units))] for _ in units])
        if not math.isnan(s):
            stats.append(s)
    stats.sort()
    lo = stats[int(math.floor(alpha / 2 * (len(stats) - 1)))]
    hi = stats[int(math.ceil((1 - alpha / 2) * (len(stats) - 1)))]
    return point, lo, hi


def permutation_test_B(items, n_perm=1000, seed=11):
    """One-sided test of sum(B) against shuffling prompt labels within each item.

    Returns (observed sum B, p) with p = (1 + #{perm >= observed}) / (1 + n_perm).
    """
    rng = random.Random(seed)
    observed = sum(decompose(it)["B"] for it in items)
    flat = [(list(it.keys()), [l for g in it.values() for l in g], len(next(iter(it.values())))) for it in items]
    count = 0
    for _ in range(n_perm):
        total = 0.0
        for keys, labels, k in flat:
            shuffled = labels[:]
            rng.shuffle(shuffled)
            total += decompose({key: shuffled[i * k:(i + 1) * k] for i, key in enumerate(keys)})["B"]
        count += total >= observed - 1e-12
    return observed, (1 + count) / (1 + n_perm)


def mcnemar_exact(correct_a, correct_b):
    """Exact two-sided McNemar on paired booleans. Returns (b, c, p): b = A right & B wrong, c = A wrong & B right."""
    b = sum(x and not y for x, y in zip(correct_a, correct_b))
    c = sum(y and not x for x, y in zip(correct_a, correct_b))
    n = b + c
    if n == 0:
        return b, c, 1.0
    tail = sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n
    return b, c, min(1.0, 2 * tail)


def holm(pvalues):
    """Holm step-down adjusted p-values, returned in the input order."""
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adj, running = [0.0] * m, 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvalues[i])
        adj[i] = min(1.0, running)
    return adj


def cohen_kappa(a, b):
    if len(a) != len(b) or not a:
        raise ValueError("ratings must be non-empty and the same length")
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)
