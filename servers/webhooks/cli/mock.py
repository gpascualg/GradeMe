

def push_webhook(GithubMethods):
    payload = {
        'ref': 'fake-org-{}/GradeMe/dev'.format(GithubMethods.MOCK_ORG_ID),
        'after': 'd5d23c937b135d7c8c92e2af63400918622b0c87',
        'repository': {
            'id': 321,
            'name': 'GradeMe',
            'owner': {
                'id': GithubMethods.MOCK_ORG_ID,
                'name': 'fake-org-{}'.format(GithubMethods.MOCK_ORG_ID)
            }
        },
        'sender': {
            'id': GithubMethods.MOCK_ORG_ID,
            'name': 'fake-org-{}'.format(GithubMethods.MOCK_ORG_ID)
        },
        'commits': [
            {
                'id': 'd5d23c937b135d7c8c92e2af63400918622b0c87',
                'message': 'Wrong network name'
            }
        ]
    }

    return GithubMethods.github_push_webhook(payload)
