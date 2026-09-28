"""Challenge models plus the grader.

Grading philosophy: judge the *outcome*, not the incantation. If the task was
"list hidden files", any command that actually lists them passes — `ls -la`,
`ls -A`, `find . -maxdepth 1`. Only where the exercise is about a specific
technique do we constrain the command itself (require_regex / reject_regex).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


# ------------------------------------------------------------------ models
@dataclass
class MCQ:
    prompt: str
    options: list[str]
    answer: int
    explain: str
    kind: str = "mcq"
    boss: bool = False
    stage: tuple[int, int] | None = None


@dataclass
class Check:
    """Every field that is set must hold for the answer to pass."""

    # ...against the stdout/stderr of the player's own command
    stdout_all: tuple[str, ...] = ()
    stdout_none: tuple[str, ...] = ()
    stdout_regex: str | None = None
    stdout_empty: bool = False
    exit_zero: bool = False

    # ...against the command text they typed
    require_regex: tuple[str, ...] = ()
    reject_regex: tuple[str, ...] = ()

    # ...against the state of the world afterwards
    state_cmd: str | None = None
    state_all: tuple[str, ...] = ()
    state_none: tuple[str, ...] = ()
    state_regex: str | None = None
    state_exit_zero: bool = False
    state_exit_nonzero: bool = False


@dataclass
class Terminal:
    prompt: str
    env: str
    check: Check
    explain: str
    accepted: tuple[str, ...] = ()        # regex fallback used in SIM mode
    setup: tuple[str, ...] = ()           # run in the sandbox before the challenge
    hint: str = ""
    sim_output: str = ""                  # shown instead of real output in SIM mode
    kind: str = "terminal"
    boss: bool = False
    stage: tuple[int, int] | None = None


@dataclass
class Domain:
    id: str
    name: str
    tier: int
    tagline: str
    questions: list
    boss: list
    env: str | None = None                # sandbox flavour, None = quiz only
    setup: tuple[str, ...] = ()           # run once when the dungeon run begins
    notes: str = ""
    _seq: list = field(default_factory=list, repr=False)

    def sequence(self) -> list:
        seq = list(self.questions)
        total = len(self.boss)
        for i, b in enumerate(self.boss):
            b.boss = True
            b.stage = (i + 1, total) if total > 1 else None
            seq.append(b)
        return seq


# ----------------------------------------------------------------- grading
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def grade_sim(challenge: Terminal, command: str) -> tuple[bool, str]:
    cmd = _norm(command)
    for pat in challenge.accepted:
        if re.fullmatch(pat, cmd) or re.search(pat, cmd):
            return True, ""
    return False, "command did not match an accepted solution"


def grade_live(challenge: Terminal, command: str, result, sandbox) -> tuple[bool, str]:
    """Returns (passed, reason-if-failed)."""
    c = challenge.check
    out = result.combined
    cmd = command.strip()

    for pat in c.reject_regex:
        if re.search(pat, cmd, re.I):
            return False, "that approach is off-limits for this challenge"
    for pat in c.require_regex:
        if not re.search(pat, cmd, re.I):
            return False, "the command is missing something the task asked for"

    if c.exit_zero and result.exit_code != 0:
        return False, f"command exited with status {result.exit_code}"
    if c.stdout_empty and out.strip():
        return False, "output should have gone somewhere other than the screen"
    for token in c.stdout_all:
        if token not in out:
            return False, f"expected {token!r} in the output"
    for token in c.stdout_none:
        if token in out:
            return False, f"{token!r} should not have been in the output"
    if c.stdout_regex and not re.search(c.stdout_regex, out, re.M):
        return False, "the output does not look like what the task asked for"

    if c.state_cmd:
        st = sandbox.exec(c.state_cmd)
        sout = st.combined
        if c.state_exit_zero and st.exit_code != 0:
            return False, "the environment was not left in the expected state"
        if c.state_exit_nonzero and st.exit_code == 0:
            return False, "the thing you were asked to remove is still there"
        for token in c.state_all:
            if token not in sout:
                return False, "the environment was not left in the expected state"
        for token in c.state_none:
            if token in sout:
                return False, "the environment still shows what should be gone"
        if c.state_regex and not re.search(c.state_regex, sout, re.M):
            return False, "the environment was not left in the expected state"

    return True, ""
