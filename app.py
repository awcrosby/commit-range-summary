import os

from dotenv import load_dotenv

from prompts import (
    criticize_patch,
    sum_commit_metadata_range,
    sum_commit_range,
    sum_message_range,
    sum_patch,
)

load_dotenv()
OWNER = os.environ.get("OWNER", "")
REPO = os.environ.get("REPO", "")
AUTHOR = os.environ.get("AUTHOR", "")
SINCE = os.environ.get("SINCE", "")
UNTIL = os.environ.get("UNTIL", "")
COMMIT_SHA = os.environ.get("COMMIT_SHA", "")

# Summarize range of commits based on commit messages
ai_reply = sum_message_range(OWNER, REPO, SINCE, UNTIL, AUTHOR)
print(ai_reply)

# Summarize commit from message and file patch metadata without code patches
ai_reply = sum_commit_metadata_range(OWNER, REPO, SINCE, UNTIL, AUTHOR)
print(ai_reply)

# Summarize single commit based on commit message and code patches
ai_reply = sum_patch(OWNER, REPO, COMMIT_SHA)
print(ai_reply)

# Summarize range of commits based on full commit including code patches
ai_reply = sum_commit_range(OWNER, REPO, SINCE, UNTIL, AUTHOR)
print(ai_reply)

# Critical review of single commit if message and code patches don't align
ai_reply = criticize_patch(OWNER, REPO, COMMIT_SHA)
print(ai_reply)
