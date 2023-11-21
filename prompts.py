from typing import Optional

from api_calls import (
    call_openai,
    get_commit_details,
    get_commit_message,
    get_commit_metadata,
    get_commit_patches,
    get_shas,
)


def sum_message_range(
    owner: str, repo: str, since: str, until: str, author: Optional[str] = None
) -> str:
    print("===Summary of commit range based on commit messages===")
    print(f"owner: {owner}\nrepo: {repo}\nauthor: {author}\nsince: {since}\nuntil: {until}")
    prompt = """
    Write a single short paragraph for a resume.

    Your input will be git commit messages.
    Do not simply list the commit messages.
    Make it devoid of any business bullshit speak and sales / leadership / marketing / social media influencer jargon

    Here is a list of the commit messages:\n{commit_messages}
    """
    shas = get_shas(owner, repo, since, until, author)
    print(f"number of commits: {len(shas)}")
    commit_messages = [get_commit_message(owner, repo, sha) for sha in shas]
    return call_openai(prompt.format(commit_messages=commit_messages))


def sum_metadata_range(
    owner: str, repo: str, since: str, until: str, author: Optional[str] = None
) -> str:
    print("===Summary of commit range based on messages and file metadata===")
    print(f"owner: {owner}\nrepo: {repo}\nauthor: {author}\nsince: {since}\nuntil: {until}")
    prompt = """
    Write a single short paragraph for a resume.

    Your input will be git commit messages and metadata about files changed.
    Do not simply list the commit messages.
    Make it devoid of any business bullshit speak and sales / leadership / marketing / social media influencer jargon

    Here is the input in json format:\n{commit_data}
    """
    shas = get_shas(owner, repo, since, until, author)
    print(f"number of commits: {len(shas)}")
    commit_data = [get_commit_metadata(owner, repo, sha) for sha in shas]
    return call_openai(prompt.format(commit_data=commit_data))


def sum_patch_range(owner: str, repo: str, since: str, until: str) -> str:
    print("===Summary of commit range based on messages and commit code patches===")
    print(f"owner: {owner}\nrepo: {repo}\nsince: {since}\nuntil: {until}")
    prompt = """
    Please write a single short paragraph for a resume.

    Your input will be code patches from git commits.
    Infer experience based on the text.
    Please be a little humble and do not use many superlatives.

    Here is a list of the code patches:\n{commit_patches}
    """
    shas = get_shas(owner, repo, since, until)
    print(f"number of commits: {len(shas)}")
    commit_patches = [get_commit_details(owner, repo, sha) for sha in shas]
    return call_openai(prompt.format(commit_patches=commit_patches))


def sum_patch(owner: str, repo: str, commit_sha: str) -> str:
    print("===Summary of single commit based on commit message and code patches===")
    prompt = """
    I need a summary of code changes made to a git repository.

    Ignore issue tracker issues and do not include or mention associated issues in the summary.

    Summarize all the changes together in a single paragraph not in a list.
    Respond with a maximum total of 4 sentences.

    Please focus on the types of changes.
    Do not focus on the the names of the files, do not focus on the number of lines edited.

    Commit message: {commit_message}

    Code patches: {patches}
    """
    commit = get_commit_patches(owner, repo, commit_sha)
    commit_message = commit["message"]
    patches = commit["files"]
    return call_openai(prompt.format(commit_message=commit_message, patches=patches))


def criticize_patch(owner: str, repo: str, commit_sha: str) -> str:
    print("===Critical review of single commit if message and code patches don't align===")
    prompt = """
    You are a sceptical software engineer doing a code review.

    Does the commit message contradict the code diff to the point where the commit message is not accurately telling the truth about the code patch?

    If so explain, if not say so.

    Commit message: {commit_message}

    Code patches: {patches}
    """
    commit = get_commit_patches(owner, repo, commit_sha)
    commit_message = commit["message"]
    patches = commit["files"]
    return call_openai(prompt.format(commit_message=commit_message, patches=patches))
