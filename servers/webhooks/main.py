from flask import Flask, request, session, g, abort, render_template, url_for, flash, redirect
from github import Github
from ipaddress import ip_address, ip_network
from multiprocessing.pool import ThreadPool

import argparse
import requests
import json
import sys
import os

from ..common.database import Database
from ..common.broadcaster import Broadcaster
from .jobs import Jobs
from .cli import GradeMeCLI


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

def github_team_add_webhook(payload):
    team = payload['team']['id']
    org = payload['repository']['owner']['id']
    repo = payload['repository']['id']
    Database().add_team_permission(org, team, repo)
    
    return json.dumps({"status": "success"})
    
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
        return json.dumps({"status": "non-existant-org"})

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


def github_webhook():
    # Enforce IP address
    src_ip = ip_address(
        u'{}'.format(
            request.headers.get('X-Forwarded-For', 
                request.headers.get('X-Real-IP', request.remote_addr)
            )
        )
    )
    whitelist = requests.get('https://api.github.com/meta', verify=False).json()['hooks']

    for valid_ip in whitelist:
        if src_ip in ip_network(valid_ip):
            break
    else:
        abort(403)

    event = request.headers.get('X-GitHub-Event', 'ping')
    if event == 'ping':
        return json.dumps({'msg': 'pong'})
    
    # Gather data
    try:
        payload = request.get_json()
    except Exception:
        abort(400)
        
    if payload is None:
        abort(202)
    
    if event == 'membership':
        return github_membership_webhook(payload)
    elif event == 'team_add':
        return github_team_add_webhook(payload)
    elif event == 'push':
        return github_push_webhook(payload)
    elif event == 'organization':
        return github_organization_webhook(payload)

    return json.dumps({"status": "skipped"})

def simulate_webhook():
    payload = {
        'ref': 'gpascualg/GradeMe/dev',
        'after': 'd5d23c937b135d7c8c92e2af63400918622b0c87',
        'repository': {
            'id': 321,
            'name': 'GradeMe',
            'owner': {
                'id': 123,
                'name': 'gpascualg'
            }
        },
        'sender': {
            'id': 123,
            'name': 'gpascualg'
        },
        'commits': [
            {
                'id': 'd5d23c937b135d7c8c92e2af63400918622b0c87',
                'message': 'Wrong network name'
            }
        ]
    }
    return github_push_webhook(payload)

def main():
    # New organizations to use
    parser = argparse.ArgumentParser(description='Classroom AutoGrader')
    parser.add_argument('--github-api-key', required=True, help='API key for the master user')
    parser.add_argument('--github-org', action='append', help='Initial Github organitzation(s)', type=str)
    parser.add_argument('--github-org-id', action='append', help='Initial Github organitzation(s)', type=int)
    parser.add_argument('--broadcast-host', default='localhost', help='Docker intercomunnication tool host')
    parser.add_argument('--broadcast-port', type=int, default=6000, help='Docker intercomunication tool port')
    parser.add_argument('--broadcast-secret', type=str, help='Shared secret between dockers')
    parser.add_argument('--mongo-host', default='mongo', help='MongoDB hostname')
    parser.add_argument('--no-github-init', action='store_true', default=False, help='Do not fetch Github data')
    parser.add_argument('--host', type=str, default='localhost', help='Server hostname')
    parser.add_argument('--port', type=int, default=80, help='Server port')
    parser.add_argument('--debug', action='store_true', help='Run server in debug mode')
    args = parser.parse_args()

    # Arguments may be submitted in ENV variables (specially in Docker via docker-compose)
    args_vars = vars(args)
    for arg in args_vars:
        args_vars[arg] = os.environ.get(arg.upper(), args_vars[arg])

    # Create databse it now
    Database.initialize(args.mongo_host)

    # Start broadcaster
    Broadcaster().run(args.broadcast_host, args.broadcast_port, args.broadcast_secret.encode('utf-8'))

    # Configure Flask app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'iuy81273ADIwqe2/·gqeWÇQE239qje'

    # Save config and api key
    Database().ensure_configured()
    Database().save_oauth_key(args.github_api_key)
    
    # Create, if not-existing, organizations
    for org in args.github_org_id or []:
        Database().create_organization_if_not_exists(org)

    # Make sure we have all users, admins, etc.
    if not args.no_github_init:        
        # Github API
        g = Github(args.github_api_key)

        orgs = list(set(list(Database().get_organizations()) + args.github_org))
        for org_name in orgs:
            print('Updating organization {}'.format(org_name))

            # Get org and ensure it is created
            org = g.get_organization(org_name)
            Database().create_organization_if_not_exists(org.id)

            # Update admins
            for admin in org.get_members(role='admin'):
                Database().Try().add_organization_member(org.id, admin.id, 'admin')

            # Update teams
            for team in org.get_teams():
                print('\tUpdating team {}'.format(team.name))

                # TODO: Use updated_at to cache queries
                Database().Try().create_team(org.id, team.id)
                
                for member in team.get_members():
                    Database().Try().add_team_member(org.id, team.id, member.id)

                for repo in team.get_repos():
                    Database().Try().add_team_permission(org.id, team.id, repo.id)

        limits = g.get_rate_limit()
        print("\nRemaining API calls")
        print(limits.core.limit)
        print(limits.core.remaining)
        print(limits.core.reset)

    # Command line and info
    cli = GradeMeCLI(
        on_run_webhook=simulate_webhook
    )
    pool = ThreadPool(1)
    pool.apply_async(cli.run, callback=lambda _: os.kill(os.getpid(), 9))

    # Done
    app.run(host=args.host, port=args.port, debug=args.debug)
