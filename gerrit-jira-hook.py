'''
        File:           gerrit-jira-hook.py
        Author:         Cedric Schwyter
        Version:        1.0
'''
import os
import logging as log
from jira import JIRA


log_path = os.path.join(os.path.dirname(__file__), 'hooks.log')
file = open(log_path, 'a+').close()
FORMAT = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
log.basicConfig(format=FORMAT, filename=log_path, level=log.DEBUG)


def jira_hook():
    '''
    The main function for the Gerrit-hook to post a comment on a JIRA-ticket 
    with the Change-Id and other information whenever an issue-id is detected in
    a commit-message. The issue-id is extracted from the commig-message by 
    running a regular expression over it and seeing if it matches anything.
    '''
    log.debug('Executing Jira comment hook...')


if __name__ == "__main__":
    jira_hook()