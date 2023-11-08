import enum
from pprint import pprint

from api_calls import (ai_criticize_commit, ai_summarize_commit,
                       ai_summarize_single_data_type,
                       get_changes_single_commit, gh_get_commit_list)


class CodeChangeType(enum.Enum):
    """Descriptions of change type for use in prompts."""

    COMMIT_MESSAGE = "git commit message text"
    PULL_REQUEST = "pull request text"
    CODE_PATCH = "code edits in the form of a code diff patch"


### Github info input
owner = "awcrosby"
repo = "galaxy-importer"
commit_sha = "573a5994fcf534fafe27372a6fe098fb7bb14c62"

# commit_message, patches, pull_requests = get_changes_single_commit(owner, repo, commit_sha)
# single_commit_summary = ai_summarize_commit(commit_message, patches, pull_requests)
# pprint(single_commit_summary)

list_of_commits = [
    "eb5ead417c703363beb04d082eb3b2a0767af6fb",
    "16c76a32839c08e1faaaa18383a4ca2328282b34",
    "475c6a00d5788b6a2e3486f10627f5967dc2f826",
    "968e0db27be862b5fac9a3e49b0f5ecf62213164",
    "05712d1d76e934f5b5952bf8cf2ac29aa310a0e8",
    "573a5994fcf534fafe27372a6fe098fb7bb14c62",
]


def get_changes_multiple_commits(owner, repo, list_of_commits):
    code_changes = []
    for commit_sha in list_of_commits:
        code_change = get_changes_single_commit(owner, repo, commit_sha)
        code_changes.append(code_change)
    return code_changes


code_changes = get_changes_multiple_commits(owner, repo, list_of_commits)
all_commit_messages = [c[0] for c in code_changes]
all_pull_requests = [c[2] for c in code_changes]
all_patches = [c[1] for c in code_changes]

commit_titles = [m.split("\n")[0] for m in all_commit_messages]
pprint(f"========= Summarizing the following commits =========\n{commit_titles}")

resp = ai_summarize_single_data_type(CodeChangeType.COMMIT_MESSAGE, changes=all_commit_messages)
pprint("========= Summary of git commit message text =========")
pprint(resp)

resp = ai_summarize_single_data_type(CodeChangeType.PULL_REQUEST, changes=all_pull_requests)
pprint("========= Summary of pull request text =========")
pprint(resp)

resp = ai_summarize_single_data_type(CodeChangeType.CODE_PATCH, changes=all_patches)
pprint("========= Summary of code code diff patches =========")
pprint(resp)
