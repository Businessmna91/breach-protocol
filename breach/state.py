"""Progress persistence — a single JSON file under XDG data home."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

from . import config


@dataclass
class Progress:
    xp: int = 0
    cleared: dict = field(default_factory=dict)   # domain_id -> {rank, accuracy, ts}
    history: list = field(default_factory=list)   # last N run summaries

    # -- io ----------------------------------------------------------------
    @classmethod
    def load(cls) -> "Progress":
        path = config.state_dir() / config.STATE_FILE
        if not path.exists():
            return cls()
        try:
            d = json.loads(path.read_text())
            return cls(xp=int(d.get("xp", 0)),
                       cleared=dict(d.get("cleared", {})),
                       history=list(d.get("history", [])))
        except (json.JSONDecodeError, ValueError, TypeError):
            backup = path.with_suffix(".corrupt.json")
            path.replace(backup)
            return cls()

    def save(self) -> None:
        path = config.state_dir() / config.STATE_FILE
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(
            {"xp": self.xp, "cleared": self.cleared, "history": self.history[-40:]},
            indent=2))
        tmp.replace(path)

    # -- derived -----------------------------------------------------------
    @property
    def level(self) -> int:
        return self.xp // config.XP_PER_LEVEL + 1

    @property
    def xp_into_level(self) -> int:
        return self.xp % config.XP_PER_LEVEL

    def rank_of(self, domain_id: str) -> str | None:
        rec = self.cleared.get(domain_id)
        return rec["rank"] if rec else None

    # -- mutation ----------------------------------------------------------
    def record(self, domain_id: str, cleared: bool, rank: str | None,
               accuracy: float, xp_gained: int) -> bool:
        """Returns True if this run set a new personal best rank."""
        self.xp += xp_gained
        improved = False
        if cleared and rank:
            prev = self.cleared.get(domain_id)
            if not prev or config.RANK_ORDER[rank] > config.RANK_ORDER[prev["rank"]]:
                self.cleared[domain_id] = {"rank": rank,
                                           "accuracy": round(accuracy),
                                           "ts": int(time.time())}
                improved = prev is not None
            elif prev:
                pass
            if domain_id not in self.cleared:
                self.cleared[domain_id] = {"rank": rank, "accuracy": round(accuracy),
                                           "ts": int(time.time())}
        self.history.append({"domain": domain_id, "cleared": cleared, "rank": rank,
                             "accuracy": round(accuracy), "xp": xp_gained,
                             "ts": int(time.time())})
        self.save()
        return improved

    def reset(self) -> None:
        self.xp = 0
        self.cleared = {}
        self.history = []
        self.save()
