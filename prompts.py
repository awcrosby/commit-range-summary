from api_calls import call_openai, get_commit_details, get_commit_list


def sum_commit_messages(owner: str, repo: str, start_date: str, end_date: str):
    print("===Summary of commit range based on commit messages===")
    prompt = """
    Please write a single short paragraph for a resume.

    Your input will be git commit messages.
    Do not simply list the commit messages.
    Infer experience based on the text.
    Please be a little humble and do not use many superlatives.

    Here is a list of the commit messages:\n{commit_messages}
    """
    commit_list = get_commit_list(owner, repo, start_date, end_date)
    commit_messages = [get_commit_details(owner, repo, sha)[0] for sha in commit_list]
    return call_openai(prompt.format(commit_messages=commit_messages))


def sum_commit_patches(owner: str, repo: str, start_date: str, end_date: str):
    print("===Summary of commit range based on commit code patches===")
    prompt = """
    Please write a single short paragraph for a resume.

    Your input will be code patches from git commits.
    Infer experience based on the text.
    Please be a little humble and do not use many superlatives.

    Here is a list of the code patches:\n{commit_patches}
    """
    commit_list = get_commit_list(owner, repo, start_date, end_date)
    commit_patches = [get_commit_details(owner, repo, sha)[1] for sha in commit_list]
    return call_openai(prompt.format(commit_patches=commit_patches))


def sum_single_commit(commit_message, patches):
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

    return call_openai(prompt.format(commit_message=commit_message, patches=patches))


def criticize_commit(commit_message, patches):
    print("===Critical review of single commit if message and code patches don't align===")
    prompt = """
    You are a sceptical software engineer doing a code review.

    Does the commit message contradict the code diff to the point where the commit message is not accurately telling the truth about the code patch?

    If so explain, if not say so.

    Commit message: {commit_message}

    Code patches: {patches}
    """

    return call_openai(prompt.format(commit_message=commit_message, patches=patches))
