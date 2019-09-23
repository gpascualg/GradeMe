from pymongo import MongoClient, ASCENDING
from datetime import datetime

import random
import string
import itertools
import re
import threading

from ..docker.singleton import ThreadedSingleton


CACHES = {}

def cache(key):
    def impl(f):
        def wrapper(self, *args, **kwargs):
            if args not in CACHES[key]:
                CACHES[key][args] = f(self, *args, **kwargs)
            return CACHES[key][args]

        CACHES[key] = {}
        return wrapper

    return impl

def clear_cache(key):
    if not key in CACHES:
        return
        
    CACHES[key] = {}

def clear_caches():
    for key in CACHES:
        clear_cache(key)

class Database(object, metaclass=ThreadedSingleton):
    __host = None

    @staticmethod
    def initialize(host):
        Database.__host = host
    
    def __init__(self):
        # Connect
        self.client = MongoClient(Database.__host)
        self.db = self.client.autograder
        self.client.server_info()

        # Save collections
        self.config = self.db.config
        self.repos = self.db.repositories
        self.users = self.db.users
        self.teams = self.db.teams
        self.sessions = self.db.sessions
        self.orgs = self.db.organizations
        self.jobs = self.db.jobs

    @cache('config')
    def get_config(self):
        return self.config.find_one()

    def ensure_configured(self):
        config = self.config.find_one()
        if not config:
            config = {
                'oauth_token': None,
                'parallel_jobs': 1
            }
            self.config.insert_one(config)
            clear_cache('config')

    def save_oauth_key(self, key):
        config = self.config.find_one()
        self.config.update_one(
            {'_id': config['_id']}, 
            {'$set': {'oauth_token': key}}
        )
        clear_cache('config')

    def save_credentials(self, host, username, password):
        config = self.config.find_one()
        self.config.update_one(
            {'_id': config['_id']}, 
            {
                '$set': {
                    'credentials': {
                        host: {
                            'username': username,
                            'password': password
                        }
                    }
                }
            }
        )
    
    def get_credentials(self, host):
        return self.config.find_one()['credentials'].get(host)

    def create_organization_if_not_exists(self, org_id, org_name, fake=False):
        if not self.get_organization_config(org_id):
            self.orgs.insert_one({
                '_id': org_id,
                'name': org_name,
                'secret': ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16)),
                'skip_admin_push': True,
                'fake': fake
            })

            clear_cache('orgs')
            clear_cache('org/config')

    @cache('orgs')
    def get_organizations(self):
        return (o['_id'] for o in self.orgs.find({}))

    @cache('orgs/name')
    def get_organizations_name(self, skip_false=True):
        if skip_false:
            return (o['name'] for o in self.orgs.find({'fake': False}))
        return (o['name'] for o in self.orgs.find({}))

    @cache('org/name')
    def get_organization_name(self, id):
        org = self.orgs.find_one({'_id': id})
        if org:
            return org['name']
        return '<not-found>'

    @cache('org/config')
    def get_organization_config(self, org):
        return self.orgs.find_one(
            {'_id': org},
            {'_id': 0}
        )

    @cache('org/config')
    def get_organization_config_by_name(self, org):
        return self.orgs.find_one(
            {'name': org},
            {'_id': 0}
        )

    @cache('org/admin')
    def get_organization_admins(self, org):
        return (u['_id'] for u in \
            self.users.find({'orgs': {'id': org, 'admin': True}}))

    def add_organization_member(self, org, member, name, permission):
        result = self.users.update_one(
            {'_id': member},
            {
                '$addToSet':
                {
                    'orgs': 
                    {
                        'id': org,
                        permission: True
                    }
                }
            }
        )

        if result.matched_count == 0:
            self.users.insert_one(
                {
                    '_id': member,
                    'name': name,
                    'orgs': [
                        {
                            'id': org,
                            permission: True
                        }
                    ],
                    'oauth': ''
                }
            )

        if permission == 'admin':
            clear_cache('org/admin')

    def remove_organization_member(self, org, member):
        self.users.update_one(
            {'_id': member},
            {
                '$pull':
                {
                    'orgs.id': org
                }
            }
        )
    
    def get_repository(self, org, repo):
        return self.repos.find_one(
            {'_id.org' : org, '_id.repo': repo}
        )

    def get_user(self, id):
        return self.users.find_one(
            {'_id': id}
        )

    def get_user_by_name(self, name):
        return self.users.find_one(
            {'name': re.compile(re.escape(name), re.IGNORECASE)}
        )

    def get_teams(self, org, repo):
        return self.teams.find(
            {'_id.org': org, 'repos': repo}
        )

    def create_team(self, org, team):
        self.teams.insert_one({
            '_id' :
            {
                'org': org,
                'team': team
            },
            'members': [],
            'permissions': []
        })

    def add_team_member(self, org, team, member):
        self.teams.update(
            {'_id.org': org, '_id.team': team},
            {
                '$addToSet':
                {
                    'members': member
                }
            }
        )

    def remove_team_member(self, org, team, member):
        self.teams.update(
            {'_id.org': org, '_id.team': team},
            {
                '$pull':
                {
                    'members': member
                }
            }
        )

    def add_team_permission(self, org, team, repo):
        self.teams.update(
            {'_id.org': org, '_id.team': team},
            {
                '$addToSet':
                {
                    'permissions': repo
                }
            }
        )

    def user_instances(self, user, search):
        orgs_where_admin = self.users.find_one(
            {'_id' : user, 'orgs.admin' : True},
            {'orgs' : 1}
        )
        orgs_where_admin = orgs_where_admin or {'orgs': []}
        orgs_where_admin = [org['id'] for org in orgs_where_admin['orgs'] if org.get('admin')]
        
        search_query = {
            '$or': 
            [
                { 'access_rights.id': user },
                *[{ '_id.org' : x } for x in orgs_where_admin]
            ]
        }

        if search is not None:
            user_id = self.get_user_by_name(search)
            if user_id is None:
                # TODO(gpascualg): Search NIUB -> id
                return []

            search_query = {
                '$and': [
                    search_query,
                    {
                        'access_rights.id': user_id['_id']
                    }
                ]
            }

        user_repos = self.repos.find(
            search_query,
            {
                '_id': 1,
                'name': 1,
                'instances': {'$slice': 10}, # TODO(gpascualg): Make this limit configurable
                'access_rights': 1
            }
        )
        user_repos = user_repos.sort([('instances.0.timestamp', -1)]) # Sort by newest repos
        user_repos = user_repos.limit(10) # Up to 10 only

        return list(parse_instances(user, user_repos, filter_out=('log', 'results')))

    def instance_result(self, user, org, repo, hash):
        orgs_where_admin = self.users.find_one(
            {'_id' : user, 'orgs.admin' : True},
            {'orgs' : 1}
        )
        orgs_where_admin = orgs_where_admin or {'orgs': []}
        orgs_where_admin = [org['id'] for org in orgs_where_admin['orgs'] if org.get('admin')]

        instance = self.repos.find_one(
            {
                '$and' : 
                [
                    {
                        '$or': 
                        [
                            { 'access_rights.id': user },
                            *[{ '_id.org' : x } for x in orgs_where_admin]
                        ]
                    },
                    {
                        '_id.org': org,
                        '_id.repo': repo,
                        'instances.hash' : hash
                    }
                ]
            },
            {
                '_id': 1,
                'name': 1,
                'instances.$': 1,
                'access_rights': 1
            }
        )

        if instance:
            instance = next(parse_instances(user, [instance], filter_out=('log')))

            if user not in self.get_organization_admins(org):
                filter_results(instance['instances'][0]['results'])

        return instance

    def create_repository(self, org, repo, name, pusher):
        # Search if repo has any team
        access_rights = []

        for team in self.get_teams(org, repo):
            for username in team['users']:
                access_rights.append({
                    'id': username,
                    'permission': 'member'
                })

        # Always add pusher
        if all(p['id'] != pusher for p in access_rights):
            access_rights = [{'id': pusher, 'permission': 'member'}]

        self.repos.insert_one(
            {
                '_id': 
                {
                    'org': org,
                    'repo': repo
                },
                'name': name,
                'access_rights': access_rights,
                'instances': [],
                'daily_usage': {}
            }
        )

    def remove_repository(self, org, repo, pusher):
        self.repos.delete_one({
            '_id.org': org,
            '_id.repo': repo
        })

    def update_daily_usage(self, org, repo, daily_usage):
        self.repos.update(
            {
                '_id.org': org,
                '_id.repo': repo
            },
            {
                '$set': 
                {
                    'daily_usage': daily_usage
                }
            }
        )

    def add_member_to_repo(self, org, repo, member):
        self.repos.update(
            {'_id.org': org, '_id.repo': repo},
            {
                '$addToSet':
                {
                    'access_rights': {'id': member, 'permission': 'member'}
                }
            }
        )

    def remove_member_from_repo(self, org, repo, member):
        self.repos.update(
            {'_id.org': org, '_id.repo': repo},
            {
                '$pull':
                {
                    'access_rights': {'id': member, 'permission': 'member'}
                }
            }
        )

    def get_instance(self, org, repo, hash, branch):
        return self.repos.find_one(
            {
                '_id.org': org,
                '_id.repo': repo,
                'instances.hash': hash,
                'instances.branch': branch
            },
            {
                '_id': 1,
                'daily_usage': 1,
                'instances.$': 1
            }
        )

    def create_instance(self, org, repo, hash, branch, title):
        self.repos.update_one(
            { '_id.org': org, '_id.repo': repo },
            { 
                '$push': 
                {
                    'instances': 
                    {
                        '$each': [{
                            'hash': hash,
                            'branch': branch,
                            'title': title,
                            'log': None,
                            'results': [],
                            'status': 'pending',
                            'timestamp': int(datetime.timestamp(datetime.now()))
                        }],
                        '$sort': {'timestamp': -1}
                    }
                }
            }
        )

    def update_instance(self, org, repo, hash, branch, status, results=[]):
        self.repos.update_one(
            {
                '_id.org': org,
                '_id.repo': repo,
                'instances.hash': hash,
                'instances.branch': branch
            },
            {
                '$set':
                {
                    'instances.$.results': results,
                    'instances.$.status': status
                }
            }
        )

    def set_instance_log(self, org, repo, hash, branch, log):
        self.repos.update_one(
            {
                '_id.org': org,
                '_id.repo': repo,
                'instances.hash': hash,
                'instances.branch': branch
            },
            {
                '$set':
                {
                    'instances.$.log': log,
                }
            }
        )

    def update_oauth(self, id, oauth):
        result = self.users.update_one(
            {'_id': id},
            {
                '$set': 
                {
                    'oauth': oauth
                }
            }
        )
        return result.matched_count == 1

    def user_by_oauth(self, oauth):
        return self.users.find_one({'oauth': oauth})

    def user(self, id):
        return self.users.find_one({'_id': id})

    def push_job(self, meta):
        self.jobs.insert_one(
            { 
                '_id':
                {
                    'org': meta['org']['id'],
                    'repo': meta['repo']['id'],
                    'hash': meta['hash']
                },
                **meta,
                'timestamp': int(datetime.timestamp(datetime.now())),
                'status': 'pending'
            }
        )

    def get_job(self):
        return self.jobs.find_one_and_update(
            {'status': 'pending'},
            {'$set': {'status': 'processing'}},
            sort=[('timestamp', 1)]
        )

    def remove_job(self, meta):
        self.jobs.delete_one(
            {
                '_id':
                {
                    'org': meta['org']['id'],
                    'repo': meta['repo']['id'],
                    'hash': meta['hash']
                }
            }
        )

    def reschedule_jobs(self):
        self.jobs.update_many({}, {'$set': {'status': 'pending'}})
        
    # def is_user_admin(self, user):
    #     return (u['_id'] for u in \
    #         self.users.find({'_id': user, 'orgs.admin': True}))

    def Try(self):
        def wrap(f):
            def _wrap(*args, **kwargs):
                try:
                    return f(*args, **kwargs)
                except:
                    return None

            return _wrap
        
        class Wrapper(object):
            def __getattribute__(other, name):
                fun = object.__getattribute__(self, name)
                return wrap(fun)

        return Wrapper()


# Merge into single objects
def parse_instances(user, user_repos, filter_out=('log',)):
    for repo in user_repos:
        # Get name
        repo['org_name'] = Database().get_organization_name(repo['_id']['org'])

        # Set scores
        for instance in repo['instances']:
            is_admin = user in Database().get_organization_admins(repo['_id']['org'])
            score, total = calc_score(instance['results'], is_admin)
            instance['score'] = score
            instance['total'] = total

        # Sort and filter instances
        repo['instances'] = sorted(repo['instances'], key=lambda instance: instance['timestamp'], reverse=True)
        repo['instances'] = [{k: v for k, v in ins.items() if k not in filter_out} for ins in repo['instances']]

        # Get usernames
        for ar in repo['access_rights']:
            user = Database().user(ar['id'])
            if user is not None:
                ar['name'] = user['name']
            else:
                ar['name'] = ar['id']

        yield repo

# Filter results if not admin
def filter_results(results):
    for section in results:
        del section['score']['private'] # No private

        public_tests = [test for test in section['tests'] if test['public']]

        for test in public_tests:
            if not test['is_score_public']:
                del test['score']
                del test['max_score'] # Should we make it public?

            if test['hide_details']:
                del test['details']
            
        section['tests'] = public_tests

def calc_score(results, is_admin):
    score = 0
    total = 0

    for section in results:
        if 'score' not in section:
            # It is an import error
            # TODO(gpascualg): If type!=1
            continue
        
        obj = section['score']['private' if is_admin else 'public']['numeric']
        score += obj['score']
        total += obj['total']
    
    return score, total
