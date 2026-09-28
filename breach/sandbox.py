"""Real command execution against throwaway Docker containers.

Nothing here ever touches the host filesystem. Every dungeon run gets a fresh
container that is force-removed when the run ends (or when the process dies).
If Docker or an image is missing, the caller degrades that domain to SIM mode.
"""
from __future__ import annotations

import atexit
import os
import subprocess
import time
from dataclasses import dataclass

from . import config


@dataclass
class Result:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False

    @property
    def combined(self) -> str:
        out = self.stdout
        if self.stderr:
            out = (out + "\n" + self.stderr) if out else self.stderr
        return out.strip("\n")


def _run(argv: list[str], timeout: int = 60) -> Result:
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return Result(p.stdout, p.stderr, p.returncode)
    except subprocess.TimeoutExpired:
        return Result("", f"command timed out after {timeout}s", 124, timed_out=True)
    except FileNotFoundError:
        return Result("", "docker binary not found on PATH", 127)


# ------------------------------------------------------------------ probes
def docker_available() -> bool:
    return _run(["docker", "info"], timeout=20).exit_code == 0


def image_present(image: str) -> bool:
    return _run(["docker", "image", "inspect", image], timeout=20).exit_code == 0


def ensure_network() -> None:
    if _run(["docker", "network", "inspect", config.NETWORK], timeout=20).exit_code != 0:
        _run(["docker", "network", "create", config.NETWORK], timeout=30)


# -------------------------------------------------------------- localstack
class LocalStack:
    """Shared fake-AWS backend for the IAM and Cloud Security domains."""

    @staticmethod
    def running() -> bool:
        r = _run(["docker", "ps", "--filter", f"name=^{config.LOCALSTACK_NAME}$",
                  "--format", "{{.Names}}"], timeout=20)
        return config.LOCALSTACK_NAME in r.stdout

    @classmethod
    def start(cls, log=print) -> bool:
        ensure_network()
        if cls.running():
            return cls.wait_ready(log=log)
        _run(["docker", "rm", "-f", config.LOCALSTACK_NAME], timeout=30)
        log("  starting LocalStack (fake AWS)...")
        r = _run([
            "docker", "run", "-d", "--name", config.LOCALSTACK_NAME,
            "--network", config.NETWORK,
            "-e", f"SERVICES={config.LOCALSTACK_SERVICES}",
            "-e", "DEBUG=0", "-e", "EAGER_SERVICE_LOADING=1",
            config.LOCALSTACK_IMAGE,
        ], timeout=120)
        if r.exit_code != 0:
            log("  ! could not start LocalStack: " + r.combined.splitlines()[-1][:120])
            return False
        atexit.register(cls.stop)
        return cls.wait_ready(log=log)

    @staticmethod
    def wait_ready(timeout: int = 120, log=print) -> bool:
        deadline = time.time() + timeout
        probe = ("import urllib.request,json,sys;"
                 "d=json.load(urllib.request.urlopen("
                 "'http://localhost:4566/_localstack/health',timeout=3));"
                 "sys.exit(0 if d.get('services',{}).get('s3') in "
                 "('available','running') else 1)")
        while time.time() < deadline:
            r = _run(["docker", "exec", config.LOCALSTACK_NAME,
                      "python3", "-c", probe], timeout=15)
            if r.exit_code == 0:
                return True
            time.sleep(3)
        log("  ! LocalStack did not report healthy in time")
        return False

    @staticmethod
    def stop() -> None:
        _run(["docker", "rm", "-f", config.LOCALSTACK_NAME], timeout=60)


# ---------------------------------------------------------------- sandbox
class Sandbox:
    """One container, one dungeon run."""

    def __init__(self, env: config.Env):
        self.env = env
        self.name = f"breach-{env.key}-{os.getpid()}"
        self.live = False

    # -- lifecycle ---------------------------------------------------------
    def start(self, log=print) -> bool:
        if not docker_available():
            return False
        if not image_present(self.env.image):
            return False
        if self.env.needs_localstack and not LocalStack.start(log=log):
            return False

        ensure_network()
        _run(["docker", "rm", "-f", self.name], timeout=60)
        argv = ["docker", "run", "-d", "--rm", "--name", self.name,
                "--network", config.NETWORK, "-w", self.env.workdir]
        if self.env.privileged:
            argv.append("--privileged")
        if self.env.entrypoint:
            argv.extend(["--entrypoint", self.env.entrypoint])
        argv.extend(self.env.extra_run_args)
        argv.append(self.env.image)
        argv.extend(self.env.keepalive)

        r = _run(argv, timeout=120)
        if r.exit_code != 0:
            log("  ! container failed to start: " + r.combined.splitlines()[-1][:140])
            return False

        atexit.register(self.stop)
        if self.env.boot_check and not self._wait_boot(self.env.boot_check, log=log):
            self.stop()
            return False
        self.live = True
        return True

    def _wait_boot(self, check: str, timeout: int = 60, log=print) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.exec(check, timeout=10).exit_code == 0:
                return True
            time.sleep(2)
        log("  ! sandbox daemon did not come up in time")
        return False

    def stop(self) -> None:
        if self.name:
            _run(["docker", "rm", "-f", self.name], timeout=60)
        self.live = False

    # -- execution ---------------------------------------------------------
    def exec(self, command: str, timeout: int = config.EXEC_TIMEOUT) -> Result:
        argv = ["docker", "exec", "-i", "-w", self.env.workdir, self.name]
        argv.extend(self.env.shell)
        argv.append(command)
        return _run(argv, timeout=timeout)

    def setup(self, commands, timeout: int = config.SETUP_TIMEOUT) -> None:
        for c in commands or ():
            self.exec(c, timeout=timeout)


