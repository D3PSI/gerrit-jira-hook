'''
        File:           gerrit-jira-hook.py
        Author:         Cedric Schwyter
        Version:        1.0
'''
import os
import sys
import re
import requests
import subprocess
import configparser
import getopt
import logging as log
import jira
from urllib.parse import unquote


log_path = os.path.join(os.environ.get('GERRIT_HOME', '/var/gerrit'), 'hooks.log')
FORMAT = '%(asctime)-12s %(levelname)-8s %(message)s'
log.basicConfig(format=FORMAT, filename=log_path, level=log.DEBUG)

config_path = os.path.join(os.environ.get('GERRIT_HOME', '/var/gerrit'), 'gerrit-jira-hook.config')
config = configparser.RawConfigParser()
config.read(config_path)

JIRA_URL = config.get('gerrit-jira-hook', 'jira_url')
JIRA_USER = config.get('gerrit-jira-hook', 'jira_user')
JIRA_PASS = config.get('gerrit-jira-hook', 'jira_pass')
jira_use_field = config.get('gerrit-jira-hook', 'jira_use_field')
if jira_use_field.lower() == 'true':
    JIRA_USE_FIELD = True
    JIRA_FIELD = config.get('gerrit-jira-hook', 'jira_field')
else:
    JIRA_USE_FIELD = False
jira_update_components = config.get('gerrit-jira-hook', 'jira_update_components')
if jira_update_components.lower() == 'true':
    JIRA_UPDATE_COMPONENTS = True
    JIRA_COMPONENT_MAPPINGS = config['gerrit-project-to-jira-component-mappings']
else:
    JIRA_UPDATE_COMPONENTS = False

PROJECTS = config.get('gerrit-jira-hook', 'gerrit_projects').split(',')

GERRIT_USER = config.get('gerrit-jira-hook', 'gerrit_user')
GERRIT_HOST = config.get('gerrit-jira-hook', 'gerrit_host')

COMMENT_TEMPLATE = """Latest change for {issue_id}
*{change_owner_username}* pushed a commit:
{change_url}
Subject: *{subject}*
Project: {project}
Branch: {branch}
Change-Id: {change_id}
Commit: {commit}
This change was reviewed and approved by *{submitter_username}*.
"""
COMMENT_TEMPLATE_REGEX = "Latest change for ([A-Z]+-[0-9]+)"

FIELD_TEMPLATE = "{project}: [{subject}|{change_url}]"

def init():
    try:
        open(log_path, 'a+').close()
        if len(sys.argv) < 2:
            log.error('Insufficient arguments supplied')
            sys.exit()
        arguments = ['change', 'change-url', 'change-owner',
                    'change-owner-username', 'project',
                    'commit', 'branch', 'submitter',
                    'submitter-username', 'newrev', 'topic']
        optlist, args = getopt.getopt(sys.argv[1:], '', [i + '=' for i in arguments])
        values = {}
        for o, a in optlist:
            values[o[2:]] = a
            log.debug('CLI-Option ' + o + ':\t\t' + a)
        values['change'] = unquote(values['change'])
        if PROJECTS[0] == 'All-Projects' or (values['project'] != None and values['project'] in PROJECTS):
            jira_hook(values)
        else:
            log.error('No project found')
            sys.exit(1)
    except PermissionError:
        print('Permission Error creating/opening log at "' + log_path + '"')
        raise


def find_issue_identifiers(change, jira_instance):
    log.debug('Running Gerrit query command...')
    proc = subprocess.Popen('ssh -p 29418 ' + GERRIT_USER + '@' + GERRIT_HOST + ' gerrit query --format TEXT change:' + change + ' limit:1',
        stdout=subprocess.PIPE, shell=True)
    out = proc.communicate()[0].decode()
    if proc.returncode != 0:
        log.error('Failed to run Gerrit query command')
        sys.exit(1)
    else:
        commit_information = {}
        commit_information['subject'] = re.search('subject: (.*)\n', out).group(1)
        log.debug('Change-Id query delivered the following subject result: ' + commit_information['subject'])
        commit_information['project'] = re.search('project: (.*)\n', out).group(1)
        log.debug('Change-Id query delivered the following project result: ' + commit_information['project'])
        log.debug('Detecting issue-id\'s...')
        issues = []
        issue_pattern = '(%s-[0-9]+)'
        projects = jira_instance.projects()
        for project in projects:
            matches = re.findall(issue_pattern % project.key, commit_information['subject'])
            for m in matches:
                log.debug('Found issue-id: ' + m)
                issues.append(m)
        return commit_information, issues


def generate_text(template, values, commit_information, issue_id):
    return template.format(change_owner_username=values['change-owner-username'],
                           change_url='https://build.revendex.com/gerrit/c/' + commit_information['project'] + '/+/' + values['change-url'],
                           issue_id=issue_id,
                           subject=commit_information['subject'],
                           project=commit_information['project'],
                           branch=values['branch'],
                           change_id=values['change'],
                           commit=values['commit'],
                           submitter_username=values['submitter-username'])


def jira_hook(values):
    '''
    The main function for the Gerrit-hook to post a comment on a JIRA-ticket 
    with the Change-Id and other information whenever an issue-id is detected in
    a commit-message. The issue-id is extracted from the commig-message by 
    running a regular expression over it and seeing if it matches anything.
    '''
    log.debug('Executing gerrit-jira-hook...')
    log.debug('Connecting to Jira-instance running at "' + JIRA_URL + '"...')
    try:
        log.debug('Logging in to Jira as user "' + JIRA_USER + '"...')
        jira_instance = jira.JIRA(JIRA_URL, basic_auth=(JIRA_USER, JIRA_PASS), logging=True)
        log.debug('Logged in to Jira')
    except requests.exceptions.ConnectTimeout:
        log.error('Connection to "' + JIRA_URL + '" as user "' + JIRA_USER
            + '" timed out')
        sys.exit(1)
    except (requests.exceptions.ConnectionError, jira.exceptions.JIRAError) as e:
        log.error('Connection to "' + JIRA_URL + '" as user "' + JIRA_USER
            + '" failed')
        log.error(e)
        sys.exit(1)
    commit_information, issue_ids = find_issue_identifiers(values['change'], jira_instance)
    for issue_id in issue_ids:
        log.debug('Generating change information text for issue "' + issue_id + '"...')
        try:
            issue = jira_instance.issue(issue_id)
            log.debug('Updating issue "' + issue_id + '"...')
            if JIRA_USE_FIELD:
                fields = jira_instance.fields()
                field_map = {field['name'] : field['id'] for field in fields}
                field_text = getattr(issue.fields, field_map[JIRA_FIELD])
                field_text_lines = []
                if field_text:
                    for line in field_text.splitlines():
                        if not values['project'] in line.split(':')[0]:
                            field_text_lines.append(line)
                field_text_lines.append(generate_text(FIELD_TEMPLATE, values, commit_information, issue_id))
                field_text = '\n'.join(sorted(field_text_lines))
                issue.update(notify=False, fields={field_map[JIRA_FIELD] : field_text})
            else:
                new_change_text = generate_text(COMMENT_TEMPLATE, values, commit_information, issue_id)
                log.debug('Trying to find and delete old comments on issue...')
                comments = issue.fields.comment.comments
                regex = re.compile(COMMENT_TEMPLATE_REGEX)
                for c in comments:
                    if regex.match(c.body) and re.search('Project: ' + values['project'], c.body):
                        log.debug('Deleting comment...')
                        c.delete()
                        log.debug('Comment deleted')
                log.debug('Posting comment to issue "' + issue_id + '"...')
                jira_instance.add_comment(issue_id, new_change_text)
                log.debug('Posted comment to issue "' + issue_id + '"')
            if JIRA_UPDATE_COMPONENTS:
                new_component_name = JIRA_COMPONENT_MAPPINGS[values['project']]
                components = []
                for component in issue.fields.components:
                    components.append({'name' : component.name})
                if new_component_name not in [c.values() for c in components]:
                    components.append({'name' : new_component_name})
                issue.update(notify=False, fields={'components': components})
            log.debug('Successfully updated issue "' + issue_id + '"')
        except:
            log.error('Failed to update issue "' + issue_id 
                + '". This is bad.\n\n\t\t\t\t\t\t\t\t\t\tV E R Y   B A D.\n')
            raise
    if len(issue_ids) > 0:
        log.debug('Success, exiting gracefully')
    else:
        log.debug('No issue-id found, exiting gracefully...')
        sys.exit(0)


if __name__ == "__main__":
    init()
