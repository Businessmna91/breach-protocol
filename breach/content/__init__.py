"""Domain registry and tier-unlock logic."""
from . import tier1, tier2, tier3

DOMAINS = tier1.DOMAINS + tier2.DOMAINS + tier3.DOMAINS
BY_ID = {d.id: d for d in DOMAINS}

TIER_LABEL = {
    1: "CLEARANCE LEVEL 1 — FUNDAMENTALS",
    2: "CLEARANCE LEVEL 2 — INFRASTRUCTURE",
    3: "CLEARANCE LEVEL 3 — SPECIALIZATION",
}


def tiers() -> dict[int, list]:
    out: dict[int, list] = {1: [], 2: [], 3: []}
    for d in DOMAINS:
        out[d.tier].append(d)
    return out


def tier_unlocked(tier: int, cleared: dict) -> bool:
    if tier == 1:
        return True
    prev = [d.id for d in DOMAINS if d.tier == tier - 1]
    return all(pid in cleared for pid in prev)
