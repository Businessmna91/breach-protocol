"""The game loop: map, dungeon runs, encounters, scoring."""
from __future__ import annotations

from . import config, content, sandbox, ui
from .grading import Terminal, grade_live, grade_sim
from .state import Progress


# ------------------------------------------------------------------- map
def draw_map(progress: Progress, env_status: dict) -> None:
    ui.banner()
    ui.header(progress)
    index: dict[str, object] = {}
    n = 0
    for tier, domains in content.tiers().items():
        unlocked = content.tier_unlocked(tier, progress.cleared)
        label = content.TIER_LABEL[tier]
        lock = "" if unlocked else f"  {ui.GREY}— locked until level {tier - 1} is cleared{ui.RESET}"
        print(f"\n {ui.BOLD}{label}{ui.RESET}{lock}")
        for d in domains:
            n += 1
            index[str(n)] = d if unlocked else None
            rec = progress.cleared.get(d.id)
            if not unlocked:
                badge = f"{ui.GREY}locked{ui.RESET}"
            elif rec:
                badge = f"{ui.AMBER}CLEARED · RANK {rec['rank']}{ui.RESET}"
            else:
                badge = f"{ui.GREY}not cleared{ui.RESET}"
            mode = env_status.get(d.id, "")
            name_color = ui.GREY if not unlocked else ui.RESET
            print(f"   {ui.BOLD}{n}{ui.RESET}) {name_color}{d.name:<16}{ui.RESET}"
                  f"{ui.GREY}{d.tagline:<34}{ui.RESET}{mode} {badge}")
    print()
    print(ui.rule())
    print(f" {ui.GREY}enter a number to start a run  ·  "
          f"'s' status  ·  'r' reset progress  ·  'q' quit{ui.RESET}")
    draw_map.index = index          # type: ignore[attr-defined]


def env_status_map(live_envs: dict) -> dict:
    out = {}
    for d in content.DOMAINS:
        if d.env is None:
            out[d.id] = f"{ui.BLUE}[QUIZ]{ui.RESET}   "
        elif live_envs.get(d.env):
            out[d.id] = f"{ui.GREEN}[LIVE]{ui.RESET}   "
        else:
            out[d.id] = f"{ui.AMBER}[SIM]{ui.RESET}    "
    return out


def probe_envs(log=print) -> dict:
    """Which sandbox flavours can actually execute on this machine right now."""
    if not sandbox.docker_available():
        return {k: False for k in config.ENVS}
    return {k: sandbox.image_present(env.image) for k, env in config.ENVS.items()}


# ------------------------------------------------------------- encounters
def show_frame(domain, ch, idx: int, total: int, hp: int, live: bool) -> None:
    ui.clear()
    stage = ""
    if getattr(ch, "boss", False):
        stage = " — BOSS" + (f" {ch.stage[0]}/{ch.stage[1]}" if ch.stage else "")
    print(ui.rule("═"))
    print(f" {ui.BOLD}{domain.name.upper()}{ui.RESET}{ui.RED}{stage}{ui.RESET}"
          f"   {ui.GREY}encounter {idx}/{total}{ui.RESET}")
    print(ui.integrity_line(hp))
    if ch.kind == "terminal":
        badge = (f"{ui.GREEN}LIVE EXECUTION{ui.RESET}" if live
                 else f"{ui.AMBER}SIMULATED — command is pattern-checked, not run{ui.RESET}")
        print(f" {ui.GREY}mode:{ui.RESET} {badge}")
    print(ui.rule("═"))
    print()
    print(ui.wrap(ch.prompt, "   "))
    print()


def ask_mcq(ch) -> bool | None:
    for i, opt in enumerate(ch.options):
        print(f"   {ui.BOLD}{i + 1}{ui.RESET}) {opt}")
    while True:
        raw = ui.ask(f"\n   {ui.BLUE}choose 1-{len(ch.options)}{ui.RESET} "
                     f"{ui.GREY}(:abort to leave){ui.RESET} > ").strip().lower()
        if raw in (":abort", ":quit", "q"):
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(ch.options):
            return int(raw) - 1 == ch.answer
        print(f"   {ui.GREY}enter a number{ui.RESET}")


def ask_terminal(ch: Terminal, box, live: bool, hp_ref: list) -> bool | None:
    env = config.ENVS[ch.env]
    print(f"   {ui.GREY}:hint (-{config.HINT_COST} integrity)   "
          f"!<command> scouts without being graded   :abort leaves the run{ui.RESET}\n")
    while True:
        raw = ui.ask(f"   {ui.MAGENTA}{env.prompt}{ui.RESET}").strip()
        if not raw:
            continue
        low = raw.lower()
        if low in (":abort", ":quit"):
            return None
        if low == ":hint":
            hp_ref[0] = max(0, hp_ref[0] - config.HINT_COST)
            print(f"   {ui.AMBER}hint:{ui.RESET} {ch.hint or 'no hint for this one'}")
            print(f"   {ui.GREY}integrity now {hp_ref[0]}/100{ui.RESET}\n")
            if hp_ref[0] <= 0:
                return False
            continue
        if raw.startswith("!"):
            scout = raw[1:].strip()
            if not scout:
                continue
            if live and box:
                res = box.exec(scout)
                _print_output(res.combined, res.exit_code)
            else:
                print(f"   {ui.GREY}scouting needs live execution — not available "
                      f"for this domain right now{ui.RESET}\n")
            continue

        # graded attempt
        if live and box:
            res = box.exec(raw)
            _print_output(res.combined, res.exit_code)
            ok, reason = grade_live(ch, raw, res, box)
        else:
            ok, reason = grade_sim(ch, raw)
            if ok and ch.sim_output:
                _print_output(ch.sim_output, 0)
        if not ok and reason:
            print(f"   {ui.GREY}{reason}{ui.RESET}")
        return ok


def _print_output(text: str, exit_code: int) -> None:
    print()
    print(f"   {ui.GREY}┌─ output {'─' * 40}{ui.RESET}")
    body = text if text.strip() else "(no output)"
    for line in body.splitlines()[:40]:
        print(f"   {ui.GREY}│{ui.RESET} {line}")
    extra = max(0, len(body.splitlines()) - 40)
    if extra:
        print(f"   {ui.GREY}│ ... {extra} more lines{ui.RESET}")
    code_color = ui.GREEN if exit_code == 0 else ui.RED
    print(f"   {ui.GREY}└─ exit {code_color}{exit_code}{ui.RESET}\n")


# ------------------------------------------------------------------- run
def run_domain(domain, progress: Progress, live_envs: dict) -> None:
    seq = domain.sequence()
    total = len(seq)
    hp = [config.MAX_INTEGRITY]
    correct = 0
    box = None
    live = False

    if domain.env:
        ui.clear()
        print(f"\n  {ui.BOLD}{domain.name}{ui.RESET} — preparing sandbox\n")
        if live_envs.get(domain.env):
            box = sandbox.Sandbox(config.ENVS[domain.env])
            print("  spinning up a throwaway container...")
            live = box.start(log=lambda m: print(m))
            if live:
                print("  seeding the scenario...")
                box.setup(domain.setup)
                print(f"  {ui.GREEN}live execution ready{ui.RESET}")
            else:
                print(f"  {ui.AMBER}falling back to simulated mode{ui.RESET}")
                box = None
        else:
            print(f"  {ui.AMBER}image not built — running this domain in "
                  f"simulated mode{ui.RESET}")
        if domain.notes:
            print()
            print(ui.wrap(f"{ui.GREY}{domain.notes}{ui.RESET}", "  "))
        ui.pause()

    aborted = False
    try:
        for i, ch in enumerate(seq, start=1):
            if live and box and getattr(ch, "setup", ()):
                box.setup(ch.setup)
            show_frame(domain, ch, i, total, hp[0], live)
            if ch.kind == "mcq":
                ok = ask_mcq(ch)
            else:
                ok = ask_terminal(ch, box, live, hp)
            if ok is None:
                aborted = True
                break
            if ok:
                correct += 1
                print(f"\n   {ui.GREEN}✓ correct{ui.RESET}")
            else:
                hp[0] = max(0, hp[0] - config.INTEGRITY_LOSS)
                print(f"\n   {ui.RED}✗ wrong — {config.INTEGRITY_LOSS} integrity"
                      f"{ui.RESET}  {ui.GREY}({hp[0]}/100 left){ui.RESET}")
            print(ui.wrap(f"{ui.GREY}{ch.explain}{ui.RESET}", "   "))
            if hp[0] <= 0:
                ui.pause()
                break
            ui.pause()
    finally:
        if box:
            box.stop()

    if aborted:
        return
    finish(domain, progress, correct, total, hp[0] > 0)


def finish(domain, progress: Progress, correct: int, total: int, survived: bool) -> None:
    ui.clear()
    accuracy = 100.0 * correct / total if total else 0.0
    if not survived:
        progress.record(domain.id, False, None, accuracy, 0)
        print(f"\n   {ui.RED}{ui.BOLD}INTEGRITY DEPLETED{ui.RESET}\n")
        print(ui.wrap(f"{domain.name} run ended early. Nothing lost — your XP and "
                      f"cleared badges are untouched. Come back when you're ready.", "   "))
        ui.pause("press Enter to return to the map")
        return

    rank = config.rank_for(accuracy)
    gained = correct * config.XP_PER_CORRECT + config.XP_CLEAR_BONUS
    improved = progress.record(domain.id, True, rank, accuracy, gained)
    print(f"\n   {ui.AMBER}{ui.BOLD}RANK {rank}{ui.RESET}   "
          f"{ui.BOLD}{domain.name} CLEARED{ui.RESET}\n")
    print(f"   {correct}/{total} correct  ·  {accuracy:.0f}% accuracy  ·  "
          f"{ui.BLUE}+{gained} XP{ui.RESET}")
    best = progress.cleared[domain.id]["rank"]
    if improved:
        print(f"   {ui.GREEN}new personal best{ui.RESET}")
    elif best != rank:
        print(f"   {ui.GREY}personal best stays at rank {best}{ui.RESET}")
    if rank != "S":
        print(f"\n   {ui.GREY}S rank needs a flawless run — replay any time.{ui.RESET}")
    newly = [t for t in (2, 3)
             if content.tier_unlocked(t, progress.cleared)
             and all(progress.cleared.get(d.id) for d in content.tiers()[t - 1])]
    if newly:
        top = max(newly)
        print(f"\n   {ui.MAGENTA}clearance level {top} available{ui.RESET}")
    ui.pause("press Enter to return to the map")


# ------------------------------------------------------------------ shell
def status_screen(progress: Progress, live_envs: dict) -> None:
    ui.clear()
    ui.header(progress)
    print(f"\n {ui.BOLD}EXECUTION ENVIRONMENTS{ui.RESET}\n")
    if not sandbox.docker_available():
        print(f"   {ui.RED}docker is not reachable{ui.RESET} — every terminal domain "
              f"will run in simulated mode.")
        print(f"   {ui.GREY}start Docker Desktop (with WSL integration) or the docker "
              f"service, then run ./setup.sh{ui.RESET}")
    else:
        for key, env in config.ENVS.items():
            ok = live_envs.get(key)
            mark = f"{ui.GREEN}ready{ui.RESET}" if ok else f"{ui.AMBER}image missing{ui.RESET}"
            print(f"   {key:<8} {ui.GREY}{env.image:<24}{ui.RESET} {mark}")
        print(f"\n   {ui.GREY}missing images? run ./setup.sh{ui.RESET}")
    print(f"\n {ui.BOLD}RECENT RUNS{ui.RESET}\n")
    for h in progress.history[-8:][::-1]:
        r = h["rank"] or "—"
        state = f"{ui.AMBER}rank {r}{ui.RESET}" if h["cleared"] else f"{ui.RED}failed{ui.RESET}"
        print(f"   {content.BY_ID[h['domain']].name:<16} {state:<22}"
              f"{ui.GREY}{h['accuracy']}%  +{h['xp']} XP{ui.RESET}")
    if not progress.history:
        print(f"   {ui.GREY}nothing yet{ui.RESET}")
    ui.pause()


def main_loop() -> None:
    progress = Progress.load()
    ui.clear()
    print("\n  probing execution environments...")
    live_envs = probe_envs()
    while True:
        draw_map(progress, env_status_map(live_envs))
        choice = ui.ask(f"\n {ui.BLUE}>{ui.RESET} ").strip().lower()
        if choice in ("q", ":quit", "quit", "exit"):
            print(f"\n {ui.GREY}session closed.{ui.RESET}\n")
            return
        if choice == "s":
            status_screen(progress, live_envs)
            continue
        if choice == "r":
            confirm = ui.ask(f" {ui.RED}erase all XP, ranks and badges? type YES{ui.RESET} > ")
            if confirm.strip() == "YES":
                progress.reset()
            continue
        domain = getattr(draw_map, "index", {}).get(choice)
        if domain is None:
            continue
        run_domain(domain, progress, live_envs)
        live_envs = probe_envs()
