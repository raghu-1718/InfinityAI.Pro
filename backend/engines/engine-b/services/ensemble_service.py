def weighted_ensemble(components: dict[str, float], weights: dict[str, float]) -> float:
    num, den = 0.0, 0.0
    for k, v in components.items():
        w = float(weights.get(k, 0.0))
        num += w * v
        den += w
    return num / den if den > 0 else list(components.values())[0]
