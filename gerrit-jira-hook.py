'''
        File:           gerrit-jira-hook.py
        Author:         Cedric Schwyter
        Version:        1.0
'''
import os
import requests
import configparser
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


def init():
    try:
        open(log_path, 'a+').close()
    except PermissionError:
        print('Permission Error creating/opening log at "' + log_path + '"')
        raise


def find_issue_identifier(commit_msg):
    return ''


def jira_hook():
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
    issue_id = find_issue_identifier('')
    if issue_id != '':
        log.info('Logging into "' + JIRA_URL + '" with user "' + JIRA_USER
            + '"...')
    else:
        log.debug('No issue-id found, exiting gracefully...')
        exit(0)


if __name__ == "__main__":
    jira_hook()
