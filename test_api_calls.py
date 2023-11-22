from unittest import mock

import pytest
from jsonschema import validate

from api_calls import COMMIT_SCHEMA, GitHubApiClient, OpenAIApiClient


@pytest.fixture
def mock_httpx_get_commit():
    commit_details_subset_from_github = {
        "commit": {
            "message": "Update token logic",
        },
        "stats": {"additions": 1, "deletions": 1, "total": 2},
        "files": [
            {
                "filename": "api_calls.py",
                "status": "modified",
                "changes": 2,
                "additions": 1,
                "deletions": 1,
                "patch": "@@ -176,13 +176,14 @@ def call_openai(content: str) -> str:\n"
                '     payload = {"model": MODEL, "messages": [{"role": "user", "content": content}]}\n'
                "     data = json.dumps(payload)\n \n"
                "-    CHAR_PER_TOKEN = 3.7  # usually 4, can reduce to allow room for prompt introduction\n"
                "+    CHAR_PER_TOKEN = 3.9  # usually 4, can reduce to be less likely to hit limit\n"
                "     token_limit = min(MODEL_TPM_LIMIT, MODEL_INPUT_CONTEXT_WINDOW_TOKENS)\n"
                "     token_estimate = int(len(content) / CHAR_PER_TOKEN)\n",
            }
        ],
    }
    with mock.patch("api_calls.httpx.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = commit_details_subset_from_github
        yield mock_get


@pytest.fixture
def mock_httpx_get_shas():
    commit_list_subset_from_github = [
        {
            "author": {},
            "commit": {},
            "sha": "3a82cb165fe5db358f84ec59fd98c6fa17e68bbe",
        },
        {
            "author": {},
            "commit": {},
            "sha": "76bdd307d931c5f4968eeea62f816ac2620f09a9",
        },
    ]
    with mock.patch("api_calls.httpx.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = commit_list_subset_from_github
        yield mock_get


@pytest.fixture
def mock_httpx_post_prompt():
    text_gen_subset_from_openai = {
        "choices": [
            {
                "finish_reason": "stop",
                "index": 0,
                "message": {
                    "content": "Made enhancements to error handling and search functionality.",
                    "role": "assistant",
                },
            }
        ],
        "model": "gpt-3.5-turbo-1106",
        "object": "chat.completion",
        "usage": {"completion_tokens": 51, "prompt_tokens": 4155, "total_tokens": 4206},
    }

    with mock.patch("api_calls.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = text_gen_subset_from_openai
        yield mock_post


def test_call_github(mock_httpx_get_commit):
    client = GitHubApiClient("owner", "repo")
    resp = client._make_get_request(url="url", params={})
    assert resp.status_code == 200


@mock.patch("api_calls.httpx.get")
def test_call_github_fail(mock_get):
    mock_get.return_value.status_code = 400
    client = GitHubApiClient("owner", "repo")
    with pytest.raises(RuntimeError, match=r".*Error calling github .*"):
        client._make_get_request(url="url", params={})


def test_get_commit_blob(mock_httpx_get_commit):
    client = GitHubApiClient("owner", "repo")
    resp_json = client._get_commit_blob("commit_sha")
    assert resp_json["commit"]["message"] == "Update token logic"
    assert resp_json["files"][0]["filename"] == "api_calls.py"
    assert resp_json["stats"]["additions"] == 1


def test_get_commit(mock_httpx_get_commit):
    client = GitHubApiClient("owner", "repo")
    commit = client.get_commit("commit_sha")
    assert commit["message"] == "Update token logic"
    assert commit["files"][0]["filename"] == "api_calls.py"
    assert commit["stats"]["additions"] == 1
    assert commit["files"][0].get("patch") is not None
    assert commit["files"][0].get("changes") == 2
    validate(commit, schema=COMMIT_SCHEMA)


def test_get_shas(mock_httpx_get_shas):
    client = GitHubApiClient("owner", "repo")
    shas = client._get_shas("since", "until", "author")
    assert shas[0] == "3a82cb165fe5db358f84ec59fd98c6fa17e68bbe"
    assert shas[1] == "76bdd307d931c5f4968eeea62f816ac2620f09a9"


@mock.patch("api_calls.GitHubApiClient._get_shas")
def test_get_commits(mock_shas, mock_httpx_get_commit):
    mock_shas.return_value = ["sha1", "sha2"]
    client = GitHubApiClient("owner", "repo")
    commits = client.get_commits("since", "until", "author")
    assert len(commits) == 2
    for commit in commits:
        assert commit["message"] == "Update token logic"
        assert commit["files"][0]["filename"] == "api_calls.py"
        assert commit["stats"]["additions"] == 1
        assert commit["files"][0].get("patch") is not None
        assert commit["files"][0].get("changes") == 2
        validate(commit, schema=COMMIT_SCHEMA)


def test_call_openai(mock_httpx_post_prompt):
    ai_reply = OpenAIApiClient().generate_chat_completion(content="prompt for ai...")
    assert ai_reply == "Made enhancements to error handling and search functionality."


@mock.patch("api_calls.httpx.post")
def test_call_openai_fail(mock_post):
    mock_post.return_value.status_code = 400
    with pytest.raises(RuntimeError, match=r".*Error calling openai .*"):
        OpenAIApiClient().generate_chat_completion(content="prompt for ai...")


def test_call_openai_token_limit(mock_httpx_post_prompt):
    with pytest.raises(RuntimeError, match=r".*Token estimate .*"):
        OpenAIApiClient().generate_chat_completion(content="prompt for ai..." * 100000)
