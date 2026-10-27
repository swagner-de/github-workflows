"""Release eligibility guard, also embedded verbatim in release-please.yaml.

CI commits are never release-producing, even when a workflow ref has a fix title.
Release PR merge commits must be processed to tag their proposed releases.
"""
import re


def release_mode(event, messages):
    if event in {"schedule", "workflow_dispatch"}:
        return "create"
    if event == "push" and any(
        re.match(r"^chore(?:\([^)]*\))?: release(?:\s|$)", message.splitlines()[0])
        for message in messages if message
    ):
        return "tag"
    return "skip"


def eligible(message, paths):
    if not paths:
        return False
    title = message.splitlines()[0]
    if re.match(r"^chore(?:\([^)]*\))?: release(?:\s|$)", title):
        return True
    if not re.match(r"^(?:fix|feat|perf|revert)(?:\([^)]*\))?!?:", title):
        return False
    excluded_files = {"renovate.json", "renovate.json5", ".renovaterc.json5"}
    return any(
        not path.startswith((".github/", "docs/"))
        and path not in excluded_files
        for path in paths
    )
