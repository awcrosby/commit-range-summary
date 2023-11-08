from dotenv import load_dotenv
import json
import requests
import os

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

def get_changes_single_commit(owner, repo, commit_sha):
    gh_commit_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
    headers = {"Authorization": f"token {GITHUB_API_KEY}"}
    commit_data = requests.get(gh_commit_url, headers=headers).json()

    commit_message = commit_data["commit"]["message"]

    FILE_KEYS = ["filename", "patch", "status", "changes"]
    patches = []
    for file in commit_data["files"]:
        d = {k: v for k, v in file.items() if k in FILE_KEYS}
        patches.append(d)

    pulls_url = gh_commit_url + "/pulls"
    pull_data = requests.get(pulls_url, headers=headers).json()
    PULL_REQUEST_KEYS = ["title", "body"]
    pull_requests = []
    for pull in pull_data:
        d = {k: v for k, v in pull.items() if k in PULL_REQUEST_KEYS}
        pull_requests.append(d)
    
    return (commit_message, patches, pull_requests)


def gh_get_commit_list(owner, repo, start_date, end_date):
    gh_commit_list_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    headers = {"Authorization": f"token {GITHUB_API_KEY}"}
    params = {"since": start_date, "until": end_date}
    r = requests.get(gh_commit_list_url, headers=headers, params=params)

    if r.status_code != 200:
        raise RuntimeError(f"Error getting commit list, status_code={r.status_code}")

    return [commit["sha"] for commit in r.json()]


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
        raise RuntimeError(f"Token estimate {token_estimate} exceeds maximum 4097 tokens for OpenAI API")

    r = requests.post(openai_url, headers=headers, data=data)
    ai_reply = r.json()['choices'][0]['message']['content']
    return ai_reply


def ai_summarize_commit(commit_message, patches, pull_requests):
    prompt = SUMMARY_PROMPT_INTRO + f"""

    Pull request text: {pull_requests}

    Commit message: {commit_message}

    Code patches: {patches}
    """

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
    PROMPT_TEMPLATE = SUMMARY_PROMPT_INTRO + """
    Here are the {data_type} items I want you to summarize: {list_of_code_changes}
    """

    code_changes_str = ""
    for i, d in enumerate(changes):
        code_changes_str += d + "\n\n\n"

    prompt = PROMPT_TEMPLATE.format(data_type=data_type, list_of_code_changes=code_changes_str)

    return call_openai(content=prompt)
