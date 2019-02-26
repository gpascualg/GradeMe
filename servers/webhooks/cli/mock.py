

def push_webhook(GithubMethods):
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

    return GithubMethods.github_push_webhook(payload)
