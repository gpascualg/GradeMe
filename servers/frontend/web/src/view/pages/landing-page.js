import { Col, Grid } from 'construct-ui';
import { route } from '../components/helper';

function color_from_status(status) {
    return 'color-' + ((status) => {
        switch (status) {
            // Fatal cases
            case 'checksum-mismatch':
                return 'red';
            case 'execution-error':
                return 'red';
            case 'missing-yml':
                return 'red';
            case 'unkown-error':
                return 'red';

            // Skipped cases
            case 'branch-mismatch':
                return 'orange';

            // Success
            case 'done':
                return 'green';

            // Unkown
            default:
                return 'red';
        }
    })(status);
}

function is_failed(status) {
    return color_from_status(status) != 'color-green';
}

function printable_date(timestamp) {
    var date = new Date(timestamp * 1000);
    
    var hours = "0" + date.getHours();
    var minutes = "0" + date.getMinutes();
    var day = "0" + date.getDate();
    var month = "0" + date.getMonth();
    var year = date.getFullYear();

    return day.substr(-2) + "/" + month.substr(-2) + "/" + year + " " +
         hours.substr(-2) + ":" + minutes.substr(-2);
}

function toggle(e, repo)
{
    if (repo.height == '0') {
        repo.height = '1000px';
    }
    else {
        repo.height = '0';
    }
}

function printable_users(access_rights) {
    var users = []
    for (var i = 0; i < access_rights.length; ++i)
    {
        if (access_rights[i]['permission'] == 'member') {
            users.push(access_rights[i]['name']);
        }
    }

    return users.join(', ');
}

function setroute(e, repo, ist) {
    m.route.set('/results/' + repo._id.org + '/' + repo._id.repo + '/' + ist.hash);
}

export default function() {
    var repos = [];

    return {
        oninit(vnode) {
            repos = vnode.attrs.repos;
        },
        view() {
            return [
                <h1 key='h1'>Tests: </h1>,
                <Grid key='grid' justify="center">
                    { repos.map((repo) => {
                        return <Col key={ repo.org_name + '/' + repo.name } span={ 12 }>
                            <div className={ 'color-repo' } onclick={ (e) => toggle(e, repo) }>
                                { repo.org_name }/{ repo.name }
                                <div className={ 'timestamp' }>
                                    [{ printable_users(repo.access_rights) }]
                                </div>
                            </div>
                            <Grid key={ repo.org_name + '/' + repo.name + '/instances' } style={ { 'max-height': repo.height || '1000px' } }>
                                {
                                    repo.instances.map((ist) => {
                                        return <Col key={ ist.hash } span={ 12 }>
                                            <div className={ color_from_status(ist.status) } onclick={ (e) => setroute(e, repo, ist) }>
                                                { !is_failed(ist.status) && 
                                                    [x/y] 
                                                }

                                                { ist.title }
                                                <div className={ 'timestamp' }>
                                                    { printable_date(ist.timestamp) }
                                                </div>
                                                { is_failed(ist.status) &&
                                                    <div className='pad-left'>Failure reason: { ist.status }</div>
                                                }
                                            </div>
                                        </Col>
                                    })
                                }
                            </Grid>
                        </Col>;
                    }) }
                </Grid>,
            ];
        },
    };
}
