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
from .git.methods import GithubMethods
from .cli.cli import GradeMeCLI


def setup_app_routes(app):
    @app.route('/', methods=['POST'])
    def github_webhook():
        # Enforce IP address
        src_ip = ip_address(
            u'{}'.format(
                request.headers.get('X-Forwarded-For', 
                    request.headers.get('X-Real-IP', request.remote_addr)
                )
            )
        )

        # TODO(gpascualg): Cache this IPs, github won't be constantly changing them
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
            return GithubMethods.github_membership_webhook(payload)
        elif event == 'team_add':
            return GithubMethods.github_team_add_webhook(payload)
        elif event == 'push':
            return GithubMethods.github_push_webhook(payload)
        elif event == 'organization':
            return GithubMethods.github_organization_webhook(payload)

        return json.dumps({"status": "skipped"})


def main():
    # New organizations to use
    parser = argparse.ArgumentParser(description='Classroom AutoGrader')
    parser.add_argument('--github-api-key', help='API key for the master user')
    parser.add_argument('--github-org', action='append', help='Initial Github organitzation(s)', type=str)
    parser.add_argument('--github-org-id', action='append', help='Initial Github organitzation(s)', type=int)
    parser.add_argument('--broadcast-host', default='localhost', help='Docker intercomunnication tool host')
    parser.add_argument('--broadcast-port', type=int, default=6000, help='Docker intercomunication tool port')
    parser.add_argument('--broadcast-secret', type=str, help='Shared secret between dockers')
    parser.add_argument('--mongo-host', default='mongo', help='MongoDB hostname')
    parser.add_argument('--no-github-init', action='store_true', default=False, help='Do not fetch Github data')
    parser.add_argument('--no-cli', action='store_true', help='Do not display CLI')
    parser.add_argument('--host', type=str, default='localhost', help='Server hostname')
    parser.add_argument('--port', type=int, default=80, help='Server port')
    parser.add_argument('--debug', action='store_true', help='Run server in debug mode')    
    args = parser.parse_args()

    # Arguments may be submitted in ENV variables (specially in Docker via docker-compose)
    args_vars = vars(args)
    for arg in args_vars:
        args_vars[arg] = os.environ.get(arg.upper(), args_vars[arg])

    if not args.github_api_key:
        parser.print_help()
        print('The following arguments are required: --github-api-key (or env GITHUB_API_KEY)')
        sys.exit(2)
        
    # Initialize database
    Database.initialize(args.mongo_host)

    # Configure Flask app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'iuy81273ADIwqe2/·gqeWÇQE239qje'

    # Save config and api key
    Database().ensure_configured()
    Database().save_oauth_key(args.github_api_key)

    # Save rabbit credentials
    with open('/run/secrets/rabbit-user') as fp:
        rabbit_username = fp.read()
    with open('/run/secrets/rabbit-pass') as fp:
        rabbit_password = fp.read()

    Database().save_credentials('rabbit', rabbit_username, rabbit_password)
    
    # Create, if not-existing, organizations
    for org in args.github_org_id or []:
        Database().create_organization_if_not_exists(org, 'fake-org-{}'.format(org))

    # Make sure we have all users, admins, etc.
    if not args.no_github_init:        
        # Github API
        g = Github(args.github_api_key)

        orgs = list(set(list(Database().get_organizations_name()) + (args.github_org or [])))
        for org_name in orgs:
            print('Updating organization {}'.format(org_name))

            # Get org and ensure it is created
            org = g.get_organization(org_name)
            Database().create_organization_if_not_exists(org.id, org_name)

            # Update admins
            for admin in org.get_members(role='admin'):
                Database().Try().add_organization_member(org.id, admin.id, admin.name, 'admin')

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

    # Mocking purposes
    if args.github_org_id:
        GithubMethods.MOCK_ORG_ID = args.github_org_id[0]

    # Command line and info
    if not args.no_cli:
        cli = GradeMeCLI(GithubMethods)
        cli.run()
        pool = ThreadPool(1)
        pool.apply_async(cli.run, callback=lambda _: os.kill(os.getpid(), 9))

    # Setup app and run it
    setup_app_routes(app)
    app.run(host=args.host, port=args.port, debug=args.debug)
