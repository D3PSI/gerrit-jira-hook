'''
        File:           gerrit-jira-hook.py
        Author:         Cedric Schwyter
        Version:        1.0
'''
import os
import sys
import requests
import configparser
import getopt
import logging as log
import jira


log_path = os.path.join(os.path.dirname(__file__), 'hooks.log')
FORMAT = '%(asctime)-12s %(levelname)-8s %(message)s'
log.basicConfig(format=FORMAT, filename=log_path, level=log.DEBUG)

config_path = os.path.join(os.path.dirname(__file__), 'gerrit-jira-hook.config')
config = configparser.RawConfigParser()
config.read(config_path)

JIRA_URL = config.get('gerrit-jira-hook', 'jira_url')
JIRA_USER = config.get('gerrit-jira-hook', 'jira_user')
JIRA_PASS = config.get('gerrit-jira-hook', 'jira_pass')

PROJECTS = config.get('gerrit-jira-hook', 'gerrit_projects')

def show_usage():
    print('\nNormal hook usage: ' + sys.argv[0] + ' --action [new|merged|abandoned] --change <change id> --commit <git hash> --change-url <url to change> --branch <branch name>')


def init():
    try:
        open(log_path, 'a+').close()
        if len(sys.argv) < 2:
            show_usage()
            exit()
        necessary = ['action=', 'change=', 'change-url=', 'commit=',
                    'project=', 'branch=', 'uploader=', 'patchset=',
                    'abandoner=', 'reason=', 'submitter=', 'kind=',
                    'is-draft=', 'change-owner=', 'newrev=', 'topic=']
        optlist, args = getopt.getopt(sys.argv[1:], '', necessary)
        id = ''
        url = ''
        hash = ''
        who = '' 
        topic = ''
        for o, a in optlist:
            if o == '--change':
                id = a
                log.debug("[DEBUG] Optlist Change-ID: " + id)
            elif o == '--change-url':
                url = a
                log.debug("[DEBUG] Optlist Change-URL: " + url)
            elif o == '--commit':
                hash = a
                log.debug("[DEBUG] Optlist Commit-ID (Hash): " + hash)
            elif o == '--action':
                what = a
                log.debug("[DEBUG] Optlist action: " + what)
            elif o == '--uploader':
                who = a
                log.debug("[DEBUG] Optlist uploader (who): " + who)
            elif o == '--submitter':
                who = a
                log.debug("[DEBUG] Optlist submitter (who): " + who)
            elif o == '--abandoner':
                who = a
                log.debug("[DEBUG] Optlist abandoner (who): " + who)
            elif o == '--branch':
                branch = a
                log.debug("[DEBUG] Optlist branch: " + branch)
            elif o == '--topic':
                topic = a
                log.debug("[DEBUG] Optlist topic: " + topic)
        if (len(what) > 0 and len(id) > 0):
            jira_hook(what, id, hash, url, who, branch, topic)
        else:
            show_usage()
    except PermissionError:
        print('Permission Error creating/opening log at "' + log_path + '"')
        raise


def find_issue_identifier(commit_msg):
    return ''


def generate_comment():
    return ''


def jira_hook(what, id, hash, url, who, branch, topic):
    '''
    The main function for the Gerrit-hook to post a comment on a JIRA-ticket 
    with the Change-Id and other information whenever an issue-id is detected in
    a commit-message. The issue-id is extracted from the commig-message by 
    running a regular expression over it and seeing if it matches anything.
    '''
    init()
    log.debug('Executing gerrit-jira-hook...')
    log.debug('Connecting to Jira-instance running at "' + JIRA_URL + '"...')
    try:
        jira_instance = jira.JIRA(JIRA_URL, basic_auth=(JIRA_USER, JIRA_PASS), logging=True)
    except (requests.exceptions.ConnectionError, jira.exceptions.JIRAError) as e:
        log.error('Connection to "' + JIRA_URL + '" as user "' + JIRA_USER
            + '" failed')
        exit(1)
    except requests.exceptions.ConnectTimeout:
        log.error('Connection to "' + JIRA_URL + '" as user "' + JIRA_USER
            + '" timed out')
        exit(1)
    issue_id = find_issue_identifier(topic)
    if issue_id != '':
        log.debug('Generating comment for Issue "' + issue_id + '"...')
        comment = generate_comment()
    else:
        log.debug('No issue-id found, exiting gracefully...')
        exit(0)


if __name__ == "__main__":
    init()
