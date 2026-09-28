"""Tier 2 — Infrastructure: Docker, IAM, Cloud Security."""
from ..grading import MCQ, Check, Domain, Terminal

# =============================================================== DOCKER
# Runs against an isolated docker-in-docker daemon: its own images, its own
# containers, no access to the host daemon.
DOCKER_SETUP = (
    "docker pull alpine:3.20 >/dev/null 2>&1",
    "docker rm -f breach-target web >/dev/null 2>&1; true",
    "docker network rm appnet >/dev/null 2>&1; true",
    "docker run -d --name breach-target alpine:3.20 "
    "sh -c 'echo \"listener bound on 0.0.0.0:9000\"; sleep 3600' >/dev/null",
    "docker run --name stale-one alpine:3.20 true >/dev/null 2>&1",
    "docker run --name stale-two alpine:3.20 true >/dev/null 2>&1",
    "mkdir -p /work/app && printf 'FROM alpine:3.20\\nCMD [\"echo\",\"hi\"]\\n' "
    "> /work/app/Dockerfile",
    "docker rmi -f myapp >/dev/null 2>&1; true",
)

docker = Domain(
    id="docker", tier=2, name="Docker", tagline="Images, containers, networking",
    env="docker", setup=DOCKER_SETUP,
    notes="Commands run against a nested, isolated Docker daemon (dind). Your host "
          "daemon, images and containers are never touched.",
    questions=[
        MCQ("What is the difference between an image and a container?",
            ["No difference", "Image is the blueprint; container is a running instance",
             "Container is the blueprint; image is the instance",
             "Images run, containers don't"], 1,
            "You build images once and run many containers from them."),
        MCQ("How do you persist data beyond a container's lifecycle?",
            ["It's automatic", "Use a volume", "Restart the container", "Use -d"], 1,
            "Volumes live outside the container's writable layer and survive removal."),
        MCQ("Why is running a container as root still a security concern?",
            ["It isn't — containers are fully isolated",
             "Container root maps to host root unless user namespaces are remapped, so a "
             "breakout lands with full privileges",
             "It only slows the container down",
             "Root is required for networking"], 1,
            "Containers are a namespace boundary, not a security boundary by default — "
            "drop privileges with USER and keep capabilities minimal."),
        Terminal(
            prompt="List the containers that are currently running.",
            env="docker",
            check=Check(stdout_all=("breach-target",), stdout_none=("stale-one",)),
            accepted=(r"docker ps$|docker ps [^a]*$",),
            explain="docker ps shows running containers only; -a adds the stopped ones.",
            hint="Two words.",
            sim_output="CONTAINER ID  IMAGE         STATUS     NAMES\n"
                       "8f1c2d3e4a5b  alpine:3.20   Up 2 min   breach-target"),
        Terminal(
            prompt="Show the logs produced by the container named breach-target.",
            env="docker",
            check=Check(stdout_all=("listener bound on 0.0.0.0:9000",)),
            accepted=(r"docker logs .*breach-target",),
            explain="docker logs replays whatever the container wrote to stdout/stderr — "
                    "the first place to look when a service won't come up.",
            hint="docker logs <name>",
            sim_output="listener bound on 0.0.0.0:9000"),
        Terminal(
            prompt="Start a detached container named web from alpine:3.20 that stays "
                   "alive (sleep 3600 is fine).",
            env="docker",
            check=Check(state_cmd="docker ps --filter name=^web$ --format '{{.Names}}'",
                        state_all=("web",)),
            accepted=(r"docker run .*-d.*--name web.*alpine",),
            explain="-d detaches; --name gives the container a stable DNS name other "
                    "containers on the same network can resolve.",
            hint="docker run -d --name web alpine:3.20 sleep 3600",
            sim_output="3f9a2e1b8c4d7f0a1b2c3d4e5f6a7b8c"),
        Terminal(
            prompt="Build an image tagged myapp from the Dockerfile in /work/app.",
            env="docker",
            check=Check(state_cmd="docker images myapp --format '{{.Repository}}'",
                        state_all=("myapp",)),
            accepted=(r"docker build .*-t myapp.*",),
            explain="-t tags the result; the final argument is the build context "
                    "directory sent to the daemon.",
            hint="docker build -t <tag> <context-path>",
            sim_output="Successfully tagged myapp:latest"),
        Terminal(
            prompt="Remove every stopped container (two are sitting there exited).",
            env="docker",
            check=Check(state_cmd="docker ps -aq --filter status=exited | wc -l",
                        state_regex=r"^\s*0\s*$"),
            accepted=(r"docker container prune( -f)?|docker rm .*stale",),
            explain="container prune clears everything in the Exited state — the standard "
                    "cleanup before a disk fills with dead layers.",
            hint="docker container prune -f",
            sim_output="Deleted Containers:\ne92f...\nTotal reclaimed space: 128MB"),
    ],
    boss=[
        Terminal(
            prompt="BOSS — Two containers can't reach each other because they share no "
                   "network. Create a user-defined bridge network called appnet and "
                   "attach the running container web to it.",
            env="docker",
            check=Check(state_cmd="docker network inspect appnet "
                                  "--format '{{range .Containers}}{{.Name}} {{end}}'",
                        state_all=("web",), state_exit_zero=True),
            accepted=(r"docker network create appnet.*docker network connect appnet web",),
            explain="Containers on the default bridge can only reach each other by IP; a "
                    "user-defined network adds DNS resolution by container name, which is "
                    "why 'can't reach the database' is almost always a network problem.",
            hint="Two commands: docker network create ..., then docker network connect ...",
            sim_output="(network created and container attached)"),
    ],
)

# ================================================================== IAM
# Every aws command is executed for real by AWS CLI v2 against LocalStack.
IAM_SETUP = (
    "aws iam create-user --user-name martin >/dev/null 2>&1; true",
    "aws iam create-user --user-name auditor >/dev/null 2>&1; true",
    "aws iam create-user --user-name deploy-bot >/dev/null 2>&1; true",
    "aws iam create-user --user-name contractor >/dev/null 2>&1; true",
    "aws iam delete-user --user-name intern >/dev/null 2>&1; true",
    "aws iam detach-user-policy --user-name auditor "
    "--policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess >/dev/null 2>&1; true",
    "aws iam put-user-policy --user-name contractor --policy-name AllAccess "
    "--policy-document '{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\","
    "\"Action\":\"s3:*\",\"Resource\":\"*\"}]}' >/dev/null 2>&1; true",
    "for k in $(aws iam list-access-keys --user-name deploy-bot "
    "--query 'AccessKeyMetadata[].AccessKeyId' --output text 2>/dev/null); do "
    "aws iam delete-access-key --user-name deploy-bot --access-key-id $k "
    ">/dev/null 2>&1; done; true",
)

iam = Domain(
    id="iam", tier=2, name="IAM", tagline="AWS identity & access management",
    env="aws", setup=IAM_SETUP,
    notes="AWS CLI v2 executes for real against LocalStack, a local fake AWS. No real "
          "account, no real credentials, no bill.",
    questions=[
        MCQ("What is the principle of least privilege?",
            ["Giving all users admin access",
             "Granting only the permissions needed to perform a task",
             "Disabling all permissions permanently",
             "Sharing root credentials across the team"], 1,
            "Least privilege shrinks the blast radius when a credential is misused."),
        MCQ("Key difference between an IAM role and an IAM user?",
            ["No real difference",
             "A role is assumed temporarily; a user holds long-term credentials",
             "A user is temporary; a role is permanent",
             "Roles are only for the root account"], 1,
            "Roles hand out short-lived credentials via sts:AssumeRole — nothing to leak "
            "in a repo."),
        MCQ("What does an IAM policy document define?",
            ["Billing alerts", "Which actions are allowed or denied on which resources",
             "Network routes", "EC2 instance types"], 1,
            "JSON with Effect, Action, Resource and optional Condition."),
        MCQ("A policy grants s3:* on Resource \"*\" to a developer 'just for testing'. "
            "Main risk?",
            ["None, it's temporary",
             "It violates least privilege — that key can read or delete any bucket "
             "in the account",
             "It will slow down S3", "It's required for testing"], 1,
            "Wildcard action on wildcard resource is exactly what least privilege exists "
            "to prevent, and 'temporary' policies have a way of becoming permanent."),
        Terminal(
            prompt="List all IAM users in the account.",
            env="aws",
            check=Check(stdout_all=("auditor", "deploy-bot")),
            accepted=(r"aws iam list-users",),
            explain="list-users enumerates the account's long-term identities — step one "
                    "of any access review.",
            hint="aws iam list-...",
            sim_output='{"Users": [{"UserName": "martin"}, {"UserName": "auditor"}]}'),
        Terminal(
            prompt="Attach the AWS managed policy ReadOnlyAccess to the user auditor.",
            env="aws",
            check=Check(state_cmd="aws iam list-attached-user-policies "
                                  "--user-name auditor",
                        state_all=("ReadOnlyAccess",)),
            accepted=(r"aws iam attach-user-policy .*--user-name auditor.*readonlyaccess",),
            explain="Managed policy ARNs under arn:aws:iam::aws:policy/ are maintained by "
                    "AWS — preferable to hand-rolled inline policies where they fit.",
            hint="aws iam attach-user-policy --user-name ... --policy-arn "
                 "arn:aws:iam::aws:policy/ReadOnlyAccess",
            sim_output="(no output = success)"),
        Terminal(
            prompt="Create an access key for the user deploy-bot.",
            env="aws",
            check=Check(state_cmd="aws iam list-access-keys --user-name deploy-bot",
                        state_all=("AccessKeyId",)),
            accepted=(r"aws iam create-access-key .*--user-name deploy-bot",),
            explain="The secret is returned exactly once. In real accounts, prefer a role "
                    "over a standing key wherever the workload can assume one.",
            hint="aws iam create-access-key --user-name ...",
            sim_output='{"AccessKey": {"AccessKeyId": "AKIA...", "Status": "Active"}}'),
        Terminal(
            prompt="Create a new IAM user named intern.",
            env="aws",
            check=Check(state_cmd="aws iam list-users", state_all=("intern",)),
            accepted=(r"aws iam create-user .*--user-name intern",),
            explain="create-user makes the identity with no permissions at all — "
                    "the correct starting point.",
            hint="aws iam create-user --user-name ...",
            sim_output='{"User": {"UserName": "intern"}}'),
        Terminal(
            prompt="Show the names of the inline policies attached directly to the "
                   "user contractor.",
            env="aws",
            check=Check(stdout_all=("AllAccess",)),
            accepted=(r"aws iam list-user-policies .*--user-name contractor",),
            explain="Inline policies are invisible in the managed-policy listing, which is "
                    "why over-permissioned users hide there during audits.",
            hint="aws iam list-user-policies --user-name ...",
            sim_output='{"PolicyNames": ["AllAccess"]}'),
    ],
    boss=[
        Terminal(
            prompt="BOSS — That AllAccess inline policy on contractor grants s3:* on "
                   "every resource. Remediate it: remove the inline policy from the user.",
            env="aws",
            check=Check(state_cmd="aws iam list-user-policies --user-name contractor",
                        state_none=("AllAccess",)),
            accepted=(r"aws iam delete-user-policy .*--user-name contractor.*"
                      r"--policy-name allaccess",),
            explain="delete-user-policy removes the inline document. In a real incident "
                    "you would also rotate the user's keys, since anything that key "
                    "touched while over-permissioned is now in scope.",
            hint="aws iam delete-user-policy --user-name ... --policy-name ...",
            sim_output="(no output = success)"),
    ],
)

# ====================================================== CLOUD SECURITY
CLOUDSEC_SETUP = (
    "aws s3api create-bucket --bucket client-data-2026 >/dev/null 2>&1; true",
    "aws s3api create-bucket --bucket static-assets >/dev/null 2>&1; true",
    "aws s3api delete-public-access-block --bucket client-data-2026 >/dev/null 2>&1; true",
    "aws s3api put-bucket-versioning --bucket client-data-2026 "
    "--versioning-configuration Status=Suspended >/dev/null 2>&1; true",
    "aws s3api delete-bucket-encryption --bucket static-assets >/dev/null 2>&1; true",
    "aws s3api put-bucket-policy --bucket static-assets --policy "
    "'{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"PublicRead\","
    "\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":\"s3:GetObject\","
    "\"Resource\":\"arn:aws:s3:::static-assets/*\"}]}' >/dev/null 2>&1; true",
    "echo confidential > /tmp/c.txt && aws s3 cp /tmp/c.txt "
    "s3://client-data-2026/payroll.csv >/dev/null 2>&1; true",
)

cloudsec = Domain(
    id="cloudsec", tier=2, name="Cloud Security", tagline="AWS network & data protection",
    env="aws", setup=CLOUDSEC_SETUP,
    notes="S3 hardening runs for real against LocalStack. GuardDuty and CloudTrail "
          "aren't available in the free LocalStack image, so those stay as knowledge "
          "questions.",
    questions=[
        MCQ("What is the AWS shared responsibility model?",
            ["AWS handles everything",
             "AWS secures the cloud itself; the customer secures what they put in it",
             "The customer manages physical hardware", "Responsibility ends at billing"], 1,
            "AWS is responsible for security *of* the cloud; you are responsible *in* it — "
            "data, identity, configuration."),
        MCQ("Key difference between a Security Group and a NACL?",
            ["No difference",
             "SG is stateful and instance-level; NACL is stateless and subnet-level",
             "NACL is stateful; SG is subnet-level", "Both are stateless"], 1,
            "Because NACLs are stateless you must allow the return traffic explicitly — "
            "the classic cause of 'the rule looks right but nothing works'."),
        MCQ("Which service records who called which AWS API, when, and from where?",
            ["CloudWatch", "CloudTrail", "Config", "GuardDuty"], 1,
            "CloudTrail is the API audit log; CloudWatch is metrics and logs; Config "
            "tracks resource configuration drift."),
        MCQ("GuardDuty flags unusual API calls from an unfamiliar IP using a developer's "
            "access key. Best immediate action?",
            ["Ignore it, probably a false positive",
             "Revoke or rotate the key, then investigate scope",
             "Delete GuardDuty", "Disable CloudTrail"], 1,
            "Contain first — kill the credential's usefulness — then work out what it "
            "touched. Never disable the logging you'll need for the investigation."),
        MCQ("What does encryption at rest protect against?",
            ["Traffic interception",
             "Unauthorised access to stored data if the underlying media is exposed",
             "DDoS", "Phishing"], 1,
            "At-rest encryption does nothing against an authorised-looking read — which is "
            "why a public bucket full of encrypted objects still leaks."),
        Terminal(
            prompt="List every S3 bucket in the account.",
            env="aws",
            check=Check(stdout_all=("client-data-2026", "static-assets")),
            accepted=(r"aws s3 ls$|aws s3api list-buckets",),
            explain="aws s3 ls with no path lists buckets; aws s3api list-buckets returns "
                    "the same thing as raw JSON.",
            hint="Two words after aws.",
            sim_output="2026-03-11 14:02:31 client-data-2026\n"
                       "2026-05-02 09:15:00 static-assets"),
        Terminal(
            prompt="Turn on all four public-access-block settings for the bucket "
                   "client-data-2026.",
            env="aws",
            check=Check(state_cmd="aws s3api get-public-access-block "
                                  "--bucket client-data-2026",
                        state_all=("true",), state_none=("false",)),
            accepted=(r"aws s3api put-public-access-block .*--bucket client-data-2026",),
            explain="Block Public Access is the account-level seatbelt: it overrides any "
                    "ACL or policy that would otherwise expose an object.",
            hint="aws s3api put-public-access-block --bucket ... "
                 "--public-access-block-configuration "
                 "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,"
                 "RestrictPublicBuckets=true",
            sim_output="(no output = success)"),
        Terminal(
            prompt="Enable default server-side encryption with AES256 on the bucket "
                   "static-assets.",
            env="aws",
            check=Check(state_cmd="aws s3api get-bucket-encryption "
                                  "--bucket static-assets",
                        state_all=("AES256",)),
            accepted=(r"aws s3api put-bucket-encryption .*--bucket static-assets.*aes256",),
            explain="Default encryption applies to every new object without the uploader "
                    "having to remember a flag.",
            hint="aws s3api put-bucket-encryption --bucket ... "
                 "--server-side-encryption-configuration "
                 "'{\"Rules\":[{\"ApplyServerSideEncryptionByDefault\":"
                 "{\"SSEAlgorithm\":\"AES256\"}}]}'",
            sim_output="(no output = success)"),
        Terminal(
            prompt="Enable versioning on client-data-2026 so overwritten or deleted "
                   "objects can be recovered.",
            env="aws",
            check=Check(state_cmd="aws s3api get-bucket-versioning "
                                  "--bucket client-data-2026",
                        state_all=("Enabled",)),
            accepted=(r"aws s3api put-bucket-versioning .*--bucket client-data-2026.*"
                      r"status=enabled",),
            explain="Versioning is the cheapest ransomware and fat-finger insurance S3 "
                    "offers; pair it with MFA delete on anything that matters.",
            hint="aws s3api put-bucket-versioning --bucket ... "
                 "--versioning-configuration Status=Enabled",
            sim_output="(no output = success)"),
        Terminal(
            prompt="Show the bucket policy currently attached to static-assets.",
            env="aws",
            check=Check(stdout_all=("PublicRead",)),
            accepted=(r"aws s3api get-bucket-policy .*--bucket static-assets",),
            explain="Resource-based policies live on the resource itself — an identity "
                    "audit alone will never surface this grant.",
            hint="aws s3api get-bucket-policy --bucket ...",
            sim_output='{"Policy": "{\\"Sid\\":\\"PublicRead\\", ...}"}'),
    ],
    boss=[
        Terminal(
            prompt="BOSS — static-assets carries a bucket policy granting s3:GetObject to "
                   "Principal \"*\" — anyone on the internet. Remove that bucket policy "
                   "entirely.",
            env="aws",
            check=Check(state_cmd="aws s3api get-bucket-policy --bucket static-assets",
                        state_exit_nonzero=True),
            accepted=(r"aws s3api delete-bucket-policy .*--bucket static-assets",),
            explain="Deleting the policy closes the exposure at its source. A get-bucket-"
                    "policy that now errors with NoSuchBucketPolicy is the proof — and in "
                    "a real response you'd follow with Block Public Access and a CloudTrail "
                    "review of what was read while it was open.",
            hint="aws s3api delete-bucket-policy --bucket ...",
            sim_output="(no output = success)"),
    ],
)

DOMAINS = [docker, iam, cloudsec]
