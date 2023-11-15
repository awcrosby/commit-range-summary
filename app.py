import enum
import os
from pprint import pprint

from dotenv import load_dotenv

from api_calls import get_commit_details
from prompts import (
    criticize_commit,
    sum_commit_messages,
    sum_commit_patches,
    sum_single_commit,
)

load_dotenv()
OWNER = os.environ.get("OWNER")
REPO = os.environ.get("REPO")
AUTHOR = os.environ.get("AUTHOR")
START_DATE = os.environ.get("START_DATE")
END_DATE = os.environ.get("END_DATE")
COMMIT_SHA = os.environ.get("COMMIT_SHA")


class CodeChangeType(enum.Enum):
    """Descriptions of change type for use in prompts."""

    COMMIT_MESSAGE = "git commit message text"
    PULL_REQUEST = "pull request text"
    CODE_PATCH = "code edits in the form of a code diff patch"


# Summarize single commit based on commit message and code patches
commit_message, patches = get_commit_details(OWNER, REPO, COMMIT_SHA)
ai_reply = sum_single_commit(commit_message, patches)
print(ai_reply)

# Summarize range of commits based on commit messages
ai_reply = sum_commit_messages(OWNER, REPO, START_DATE, END_DATE, AUTHOR)
print(ai_reply)

# Summarize range of commits based on commit code patches
ai_reply = sum_commit_patches(OWNER, REPO, START_DATE, END_DATE)
print(ai_reply)

# Critical review of single commit if message and code patches don't align
commit_message, patches = get_commit_details(OWNER, REPO, COMMIT_SHA)
ai_reply = criticize_commit(commit_message, patches)
print(ai_reply)
