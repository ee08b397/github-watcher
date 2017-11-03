import json
import os.path
import time

import unidiff
import requests
from pync import Notifier


GITHUB_API = 'https://api.github.com'
WATCHER_ALERT_LOG = '/tmp/watcher_alert.log'

CONFIG = {
    'akellehe': {
        'fb_calendar': {
            'deploy/': None
        }
    }
}

try:
    with open(os.path.join(os.path.expanduser('~'), '.github'), 'rb') as github_auth_fp:
        oauth_token = github_auth_fp.read().strip()
except IOError as e:
    print "You must store your github access token at ~/.github." 
    print "  1. Go to github.braintreeps.com and"
    print "  2. click your avatar in the top right then"
    print "  3. click Settings then"
    print "  4. click Personal access tokens on the left then"
    print "  5. Generate access token then"
    print "  6. click repo and user permissions checkboxes. next"
    print "  7. click Generate Token. "
    print "  8. SAVE THAT. copy/paste to ~/.github you will never see it again."

headers = {'Authorization': 'token {}'.format(oauth_token)}


def get_open_pull_requests(user, repo):
    resource = GITHUB_API + '/repos/{user}/{repo}/pulls?state=open'.format(
                **{'user': user, 'repo': repo})
    return requests.get(resource, headers=headers).json()


def get_diff(pull_request):
    diff_url = pull_request.get('diff_url')
    return requests.get(diff_url, headers=headers).text


def get_watched_file(user, repo, hunk_path):
    paths = CONFIG.get(user, {}).get(repo, [])
    if not paths:
        return None
    for path in paths:
        if hunk_path == path:
            return path
    return None


def get_watched_directory(user, repo, hunk_path):
    paths = CONFIG.get(user, {}).get(repo, [])
    if not paths:
        return None
    for path in paths:
        if hunk_path.startswith(path):
            return path
    return None


def alert(user, repo, file, range, pr_link):
    msg = 'Found a PR effecting {file} {range}'.format(
	file=file,
	range=str(range))

    Notifier.notify(
	msg,
	title='Github Watcher',
        open=pr_link)


def are_watched_lines(watchpaths, filepath, start, end):
    if filepath not in watchpaths:
        return False
    for watched_start, watched_end in watchpaths[filepath]:
        if watched_start < start < watched_end:
            return True
        if watched_start < end < watched_end:
            return True
    return False


def alert_if_watched_changes(user, repo, patched_file, link, source_or_target='source'):
    filepath = getattr(patched_file, source_or_target + '_file')
    if filepath.startswith('a/') or filepath.startswith('b/'):
        filepath = filepath[2:]

    watched_directory = get_watched_directory(user, repo, filepath)
    if watched_directory and not already_alerted(link):
        alert(user, repo, watched_directory, '', link)
        mark_as_alerted(link)
        return True

    watched_file = get_watched_file(user, repo, filepath)
    if watched_file:
        for hunk in patched_file:
            start = getattr(hunk, source_or_target + '_start')
            offset = getattr(hunk, source_or_target + '_length')
            end = start + offset
            if are_watched_lines(watchpaths, filepath, start, end):
                if not already_alerted(link):
                    alert(user, repo, watched_file, (start, end), link)
                    mark_as_alerted(link)
                return True
    return False


def mark_as_alerted(pr_link):
    with open(WATCHER_ALERT_LOG, 'a+') as fp:
        fp.write(pr_link + '\n')


def already_alerted(pr_link):
    try:
        with open(WATCHER_ALERT_LOG, 'rb') as fp:
            alerted = fp.readlines()
            for line in alerted:
                if pr_link in line:
                    return True
    except IOError as e:
        pass
    return False


if __name__ == '__main__':
    while True:
        for user, repo_watchpaths in CONFIG.items():
            for repo, watchpaths in repo_watchpaths.items():
                open_prs = get_open_pull_requests(user, repo)
                for open_pr in open_prs:
                    link = open_pr.get('_links', {}).get('html', {}).get('href', '')
                    patchset = unidiff.PatchSet.from_string(get_diff(open_pr))
                    for patched_file in patchset:
                        if alert_if_watched_changes(user, repo, patched_file, link, 'source'):
                            continue
                        alert_if_watched_changes(user, repo, patched_file, link, 'target')
        time.sleep(60 * 10) # 10 minutes
