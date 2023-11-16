import json
import os
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv
from jsonschema import validate

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

COMMIT_SCHEMA = {
    "type": "object",
    "properties": {
        "message": {"type": "string"},
        "stats": {
            "type": "object",
            "properties": {
                "additions": {"type": "number"},
                "deletions": {"type": "number"},
                "total": {"type": "number"},
            },
            "additionalProperties": False,
        },
        "files": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "status": {"type": "string"},
                    "changes": {"type": "number"},
                    "additions": {"type": "number"},
                    "deletions": {"type": "number"},
                    "patch": {"type": "string"},
                },
                "additionalProperties": False,
                "required": ["filename"],
            },
        },
    },
    "additionalProperties": False,
    "required": ["message", "stats", "files"],
}


def call_github(url: str, params: dict[str, str]) -> requests.models.Response:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {GITHUB_API_KEY}",
    }
    r = requests.get(url, headers=headers, params=params)

    if r.status_code != 200:
        message = r.json().get("message", "")
        raise RuntimeError(f"Error calling github api, {r.status_code} {r.reason}: {message}")

    return r


def get_commit(owner: str, repo: str, commit_sha: str) -> Dict[str, Any]:
    gh_commit_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
    return call_github(gh_commit_url, params={}).json()


def get_commit_message(owner: str, repo: str, commit_sha: str) -> str:
    commit = get_commit(owner, repo, commit_sha)
    return commit["commit"]["message"]


def get_commit_metadata(owner: str, repo: str, commit_sha: str) -> Dict[str, Any]:
    """Remove code patches from commit details"""
    commit_details = get_commit_details(owner, repo, commit_sha)
    for file in commit_details["files"]:
        file.pop("patch", None)

    validate(commit_details, schema=COMMIT_SCHEMA)
    return commit_details


def get_commit_patches(owner: str, repo: str, commit_sha: str) -> Dict[str, Any]:
    """Remove metadata from commit details"""
    commit_details = get_commit_details(owner, repo, commit_sha)
    for file in commit_details["files"]:
        file.pop("additions", None)
        file.pop("changes", None)
        file.pop("deletions", None)
        file.pop("status", None)

    validate(commit_details, schema=COMMIT_SCHEMA)
    return commit_details


def get_commit_details(owner: str, repo: str, commit_sha: str) -> Dict[str, Any]:
    commit = get_commit(owner, repo, commit_sha)

    FILE_KEYS = ["patch", "filename", "status", "additions", "deletions", "changes"]
    files = []
    for file in commit["files"]:
        d = {k: v for k, v in file.items() if k in FILE_KEYS}
        files.append(d)

    commit_details = {
        "message": commit["commit"]["message"],
        "stats": commit["stats"],
        "files": files,
    }

    validate(commit_details, schema=COMMIT_SCHEMA)
    return commit_details


def get_commit_list(
    owner: str, repo: str, start_date: str, end_date: str, author: Optional[str] = None
) -> list[str]:
    gh_commit_list_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"since": start_date, "until": end_date}
    if author:
        params["author"] = author

    resp = call_github(gh_commit_list_url, params)

    commits = resp.json()
    while "next" in resp.links:
        resp = call_github(
            resp.links["next"]["url"],
            params,
        )
        commits.extend(resp.json())

    return [commit["sha"] for commit in commits]


def get_pull_requests(owner: str, repo: str, commit_sha: str) -> list[Dict]:
    pulls_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}/pulls"

    resp_json = call_github(pulls_url, params={}).json()

    PULL_REQUEST_KEYS = ["title", "body"]
    pull_requests = []
    for pull in resp_json:
        d = {k: v for k, v in pull.items() if k in PULL_REQUEST_KEYS}
        pull_requests.append(d)

    return pull_requests


def call_openai(content: str) -> str:
    openai_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    # MODEL = "gpt-4-1106-preview"
    # MODEL_INPUT_CONTEXT_WINDOW_TOKENS = 128000
    # MODEL_TPM_LIMIT = 150000

    MODEL = "gpt-3.5-turbo-1106"
    MODEL_INPUT_CONTEXT_WINDOW_TOKENS = 16385
    MODEL_TPM_LIMIT = 90000

    payload = {"model": MODEL, "messages": [{"role": "user", "content": content}]}
    data = json.dumps(payload)

    CHAR_PER_TOKEN = 3.7  # usually 4, can reduce to allow room for prompt introduction
    token_limit = min(MODEL_TPM_LIMIT, MODEL_INPUT_CONTEXT_WINDOW_TOKENS)
    token_estimate = int(len(content) / CHAR_PER_TOKEN)
    if token_estimate > token_limit:
        raise RuntimeError(
            f"Token estimate {token_estimate} exceeds maximum {token_limit} tokens for OpenAI API"
        )

    r = requests.post(openai_url, headers=headers, data=data)

    if r.status_code != 200:
        raise RuntimeError(
            f"Error calling openai api, {r.status_code} {r.reason}: {r.json()['error']['message']}"
        )

    ai_reply = r.json()["choices"][0]["message"]["content"]
    return ai_reply
