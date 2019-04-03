import json

from ...common.database import Database
from ..jobs import Jobs


class GithubMethods(object):
    MOCK_ORG_ID = None

    @staticmethod
    def github_membership_webhook(payload):
        action = payload['action']
        member = payload['member']['id']
        team = payload['team']['id']
        org = payload['organization']['id']

        if action == 'removed':
            Database().remove_team_member(org, team, member)
        elif action == 'added':
            Database().add_team_member(org, team, member)

        return json.dumps({"status": "success"})

    @staticmethod
    def github_team_add_webhook(payload):
        team = payload['team']['id']
        org = payload['repository']['owner']['id']
        repo = payload['repository']['id']
        Database().add_team_permission(org, team, repo)
        
        return json.dumps({"status": "success"})
    
    @staticmethod
    def github_organization_webhook(payload):
        action = payload['action']
        if action == 'member_invited':
            return json.dumps({'status': 'skipped'})
        
        permission = payload['membership']['role']
        if permission != 'admin':
            return json.dumps({'status': 'skipped'})

        member = payload['membership']['user']['id']
        org = payload['organization']['id']

        if action == 'member_added':
            Database().add_organization_member(org, member, permission)
        elif action == 'member_removed':
            Database().remove_organization_member(org, member)

    @staticmethod
    def github_push_webhook(payload):
        # Determining the branch is tricky, as it only appears for certain event
        # types an at different levels
        branch = None
        try:
            # Case 1: a ref_type indicates the type of ref.
            # This true for create and delete events.
            if 'ref_type' in payload:
                if payload['ref_type'] == 'branch':
                    branch = payload['ref']

            # Case 2: a pull_request object is involved. This is pull_request and
            # pull_request_review_comment events.
            elif 'pull_request' in payload:
                # This is the TARGET branch for the pull-request, not the source
                # branch
                branch = payload['pull_request']['base']['ref']

            else:
                # Push events provide a full Git ref in 'ref' and not a 'ref_type'.
                branch = payload['ref'].split('/', 2)[2]

        except KeyError:
            # If the payload structure isn't what we expect, we'll live without
            # the branch name
            pass

        # All current events have a repository, but some legacy events do not
        org = payload['repository']['owner']['id']
        repo = payload['repository']['id']
        author = payload['sender']['id']
        sha = payload['after']

        # The following authors are ignored
        try:
            if Database().get_organization_config(org)['skip_admin_push']:
                if author in Database().get_organization_admins(org):
                    return json.dumps({"status": "skipped"})
        except:
            return json.dumps({"status": "non-existant-org: {}".format(org)})

        # Does this repository already exist?
        if Database().get_repository(org, repo) is None:
            Database().create_repository(org, repo, author)

        # Create a test based on the commit message
        commit = filter(lambda x: x['id'] == sha, payload['commits'])
        message = next(commit)['message']
        Database().create_instance(org, repo, sha, branch, message)

        # This push information into the queue
        Jobs().post({
            'org': {'id': org, 'name': payload['repository']['owner']['name']},
            'repo': {'id': repo, 'name': payload['repository']['name']},
            'branch': branch,
            'hash': sha
        })

        return json.dumps({"status": "success"})
