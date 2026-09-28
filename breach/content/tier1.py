"""Tier 1 — Fundamentals: Python, PowerShell, Linux."""
from ..grading import MCQ, Check, Domain, Terminal

# =============================================================== PYTHON
PY_SETUP = (
    "mkdir -p /home/agent",
    "printf 'print(\"report generated\")\\n' > /home/agent/script.py",
    "awk 'BEGIN{for(i=1;i<=240;i++) printf \"10.0.0.%d - GET /index %d\\n\", "
    "i%250, (i%7==0?500:200)}' > /home/agent/access.log",
    "awk 'BEGIN{for(i=1;i<=200000;i++) printf \"%d %s payload\\n\", i, "
    "(i%9==0?\"ERROR\":\"INFO\")}' > /home/agent/big.log",
    "rm -f /home/agent/log.txt; rm -rf /home/agent/venv; "
    "pip uninstall -y requests >/dev/null 2>&1 || true",
)

python = Domain(
    id="python", tier=1, name="Python", tagline="Core syntax, control flow, OOP",
    env="python", setup=PY_SETUP,
    questions=[
        MCQ("Which keyword defines a function in Python?",
            ["func", "def", "lambda", "method"], 1,
            "def declares a function; lambda makes small anonymous ones."),
        MCQ("What data type does {1:'a', 2:'b'} represent?",
            ["list", "tuple", "dict", "set"], 2,
            "Curly braces with key:value pairs are a dict."),
        MCQ("Which construct handles exceptions in Python?",
            ["catch/throw", "on error resume", "try/except", "rescue/end"], 2,
            "Python uses try/except (optionally else/finally)."),
        MCQ("Inside a class method, what does self refer to?",
            ["the class itself", "the instance calling the method",
             "a global variable", "nothing, it's optional"], 1,
            "self is the conventional name for the instance the method was called on."),
        MCQ("You need to read a 4 GB log line-by-line without exhausting RAM. Best approach?",
            ["file.read() then split on newlines",
             "Iterate directly over the file object with a for loop",
             "Load the whole file into a list first",
             "Use readlines() then reverse it"], 1,
            "Iterating a file object streams it line by line instead of buffering it all."),
        Terminal(
            prompt="Print the squares of 0 through 3 as a list, using a single "
                   "python3 -c one-liner with a list comprehension.",
            env="python",
            check=Check(stdout_all=("[0, 1, 4, 9]",), require_regex=(r"for\s+\w+\s+in",)),
            accepted=(r"python3? -c .*for .* in range\(4\)",),
            explain="range(4) yields 0-3; ** squares each element inside the comprehension.",
            hint="python3 -c \"print([...])\"",
            sim_output="[0, 1, 4, 9]"),
        Terminal(
            prompt="Run script.py so its output lands in log.txt instead of the screen.",
            env="python",
            check=Check(stdout_empty=True, state_cmd="cat /home/agent/log.txt",
                        state_all=("report generated",)),
            accepted=(r"python3? script\.py *> *log\.txt",),
            explain="> redirects stdout to a file, truncating it each run (>> appends).",
            hint="Redirect stdout with >",
            sim_output="(no console output — everything written to log.txt)"),
        Terminal(
            prompt="Install the requests library with pip.",
            env="python",
            check=Check(state_cmd="python3 -c 'import requests; print(requests.__name__)'",
                        state_all=("requests",)),
            accepted=(r"pip3? install .*requests",),
            explain="pip resolves the package on PyPI and installs it into the active "
                    "interpreter's site-packages.",
            hint="pip install <package>",
            sim_output="Successfully installed requests-2.32.0"),
        Terminal(
            prompt="Create a virtual environment named venv in the current directory.",
            env="python",
            check=Check(state_cmd="test -x /home/agent/venv/bin/python && echo OK",
                        state_all=("OK",)),
            accepted=(r"python3? -m venv venv",),
            explain="-m venv runs the venv module, scaffolding an isolated interpreter "
                    "so project dependencies stay project-local.",
            hint="Run the venv module with -m",
            sim_output="(venv/ created)"),
        Terminal(
            prompt="access.log has 240 lines. Using Python only (no wc, no grep), print "
                   "how many of them contain the status code 500.",
            env="python",
            check=Check(stdout_regex=r"\b34\b",
                        reject_regex=(r"\bwc\b", r"\bgrep\b")),
            accepted=(r"python3? -c .*500.*access\.log|python3? -c .*access\.log.*500",),
            explain="Counting inside Python keeps the logic portable and lets you build on "
                    "it — filtering, parsing, aggregating — without shelling out.",
            hint="Open the file, loop its lines, count the matches.",
            sim_output="34"),
    ],
    boss=[
        Terminal(
            prompt="BOSS — big.log is 200,000 lines. Print the number of lines containing "
                   "ERROR without ever holding the whole file in memory: no .read(), no "
                   ".readlines(), no shell tools.",
            env="python",
            check=Check(stdout_regex=r"\b22222\b",
                        reject_regex=(r"\.read\(\)", r"\.readlines\(\)",
                                      r"\bwc\b", r"\bgrep\b")),
            accepted=(r"python3? -c .*for .* in (open|f).*error",),
            explain="Streaming the file object one line at a time keeps memory flat no "
                    "matter how large the log gets — the difference between a script that "
                    "works on your laptop and one that survives a production log.",
            hint="sum(1 for line in open(...) if ...)",
            sim_output="22222"),
    ],
)

# =========================================================== POWERSHELL
PWSH_SETUP = (
    "New-Item -ItemType Directory -Force -Path /home/agent/data | Out-Null",
    "'alpha' | Set-Content /home/agent/notes.txt",
    "'secret' | Set-Content /home/agent/.hidden_key",
    "1..6 | ForEach-Object { 'x' * (1000 * $_) | "
    "Set-Content \"/home/agent/data/file$_.dat\" }",
    "1..40 | ForEach-Object { if ($_ % 5 -eq 0) { \"ERROR job $_ failed\" } "
    "else { \"INFO job $_ ok\" } } | Set-Content /home/agent/app.log",
    "Remove-Item -Recurse -Force /home/agent/Reports,/home/agent/files.csv "
    "-ErrorAction SilentlyContinue",
    "New-Item -ItemType Directory -Force -Path /home/agent/archive | Out-Null",
    "'old' | Set-Content /home/agent/archive/archive_2019.txt",
    "(Get-Item /home/agent/archive/archive_2019.txt).LastWriteTime = "
    "(Get-Date).AddDays(-400)",
    "'fresh' | Set-Content /home/agent/data/recent_report.txt",
)

powershell = Domain(
    id="powershell", tier=1, name="PowerShell", tagline="Cmdlets, pipeline, objects",
    env="pwsh", setup=PWSH_SETUP,
    notes="Live cmdlets run in PowerShell 7 on Linux. Windows-only modules "
          "(LocalAccounts, ActiveDirectory, Get-Service, execution policy) can't "
          "execute there, so those stay as knowledge questions.",
    questions=[
        MCQ("What symbol pipes objects between cmdlets?",
            ["&", "|", ">>", ";"], 1,
            "| passes whole objects, not text, from one cmdlet to the next — the core "
            "difference from a POSIX shell."),
        MCQ("Which cmdlet retrieves Active Directory user objects?",
            ["Get-User", "Get-ADUser", "Find-ADUser", "Get-Account"], 1,
            "Get-ADUser ships in the ActiveDirectory module (Windows / RSAT only)."),
        MCQ("What does Set-ExecutionPolicy RemoteSigned do?",
            ["Disables all scripts",
             "Allows local scripts unsigned; downloaded scripts need a signature",
             "Allows any script from anywhere", "Enables PS remoting"], 1,
            "RemoteSigned trusts locally-authored scripts but demands a signature on "
            "anything that arrived from elsewhere."),
        MCQ("Which cmdlet runs commands on a remote computer over WinRM?",
            ["Invoke-Command", "Remote-Exec", "Start-Remote", "Connect-Computer"], 0,
            "Invoke-Command runs a script block against one or many remote sessions."),
        MCQ("What does the -WhatIf parameter do?",
            ["Executes the command twice",
             "Shows what would happen without making changes",
             "Only asks for confirmation", "Logs the command to a file"], 1,
            "-WhatIf previews the effect — the safest habit to build before any "
            "destructive cmdlet."),
        Terminal(
            prompt="List everything in the current directory, including hidden files.",
            env="pwsh",
            check=Check(stdout_all=(".hidden_key", "notes.txt")),
            accepted=(r"(get-childitem|gci|ls|dir)( .*)?-force",),
            explain="Get-ChildItem hides dotfiles by default; -Force reveals hidden and "
                    "system items.",
            hint="Get-ChildItem has a switch that stops it hiding things.",
            sim_output="Mode   Length Name\n----   ------ ----\n-a---        6 .hidden_key\n"
                       "-a---        6 notes.txt"),
        Terminal(
            prompt="Show the 3 largest files in ./data, largest first.",
            env="pwsh",
            check=Check(stdout_all=("file6.dat", "file5.dat", "file4.dat"),
                        stdout_none=("file1.dat",)),
            accepted=(r"sort-object .*length .*-desc.*select.*-first 3|"
                      r"sort .*length .*-desc.*select.*-first 3",),
            explain="Sort-Object orders by any property on the object; Select-Object "
                    "-First trims the pipeline.",
            hint="Get-ChildItem | Sort-Object ... | Select-Object -First 3",
            sim_output="file6.dat\nfile5.dat\nfile4.dat"),
        Terminal(
            prompt="Create a directory named Reports in the current folder.",
            env="pwsh",
            check=Check(state_cmd="Test-Path /home/agent/Reports -PathType Container",
                        state_all=("True",)),
            accepted=(r"new-item .*-itemtype directory.*reports|mkdir reports",),
            explain="New-Item -ItemType Directory is the explicit form; mkdir is an alias "
                    "for it in PowerShell.",
            hint="New-Item -ItemType Directory -Path ...",
            sim_output="Mode  LastWriteTime  Name\nd----  9/17/2026 9:14  Reports"),
        Terminal(
            prompt="Export the name and length of every file in ./data to files.csv, "
                   "without the type-information header line.",
            env="pwsh",
            check=Check(state_cmd="Get-Content /home/agent/files.csv -Raw",
                        state_all=("Name", "file1.dat"),
                        state_none=("#TYPE",)),
            accepted=(r"export-csv.*files\.csv.*-notypeinformation|"
                      r"export-csv .*-notypeinformation.*files\.csv",),
            explain="Export-Csv serialises pipeline objects; -NoTypeInformation drops the "
                    "#TYPE line that breaks most downstream parsers.",
            hint="Get-ChildItem ./data | Select-Object Name,Length | Export-Csv ...",
            sim_output="(files.csv written)"),
        Terminal(
            prompt="Count how many lines in app.log contain ERROR.",
            env="pwsh",
            check=Check(stdout_regex=r"\b8\b"),
            accepted=(r"select-string .*error.*measure|"
                      r"get-content .*app\.log.*error.*(count|measure)",),
            explain="Select-String is PowerShell's grep; piping to Measure-Object counts "
                    "the match objects it emits.",
            hint="Select-String -Pattern ERROR | Measure-Object",
            sim_output="Count : 8"),
    ],
    boss=[
        Terminal(
            prompt="BOSS — Incident triage: list every file anywhere under the current "
                   "directory that was modified in the last 24 hours.",
            env="pwsh",
            check=Check(stdout_all=("recent_report.txt",),
                        stdout_none=("archive_2019.txt",)),
            accepted=(r"get-childitem .*-recurse.*where-object.*lastwritetime.*"
                      r"(adddays\(-1\)|addhours\(-24\))",),
            explain="Recurse walks the tree, Where-Object filters on LastWriteTime — the "
                    "same shape you'd use to spot recently tampered files on a host.",
            hint="Get-ChildItem -Recurse -File | Where-Object { $_.LastWriteTime -gt "
                 "(Get-Date).AddDays(-1) }",
            sim_output="recent_report.txt"),
    ],
)

# ================================================================ LINUX
LINUX_SETUP = (
    "mkdir -p /home/agent/scripts /var/log/app",
    "printf 'personal notes\\n' > /home/agent/notes.txt",
    "printf 'KEY=abc123\\n' > /home/agent/.hidden_key",
    "printf '#!/bin/bash\\necho deploying\\n' > /home/agent/scripts/deploy.sh",
    "chmod 644 /home/agent/scripts/deploy.sh",
    "printf 'fresh data\\n' > /home/agent/recent_report.txt",
    "printf 'old data\\n' > /home/agent/archive_2019.txt",
    "touch -d '3 days ago' /home/agent/archive_2019.txt",
    "seq 1 120 | sed 's/^/line /' > /var/log/auth.log",
    "sed -i '1s/.*/boot sequence start/' /var/log/auth.log",
    "for n in 12 30 44 61 77 95 118; do "
    "sed -i \"${n}s/.*/FAILED login attempt for user root/\" /var/log/auth.log; done",
    "sed -i '120s/.*/session closed for user root/' /var/log/auth.log",
    "printf 'FAILED but this file is not a .log\\n' > /var/log/notes.txt",
    "printf 'service restart FAILED\\n' > /var/log/app/debug.log",
    "mkdir -p /usr/local/bin && printf '#!/bin/sh\\n' > /usr/local/bin/sshd-helper",
)

linux = Domain(
    id="linux", tier=1, name="Linux", tagline="Shell, permissions, processes",
    env="linux", setup=LINUX_SETUP,
    questions=[
        MCQ("What does chmod 750 file.sh grant?",
            ["Owner rwx, group r-x, others none", "Owner rw, group rw, others rw",
             "Full access for everyone", "Read-only for all"], 0,
            "7=rwx (owner), 5=r-x (group), 0=none (others)."),
        MCQ("Which command shows filesystem space usage in human-readable units?",
            ["df -h", "du space", "disk -status", "free -m"], 0,
            "df reports per-filesystem usage; du sums the size of a directory tree."),
        MCQ("What does `systemctl status <service>` do?",
            ["Starts the service", "Reports state plus recent journal lines",
             "Stops the service", "Removes the unit file"], 1,
            "status is read-only — it reports state and tails the unit's recent logs."),
        MCQ("Which is the safest first move when a process is misbehaving?",
            ["kill -9 immediately", "Send SIGTERM first and let it clean up",
             "Reboot the host", "Delete the binary"], 1,
            "SIGTERM lets a process flush buffers and release locks; SIGKILL (-9) gives "
            "it no chance to do either."),
        Terminal(
            prompt="Show a detailed long-format listing of the current directory, "
                   "including hidden files.",
            env="linux",
            check=Check(stdout_all=(".hidden_key", "notes.txt"),
                        stdout_regex=r"^[-dl][rwx-]{9}"),
            accepted=(r"ls -(la|al|lah|alh)",),
            explain="-l gives the long format (permissions, owner, size); -a includes "
                    "dotfiles.",
            hint="Two flags on ls.",
            sim_output="-rw-r--r-- 1 root root 11 Sep 17 09:12 .hidden_key\n"
                       "-rw-r--r-- 1 root root 15 Sep 17 09:12 notes.txt"),
        Terminal(
            prompt="Search recursively under /var/log for the word FAILED, but only "
                   "inside files named *.log.",
            env="linux",
            check=Check(stdout_all=("auth.log", "FAILED"),
                        stdout_none=("notes.txt",)),
            accepted=(r"grep -r.*failed.*/var/log.*--include=.?\*\.log",),
            explain="-r recurses; --include restricts which filenames grep will open — "
                    "without it you also pull in /var/log/notes.txt.",
            hint="grep -r PATTERN PATH --include=...",
            sim_output="/var/log/auth.log:12:FAILED login attempt for user root"),
        Terminal(
            prompt="List every regular file under /home modified in the last 60 minutes.",
            env="linux",
            check=Check(stdout_all=("recent_report.txt",),
                        stdout_none=("archive_2019.txt",)),
            accepted=(r"find /home .*-mmin -60",),
            explain="-mmin -60 means 'modified fewer than 60 minutes ago'; -type f "
                    "restricts it to regular files.",
            hint="find /home -mmin ...",
            sim_output="/home/agent/recent_report.txt"),
        Terminal(
            prompt="Give scripts/deploy.sh permissions: owner rwx, group r-x, "
                   "others nothing.",
            env="linux",
            check=Check(state_cmd="stat -c %a /home/agent/scripts/deploy.sh",
                        state_regex=r"^750$"),
            accepted=(r"chmod (750|u=rwx,g=rx,o=) .*deploy\.sh",),
            explain="Octal 750 maps directly to rwx/r-x/---; the symbolic form "
                    "u=rwx,g=rx,o= does the same thing.",
            hint="chmod <octal> <file>",
            sim_output="(no output = success)"),
        Terminal(
            prompt="Show only the last 20 lines of /var/log/auth.log.",
            env="linux",
            check=Check(stdout_all=("session closed for user root",),
                        stdout_none=("boot sequence start",),
                        reject_regex=(r"^cat\b",)),
            accepted=(r"tail -n? ?20 /var/log/auth\.log",),
            explain="tail -n 20 reads from the end — essential when the file is too big "
                    "to cat.",
            hint="tail -n <count> <file>",
            sim_output="line 101\n...\nsession closed for user root"),
        Terminal(
            prompt="Print the number of lines in /var/log/auth.log that mention FAILED.",
            env="linux",
            check=Check(stdout_regex=r"^\s*7\s*$"),
            accepted=(r"grep -c.*fail.*auth\.log",
                      r"grep .*fail.*auth\.log.*\| *wc -l"),
            explain="grep -c counts matching lines directly; piping to wc -l is the "
                    "long way round to the same number.",
            hint="grep has a counting flag.",
            sim_output="7"),
    ],
    boss=[
        Terminal(
            prompt="BOSS — You suspect this host has been tampered with. Find every "
                   "regular file under /usr that was modified in the last 24 hours. "
                   "One of them does not belong.",
            env="linux",
            check=Check(stdout_all=("sshd-helper",),
                        stdout_none=("/usr/bin/ls",)),
            accepted=(r"find /usr .*-(mtime -1|mmin -1440)",),
            explain="Freshly written binaries in system paths are a classic persistence "
                    "signal. find -mtime -1 surfaces them in seconds — here, a planted "
                    "sshd-helper sitting in /usr/local/bin.",
            hint="find /usr -type f -mtime -1",
            sim_output="/usr/local/bin/sshd-helper"),
    ],
)

DOMAINS = [python, powershell, linux]
