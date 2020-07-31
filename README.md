# gerrit-jira-hook

A hook for our company's legacy Gerrit to integrate Change-Id's into Jira >=v7.0

## Dependencies

This hook runs on Python 3 only. It requires the Gerrit hook plugin to be installed and active. Install the dependencies with:

    pip install -r requirements.txt

## Installation

Navigate to the Gerrit instance's Gerrit directory (usually in `/var/gerrit/`). This directory will be referred to as `$GERRIT_HOME`.

### 1. Installing the hook

Simply copy the `gerrit-jira-hook`- and the corresponding `gerrit-jira-hook.config`-file to `$GERRIT_HOME/hooks`. Verify that the executable actually has the correct permissions and ownership to be able to run. That's it. Simple as that.

### 2. Configuring the hook

Configure the hook by setting the appropriate values in `gerrit-jira-hook.config` for the Jira connection:

    [gerrit-jira-hook]
        jira_url = https://jira.example.com             # The remote Jira server instance
        jira_user = username                            # A Jira user with permission to add comments to tickets
        jira_pass = access_token/password               # A Jira API access token
        gerrit_user = gerrit_jira                       # A user with full SSH access to Gerrit
        gerrit_projects = All-Projects                  # Run hook for all projects
        # OR:
        gerrit_projects = project1,project2,project3    # Run hook only for certain projects

The `gerrit_user` must be a user with full SSH access to Gerrit. It must be configured to have access via authorized public key.

### 3. Enabling the hook

Add the following configuration to `$GERRIT_HOME/etc/gerrit.config`:

    [hooks]
        path = $GERRIT_HOME/hooks
        changeMergedHook = gerrit-jira-hook

You should now see a comment being added to a Jira ticket whenever the corresponding valid Jira Issue-Id is found in the commit message.
Enjoy!
