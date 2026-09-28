# Breach Protocol — Terminal Edition

A boot.dev-style learning RPG that runs entirely in your terminal, where the
terminal challenges execute **real commands against real sandboxed
environments** — not a scripted fake shell.

9 domains across 3 tiers. Integrity (HP) resets to 100 each run; a wrong
answer costs 20; hitting 0 ends the run with no progress lost. Clearing a
domain earns a rank (S/A/B/C, by accuracy) and a permanent badge. XP and
badges persist in `~/.local/share/breach-protocol/progress.json`.

## What's actually live vs. simulated

| Domain          | Tier | Execution                                             |
|------------------|------|--------------------------------------------------------|
| Python           | 1    | **Live** — real `python3` in a container               |
| PowerShell       | 1    | **Live** — real PowerShell 7 (`pwsh`) in a container*   |
| Linux            | 1    | **Live** — real bash/coreutils in a container           |
| Docker           | 2    | **Live** — real `docker` CLI against a nested, isolated daemon (your host Docker is never touched) |
| IAM              | 2    | **Live** — real AWS CLI v2 against LocalStack (fake AWS, no account, no bill) |
| Cloud Security   | 2    | **Live** — same, LocalStack S3/IAM                      |
| Python ML        | 3    | Scenario/multiple-choice (judgement-based topic, no terminal) |
| Web Security      | 3    | Scenario/multiple-choice, 3-stage connected boss         |
| SOC Analyst      | 3    | Scenario/multiple-choice, 3-stage connected boss         |

\* PowerShell runs PS7 on Linux, so Windows-only cmdlets (`Get-LocalUser`,
`Get-Service`, `Set-ExecutionPolicy`, anything needing Active Directory) can't
execute there — those specific questions stay multiple-choice; everything
else (pipeline, `Get-ChildItem`, `Where-Object`, `Sort-Object`, `Export-Csv`,
`Select-String`...) runs for real.

Every terminal challenge is tagged **[LIVE]** or **[SIM]** on screen, and the
map screen tags each domain the same way, so you always know which you're
getting. If Docker isn't running, or an image hasn't been built yet, that
domain automatically falls back to **[SIM]** mode: your command is checked
against accepted patterns instead of executed, so the game is still fully
playable without any setup.

## Setup

Requirements already on your machine per what you told me: Docker, AWS CLI
v2 (only used on your host to confirm it's there — the game brings its own
inside containers), Python 3.11+, WSL.

```bash
cd breach-protocol
chmod +x setup.sh
./setup.sh          # builds the 5 sandbox images (a few minutes, first time)
python3 -m breach   # launch
```

No pip packages required — the game itself is stdlib-only Python. `setup.sh`
only builds Docker images; nothing is installed onto your WSL distro or your
host.

## How execution actually works

- **Linux / Python / PowerShell**: each dungeon run starts one throwaway
  container (`--rm`), seeds it with the scenario's files/logs, and every
  command you type is run inside it via `docker exec`. The container is
  destroyed the moment the run ends, aborts, or crashes.
- **Docker**: your commands run against a **nested** Docker daemon
  (`docker:dind`, `--privileged`, isolated network) — its own images, its own
  containers. Your host Docker installation, images, and containers are
  never touched.
- **IAM / Cloud Security**: a shared `breach-localstack` container is started
  once and reused across runs (it's slow to boot, cheap to keep warm). Real
  `aws` CLI commands hit `http://breach-localstack:4566` instead of AWS —
  same API shapes, same output format, zero real infrastructure or cost.
- Everything above lives on one private Docker network (`breach-net`),
  isolated from anything else on your machine.

### Grading

Each live challenge is graded on **outcome**, not exact wording — "list
hidden files" accepts `ls -la`, `ls -A`, or anything else that actually does
it. A few challenges (e.g. "don't use `.read()`" in the Python boss) also
check the command text itself, when the point of the exercise is the
technique rather than just the result. If live execution isn't available,
the same challenge falls back to checking your command against a set of
accepted patterns (**[SIM]** mode) — clearly labeled either way.

`:hint` costs 5 integrity and shows a nudge. `!<command>` runs a command
without grading it, to poke around before committing to an answer (live
domains only). `:abort` leaves the run without penalty (no progress for that
run is recorded either).

## Uninstall / cleanup

```bash
docker rm -f breach-localstack        # if it's still running
docker network rm breach-net
docker rmi breach-linux breach-python breach-pwsh breach-dind breach-aws
rm -rf ~/.local/share/breach-protocol # wipes XP/progress
```
