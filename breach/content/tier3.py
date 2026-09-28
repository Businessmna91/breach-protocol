"""Tier 3 — Specialization: Python ML, Web Security, SOC Analyst.

No sandbox: these are judgement domains, so they stay scenario/multiple-choice.
Web Security and SOC Analyst end in a connected three-stage boss.
"""
from ..grading import MCQ, Domain

pyml = Domain(
    id="pyml", tier=3, name="Python ML", tagline="Data, models, evaluation",
    questions=[
        MCQ("Why split data into training and test sets?",
            ["Only to make training faster",
             "To estimate how well the model generalises to unseen data",
             "It's optional and rarely done", "To reduce storage"], 1,
            "Test data is your only honest estimate of real-world performance."),
        MCQ("What is overfitting?",
            ["Good on new data, bad on training data",
             "The model learns the training data, noise included, and fails to generalise",
             "A model that trains too fast", "A data cleaning step"], 1,
            "Overfit models memorise instead of learning the underlying pattern."),
        MCQ("Which is a supervised learning task?",
            ["Clustering customers with no labels",
             "Predicting house prices from labelled examples",
             "Dimensionality reduction", "Topic discovery in unlabelled text"], 1,
            "Supervised learning trains on paired inputs and known outputs."),
        MCQ("What does a confusion matrix show for a classifier?",
            ["Only overall accuracy",
             "The breakdown of true/false positives and negatives per class",
             "Training time", "Feature count"], 1,
            "It cross-tabs predicted against actual, exposing the error types accuracy "
            "hides."),
        MCQ("What is the purpose of cross-validation?",
            ["Speeding up training",
             "A more reliable performance estimate by testing across multiple splits",
             "Reducing features", "Visualising data"], 1,
            "K-fold averages across folds, so one lucky split can't flatter the model."),
        MCQ("A common way to handle missing values?",
            ["Discard the dataset",
             "Impute (mean/median) or drop rows, depending on how much is missing and why",
             "Always delete the column", "Duplicate existing rows"], 1,
            "The mechanism of missingness matters — data missing not at random can bias "
            "any imputation you choose."),
        MCQ("Why is data leakage dangerous in an ML pipeline?",
            ["It slows training",
             "Information from the test set influences training, inflating scores that "
             "collapse in production",
             "It only affects deep learning", "It corrupts the CSV"], 1,
            "Fitting a scaler or imputer before the split is the classic way to leak — "
            "fit on train only, then transform test."),
    ],
    boss=[
        MCQ("BOSS — Your classifier hits 99% accuracy, but 99% of the dataset is one "
            "class. What do you check first?",
            ["Celebrate, the model is great",
             "Whether accuracy is misleading — inspect precision, recall and the "
             "confusion matrix",
             "Add more epochs", "Ship it"], 1,
            "On imbalanced data a model that always predicts the majority class scores "
            "99% while detecting nothing. Precision/recall on the minority class is the "
            "number that matters."),
    ],
)

websec = Domain(
    id="websec", tier=3, name="Web Security", tagline="OWASP-style application risks",
    questions=[
        MCQ("What is Cross-Site Scripting (XSS)?",
            ["Overloading a server with traffic",
             "Injecting attacker-controlled script into pages other users view",
             "Network sniffing of cookies only", "A form of SQL injection"], 1,
            "Untrusted input reaching output unescaped lets attacker script run in the "
            "victim's session."),
        MCQ("What is SQL Injection?",
            ["Encrypting a database",
             "Untrusted input altering the structure of a SQL query",
             "A firewall bypass", "A type of XSS"], 1,
            "The bug is concatenation: data crosses into the code channel."),
        MCQ("What is CSRF?",
            ["Stealing a password directly",
             "Tricking an authenticated browser into issuing an unwanted request",
             "A denial of service attack", "An SQL exploit"], 1,
            "CSRF rides the victim's existing session — the request is authentic, the "
            "intent isn't."),
        MCQ("Why is client-side validation insufficient?",
            ["It isn't — it's enough on its own",
             "Anyone can bypass the browser and call the API directly, so the server must "
             "re-validate",
             "It slows the page down", "It only matters for file uploads"], 1,
            "Client validation is a UX feature. The server is the only trust boundary."),
        MCQ("What does a Content-Security-Policy header do?",
            ["Speeds up rendering",
             "Restricts which content sources the browser will load, limiting XSS impact",
             "Manages cookies only", "Compresses responses"], 1,
            "CSP is defence in depth: even if script is injected, the browser refuses to "
            "run it from untrusted origins."),
        MCQ("Where does Broken Access Control usually bite?",
            ["Only in login forms",
             "Authenticated endpoints that don't re-check whether *this* user owns the "
             "object being requested",
             "Only in admin panels", "Only over HTTP"], 1,
            "Changing /invoice/1001 to /invoice/1002 and getting someone else's data is "
            "IDOR — the most common variant, and consistently near the top of the OWASP "
            "Top 10."),
    ],
    boss=[
        MCQ("BOSS 1/3 — A login form concatenates user input straight into a SQL query "
            "string. What is the fix?",
            ["Add more input fields",
             "Use parameterised queries / prepared statements",
             "Disable the login page", "Encrypt only the password field"], 1,
            "Parameterisation keeps data out of the code channel, so no input can change "
            "the query's structure — escaping by hand always loses eventually."),
        MCQ("BOSS 2/3 — The SQL fix ships, but a pentest still finds reflected XSS on a "
            "search page that echoes the query back unescaped. Best fix?",
            ["Context-aware output encoding when rendering into HTML",
             "Delete the search feature", "Block the word 'script' in input",
             "Nothing, XSS isn't serious"], 0,
            "Encode on output, in the context you're rendering into. Blocklists lose to "
            "the first encoding trick an attacker tries."),
        MCQ("BOSS 3/3 — Both are fixed. Final review: no security headers, and session "
            "cookies carry no Secure or HttpOnly flags. Priority fix?",
            ["Set Secure, HttpOnly and SameSite on session cookies and add core "
             "security headers",
             "Increase cookie lifetime for convenience",
             "Drop HTTPS since it adds latency", "Ignore — cookies aren't attacker-relevant"],
            0,
            "HttpOnly keeps JavaScript away from the session cookie (so a future XSS can't "
            "steal it), Secure keeps it off plaintext connections, SameSite blunts CSRF. "
            "Layered controls, each covering the others' failures."),
    ],
)

soc = Domain(
    id="soc", tier=3, name="SOC Analyst", tagline="Triage, detection, response",
    questions=[
        MCQ("In SIEM terms, what is a false positive?",
            ["A real attack that was missed",
             "An alert that fires but turns out not to be a real threat",
             "A successful detection", "A type of malware"], 1,
            "Volume matters: enough false positives and analysts start ignoring the "
            "channel entirely."),
        MCQ("What is the first phase of the NIST incident response lifecycle?",
            ["Eradication", "Preparation", "Recovery", "Containment"], 1,
            "Preparation happens before anything goes wrong — tooling, runbooks, "
            "access, contacts."),
        MCQ("What does IOC stand for?",
            ["Internal Operations Center", "Indicator of Compromise",
             "Incident Operations Chart", "Internet Origin Check"], 1,
            "Hashes, IPs, domains, registry keys — artefacts suggesting a host was "
            "touched."),
        MCQ("Why correlate across multiple log sources?",
            ["It isn't necessary", "Single-source signals miss chains that only appear "
             "when endpoint, network and identity data are lined up on one timeline",
             "Only for compliance", "To reduce storage"], 1,
            "A failed login means little; failed logins plus a new scheduled task plus "
            "outbound traffic to a new host is a story."),
        MCQ("Why does triage severity matter?",
            ["It doesn't, all alerts are equal",
             "It focuses limited analyst time on the highest-impact threats first",
             "It's only for reporting", "Severity is set by end users"], 1,
            "Triage is queue management under scarcity — the core SOC skill."),
        MCQ("What is the risk of wiping a compromised host immediately?",
            ["None, it's always right",
             "You destroy the forensic evidence needed to scope the incident",
             "It takes too long", "It voids the warranty"], 1,
            "Contain first, preserve evidence, then eradicate — otherwise you never learn "
            "how they got in, and they come back the same way."),
    ],
    boss=[
        MCQ("BOSS 1/3 — Repeated failed logins from one IP, then a single success, then "
            "a large outbound transfer at 03:00. Most likely?",
            ["Normal maintenance",
             "A successful brute-force followed by probable exfiltration",
             "A routine software update", "User error"], 1,
            "Failure burst, then success, then anomalous volume off-hours: the classic "
            "compromise chain."),
        MCQ("BOSS 2/3 — The account is confirmed compromised. Immediate containment step?",
            ["Disable the account and force a credential reset, preserving the host",
             "Delete the user account permanently", "Wait for the next standup",
             "Email the user and move on"], 0,
            "Disabling cuts access in seconds without destroying the audit trail that "
            "deletion would take with it. Revoke active sessions and tokens too — a "
            "password reset alone won't kill a live session."),
        MCQ("BOSS 3/3 — Contained. What comes next in the NIST lifecycle?",
            ["Eradication and recovery — remove the foothold, then restore clean access",
             "Close the ticket", "Publicly announce the breach before investigating",
             "Skip to lessons learned"], 0,
            "Preparation → Detection & Analysis → Containment → Eradication → Recovery → "
            "Lessons Learned. Recovery without eradication just hands the host back."),
    ],
)

DOMAINS = [pyml, websec, soc]
