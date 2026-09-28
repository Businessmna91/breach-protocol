"""Static configuration: game rules, sandbox environments, filesystem paths."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------- game rules
MAX_INTEGRITY = 100
INTEGRITY_LOSS = 20          # per wrong answer
HINT_COST = 5                # integrity cost of :hint on a terminal challenge
XP_PER_CORRECT = 15
XP_CLEAR_BONUS = 10
XP_PER_LEVEL = 100

RANK_ORDER = {"S": 4, "A": 3, "B": 2, "C": 1}


def rank_for(accuracy: float) -> str:
    if accuracy >= 100:
        return "S"
    if accuracy >= 85:
        return "A"
    if accuracy >= 60:
        return "B"
    return "C"


# ---------------------------------------------------------------- persistence
def state_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    p = Path(base) / "breach-protocol"
    p.mkdir(parents=True, exist_ok=True)
    return p


STATE_FILE = "progress.json"

# ---------------------------------------------------------------- sandboxing
NETWORK = "breach-net"
LOCALSTACK_NAME = "breach-localstack"
LOCALSTACK_IMAGE = "localstack/localstack:3"
LOCALSTACK_SERVICES = "iam,sts,s3,ec2,kms,secretsmanager,logs"

EXEC_TIMEOUT = 30            # seconds for a single graded command
SETUP_TIMEOUT = 180          # seconds for per-challenge setup


@dataclass(frozen=True)
class Env:
    """A sandbox flavour: one throwaway container per dungeon run."""

    key: str
    image: str
    shell: tuple[str, ...]          # argv prefix; user command appended as one arg
    workdir: str
    prompt: str                     # what the fake-but-real prompt looks like
    privileged: bool = False
    needs_localstack: bool = False
    boot_check: str | None = None   # command polled until exit 0 before play
    entrypoint: str | None = None   # --entrypoint override for keeping it alive
    keepalive: tuple[str, ...] = ("sleep", "infinity")
    extra_run_args: tuple[str, ...] = field(default_factory=tuple)


ENVS: dict[str, Env] = {
    "linux": Env(
        key="linux",
        image="breach-linux:latest",
        shell=("bash", "-lc"),
        workdir="/home/agent",
        prompt="agent@breach:~$ ",
    ),
    "python": Env(
        key="python",
        image="breach-python:latest",
        shell=("bash", "-lc"),
        workdir="/home/agent",
        prompt="agent@breach:~$ ",
    ),
    "pwsh": Env(
        key="pwsh",
        image="breach-pwsh:latest",
        shell=("pwsh", "-NoLogo", "-NonInteractive", "-Command"),
        workdir="/home/agent",
        prompt="PS /home/agent> ",
        entrypoint="/bin/sh",
        keepalive=("-c", "sleep infinity"),
    ),
    "docker": Env(
        key="docker",
        image="breach-dind:latest",
        shell=("sh", "-lc"),
        workdir="/work",
        prompt="agent@breach-dind:/work$ ",
        privileged=True,
        boot_check="docker info >/dev/null 2>&1",
        keepalive=(),   # image's own entrypoint starts dockerd
        extra_run_args=("-e", "DOCKER_TLS_CERTDIR="),
    ),
    "aws": Env(
        key="aws",
        image="breach-aws:latest",
        shell=("bash", "-lc"),
        workdir="/work",
        prompt="agent@breach-aws:/work$ ",
        needs_localstack=True,
        entrypoint="/bin/sh",
        keepalive=("-c", "sleep infinity"),
    ),
}
