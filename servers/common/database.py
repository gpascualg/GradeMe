from pymongo import MongoClient, ASCENDING
import random
import string


CACHES = {}

def cache(f):
    def wrapper(self, *args, **kwargs):
        if args not in CACHES[f]:
            CACHES[f][args] = f(self, *args, **kwargs)
        return CACHES[f][args]

    CACHES[f] = {}
    return wrapper


class Database(object):
    __instance = None
    __host = None

    @staticmethod
    def initialize(host):
        Database.__host = host

    def __new__(cls):
        if Database.__instance is None:
            Database.__instance = object.__new__(cls)
            
        return Database.__instance

    def __init__(self):
        # Connect
        self.db = MongoClient(Database.__host).autograder

        # Save collections
        self.config = self.db.config
        self.repos = self.db.repositories
        self.users = self.db.users
        self.teams = self.db.teams
        self.sessions = self.db.sessions
        self.orgs = self.db.organizations

    def __clear_cache(self, f):
        if not f in CACHES:
            return
        
        if isinstance(CACHES[f], (list, dict)):
            CACHES[f] = type(CACHES[f])()
        else:
            CACHES[f] = None

    def __clear_caches(self):
        for f in CACHES:
            self.__clear_cache(f)

    @cache
    def get_config(self):
        return self.config.find_one()

    def create_organization_if_not_exists(self, org):
        if not self.get_organization_config(org):
            self.orgs.insert_one({
                '_id': org,
                'secret': ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16)),
                'skip_admin_push': True
            })

            self.__clear_cache(self.get_organizations)

    @cache
    def get_organizations(self):
        return (o['_id'] for o in self.orgs.find({}))

    @cache
    def get_organization_config(self, org):
        return self.orgs.find_one(
            {'_id': org},
            {'_id': 0}
        )

    @cache
    def get_organization_admins(self, org):
        return (u['_id'] for u in \
            self.users.find({'orgs': {'name': org, 'permission': 'admin'}}))

    def add_organization_member(self, org, member, permission):
        result = self.users.update_one(
            {'_id': member},
            {
                '$addToSet':
                {
                    'orgs': 
                    {
                        'name': org,
                        'permission': permission
                    }
                }
            }
        )

        if result.modified_count == 0:
            self.users.insert_one(
                {
                    '_id': member,
                    'orgs': [
                        {
                            'name': org,
                            'permission': permission
                        }
                    ]
                }
            )

        if permission == 'admin':
            self.__clear_cache(self.get_organization_admins)

    def remove_organization_member(self, org, member):
        self.users.update_one(
            {'_id': member},
            {
                '$pull':
                {
                    'orgs.name': org
                }
            }
        )
    
    def get_repository(self, org, repo):
        return self.repos.find_one(
            {'_id.org' : org, '_id.repo': repo}
        )

    def get_user(self, username):
        return self.users.find_one(
            {'_id': username}
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

    def create_repository(self, org, repo, pusher):
        # Search if repo has any team
        access_rights = []

        for team in self.get_teams(org, repo):
            for username in team['users']:
                access_rights.append({
                    'name': username,
                    'permission': 'user'
                })

        # Always add pusher
        if all(p['name'] != pusher for p in access_rights):
            access_rights = [{'name': pusher, 'permission': 'user'}]

        self.repos.insert_one(
            {
                '_id': 
                {
                    'org': org,
                    'repo': repo
                },
                'access_rights': access_rights,
                'instances': [],
                'daily_usage': {}
            }
        )

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
                'max_per_day': 1,
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
                        'hash': hash,
                        'branch': branch,
                        'title': title,
                        'log': None,
                        'results': [],
                        'status': 'pending'
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
