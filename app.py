import os

from dotenv import load_dotenv

from prompts import (
    criticize_patch,
    sum_message_range,
    sum_metadata_range,
    sum_patch,
    sum_patch_range,
)

load_dotenv()
OWNER = os.environ.get("OWNER", "")
REPO = os.environ.get("REPO", "")
AUTHOR = os.environ.get("AUTHOR", "")
SINCE = os.environ.get("SINCE", "")
UNTIL = os.environ.get("UNTIL", "")
COMMIT_SHA = os.environ.get("COMMIT_SHA", "")

# Summarize commit from message and file patch metadata
ai_reply = sum_metadata_range(OWNER, REPO, SINCE, UNTIL, AUTHOR)
print(ai_reply)
exit()

# Summarize single commit based on commit message and code patches
ai_reply = sum_patch(OWNER, REPO, COMMIT_SHA)
print(ai_reply)

# Summarize range of commits based on commit messages
ai_reply = sum_message_range(OWNER, REPO, SINCE, UNTIL, AUTHOR)
print(ai_reply)

# Summarize range of commits based on commit code patches
ai_reply = sum_patch_range(OWNER, REPO, SINCE, UNTIL)
print(ai_reply)

# Critical review of single commit if message and code patches don't align
ai_reply = criticize_patch(OWNER, REPO, COMMIT_SHA)
print(ai_reply)
