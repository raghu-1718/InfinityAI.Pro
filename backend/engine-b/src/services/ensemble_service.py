from typing import Dict


def weighted_ensemble(
    components: Dict[str, float],
    weights: Dict[str, float]
) -> float:
    """
    Weighted average with normalization and safety guards.
    """
    if not components:
        return 0.0

    num, den = 0.0, 0.0

    for k, v in components.items():
        w = float(weights.get(k, 0.0))
        num += w * float(v)
        den += w

    if den > 0:
        return num / den

    # Fallback: simple mean
    return sum(components.values()) / len(components)
