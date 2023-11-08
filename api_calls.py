import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()
GITHUB_API_KEY = os.environ.get("GITHUB_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

SUMMARY_PROMPT_INTRO = """
I need a summary of code changes made to a git repository.

Ignore issue tracker issues and do not include or mention associated issues in the summary.

Summarize all the changes together in a single paragraph not in a list.
Respond with a maximum total of 4 sentences.

Please focus on the types of changes.
Do not focus on the the names of the files, do not focus on the number of lines edited.
"""


def call_github(url, params):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {GITHUB_API_KEY}",
    }
    r = requests.get(url, headers=headers, params=params)

    if r.status_code != 200:
        raise RuntimeError(f"Error calling github api, status_code={r.status_code}")

    return r.json()


def get_commit_details(owner, repo, commit_sha):
    gh_commit_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"

    resp_json = call_github(gh_commit_url, params={})

    commit_message = resp_json["commit"]["message"]

    FILE_KEYS = ["filename", "patch", "status", "changes"]
    patches = []
    for file in resp_json["files"]:
        d = {k: v for k, v in file.items() if k in FILE_KEYS}
        patches.append(d)

    return (commit_message, patches)


def get_commit_list(owner, repo, start_date, end_date):
    gh_commit_list_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"since": start_date, "until": end_date}

    resp_json = call_github(gh_commit_list_url, params)
    return [commit["sha"] for commit in resp_json]


def get_pull_requests(owner, repo, commit_sha):
    pulls_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}/pulls"

    resp_json = call_github(pulls_url, params={})

    PULL_REQUEST_KEYS = ["title", "body"]
    pull_requests = []
    for pull in resp_json:
        d = {k: v for k, v in pull.items() if k in PULL_REQUEST_KEYS}
        pull_requests.append(d)

    return pull_requests


def call_openai(content):
    openai_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    payload = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": content}]}
    data = json.dumps(payload)

    token_estimate = int(len(content) / 4)
    if token_estimate > 4097:
        raise RuntimeError(
            f"Token estimate {token_estimate} exceeds maximum 4097 tokens for OpenAI API"
        )

    r = requests.post(openai_url, headers=headers, data=data)
    ai_reply = r.json()["choices"][0]["message"]["content"]
    return ai_reply


def ai_summarize_commit(commit_message, patches, pull_requests):
    prompt = (
        SUMMARY_PROMPT_INTRO
        + f"""

    Pull request text: {pull_requests}

    Commit message: {commit_message}

    Code patches: {patches}
    """
    )

    return call_openai(content=prompt)


def ai_criticize_commit(commit_message, patches):
    prompt = f"""
    You are a sceptical software engineer doing a code review.

    Does the commit message contradict the code diff to the point where the commit message is not accurately telling the truth about the code patch?

    If so explain, if not say so.

    Commit message: {commit_message}

    Code patches: {patches}
    """

    return call_openai(content=prompt)


def ai_summarize_single_data_type(data_type, changes):
    PROMPT_TEMPLATE = (
        SUMMARY_PROMPT_INTRO
        + """
    Here are the {data_type} items I want you to summarize: {list_of_code_changes}
    """
    )

    str_code_changes = ""
    for i, d in enumerate(changes):
        str_code_changes += str(d) + "\n\n\n"

    prompt = PROMPT_TEMPLATE.format(data_type=data_type, list_of_code_changes=str_code_changes)

    return call_openai(content=prompt)
