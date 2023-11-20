from unittest.mock import patch

import pytest
from jsonschema import validate

from api_calls import (
    COMMIT_SCHEMA,
    call_github,
    get_commit,
    get_commit_details,
    get_commit_list,
    get_commit_message,
    get_commit_metadata,
    get_commit_patches,
)


@pytest.fixture
def mock_requests_get_commit():
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
    with patch("api_calls.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = commit_details_subset_from_github
        yield mock_get


@pytest.fixture
def mock_requests_get_commit_list():
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
    with patch("api_calls.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = commit_list_subset_from_github
        yield mock_get


def test_call_github(mock_requests_get_commit):
    resp = call_github(url="url", params={})
    assert resp.status_code == 200


def test_get_commit(mock_requests_get_commit):
    resp_json = get_commit("owner", "repo", "commit_sha")
    assert resp_json["commit"]["message"] == "Update token logic"
    assert resp_json["files"][0]["filename"] == "api_calls.py"


def test_get_commit_message(mock_requests_get_commit):
    resp = get_commit_message("owner", "repo", "commit_sha")
    assert resp == "Update token logic"


def test_get_commit_details(mock_requests_get_commit):
    commit_details = get_commit_details("owner", "repo", "commit_sha")
    assert commit_details["message"] == "Update token logic"
    assert commit_details["stats"]["additions"] == 1
    assert commit_details["files"][0]["filename"] == "api_calls.py"
    assert commit_details["files"][0].get("patch") is not None
    assert commit_details["files"][0].get("changes") == 2
    validate(commit_details, schema=COMMIT_SCHEMA)


def test_get_commit_metadata(mock_requests_get_commit):
    commit_metadata = get_commit_metadata("owner", "repo", "commit_sha")
    assert commit_metadata["message"] == "Update token logic"
    assert commit_metadata["stats"]["additions"] == 1
    assert commit_metadata["files"][0]["filename"] == "api_calls.py"
    assert commit_metadata["files"][0].get("patch") is None
    assert commit_metadata["files"][0].get("changes") == 2
    validate(commit_metadata, schema=COMMIT_SCHEMA)


def test_get_commit_patches(mock_requests_get_commit):
    commit_details = get_commit_patches("owner", "repo", "commit_sha")
    assert commit_details["message"] == "Update token logic"
    assert commit_details["stats"]["additions"] == 1
    assert commit_details["files"][0]["filename"] == "api_calls.py"
    assert commit_details["files"][0].get("patch") is not None
    assert commit_details["files"][0].get("additions") is None
    assert commit_details["files"][0].get("changes") is None
    assert commit_details["files"][0].get("deletions") is None
    assert commit_details["files"][0].get("status") is None
    validate(commit_details, schema=COMMIT_SCHEMA)


def test_get_commit_list(mock_requests_get_commit_list):
    commit_list = get_commit_list("owner", "repo", "start_date", "end_date")
    assert commit_list[0] == "3a82cb165fe5db358f84ec59fd98c6fa17e68bbe"
    assert commit_list[1] == "76bdd307d931c5f4968eeea62f816ac2620f09a9"
