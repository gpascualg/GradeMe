from flask import Flask, request, session, g, abort, render_template, url_for, flash, redirect
from github import Github
from ipaddress import ip_address, ip_network
from multiprocessing.pool import ThreadPool

import argparse
import logging
import requests
import json
import sys
import os

from ..common.database import Database
from ..common.logger import logger, setup_logger
from .git.methods import GithubMethods
from .cli.cli import GradeMeCLI
from .jobs import Jobs


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

        logger.info(f'Received webhook from {src_ip}')

        # TODO(gpascualg): Cache this IPs, github won't be constantly changing them
        whitelist = requests.get('https://api.github.com/meta', verify=False).json()['hooks']

        for valid_ip in whitelist:
            if src_ip in ip_network(valid_ip):
                break
        else:
            logger.critical(f'Webhook from {src_ip} is not whitelisted!')
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
        
        logger.info(f'Webhook event is {event}')

        try:
            if event == 'repository':
                return GithubMethods.repository(payload)
            elif event == 'member':
                return GithubMethods.member(payload)
            elif event == 'membership':
                return GithubMethods.github_membership_webhook(payload)
            elif event == 'team_add':
                return GithubMethods.github_team_add_webhook(payload)
            elif event == 'push':
                return GithubMethods.github_push_webhook(payload)
            elif event == 'organization':
                return GithubMethods.github_organization_webhook(payload)

            return json.dumps({"status": "skipped"})
        except:
            logger.exception("Fatal error in main loop")
            abort(500)

def main(return_app):
    # New organizations to use
    parser = argparse.ArgumentParser(description='Classroom AutoGrader')
    parser.add_argument('--github-api-key', help='API key for the master user')
    parser.add_argument('--github-org', action='append', help='Initial Github organitzation(s)', type=str)
    parser.add_argument('--github-fake-id', action='append', help='Initial Github organitzation(s)', type=int)
    parser.add_argument('--mongo-host', default='mongo', help='MongoDB hostname')
    parser.add_argument('--no-github-init', action='store_true', default=False, help='Do not fetch Github data')
    parser.add_argument('--no-cli', action='store_true', help='Do not display CLI')
    parser.add_argument('--host', type=str, default='localhost', help='Server hostname')
    parser.add_argument('--port', type=int, default=80, help='Server port')
    parser.add_argument('--debug', action='store_true', help='Run server in debug mode')
    parser.add_argument('--debug-log', action='store_true', help='Log debug messages')
    args = parser.parse_args()

    # Logging level
    logging_level = logging.DEBUG if args.debug or args.debug_log else logging.ERROR
    setup_logger(logging_level)

    # Arguments may be submitted in ENV variables (specially in Docker via docker-compose)
    args_vars = vars(args)
    for arg in args_vars:
        args_vars[arg] = os.environ.get(arg.upper(), args_vars[arg])

    if not args.github_api_key:
        parser.print_help()
        logger.critical('The following arguments are required: --github-api-key (or env GITHUB_API_KEY)')
        sys.exit(2)
        
    # Initialize database
    Database.initialize(args.mongo_host)

    # Configure Flask app
    app = Flask(__name__)
    with open('/run/secrets/FLASK_SECRET') as fp:
        app.config['SECRET_KEY'] = fp.read().strip()

    # Save config and api key
    Database().ensure_configured()
    Database().save_oauth_key(args.github_api_key)
    
    # Create, if not-existing, organizations
    for org in args.github_fake_id or []:
        Database().create_organization_if_not_exists(org, 'fake-org-{}'.format(org), fake=True)

    # Make sure we have all users, admins, etc.
    if not args.no_github_init:
        # Github API
        g = Github(args.github_api_key)

        orgs = list(set(list(Database().get_organizations_name()) + (args.github_org or [])))
        for org_name in orgs:
            logger.info(f'Updating organization {org_name}')

            # Get org and ensure it is created
            org = g.get_organization(org_name)
            Database().create_organization_if_not_exists(org.id, org_name)

            # Update members
            for user in org.get_members(role='member'):
                logger.info(f'Updating member {user.login}')
                Database().add_organization_member(org.id, user.id, user.login, 'member')

            # Update admin
            for user in org.get_members(role='admin'):
                logger.info(f'Updating admin {user.login}')
                Database().add_organization_member(org.id, user.id, user.login, 'admin')

            # Fetch collaborators too
            for collab in org.get_outside_collaborators():
                logger.info(f'Updating outside collab {collab.login}')
                Database().add_organization_member(org.id, collab.id, collab.login, 'member')

            # Update teams
            for team in org.get_teams():
                logger.info(f'Updating team {team.name}')

                # TODO: Use updated_at to cache queries
                Database().Try().create_team(org.id, team.id)
                
                for member in team.get_members():
                    Database().Try().add_team_member(org.id, team.id, member.id)

                for repo in team.get_repos():
                    Database().Try().add_team_permission(org.id, team.id, repo.id)

        limits = g.get_rate_limit()
        logger.info(f"API calls: {limits.core.remaining}/{limits.core.limit} - Resets on {limits.core.reset}")

    # Reschedule pending jobs
    logger.info('Rescheduling jobs')
    Database().reschedule_jobs()

    # Mocking purposes
    if args.github_fake_id:
        GithubMethods.MOCK_ORG_ID = args.github_fake_id[0]

    # Command line and info
    if not args.no_cli:
        cli = GradeMeCLI(GithubMethods)
        cli.run()
        pool = ThreadPool(1)
        pool.apply_async(cli.run, callback=lambda _: os.kill(os.getpid(), 9))

    # Setup app and run it
    setup_app_routes(app)

    # Execute jobs in the main worker/thread only
    Jobs()

    if return_app:
        return app

    app.run(host=args.host, port=args.port, debug=args.debug)
